"""Run the pilot.

    python run_pilot.py --suggest-models          # list current OpenRouter models by lab
    python run_pilot.py --mock --limit 3          # offline smoke test of the whole harness
    python run_pilot.py --dry-run                 # 1 task per type, all conditions, real models
    python run_pilot.py                           # the full run (resumable; rerun to continue)
    python report.py                              # write results/report.md

Conditions (paper, Pilot design):
  a  best single frontier model, one pass
  b  same model given the panel's token budget: k samples, majority vote
     (or self-review for code), then a self-critique pass
  c  the panel with the hub
  d  the panel with the hub removed
"""
import argparse, json, os, random, statistics, sys, time, zlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import checkers, panel, task_bank
from backend import Accounting, MockBackend, OpenRouterBackend
from panel import P, Seat

RESULTS = "results"


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    for k in ("seats", "hub", "baseline"):
        if k not in cfg:
            raise SystemExit(f"config is missing '{k}'")
    if "REPLACE" in json.dumps(cfg):
        raise SystemExit("config.json still has REPLACE-ME placeholders: run --suggest-models and pin real model ids")
    return cfg


def result_path(cond, tid):
    return os.path.join(RESULTS, cond, tid + ".json")


def load_results(cond):
    d = os.path.join(RESULTS, cond)
    out = {}
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".json"):
                with open(os.path.join(d, fn)) as f:
                    r = json.load(f)
                out[r["task_id"]] = r
    return out


def save_result(r):
    os.makedirs(os.path.dirname(result_path(r["condition"], r["task_id"])), exist_ok=True)
    with open(result_path(r["condition"], r["task_id"]), "w") as f:
        json.dump(r, f, indent=1)


def make_seats(cfg):
    seats = []
    for i, s in enumerate(cfg["seats"]):
        seats.append(Seat(letter=panel.LETTERS[i], model=s["model"], label=s.get("label", s["model"]), weight=float(s.get("weight", 1.0)),
                          tier_class=s.get("class", cfg.get("tier", "mid")), lens=s.get("lens", "")))
    return seats


def majority(values):
    counts = {}
    for v in values:
        if v is None:
            continue
        counts[v] = counts.get(v, 0) + 1
    if not counts:
        return None
    best = max(counts.values())
    for v in values:  # first among the tied
        if v is not None and counts[v] == best:
            return v


# ------------------------------------------------------------ conditions ----
def run_a(task, cfg, api, ctx):
    text = api.chat(cfg["baseline"], P.baseline_system, task["prompt"], cfg.get("baseline_temperature", 0.3), ctx=dict(ctx, step="single-pass"))
    return {"answer": text}


def run_b(task, cfg, api, ctx, k):
    """Compute-matched single model: k samples, then majority vote (numbers,
    strings) or a self-review pick (code), then one self-critique pass."""
    model = cfg["baseline"]
    samples = panel.pool([(lambda: api.chat(model, P.baseline_system, task["prompt"], cfg.get("sample_temperature", 0.7), ctx=dict(ctx, step="sample"))) for _ in range(k)], 4)
    if task["answer_type"] == "code":
        cands = "\n\n".join(f"Candidate {i + 1}:\n{s}" for i, s in enumerate(samples))
        review = (f"Request:\n{task['prompt']}\n\nYou wrote these candidate answers earlier:\n{cands}\n\n"
                  "Pick the best candidate, checking each against the visible examples by hand, and fix any bug you find. "
                  "Reply with the final complete function in one ```python code block.")
        winner = api.chat(model, P.baseline_system, review, 0.3, ctx=dict(ctx, step="self-review"))
        key = None
    else:
        keys = [checkers.norm_string(checkers.extract_final(s)) for s in samples]
        if task["answer_type"] == "number":
            keys = [None if checkers.parse_number(kk) is None else round(checkers.parse_number(kk), max(2, int(task.get("precision", 0)))) for kk in keys]
        key = majority(keys)
        winner = next((s for s, kk in zip(samples, keys) if kk == key), samples[0])
    critique = (f"Request:\n{task['prompt']}\n\nYour answer:\n{winner}\n\n"
                "Check this answer for errors step by step: recompute every figure, re-read the question for anything missed, and test code against the visible examples by hand. "
                "Then give the final answer in the format the request asks for (a FINAL: line, or one ```python block).")
    final = api.chat(model, P.baseline_system, critique, 0.3, ctx=dict(ctx, step="self-critique"))
    return {"answer": final, "k": k, "majority_key": key, "samples": samples}


