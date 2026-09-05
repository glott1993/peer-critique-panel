# Pilot results

Run started 2026-09-05T20:25:25Z; OpenRouter; tasks from `tasks/pilot2_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | logic | math | multi | multi4 | all |
|---|---|---|---|---|---|---|---|
| a: single frontier model, one pass (temperature 0.3) | 24/30 = 80.0% [62.7%, 90.5%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 37/40 = 92.5% [80.1%, 97.4%] | 39/40 = 97.5% [87.1%, 99.6%] | 230/240 = 95.8% [92.5%, 97.7%] |

## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)


## No-answer items (refused or failed after retries) and accuracy on answered items

| condition | no answer | of which code / data / logic / math / multi / multi4 | accuracy, no-answer counted wrong | accuracy on answered items |
|---|---|---|---|---|
| a | 6/240 | 6 / 0 / 0 / 0 / 0 / 0 | 95.8% | 230/234 = 98.3% |

A no-answer item is one where every attempt (7 per task) returned an empty or filtered reply, or failed outright; the error text in `results/<condition>/<task>.json` says which. Panel conditions can route around a seat that declines; single-model conditions cannot.

## Cost per item

| condition | mean tokens | mean cost | median seconds | calls per item | call errors |
|---|---|---|---|---|---|
| a | 3,147 | $0.0599 | 16 | 1.2 | 49 |

## Readout against the paper's falsification conditions


Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): a: 6
