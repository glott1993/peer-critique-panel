# Pilot: does the panel earn its cost, and does the hub add anything?

This folder is the compute-matched pilot described in the paper's *Pilot design* section. It runs four conditions over the same checkable tasks and reports accuracy with intervals, cost, and what the hub actually did.

| condition | what runs |
| --- | --- |
| **a** | the best single frontier model, one pass |
| **b** | the same model given the panel's token budget: k samples, majority vote (numbers, strings) or self-review (code), then a self-critique pass; k is set per task type from the tokens condition c actually used |
| **c** | the panel with the hub (the full six-step protocol from the prototype: decompose, bid, seat-anonymous critique with a designated dissenter, revise to agreement, hub interrogation with checks computed outside the panel, release gates) |
| **d** | the panel with the hub removed, to isolate what the hub adds |

**Falsification, fixed in advance.** If c does not beat b on checkable tasks, the panel is not earning its cost. If c does not beat d, the hub is decoration. `report.py` prints the readout either way, and whichever way it comes out goes in the repository.

## Tasks

`make_tasks.py` writes `tasks/fresh_tasks.json`: 64 original items, 24 math, 20 data, 20 code. Math and data answers are computed by the same code that writes the prompt, so the key is right by construction; every code task's reference solution is run against its visible and hidden tests before export. A fixed seed makes the set reproducible; `--seed` draws a fresh one. The paper also lists factual lookups with a required source; those need web-enabled seats and are deferred, with data tasks (small CSV tables with aggregation questions) in their place.

Scoring: a stored integer must match exactly; a stored decimal must match to within half a unit of the requested precision plus 0.01%, so rounding differences pass and arithmetic slips fail; strings are compared after normalization; code must pass the hidden tests. All four conditions see the same prompt, including the same visible code examples; only the hub runs them mechanically.

## Setup (about 15 minutes)

1. **OpenRouter.** Create an account at openrouter.ai, add credit (see the cost note below), and create an API key. Then:
   `export OPENROUTER_API_KEY=sk-or-...` (Windows PowerShell: `$env:OPENROUTER_API_KEY="sk-or-..."`).
2. **Python 3.10+** and `pip install -r requirements.txt` (only `requests`).
3. `python make_tasks.py`
4. `python run_pilot.py --suggest-models` prints the newest models per lab with prices. Copy `config.example.json` to `config.json` and pin exact ids: one mid-class seat per lab, a frontier-class hub, and the frontier baseline.
5. `python run_pilot.py --dry-run` runs one task of each type through all four conditions. Read the cost column; the full run is roughly 21 times the dry-run total.
6. `python run_pilot.py` runs everything. It is resumable: results are written per task, so if it stops, run it again and it continues. Order is a, c, d, b (b is sized from c).
7. `python report.py` writes `results/report.md` and `results/summary.json`.

