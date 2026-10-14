"""Pick the tasks worth spending panel money on.

    python select_subset.py --results results2 --conds seat1,seat2,seat3,seat4 --extra 30 --out results2/subset.txt

Writes one task id per line (to --out as plain UTF-8, or to stdout): every task at least one listed condition got wrong
(or could not answer), plus `extra` tasks drawn at random from those every
listed condition got right, so the run can also measure harm. The draw is
seeded, so the same subset comes back on every call.
"""
import argparse, json, os, random, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results2")
    ap.add_argument("--conds", default="seat1,seat2,seat3,seat4")
    ap.add_argument("--extra", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="", help="write the ids here (UTF-8, no BOM); PowerShell's > would write UTF-16")
    a = ap.parse_args()
    conds = [c.strip() for c in a.conds.split(",") if c.strip()]
    res = {}
    for c in conds:
        d = os.path.join(a.results, c)
        if not os.path.isdir(d):
            sys.exit(f"no results for {c}")
        for fn in os.listdir(d):
            if fn.endswith(".json"):
                r = json.load(open(os.path.join(d, fn)))
                res.setdefault(r["task_id"], {})[c] = r["correct"] and not r.get("error")
    ids = sorted(res)
    missed = [t for t in ids if not all(res[t].get(c, False) for c in conds)]
    clean = [t for t in ids if all(res[t].get(c, False) for c in conds)]
    rng = random.Random(a.seed)
    sample = sorted(rng.sample(clean, min(a.extra, len(clean))))
    ids_out = missed + sample
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(ids_out) + "\n")
    else:
        for t in ids_out:
            print(t)
    print(f"# {len(missed)} tasks missed by at least one of {conds}; {len(sample)} sampled from {len(clean)} tasks all got right; {len(missed) + len(sample)} total", file=sys.stderr)


if __name__ == "__main__":
    main()
