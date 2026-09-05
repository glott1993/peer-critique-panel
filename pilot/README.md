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
