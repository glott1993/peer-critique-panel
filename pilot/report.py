"""Summarize results/ into results/report.md and results/summary.json.

Metrics (fixed before the first run; see the paper's Pilot design):
  accuracy per condition and task type, with 95% Wilson intervals
  paired differences c-a, c-b, c-d, b-a with 95% bootstrap intervals
  tokens, cost and seconds per item
  hub catch rate: pre-hub-wrong answers the hub sent back (and how many
  ended right), false-alarm rate on pre-hub-right answers, and the harm
  rate (right answers turned wrong under interrogation)
  deadlock rate: panels that hit the round budget without agreement
"""
import json, math, os, random, statistics
from collections import defaultdict

RESULTS = "results"
COND_NAMES = {"a": "single frontier model, one pass", "b": "same model, compute-matched (self-consistency + self-critique)",
              "c": "panel with hub", "d": "panel without hub"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def paired_bootstrap(x, y, iters=5000, seed=0):
    """x, y: lists of 0/1 over the same tasks. Returns (mean diff, lo, hi)."""
    n = len(x)
    if n == 0:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    d = [xi - yi for xi, yi in zip(x, y)]
    diffs = []
    for _ in range(iters):
        s = [d[rng.randrange(n)] for _ in range(n)]
        diffs.append(sum(s) / n)
    diffs.sort()
    return (sum(d) / n, diffs[int(0.025 * iters)], diffs[int(0.975 * iters) - 1])


def load():
    res = {}
    for cond in os.listdir(RESULTS) if os.path.isdir(RESULTS) else []:
        d = os.path.join(RESULTS, cond)
        if os.path.isdir(d) and len(cond) == 1:
            res[cond] = {}
            for fn in os.listdir(d):
                if fn.endswith(".json"):
                    with open(os.path.join(d, fn)) as f:
                        r = json.load(f)
                    res[cond][r["task_id"]] = r
    return res


def pct(x):
    return f"{100 * x:.1f}%"


def main():
    res = load()
    if not res:
        raise SystemExit("no results yet")
    meta = json.load(open(os.path.join(RESULTS, "run_meta.json"))) if os.path.exists(os.path.join(RESULTS, "run_meta.json")) else {}
    types = sorted({r["type"] for c in res.values() for r in c.values()})
    conds = [c for c in "abcd" if c in res]
    lines = ["# Pilot results", ""]
    if meta:
        lines.append(f"Run started {meta.get('started')}; {'MOCK backend (no real models)' if meta.get('mock') else 'OpenRouter'}; tasks from `{meta.get('tasks_file')}`.")
        cfg = meta.get("config", {})
        if cfg.get("seats"):
            lines.append("Seats: " + ", ".join(s["model"] for s in cfg["seats"]) + f". Hub: {cfg.get('hub')}. Baseline: {cfg.get('baseline')}. Rounds {cfg.get('rounds')}, hub budget {cfg.get('hub_budget')}, dissenter {cfg.get('dissenter')}.")
        lines.append("")
    summary = {"accuracy": {}, "differences": {}, "hub": {}, "cost": {}}

    # accuracy table
    lines += ["## Accuracy (95% Wilson interval)", "", "| condition | " + " | ".join(types) + " | all |", "|---|" + "---|" * (len(types) + 1)]
    for c in conds:
        row = [f"{c}: {COND_NAMES.get(c, c)}"]
        summary["accuracy"][c] = {}
        for t in types + ["all"]:
            rs = [r for r in res[c].values() if t == "all" or r["type"] == t]
            k = sum(1 for r in rs if r["correct"]); n = len(rs)
            p, lo, hi = wilson(k, n)
            row.append(f"{k}/{n} = {pct(p)} [{pct(lo)}, {pct(hi)}]" if n else "-")
            summary["accuracy"][c][t] = {"k": k, "n": n, "p": p, "lo": lo, "hi": hi}
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # paired differences
    lines += ["## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)", ""]
    for x, y in (("c", "a"), ("c", "b"), ("c", "d"), ("b", "a"), ("d", "a")):
        if x in res and y in res:
            common = sorted(set(res[x]) & set(res[y]))
            if not common:
                continue
            m, lo, hi = paired_bootstrap([int(res[x][t]["correct"]) for t in common], [int(res[y][t]["correct"]) for t in common])
            verdict = "interval excludes zero" if lo > 0 or hi < 0 else "interval includes zero"
            lines.append(f"- {x} minus {y}: {100 * m:+.1f} points [{100 * lo:+.1f}, {100 * hi:+.1f}] over {len(common)} tasks ({verdict})")
            summary["differences"][f"{x}-{y}"] = {"mean": m, "lo": lo, "hi": hi, "n": len(common)}
            for t in types:
                sub = [tt for tt in common if res[x][tt]["type"] == t]
                if len(sub) >= 5:
                    m2, lo2, hi2 = paired_bootstrap([int(res[x][tt]["correct"]) for tt in sub], [int(res[y][tt]["correct"]) for tt in sub])
                    lines.append(f"    - {t}: {100 * m2:+.1f} [{100 * lo2:+.1f}, {100 * hi2:+.1f}] over {len(sub)}")
    lines.append("")

    # cost
    lines += ["## Cost per item", "", "| condition | mean tokens | mean cost | median seconds | calls per item | call errors |", "|---|---|---|---|---|---|"]
    for c in conds:
        rs = list(res[c].values())
        tok = statistics.mean(r["tokens"] for r in rs); cost = statistics.mean(r["cost"] for r in rs); sec = statistics.median(r["seconds"] for r in rs)
        calls = statistics.mean(r.get("calls", 0) for r in rs); errs = sum(r.get("call_errors", 0) for r in rs)
        lines.append(f"| {c} | {tok:,.0f} | ${cost:.4f} | {sec:.0f} | {calls:.1f} | {errs} |")
        summary["cost"][c] = {"mean_tokens": tok, "mean_cost": cost, "median_seconds": sec, "total_cost": sum(r["cost"] for r in rs)}
    if "b" in res:
        ks = sorted({(r["type"], r.get("k")) for r in res["b"].values()})
        lines.append("")
        lines.append("Condition b sample counts (k) by type: " + ", ".join(f"{t}: {k}" for t, k in ks))
    lines.append("")

    # hub metrics
    if "c" in res:
        rs = [r for r in res["c"].values() if not r.get("error")]
        wrong_pre = [r for r in rs if not r.get("pre_hub_correct")]
        right_pre = [r for r in rs if r.get("pre_hub_correct")]
        caught = [r for r in wrong_pre if r.get("hub_sent_back")]
        fixed = [r for r in wrong_pre if r["correct"]]
        false_alarm = [r for r in right_pre if r.get("hub_sent_back")]
        harmed = [r for r in right_pre if not r["correct"]]
        deadlock_c = [r for r in rs if not r.get("agreed")]
        shipped = [r for r in rs if r.get("shipped")]
        lines += ["## What the hub did (condition c)", "",
                  f"- Answers submitted to the hub: {len(rs)}; wrong before the hub: {len(wrong_pre)}; right before the hub: {len(right_pre)}",
                  f"- Catch rate: {len(caught)}/{len(wrong_pre)} wrong answers were sent back" + (f" ({pct(len(caught) / len(wrong_pre))})" if wrong_pre else ""),
                  f"- Repair rate: {len(fixed)}/{len(wrong_pre)} wrong answers ended right after interrogation" + (f" ({pct(len(fixed) / len(wrong_pre))})" if wrong_pre else ""),
                  f"- False alarms: {len(false_alarm)}/{len(right_pre)} right answers were sent back" + (f" ({pct(len(false_alarm) / len(right_pre))})" if right_pre else ""),
                  f"- Harm: {len(harmed)}/{len(right_pre)} right answers ended wrong after interrogation" + (f" ({pct(len(harmed) / len(right_pre))})" if right_pre else ""),
                  f"- Panel deadlocks (no agreement within the round budget): {len(deadlock_c)}/{len(rs)}" + (f" ({pct(len(deadlock_c) / len(rs))})" if rs else ""),
                  f"- Released with all three gates met: {len(shipped)}/{len(rs)}; the rest shipped with a flag",
                  f"- Mean hub questions per item: {statistics.mean(r.get('hub_questions', 0) for r in rs):.1f}" if rs else "", ""]
        summary["hub"] = {"n": len(rs), "wrong_pre": len(wrong_pre), "caught": len(caught), "fixed": len(fixed), "right_pre": len(right_pre), "false_alarm": len(false_alarm), "harmed": len(harmed), "deadlock": len(deadlock_c), "shipped": len(shipped)}
        # accuracy of shipped vs flagged
        if shipped and len(shipped) < len(rs):
            flagged = [r for r in rs if not r.get("shipped")]
            lines.append(f"Accuracy when all gates were met: {pct(sum(r['correct'] for r in shipped) / len(shipped))}; when released with a flag: {pct(sum(r['correct'] for r in flagged) / len(flagged))}. A large gap means the flag is informative.")
            lines.append("")
    if "d" in res:
        rs = [r for r in res["d"].values() if not r.get("error")]
        dl = [r for r in rs if not r.get("agreed")]
        lines.append(f"Condition d deadlocks: {len(dl)}/{len(rs)}" + (f" ({pct(len(dl) / len(rs))})" if rs else ""))
        lines.append("")

    # falsification readout
    lines += ["## Readout against the paper's falsification conditions", ""]
    dcb, dcd = summary["differences"].get("c-b"), summary["differences"].get("c-d")
    if dcb:
        lines.append(f"- Panel earning its cost (c beats b): {'yes' if dcb['lo'] > 0 else ('no' if dcb['hi'] < 0 else 'not shown at this sample size')} (c-b = {100 * dcb['mean']:+.1f} points, interval [{100 * dcb['lo']:+.1f}, {100 * dcb['hi']:+.1f}])")
    if dcd:
        lines.append(f"- Hub adding value (c beats d): {'yes' if dcd['lo'] > 0 else ('no' if dcd['hi'] < 0 else 'not shown at this sample size')} (c-d = {100 * dcd['mean']:+.1f} points, interval [{100 * dcd['lo']:+.1f}, {100 * dcd['hi']:+.1f}])")
    lines.append("")
    errs = {c: sum(1 for r in res[c].values() if r.get("error")) for c in conds}
    if any(errs.values()):
        lines.append("Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): " + ", ".join(f"{c}: {n}" for c, n in errs.items() if n))
        lines.append("")

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "report.md"), "w") as f:
        f.write("\n".join(lines))
    with open(os.path.join(RESULTS, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("\n".join(lines))
    print(f"\nwrote {RESULTS}/report.md and {RESULTS}/summary.json")


if __name__ == "__main__":
    main()