def run_panel_cond(task, cfg, api, ctx, with_hub, catalogue, seed):
    pcfg = {"seats": make_seats(cfg), "hub": cfg["hub"] if with_hub else None, "rounds": int(cfg.get("rounds", 3)),
            "hub_budget": int(cfg.get("hub_budget", 6)), "dissenter": bool(cfg.get("dissenter", True)), "tier": cfg.get("tier", "mid"),
            "catalogue": catalogue, "rng": random.Random(seed), "ctx": ctx}
    return panel.run_panel(task["prompt"], pcfg, api, task=task, prelude=task_bank.TEST_PRELUDE)


# ------------------------------------------------------------------ main ----
def suggest_models(api):
    models = api.list_models()
    labs = ["anthropic/", "openai/", "google/", "x-ai/", "deepseek/", "meta-llama/", "mistralai/", "qwen/", "amazon/", "cohere/"]
    for lab in labs:
        ms = [m for m in models if m.get("id", "").startswith(lab)]
        ms.sort(key=lambda m: -(m.get("created") or 0))
        if not ms:
            continue
        print(f"\n{lab}")
        for m in ms[:6]:
            pr = m.get("pricing") or {}
            try:
                pin, pout = float(pr.get("prompt", 0)) * 1e6, float(pr.get("completion", 0)) * 1e6
            except (TypeError, ValueError):
                pin = pout = 0
            created = time.strftime("%Y-%m-%d", time.gmtime(m.get("created") or 0))
            print(f"  {m['id']:<48} {created}  ${pin:6.2f}/M in  ${pout:7.2f}/M out  ctx {m.get('context_length')}")
    print("\nPin exact ids in config.json; the run records them as the version stamps for the catalogue.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--tasks", default="tasks/fresh_tasks.json")
    ap.add_argument("--conditions", default="a,c,d,b", help="order matters: b is sized from c")
    ap.add_argument("--limit", type=int, default=0, help="tasks per type (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="1 task per type")
    ap.add_argument("--mock", action="store_true", help="offline mock backend")
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--suggest-models", action="store_true")
    a = ap.parse_args()

    os.makedirs(RESULTS, exist_ok=True)
    acc = Accounting(os.path.join(RESULTS, "calls.jsonl"))
    with open(a.tasks) as f:
        tasks = json.load(f)["tasks"]

    if a.mock:
        cfg = {"seats": [{"model": "mock/seat-1"}, {"model": "mock/seat-2"}, {"model": "mock/seat-3"}], "hub": "mock/hub", "baseline": "mock/frontier",
               "rounds": 2, "hub_budget": 4, "dissenter": True, "tier": "mid", "task_workers": 4}
        api = MockBackend(tasks, acc, quality={"frontier": 0.75, "hub": 0.9, "seat": 0.6}, seed=a.seed)
    else:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise SystemExit("set OPENROUTER_API_KEY first (openrouter.ai -> Keys)")
        cfg = load_config(a.config) if not a.suggest_models else {"seats": [], "hub": "", "baseline": ""}
        api = OpenRouterBackend(key, acc)
        if a.suggest_models:
            suggest_models(api)
            return

    limit = 1 if a.dry_run else a.limit
    if limit:
        chosen, seen = [], {}
        for t in tasks:
            if seen.get(t["type"], 0) < limit:
                chosen.append(t); seen[t["type"]] = seen.get(t["type"], 0) + 1
        tasks = chosen
    workers = a.workers or int(cfg.get("task_workers", 2))
    conds = [c.strip() for c in a.conditions.split(",") if c.strip()]

    # version stamps for the run
    with open(os.path.join(RESULTS, "run_meta.json"), "w") as f:
        json.dump({"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "config": cfg, "tasks_file": a.tasks, "n_tasks": len(tasks), "conditions": conds, "mock": a.mock}, f, indent=1)

    cat_path = os.path.join(RESULTS, "catalogue.json")
    catalogue = json.load(open(cat_path)) if os.path.exists(cat_path) else {}

    for cond in conds:
        done = load_results(cond)
        todo = [t for t in tasks if t["id"] not in done]
        print(f"\n== condition {cond}: {len(done)} done, {len(todo)} to run")
        k_by_type = {}
        if cond == "b":
            res_a, res_c = load_results("a"), load_results("c")
            for ttype in {t["type"] for t in tasks}:
                ta = [r["tokens"] for r in res_a.values() if r["type"] == ttype and r.get("tokens")]
                tc = [r["tokens"] for r in res_c.values() if r["type"] == ttype and r.get("tokens")]
                if ta and tc:
                    k_by_type[ttype] = max(3, min(12, round(statistics.median(tc) / max(1, statistics.median(ta)))))
                else:
                    k_by_type[ttype] = int(cfg.get("default_k", 5))
            print("   compute-matched k per type:", k_by_type)

        def one(task, cond=cond):
            ctx = {"task": task["id"], "condition": cond}
            t0 = time.time()
            try:
                if cond == "a":
                    out = run_a(task, cfg, api, ctx)
                elif cond == "b":
                    out = run_b(task, cfg, api, ctx, k_by_type[task["type"]])
                elif cond == "c":
                    out = run_panel_cond(task, cfg, api, ctx, True, catalogue, a.seed + zlib.crc32(task["id"].encode()) % 10000)
                elif cond == "d":
                    out = run_panel_cond(task, cfg, api, ctx, False, catalogue, a.seed + zlib.crc32(task["id"].encode()) % 10000)
                else:
                    raise SystemExit(f"unknown condition {cond}")
                err = None
            except Exception as e:  # keep going; the task is recorded as failed and can be rerun
                out, err = {"answer": ""}, f"{type(e).__name__}: {e}"[:500]
            usage = acc.take(task["id"], cond)
            ok, detail = checkers.score(task, out.get("answer", ""), task_bank.TEST_PRELUDE)
            rec = {"task_id": task["id"], "type": task["type"], "condition": cond, "correct": bool(ok) and not err, "detail": detail, "error": err,
                   "seconds": round(time.time() - t0, 1), "tokens": usage["prompt_tokens"] + usage["completion_tokens"],
                   "prompt_tokens": usage["prompt_tokens"], "completion_tokens": usage["completion_tokens"], "cost": round(usage["cost"], 5), "calls": usage["calls"], "call_errors": usage["errors"]}
            if cond in ("c", "d"):
                pre_ok, _ = checkers.score(task, out.get("pre_hub_answer", ""), task_bank.TEST_PRELUDE) if not err else (False, "")
                rec.update({"pre_hub_correct": bool(pre_ok), "agreed": out.get("agreed"), "rounds_used": out.get("rounds_used"), "gates": out.get("gates"), "shipped": out.get("shipped"),
                            "hub_questions": out.get("hub_questions"), "hub_open": out.get("hub_open"), "hub_sent_back": out.get("hub_sent_back"), "hub_corrected": out.get("hub_corrected"),
                            "checks": out.get("checks"), "author": out.get("author"), "seats": out.get("seats"), "log": out.get("log")})
            if cond == "b":
                rec.update({"k": out.get("k"), "majority_key": out.get("majority_key")})
            rec["answer"] = out.get("answer", "")
            save_result(rec)
            return rec

        if todo:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(one, t): t for t in todo}
                for fut in as_completed(futs):
                    r = fut.result()
                    flag = "ok " if r["correct"] else ("ERR" if r["error"] else "no ")
                    print(f"   [{flag}] {r['task_id']:<8} {r['type']:<5} tokens {r['tokens']:>7}  ${r['cost']:.4f}  {r['seconds']:>6}s  {r['detail'][:70]}")
            with open(cat_path, "w") as f:
                json.dump(catalogue, f, indent=1)
        allr = load_results(cond)
        n = len(allr); c = sum(1 for r in allr.values() if r["correct"]); cost = sum(r["cost"] for r in allr.values())
        print(f"   condition {cond}: {c}/{n} correct ({100 * c / max(1, n):.1f}%), total cost ${cost:.2f}")
    print("\nDone. Run: python report.py")


if __name__ == "__main__":
    main()
