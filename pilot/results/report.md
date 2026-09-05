# Pilot results

Run started 2026-09-05T13:52:53Z; OpenRouter; tasks from `tasks/fresh_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | math | all |
|---|---|---|---|---|
| a: single frontier model, one pass | 12/20 = 60.0% [38.7%, 78.1%] | 20/20 = 100.0% [83.9%, 100.0%] | 23/24 = 95.8% [79.8%, 99.3%] | 55/64 = 85.9% [75.4%, 92.4%] |
| b: same model, compute-matched (self-consistency + self-critique) | 18/20 = 90.0% [69.9%, 97.2%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 62/64 = 96.9% [89.3%, 99.1%] |
| c: panel with hub | 20/20 = 100.0% [83.9%, 100.0%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 64/64 = 100.0% [94.3%, 100.0%] |
| d: panel without hub | 20/20 = 100.0% [83.9%, 100.0%] | 20/20 = 100.0% [83.9%, 100.0%] | 24/24 = 100.0% [86.2%, 100.0%] | 64/64 = 100.0% [94.3%, 100.0%] |

## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)

- c minus a: +14.1 points [+6.2, +23.4] over 64 tasks (interval excludes zero)
    - code: +40.0 [+20.0, +60.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +4.2 [+0.0, +12.5] over 24
- c minus b: +3.1 points [+0.0, +7.8] over 64 tasks (interval includes zero)
    - code: +10.0 [+0.0, +25.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- c minus d: +0.0 points [+0.0, +0.0] over 64 tasks (interval includes zero)
    - code: +0.0 [+0.0, +0.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +0.0 [+0.0, +0.0] over 24
- b minus a: +10.9 points [+3.1, +18.8] over 64 tasks (interval excludes zero)
    - code: +30.0 [+10.0, +50.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +4.2 [+0.0, +12.5] over 24
- d minus a: +14.1 points [+6.2, +23.4] over 64 tasks (interval excludes zero)
    - code: +40.0 [+20.0, +60.0] over 20
    - data: +0.0 [+0.0, +0.0] over 20
    - math: +4.2 [+0.0, +12.5] over 24

## Cost per item

| condition | mean tokens | mean cost | median seconds | calls per item | call errors |
|---|---|---|---|---|---|
| a | 941 | $0.0164 | 5 | 1.3 | 22 |
| b | 13,153 | $0.2088 | 119 | 37.1 | 1525 |
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
