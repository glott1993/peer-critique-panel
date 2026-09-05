# Pilot results

Run started 2026-09-05T15:13:02Z; OpenRouter; tasks from `tasks/fresh_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | math | all |
|---|---|---|---|---|
| a: single frontier model, one pass (temperature 0.3) | 12/20 = 60.0% [38.7%, 78.1%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 56/64 = 87.5% [77.2%, 93.5%] |
| a2: single frontier model, one pass (temperature 0.7) | 12/20 = 60.0% [38.7%, 78.1%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 56/64 = 87.5% [77.2%, 93.5%] |
| b: same model, compute-matched (self-consistency + self-critique) | 18/20 = 90.0% [69.9%, 97.2%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 62/64 = 96.9% [89.3%, 99.1%] |
| c: panel with hub | 20/20 = 100.0% [83.9%, 100.0%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 64/64 = 100.0% [94.3%, 100.0%] |
| d: panel without hub | 20/20 = 100.0% [83.9%, 100.0%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 64/64 = 100.0% [94.3%, 100.0%] |

## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)

- c minus a: +12.5 points [+4.7, +21.9] over 64 tasks (interval excludes zero)
    - code: +40.0 [+20.0, +60.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- c minus a2: +12.5 points [+4.7, +21.9] over 64 tasks (interval excludes zero)
    - code: +40.0 [+20.0, +60.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- c minus b: +3.1 points [+0.0, +7.8] over 64 tasks (interval includes zero)
    - code: +10.0 [+0.0, +25.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- c minus d: +0.0 points [+0.0, +0.0] over 64 tasks (interval includes zero)
    - code: +0.0 [+0.0, +0.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- b minus a: +9.4 points [+3.1, +17.2] over 64 tasks (interval excludes zero)
    - code: +30.0 [+10.0, +50.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- d minus a: +12.5 points [+4.7, +21.9] over 64 tasks (interval excludes zero)
    - code: +40.0 [+20.0, +60.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- a2 minus a: +0.0 points [+0.0, +0.0] over 64 tasks (interval includes zero)
    - code: +0.0 [+0.0, +0.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24

## No-answer items (refused or failed after retries) and accuracy on answered items

| condition | no answer | of which code / data / math | accuracy, no-answer counted wrong | accuracy on answered items |
|---|---|---|---|---|
| a | 8/64 | 8 / 0 / 0 | 87.5% | 56/56 = 100.0% |
| a2 | 8/64 | 8 / 0 / 0 | 87.5% | 56/56 = 100.0% |
| b | 2/64 | 2 / 0 / 0 | 96.9% | 62/62 = 100.0% |
| c | 0/64 | 0 / 0 / 0 | 100.0% | 64/64 = 100.0% |
| d | 0/64 | 0 / 0 / 0 | 100.0% | 64/64 = 100.0% |

A no-answer item is one where every attempt (7 per task) returned an empty or filtered reply, or failed outright; the error text in `results/<condition>/<task>.json` says which. Panel conditions can route around a seat that declines; single-model conditions cannot.

## Cost per item

| condition | mean tokens | mean cost | median seconds | calls per item | call errors |
|---|---|---|---|---|---|
| a | 927 | $0.0160 | 6 | 2.0 | 74 |
| a2 | 850 | $0.0141 | 6 | 1.8 | 56 |
| b | 13,153 | $0.2088 | 121 | 37.3 | 1562 |
| c | 74,140 | $0.1835 | 142 | 26.1 | 0 |
| d | 62,258 | $0.1080 | 103 | 22.8 | 0 |

Condition b sample counts (k) by type: code: 12, data: 12, math: 12

## What the hub did (condition c)

- Answers submitted to the hub: 64; wrong before the hub: 0; right before the hub: 64
- Catch rate: 0/0 wrong answers were sent back
- Repair rate: 0/0 wrong answers ended right after interrogation
- False alarms: 56/64 right answers were sent back (87.5%)
- Harm: 0/64 right answers ended wrong after interrogation (0.0%)
- Panel deadlocks (no agreement within the round budget): 8/64 (12.5%)
- Released with all three gates met: 52/64; the rest shipped with a flag
- Mean hub questions per item: 3.5

Accuracy when all gates were met: 100.0%; when released with a flag: 100.0%. A large gap means the flag is informative.

Condition d deadlocks: 9/64 (14.1%)

## Readout against the paper's falsification conditions

- Panel earning its cost (c beats b): not shown at this sample size (c-b = +3.1 points, interval [+0.0, +7.8])
- Hub adding value (c beats d): not shown at this sample size (c-d = +0.0 points, interval [+0.0, +0.0])

Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): a: 8, a2: 8, b: 2
