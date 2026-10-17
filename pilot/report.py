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

import sys
RESULTS = sys.argv[sys.argv.index("--results") + 1] if "--results" in sys.argv else "results"
COND_NAMES = {"a": "single frontier model, one pass (temperature 0.3)", "a2": "single frontier model, one pass (temperature 0.7)",
              "a3": "single frontier model from another lab, one pass",
              "b": "same model, token-matched (k samples + self-critique)", "bd": "same model, dollar-matched (k samples + self-critique)",
              "c": "panel with hub", "c2": "panel with hub, second pass, hub reads the catalogue built by the first", "d": "panel without hub"}
COND_ORDER = ("a", "a2", "a3", "b", "bd", "c", "c2", "d")


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
        if os.path.isdir(d) and (cond in COND_ORDER or (cond.startswith("seat") and cond[4:].isdigit())):
            res[cond] = {}
            for fn in os.listdir(d):
                if fn.endswith(".json"):
                    with open(os.path.join(d, fn)) as f:
                        r = json.load(f)
                    res[cond][r["task_id"]] = r
    return res


def pct(x):
    return f"{100 * x:.1f}%"


def fisher_exact(a, b, c, d):
    """Fisher's exact test on the 2x2 table [[a, b], [c, d]] (rows: two groups; columns: wrong, right).
    Returns (p one-sided that group 1 has more wrong than chance, p two-sided, odds ratio). Two-sided p sums the
    probabilities of every table at most as likely as the observed one, as R's fisher.test does. No scipy needed."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    if n == 0 or r1 == 0 or r1 == n or c1 == 0 or c1 == n:
        return (1.0, 1.0, float("nan"))
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    tot = math.comb(n, c1)
    probs = {x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / tot for x in range(lo, hi + 1)}
    p_obs = probs[a]
    one_sided = sum(p for x, p in probs.items() if x >= a)
    two_sided = min(1.0, sum(p for p in probs.values() if p <= p_obs * (1 + 1e-9)))
    odds = (a * d) / (b * c) if b * c else float("inf")
    return (one_sided, two_sided, odds)


def panel_stage_lines(res):
    """Added for v1.3: stage-by-stage lines for the panel conditions (c, c2, d). Everything here is computed from fields
    the per-task records already carry: pre_critique_correct (first draft), pre_hub_correct, correct, agreed, gates, shipped,
    hub_questions and checks. Task ids are listed for every count so the lines can be spot-checked against the records."""
    panel = [c for c in ("c", "c2", "d") if c in res and any("pre_critique_correct" in r for r in res[c].values())]
    if not panel:
        return []
    # task order is fixed here (sorted ids) so the block reads the same on every platform; load() walks the folder in
    # directory order, which differs between Windows and Linux
    ok = {c: {t: r for t, r in sorted(res[c].items()) if not r.get("error") and "pre_critique_correct" in r} for c in panel}

    def ids(lst):
        lst = list(lst)  # callers pass generators, which are always truthy
        return ", ".join(sorted(lst)) if lst else "none"

    out = ["## Panel stages, flags and checks (added for v1.3)", "",
           "First draft = the assembled answer before any critique (pre_critique_correct); pre-hub = after critique and revision (pre_hub_correct); final = correct. "
           "In d there is no hub, so pre-hub and final coincide.", ""]
    # first-draft accuracy and the three stages
    out.append("### First draft, after critique, final")
    out.append("")
    for c in panel:
        rs = ok[c]
        d = sum(1 for r in rs.values() if r["pre_critique_correct"]); p = sum(1 for r in rs.values() if r["pre_hub_correct"]); f = sum(1 for r in rs.values() if r["correct"])
        out.append(f"- {c}: first draft right {d}/{len(rs)} ({pct(d / len(rs)) if rs else '-'}); after critique {p}; final {f}. Wrong first drafts: {ids(t for t, r in rs.items() if not r['pre_critique_correct'])}")
    out.append("")
    # critique-only flips (first draft -> pre-hub) and hub flips (pre-hub -> final)
    out.append("### Critique alone (first draft to pre-hub) and the hub alone (pre-hub to final)")
    out.append("")
    for c in panel:
        rs = ok[c]
        rw = [t for t, r in rs.items() if r["pre_critique_correct"] and not r["pre_hub_correct"]]
        wr = [t for t, r in rs.items() if not r["pre_critique_correct"] and r["pre_hub_correct"]]
        out.append(f"- {c} critique: right first draft to wrong pre-hub {len(rw)} ({ids(rw)}); wrong first draft to right pre-hub {len(wr)} ({ids(wr)}); net {len(wr) - len(rw):+d}")
        if c != "d":
            hrw = [t for t, r in rs.items() if r["pre_hub_correct"] and not r["correct"]]
            hwr = [t for t, r in rs.items() if not r["pre_hub_correct"] and r["correct"]]
            out.append(f"- {c} hub: right pre-hub to wrong final {len(hrw)} ({ids(hrw)}); wrong pre-hub to right final {len(hwr)} ({ids(hwr)}); net {len(hwr) - len(hrw):+d}")
    out.append("")
    # pairwise flips, first draft and final
    out.append("### Pairwise flips between panel conditions (tasks present in both)")
    out.append("")
    for i, x in enumerate(panel):
        for y in panel[i + 1:]:
            common = sorted(set(ok[x]) & set(ok[y]))
            if not common:
                continue
            drw = [t for t in common if ok[x][t]["pre_critique_correct"] and not ok[y][t]["pre_critique_correct"]]
            dwr = [t for t in common if not ok[x][t]["pre_critique_correct"] and ok[y][t]["pre_critique_correct"]]
            frw = [t for t in common if ok[x][t]["correct"] and not ok[y][t]["correct"]]
            fwr = [t for t in common if not ok[x][t]["correct"] and ok[y][t]["correct"]]
            out.append(f"- {x} vs {y} over {len(common)}: first draft differs on {len(drw) + len(dwr)} (right in {x} only: {ids(drw)}; right in {y} only: {ids(dwr)}); "
                       f"final differs on {len(frw) + len(fwr)} (right in {x} only: {ids(frw)}; right in {y} only: {ids(fwr)})")
    out.append("")
    # deadlocked vs agreed
    out.append("### Accuracy by agreement")
    out.append("")
    for c in panel:
        rs = ok[c]
        dl = {t: r for t, r in rs.items() if not r.get("agreed")}; ag = {t: r for t, r in rs.items() if r.get("agreed")}
        kd = sum(r["correct"] for r in dl.values()); ka = sum(r["correct"] for r in ag.values())
        p1, p2, odds = fisher_exact(len(dl) - kd, kd, len(ag) - ka, ka)
        out.append(f"- {c}: deadlocked {kd}/{len(dl)}" + (f" ({pct(kd / len(dl))})" if dl else "") + f", agreed {ka}/{len(ag)}" + (f" ({pct(ka / len(ag))})" if ag else "")
                   + f"; Fisher's exact p = {p1:.4f} one-sided (deadlocked more often wrong), {p2:.4f} two-sided, odds ratio {odds:.2f}. Wrong when deadlocked: {ids(t for t, r in dl.items() if not r['correct'])}; wrong when agreed: {ids(t for t, r in ag.items() if not r['correct'])}")
    out.append("")
    # flagged releases by reason, and Fisher flagged vs unflagged
    out.append("### Flagged releases by reason (a task can fail more than one gate)")
    out.append("")
    for c in panel:
        rs = ok[c]
        flagged = {t: r for t, r in rs.items() if not r.get("shipped")}; shipped = {t: r for t, r in rs.items() if r.get("shipped")}
        fw = sum(1 for r in flagged.values() if not r["correct"]); sw = sum(1 for r in shipped.values() if not r["correct"])
        p1, p2, odds = fisher_exact(fw, len(flagged) - fw, sw, len(shipped) - sw)
        out.append(f"- {c}: flagged {len(flagged)} ({fw} wrong), all gates met {len(shipped)} ({sw} wrong); Fisher's exact p = {p1:.4f} one-sided (flagged more often wrong), {p2:.4f} two-sided, odds ratio {odds:.2f}")
        # the agreement gate is read from the record's own `agreed` field (the same field "Accuracy by agreement" uses); the
        # other two from `gates`, which the harness always writes; a record without gates can only be flagged for deadlock
        reasons = [("deadlock", lambda r: not r.get("agreed")), ("hub questions open", lambda r: not (r.get("gates") or {}).get("hub_clear", True)), ("failed check", lambda r: not (r.get("gates") or {}).get("checks_ok", True))]
        for name, bad in reasons:
            lst = {t: r for t, r in flagged.items() if bad(r)}
            if lst:
                k = sum(r["correct"] for r in lst.values())
                out.append(f"    - {name}: {len(lst)} tasks, {k} right ({pct(k / len(lst))}); wrong: {ids(t for t, r in lst.items() if not r['correct'])}")
        combos = {}
        for t, r in flagged.items():
            key = "+".join(name for name, bad in reasons if bad(r)) or "no gate recorded"
            combos.setdefault(key, []).append(t)
        if len(combos) > 1:
            out.append("    - overlaps: " + "; ".join(f"{key} only: {len(lst)} ({sum(rs[t]['correct'] for t in lst)} right)" if "+" not in key else f"{key}: {len(lst)} ({sum(rs[t]['correct'] for t in lst)} right)" for key, lst in sorted(combos.items(), key=lambda kv: (-len(kv[1]), kv[0]))))
    out.append("")
    # hub questions used
    hubc = [c for c in panel if any(r.get("hub_questions") for r in ok[c].values())]
    if hubc:
        out.append("### Hub questions used")
        out.append("")
        for c in hubc:
            rs = ok[c]
            dist = {}
            for r in rs.values():
                dist[r.get("hub_questions") or 0] = dist.get(r.get("hub_questions") or 0, 0) + 1
            top = max(dist)
            at = [t for t, r in rs.items() if (r.get("hub_questions") or 0) == top]
            out.append(f"- {c}: questions per task {dict(sorted(dist.items()))}; mean {statistics.mean((r.get('hub_questions') or 0) for r in rs.values()):.2f}; at the most used ({top}): {len(at)} tasks, {sum(rs[t]['correct'] for t in at)} right; "
                       f"no question asked: {ids(t for t, r in rs.items() if not r.get('hub_questions'))}")
        out.append("")
    # checks run and failed
    chk = [c for c in panel if any(r.get("checks") for r in ok[c].values())]
    if chk:
        out.append("### Checks ordered by the hub and run outside the panel")
        out.append("")
        for c in chk:
            rs = ok[c]
            allc = [(t, x) for t, r in rs.items() for x in (r.get("checks") or [])]
            kinds = {}
            for _, x in allc:
                k = (x.get("kind"), "valid" if x.get("valid") else "invalid", "pass" if x.get("ok") else "fail")
                kinds[k] = kinds.get(k, 0) + 1
            failed = [(t, x) for t, x in allc if x.get("valid") and not x.get("ok")]
            out.append(f"- {c}: {len(allc)} checks on {len({t for t, _ in allc})} tasks; " + "; ".join(f"{k[0]} {k[1]} {k[2]}: {v}" for k, v in sorted(kinds.items(), key=str))
                       + f". Failed: {len(failed)} on {len({t for t, _ in failed})} tasks" + (" (" + "; ".join(f"{t} {x.get('kind')}: pre-hub {'right' if rs[t]['pre_hub_correct'] else 'wrong'}, final {'right' if rs[t]['correct'] else 'wrong'}, release {'blocked' if not (rs[t].get('gates') or {}).get('checks_ok', True) else 'not blocked'}" for t, x in failed) + ")" if failed else ""))
        out.append("")
    return out


def main():
    res = load()
    if not res:
        raise SystemExit("no results yet")
    meta = json.load(open(os.path.join(RESULTS, "run_meta.json"))) if os.path.exists(os.path.join(RESULTS, "run_meta.json")) else {}
    types = sorted({r["type"] for c in res.values() for r in c.values()})
    seat_conds = sorted([c for c in res if c.startswith("seat")], key=lambda c: int(c[4:]))
    conds = [c for c in COND_ORDER if c in res] + seat_conds
    seat_models = {f"seat{i + 1}": sd.get("label") or sd.get("model") for i, sd in enumerate((meta.get("config") or {}).get("seats", []))}
    for c in seat_conds:
        COND_NAMES[c] = f"seat model alone, one pass: {seat_models.get(c, c)}"
    # the strongest single seat model, for comparisons
    seat_best = max(seat_conds, key=lambda c: sum(r["correct"] for r in res[c].values()) / max(1, len(res[c]))) if seat_conds else None
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
    pairs = [("c", "a"), ("c", "a2"), ("c", "a3"), ("c", "b"), ("c", "bd"), ("c", "d"), ("c2", "c"), ("c2", "d"), ("d", "b"), ("d", "bd"), ("b", "a"), ("bd", "a"), ("d", "a"), ("a2", "a"), ("a3", "a")]
    if seat_best:
        pairs += [("c", seat_best), ("d", seat_best), ("a", seat_best)] + [(seat_best, c2) for c2 in seat_conds if c2 != seat_best]
    for x, y in pairs:
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

    # refusals / no-answer items, and accuracy on answered items only
    lines += ["## No-answer items (refused or failed after retries) and accuracy on answered items", "",
              "| condition | no answer | of which " + " / ".join(types) + " | accuracy, no-answer counted wrong | accuracy on answered items |", "|---|---|---|---|---|"]
    for c in conds:
        rs = list(res[c].values()); na = [r for r in rs if r.get("error")]; ans = [r for r in rs if not r.get("error")]
        by = " / ".join(str(sum(1 for r in na if r["type"] == t)) for t in types)
        acc_all = sum(r["correct"] for r in rs) / max(1, len(rs)); acc_ans = sum(r["correct"] for r in ans) / max(1, len(ans))
        lines.append(f"| {c} | {len(na)}/{len(rs)} | {by} | {pct(acc_all)} | {sum(r['correct'] for r in ans)}/{len(ans)} = {pct(acc_ans)} |")
    lines.append("")
    lines.append("A no-answer item is one where every attempt (7 per task) returned an empty or filtered reply, or failed outright; the error text in `results/<condition>/<task>.json` says which. Panel conditions can route around a seat that declines; single-model conditions cannot.")
    lines.append("")

    # cost
    lines += ["## Cost per item", "", "| condition | mean tokens | mean cost | median seconds | calls per item | call errors |", "|---|---|---|---|---|---|"]
    for c in conds:
        rs = list(res[c].values()) or [{"tokens": 0, "cost": 0, "seconds": 0}]
        tok = statistics.mean(r["tokens"] for r in rs); cost = statistics.mean(r["cost"] for r in rs); sec = statistics.median(r["seconds"] for r in rs)
        calls = statistics.mean(r.get("calls", 0) for r in rs); errs = sum(r.get("call_errors", 0) for r in rs)
        lines.append(f"| {c} | {tok:,.0f} | ${cost:.4f} | {sec:.0f} | {calls:.1f} | {errs} |")
        summary["cost"][c] = {"mean_tokens": tok, "mean_cost": cost, "median_seconds": sec, "total_cost": sum(r["cost"] for r in rs)}
    for cnd in ("c", "c2", "d"):
        if cnd in res:
            rs = [r for r in res[cnd].values() if not r.get("error") and "pre_critique_correct" in r]
            if rs:
                dw = [r for r in rs if not r["pre_critique_correct"]]; dr = [r for r in rs if r["pre_critique_correct"]]
                lines.append("")
                lines.append(f"Critique in condition {cnd}: first draft right on {len(dr)}/{len(rs)} ({pct(len(dr) / len(rs))}); "
                             f"of {len(dw)} wrong first drafts, {sum(r['correct'] for r in dw)} ended right after critique and revision ({pct(sum(r['correct'] for r in dw) / len(dw)) if dw else '-'}); "
                             f"of {len(dr)} right first drafts, {sum(1 for r in dr if not r['correct'])} ended wrong ({pct(sum(1 for r in dr if not r['correct']) / len(dr)) if dr else '-'}).")
    if "b" in res:
        ks = sorted({(r["type"], r.get("k") or 0) for r in res["b"].values() if not r.get("error")})
        lines.append("")
        lines.append("Condition b sample counts (k) by type: " + ", ".join(f"{t}: {k}" for t, k in ks))
    lines.append("")

    # hub metrics, one block per hub condition (c, and c2 when the catalogue test has run)
    for hub_cond in [x for x in ("c", "c2") if x in res]:
        rs = [r for r in res[hub_cond].values() if not r.get("error")]
        wrong_pre = [r for r in rs if not r.get("pre_hub_correct")]
        right_pre = [r for r in rs if r.get("pre_hub_correct")]
        caught = [r for r in wrong_pre if r.get("hub_sent_back")]
        fixed = [r for r in wrong_pre if r["correct"]]
        false_alarm = [r for r in right_pre if r.get("hub_sent_back")]
        harmed = [r for r in right_pre if not r["correct"]]
        deadlock_c = [r for r in rs if not r.get("agreed")]
        shipped = [r for r in rs if r.get("shipped")]
        lines += [f"## What the hub did (condition {hub_cond}{', second pass with the catalogue' if hub_cond == 'c2' else ''})", "",
                  f"- Answers submitted to the hub: {len(rs)}; wrong before the hub: {len(wrong_pre)}; right before the hub: {len(right_pre)}",
                  f"- Catch rate: {len(caught)}/{len(wrong_pre)} wrong answers were sent back" + (f" ({pct(len(caught) / len(wrong_pre))})" if wrong_pre else ""),
                  f"- Repair rate: {len(fixed)}/{len(wrong_pre)} wrong answers ended right after interrogation" + (f" ({pct(len(fixed) / len(wrong_pre))})" if wrong_pre else ""),
                  f"- False alarms: {len(false_alarm)}/{len(right_pre)} right answers were sent back" + (f" ({pct(len(false_alarm) / len(right_pre))})" if right_pre else ""),
                  f"- Harm: {len(harmed)}/{len(right_pre)} right answers ended wrong after interrogation" + (f" ({pct(len(harmed) / len(right_pre))})" if right_pre else ""),
                  f"- Panel deadlocks (no agreement within the round budget): {len(deadlock_c)}/{len(rs)}" + (f" ({pct(len(deadlock_c) / len(rs))})" if rs else ""),
                  f"- Released with all three gates met: {len(shipped)}/{len(rs)}; the rest shipped with a flag",
                  f"- Mean hub questions per item: {statistics.mean(r.get('hub_questions', 0) for r in rs):.1f}" if rs else "", ""]
        summary.setdefault("hub", {})[hub_cond] = {"n": len(rs), "wrong_pre": len(wrong_pre), "caught": len(caught), "fixed": len(fixed), "right_pre": len(right_pre), "false_alarm": len(false_alarm), "harmed": len(harmed), "deadlock": len(deadlock_c), "shipped": len(shipped)}
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

    lines += panel_stage_lines(res)

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "report.md"), "w") as f:
        f.write("\n".join(lines))
    with open(os.path.join(RESULTS, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("\n".join(lines))
    print(f"\nwrote {RESULTS}/report.md and {RESULTS}/summary.json")


if __name__ == "__main__":
    main()
