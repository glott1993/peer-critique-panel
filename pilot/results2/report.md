# Pilot results

Run started 2026-09-05T18:45:07Z; OpenRouter; tasks from `tasks/pilot2_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | logic | math | multi | all |
|---|---|---|---|---|---|---|
| a: single frontier model, one pass (temperature 0.3) | 25/30 = 83.3% [66.4%, 92.7%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 28/40 = 70.0% [54.6%, 81.9%] | 183/200 = 91.5% [86.8%, 94.6%] |

## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)


## No-answer items (refused or failed after retries) and accuracy on answered items

| condition | no answer | of which code / data / logic / math / multi | accuracy, no-answer counted wrong | accuracy on answered items |
|---|---|---|---|---|
| a | 9/200 | 5 / 0 / 0 / 0 / 4 | 91.5% | 183/191 = 95.8% |

A no-answer item is one where every attempt (7 per task) returned an empty or filtered reply, or failed outright; the error text in `results/<condition>/<task>.json` says which. Panel conditions can route around a seat that declines; single-model conditions cannot.

## Cost per item

| condition | mean tokens | mean cost | median seconds | calls per item | call errors |
|---|---|---|---|---|---|
| a | 2,306 | $0.0378 | 13 | 1.4 | 88 |

## Readout against the paper's falsification conditions


Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): a: 9
