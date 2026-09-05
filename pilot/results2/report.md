# Pilot results

Run started 2026-09-05T18:05:27Z; OpenRouter; tasks from `tasks/pilot2_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | logic | math | all |
|---|---|---|---|---|---|
| a: single frontier model, one pass (temperature 0.3) | 25/30 = 83.3% [66.4%, 92.7%] | 58/60 = 96.7% [88.6%, 99.1%] | 50/50 = 100.0% [92.9%, 100.0%] | 59/60 = 98.3% [91.1%, 99.7%] | 192/200 = 96.0% [92.3%, 98.0%] |

## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)


## No-answer items (refused or failed after retries) and accuracy on answered items

| condition | no answer | of which code / data / logic / math | accuracy, no-answer counted wrong | accuracy on answered items |
|---|---|---|---|---|
| a | 5/200 | 5 / 0 / 0 / 0 | 96.0% | 192/195 = 98.5% |

A no-answer item is one where every attempt (7 per task) returned an empty or filtered reply, or failed outright; the error text in `results/<condition>/<task>.json` says which. Panel conditions can route around a seat that declines; single-model conditions cannot.

## Cost per item

| condition | mean tokens | mean cost | median seconds | calls per item | call errors |
|---|---|---|---|---|---|
| a | 1,333 | $0.0204 | 8 | 1.2 | 45 |

## Readout against the paper's falsification conditions


Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): a: 5