Two tunables in `config.json`: `answer_tokens` (cap on calls that write an answer; 6000 by default) and `max_k` (cap on condition b's samples; 12 by default). Lowering `max_k` under-budgets b relative to c and should be reported if used.

Added after the first run: condition `a2` (one pass at the sampling temperature, `--conditions a2`), a no-answer table in the report (items where every attempt returned an empty or filtered reply are counted separately from wrong answers), `provider_pins` in `config.json` to keep a lab's model on the lab's own endpoint (fallback hosts returned empty, filtered replies), and automatic retry of errored tasks on rerun.

`python run_pilot.py --mock --limit 3` runs the whole harness offline with a fake backend, which is how it was tested; the numbers it prints mean nothing.

## Cost

Condition c makes roughly 15 to 25 model calls per item at the mid tier; d somewhat fewer; b makes k+1 calls to the frontier model; a makes one. With mid-class seats and a frontier hub, expect the full 64-item run to land somewhere between $25 and $60 of credit; the dry run tells you your actual number before you commit. `results/calls.jsonl` has every call with its tokens and cost.

## Safety note

Code tasks execute model-written Python locally, in a separate interpreter with a CPU and memory limit and a timeout. That is a guard against accidents, not a sandbox against hostile code. Run the pilot in a disposable environment (a container, a VM, or a fresh virtualenv on a machine that holds nothing sensitive).

## What gets recorded

- `results/<condition>/<task>.json`: the answer, correct or not, tokens, cost, seconds; for c and d also the pre-hub answer and whether it was right, agreement, rounds, gates, hub questions, checks, and the full step log.
- `results/calls.jsonl`: every model call.
- `results/run_meta.json`: the pinned model ids (the version stamps) and settings.
- `results/catalogue.json`: the cross-run catalogue the hub reads from.

## Files

| file | role |
| --- | --- |
| `make_tasks.py`, `task_bank.py` | build and verify the task set |
| `checkers.py` | answer extraction, tolerances, sandboxed test runner, the hub's arithmetic evaluator |
| `panel.py` | the protocol, ported prompt for prompt from `prototype/peer-critique-panel.html` |
| `backend.py` | OpenRouter client with retries and accounting; offline mock |
| `run_pilot.py` | conditions, resumable runs, compute matching |
| `report.py` | metrics and the falsification readout |


## Pilot 2 (harder, larger)

Pilot 1 hit a ceiling: every answered item was right in every condition. Pilot 2 uses a task set built to sit at 50 to 85% single-model accuracy, four times larger, and adds three things the first run was missing.

- **Tasks** (`make_tasks2.py`, default 200 = 60 math, 60 data, 30 code, 50 logic): multi-step exact computations (FIFO inventory, payroll with daily overtime, amortization with an extra payment, month-by-month account simulations, inclusion-exclusion counts, Chinese remainders, business-day dates, exact probabilities as fractions); two-table data questions that need a join; 30 harder functions with larger hidden test sets (`task_bank2.py`, verified on export); four-house logic puzzles with a unique solution proven by exhaustive search. `--level 1|2|3` scales the math, data, and logic difficulty.
- **Conditions:** a (one pass, 0.3), a2 (one pass, 0.7), a3 (one pass, a frontier model from a second lab; set `baseline_alt`), b (token-matched: k samples + self-critique), bd (dollar-matched: k chosen from cost rather than tokens; shares its draws with b so the pair costs little more than b alone), c (panel with hub), d (panel without hub).
- **New measures:** accuracy of the panel's first draft before any critique, so critique's contribution is separated from the hub's; token- and dollar-matched baselines side by side; no-answer items separate from wrong answers, with the serving provider logged per call.

Calibration on September 5, 2026 put the level 2 set at 96% for a one-pass frontier model (logic 100%, math 98%), so level 3 is the one to run: 40 math (longer simulations, four-factor products, four-divisor counts, 60 to 90 business days with six holidays), 40 composite tasks of three independent parts each where only a fully correct answer counts, 50 data questions over 80-row tables with duplicate rows to be counted once, 30 code, 40 five-house puzzles.

### Runbook (from `pilot/`, results go to `results2/`)

```
python make_tasks2.py --level 3
python -c "import json; c=json.load(open('config.json')); c.update({'baseline_alt': 'REPLACE-WITH-SECOND-LAB-FRONTIER-ID', 'max_k_dollars': 16, 'sample_workers': 3}); json.dump(c, open('config.json', 'w'), indent=2)"

# Stage 1, calibration (about $6): the single model alone, all 200 tasks
nohup python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions a --workers 2 >> run2.log 2>&1 &
python report.py --results results2 | head -20        # want roughly 50 to 85% per type; if a type sits at 100%, regenerate with --level 3 and redo stage 1 (rm -rf results2 first)

# Stage 2 (about $100 for 200 tasks): the panel with and without the hub
nohup python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions c,d --workers 2 >> run2.log 2>&1 &

# Stage 3 (about $100): the matched single-model baselines (b and bd together), one task at a time to respect rate limits
nohup python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions b --workers 1 >> run2.log 2>&1 &

# Optional (about $12): one pass from a second lab's frontier model
nohup python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions a3 --workers 1 >> run2.log 2>&1 &

python report.py --results results2
```

Add `--limit 30` to every run for a 120-task version at about 60% of the cost; the same subset is used in every condition. Status line: `pgrep -f run_pilot.py >/dev/null && echo running || echo stopped; ls results2/*/ | grep -c json; grep -l '"error": "' results2/*/*.json 2>/dev/null | wc -l`.

The runbook above is the September 2026 plan as it was run in a GitHub Codespace. The section below replaces it.

## Pilot 2, second attempt (October 2026)

### What happened and what survived

The GitHub account was suspended by automated abuse detection on September 6, 2026, in the middle of the panel run, and reinstated on October 14. The Codespace that held the September runs was deleted by GitHub's 30-day retention while the account was locked, and a deleted codespace cannot be reopened. The last commit before the suspension (September 6, 01:22 UTC) saved:

- `tasks/pilot2_tasks.json`: the 240-task level 3 set (40 math, 40 three-part composites, 40 four-part composites, 50 data, 30 code, 40 five-house logic puzzles).
- `results2/a`: the frontier baseline (Claude Opus 5, one pass) on all 240: 230 right, 4 wrong, 6 refused (all code, empty content-filter replies from Anthropic's own endpoint). This condition is kept: its code path is untouched by the fixes below (one call, no JSON steps, and the baseline is exempt from the reasoning budget), every call finished with `stop`, and none of its misses were truncations.
- `results2/seat1` (Claude Sonnet 5 alone) and `results2/seat2` (GPT-5.6 Luna Pro alone): partial, and from before the reasoning fix (34 of Sonnet's 240 came back empty; GPT reached 162 of 240). Both are deleted before the rerun so that all four seats run under one harness version.
- `results2/calls.jsonl`: every call from those runs, with tokens and cost.

Lost with the Codespace: Gemini 3.8 Flash and DeepSeek V4 Pro alone, the rest of GPT's run, the 108-task subset, and the partial panel run. The author's notes of September 8 record the September seat figures under the earlier caps as Sonnet 5 87.1%, GPT-5.6 Luna Pro 86.2%, Gemini 3.8 Flash 87.1% and DeepSeek V4 Pro 92.9% (the records themselves are gone); the October rerun under the fixed budgets gives 88.3%, 87.9%, 86.7% and 97.5%. The four-point move in DeepSeek's figure comes from the settings, not the model, and it is larger than any difference between conditions in the pilot.

The harness fixes made on September 6 to 8 lived only on that Codespace and in a zip saved to the author's PC. The October 14 commit restores them: a per-model reasoning budget sent through OpenRouter (`reasoning` in `config.json`, longest model prefix wins, the frontier baseline exempt), a 5,000-token cap on JSON-only steps (`json_tokens`; the old 1,500 was spent entirely on thinking by Sonnet 5 and DeepSeek V4, which then returned nothing and collapsed the panel on 89 of 108 tasks), empty replies charged at their real cost and retried, condition `c2` (a second pass of the panel with hub whose hub reads the catalogue the first pass built), the catalogue saved after every task, and `select_subset.py --out` (PowerShell's `>` writes UTF-16, which the id reader could not use).

The October 15 fix, found by the stage 3 trial on the Razer: DeepSeek V4 Pro accepts `reasoning.effort: low` but does not bound its thinking by it. On the JSON-only steps (bid, compare, critique, vote) it spent the whole 5,000-token cap thinking and returned nothing on 62 of 133 calls (the calls log's count; the first write-up said 58), and six of the trial's twelve tasks died after the six retries; the other four models had no call errors at all. `reasoning_json` in `config.json` now gives a separate reasoning setting, by model prefix, for the steps capped at `json_tokens`; for `deepseek/` it is `{"effort": "none"}`, which turns thinking off for those steps only. A twelve-call probe on two of the failed tasks: with thinking on, three of four calls burned the cap; with it off, every call returned its JSON in 16 to 590 tokens and a few seconds. Answer-writing steps (draft, assemble, revise, panel reply) keep the seat's normal reasoning, so the seats answer in the panel as they did alone in stage 1. The trial's `results2/c` folder and the catalogue were cleared and condition c started fresh under this version. (It did not end under one harness: the October 16 fix below was made during the c run, and the last six c tasks completed under it.)

The October 16 fix, found by the full condition c run: six of 104 tasks ended in an error because one model gave up after its retries and the harness ended the task, although the paper says a panel routes around a seat that declines. Four were DeepSeek calls at the 16,000-token answer cap that returned nothing six times (three replies to the hub and one revision; the first write-up called them drafts); one was an Opus content-filter refusal at the hub; one was Opus overrunning the hub's 5,000-token JSON cap. `panel.py` now treats a call that gives up (the backend's `RuntimeError`) as a decline: the seat abstains on bids, comparisons, critiques and votes (an abstention is not an objection); its draft, revision or reply to the hub passes to another seat; parts no seat will stitch ship in order; and a hub that gives up leaves the answer flagged, as a deadlock does, instead of failing it. A task now fails only when every seat declines to draft a component, or on a configuration error (`ValueError`). Declines are recorded under `declined` in the task file and as `declined` counts in the catalogue. None of this runs unless a call gives up, so tasks that completed before the fix are unchanged, and the six errored tasks were retried under it. The calls log also shows that most c tasks ran more than once before the fix, for reasons unrelated to their answers: the process slept for about seven hours on the night of October 15 to 16 and then lost the network, which ended about 75 tasks at their first call, so roughly 78 of the 104 kept c records are a second or third run of their task (c2 and d ran every task once). The records keep the last run; `calls.jsonl` keeps every attempt. `--mock-fail "mock/seat-2:draft,vote;mock/hub:hub-ask"` makes the mock backend give up at named steps so the paths can be checked offline:

```
python run_pilot.py --mock --tasks tasks/pilot2_tasks.json --results results2-mock --conditions c,d --limit 1 --workers 4 --mock-fail "mock/seat-2:bid,draft,compare,critique,revise,vote,panel-reply"
python run_pilot.py --mock --tasks tasks/pilot2_tasks.json --results results2-mock --conditions c --limit 1 --workers 4 --mock-fail "mock/hub:hub-ask"
```

Expect no `[ERR]` lines from either; a task fails only when every seat declines to draft (`--mock-fail "mock/seat-1:draft;mock/seat-2:draft;mock/seat-3:draft"`).

The October 17 correction, found by the offline analysis for v1.3 (`proposal/v1.3-analysis-notes.md`, section 9): one answer key was wrong. `make_tasks2.py`, `tax_credit()`, charged the whole second tax bracket even when the income fell below its top, so the stored key for multi2-02 part C (income $57,400, brackets 10% to $14,000, 22% to $60,000, 32% above) was 10,090.00 when the correct figure is 9,518.00 (1,400 + 0.22 x 43,400 = 10,948 tax, credit 1,800 - 0.05 x 7,400 = 1,430). Every condition (a, the four seats, c, c2, d) answered 9,518.00 and was scored wrong; no other task in the 240 has an income below its bracket top. The generator's second-bracket term is now `max(0, min(inc, b2) - b1) * r2 / 100`, and `tasks/pilot2_tasks.json` was patched by hand (part C of multi2-02 set to 9518.0) rather than regenerated; regenerating with the fixed generator at the same seed reproduces the patched file exactly. The eight stored `results2/*/multi2-02.json` records were rescored offline with `checkers.score`, no model calls: `correct` and `detail` in all eight, and in c, c2 and d also `pre_critique_correct` (the step-3 draft in the log) and `pre_hub_correct` (the last step-4 revision). Seven records become right; seat3 stays wrong because it also missed part B (3,751.80 for 3,689.40). `report.md` was regenerated: a 231/240, seat1 212, seat2 211, seat3 208, seat4 234, c 96/104, c2 93/104, d 97/104; seat4 minus seat3 moves from +10.4 [+6.2, +15.0] to +10.8 [+6.7, +15.4] and the other twelve paired differences are unchanged.

The October 17 guard, for the next run (no stored record was changed by it): a revision (step 4) or a corrected answer sent with a reply to the hub (step 5) used to replace the panel's answer unchecked, as any text over 20 characters. In pilot 2 six of the panel's 26 wrong answers were right values whose revision or hub reply had dropped the FINAL line (c data2-49, which put it at the end of a prose line; c2 multi4-34 and multi4-38, both counted as hub harm; c2 logic2-06; d logic2-01 and logic2-34), against one such loss among the 93 wrong answers of the five single-model conditions. The scoring rule is the same for every condition; the exposure is not, because the panel rewrites each answer three to six times. `panel.py` now refuses a replacement that has lost the format the standing answer had (`keeps_format`: a FINAL line, or a code block for a code task; a malformed text may still replace a malformed one), keeps the standing text, and records the refusal under `refused` in the task file and as `refused` in the step log, so a refused text is never silently dropped. Records from the October 14 to 17 runs predate the guard; a later run under it is not comparable on these six tasks without saying so. `--mock-malformed "mock/seat-2:revise,panel-reply"` makes the mock backend drop the format at those steps so the paths can be checked offline: expect refusals in the records and no final answer without its FINAL line.

### Rules

- The harness never runs in GitHub Codespaces again. The account was restricted for it once, and GitHub's reinstatement notice says a repeat may be permanent. Runs happen on a local machine; the Razer Blade 18 is the one in use.
- The OpenRouter key lives in an environment variable set by hand in a terminal. It is never typed into a chat, a file, or a commit.
- Every stage is resumable: results are written per task, errored tasks retry on the next run, and a stopped run continues from where it was. Rerunning a finished stage costs nothing.
- Calibration precedes spend: the four seats and the subset come first, then a priced trial of the panel, then the panel runs.

### Setup on the Razer (Windows)

Code projects with a git repository live in `C:\Users\gmagi\code`. Claude Code on the PC runs these lines in its shell (Git Bash); the PowerShell forms are given where they differ. If `python` is not on the path, `py -3` is the same thing.

```
cd /c/Users/gmagi/code
git clone https://github.com/glott1993/peer-critique-panel
cd peer-critique-panel/pilot
python -m venv .venv
source .venv/Scripts/activate            # PowerShell: .\.venv\Scripts\Activate.ps1 (if scripts are blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)
python -m pip install -r requirements.txt
```

The key, typed by the author in a PowerShell window (not in Claude Code), then a new terminal so it takes effect:

```
setx OPENROUTER_API_KEY "the-key"
```

Check in the new terminal: `echo ${#OPENROUTER_API_KEY}` (PowerShell: `$env:OPENROUTER_API_KEY.Length`) prints 73.

Offline check, no API calls and no cost; expect six tasks per condition and a clean exit:

```
python run_pilot.py --mock --tasks tasks/pilot2_tasks.json --results results2-mock --conditions a,seat1,c,c2,d --limit 1 --workers 4
rm -rf results2-mock                     # PowerShell: Remove-Item -Recurse -Force results2-mock
```

Live smoke test, six Gemini calls, a few cents; expect six `[ok ]` or `[no ]` lines and no `ERR`:

```
python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2-smoke --conditions seat3 --limit 1 --workers 1
rm -rf results2-smoke
```

Status line, from `pilot/` (files written so far, then tasks that ended in an error; the `[A-Z]` keeps the count to the task's own error field, which starts with the exception's name, because a record where the panel routed around a call carries that call's error text under `declined`):

```
ls results2/*/ | grep -c json; grep -l '"error": "[A-Z]' results2/*/*.json 2>/dev/null | wc -l
```

PowerShell: `(Get-ChildItem results2\*\*.json).Count; (Select-String -Path results2\*\*.json -Pattern '"error": "[A-Z]' -CaseSensitive -List | Measure-Object).Count`

### Stages and costs

Bring the OpenRouter balance to about $300 before stage 3 and set the key's spending limit to match. Prices are per the ids pinned in `config.json`; `results2/calls.jsonl` records what each call actually cost.

**Stage 1, the four seats alone (about $15; an hour or two).** The September seat1 and seat2 folders go first so the four seats share one harness version.

```
rm -rf results2/seat1 results2/seat2     # PowerShell: Remove-Item -Recurse -Force results2\seat1, results2\seat2
python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions seat1,seat2,seat3,seat4 --workers 3
python report.py --results results2
```

Done when the status line reads 1200 files (a's 240 plus four seats of 240) and the error count is about 6 (a's refusals, which stay). The report's per-seat accuracy should land near September's 86 to 93%. A seat far below that means empty replies, not a weak model: read the error text (`grep -ho '"error": "[^"]*' results2/seat*/*.json | sort | uniq -c`) before going on.

**Stage 2, the subset (free).** Every task at least one seat missed, plus 30 the seats all got right so harm can be measured.

```
python select_subset.py --results results2 --conds seat1,seat2,seat3,seat4 --extra 30 --out results2/subset.txt
```

It reports the counts; September's version came to 78 + 30 = 108.

**Stage 3, a priced trial of the panel (about $10).** Two tasks per type from the subset, with a fresh catalogue.

```
rm -f results2/catalogue.json            # PowerShell: Remove-Item -Force results2\catalogue.json
python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions c --ids results2/subset.txt --limit 2 --workers 2
```

The last line of the output gives the trial's total cost. Divide by the number of tasks run and multiply by the subset size for condition c; budget about the same again for c2 and 60% of it for d. Stop here if the total is over $300 and decide; the trial's results count toward c and are not rerun. If tasks end in `[ERR]`, read the error text before projecting: a seat that burns its whole cap thinking on JSON steps is a reasoning setting to fix (`reasoning_json`), not a weak model, and after a harness change the trial is cleared and c starts fresh.

**Stage 4, the panel runs: c, then c2, then d, each on the whole subset (roughly $150 to $250 in all; the trial gives the real number).**

```
python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions c --ids results2/subset.txt --workers 3
python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions c2 --ids results2/subset.txt --workers 3
python run_pilot.py --tasks tasks/pilot2_tasks.json --results results2 --conditions d --ids results2/subset.txt --workers 3
python report.py --results results2
```

c2 runs right after c and before d because condition d also writes to the shared catalogue (its critique rounds update the per-seat tallies), and the c2 test is about the catalogue that c built. Each run is done when its folder holds as many files as `subset.txt` has lines and the error count has not grown; a stopped run is restarted with the same line.

**Stage 5.** Commit the results (`git add -A && git commit -m "Pilot 2 results" && git push` from the repository root) and write v1.3 from `results2/report.md`.

The matched single-model baselines (b and bd, about $50 on the subset) are optional for this pilot: its question is whether critique plus a hub lifts four mid-class seats above the best of them alone and toward the frontier model's one pass (condition a). Run them afterwards only if the panel result makes the comparison worth paying for.

