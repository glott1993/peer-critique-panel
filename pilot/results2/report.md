# Pilot results

Run started 2026-10-17T07:20:20Z; OpenRouter; tasks from `tasks/pilot2_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | logic | math | multi | multi4 | all |
|---|---|---|---|---|---|---|---|
| a: single frontier model, one pass (temperature 0.3) | 24/30 = 80.0% [62.7%, 90.5%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 37/40 = 92.5% [80.1%, 97.4%] | 39/40 = 97.5% [87.1%, 99.6%] | 230/240 = 95.8% [92.5%, 97.7%] |
| c: panel with hub | 13/14 = 92.9% [68.5%, 98.7%] | 17/18 = 94.4% [74.2%, 99.0%] | 7/7 = 100.0% [64.6%, 100.0%] | 15/15 = 100.0% [79.6%, 100.0%] | 21/22 = 95.5% [78.2%, 99.2%] | 22/28 = 78.6% [60.5%, 89.8%] | 95/104 = 91.3% [84.4%, 95.4%] |
| c2: panel with hub, second pass, hub reads the catalogue built by the first | 13/14 = 92.9% [68.5%, 98.7%] | 17/18 = 94.4% [74.2%, 99.0%] | 6/7 = 85.7% [48.7%, 97.4%] | 15/15 = 100.0% [79.6%, 100.0%] | 20/22 = 90.9% [72.2%, 97.5%] | 21/28 = 75.0% [56.6%, 87.3%] | 92/104 = 88.5% [80.9%, 93.3%] |
| d: panel without hub | 14/14 = 100.0% [78.5%, 100.0%] | 18/18 = 100.0% [82.4%, 100.0%] | 5/7 = 71.4% [35.9%, 91.8%] | 15/15 = 100.0% [79.6%, 100.0%] | 21/22 = 95.5% [78.2%, 99.2%] | 23/28 = 82.1% [64.4%, 92.1%] | 96/104 = 92.3% [85.6%, 96.1%] |
| seat1: seat model alone, one pass: Anthropic mid | 29/30 = 96.7% [83.3%, 99.4%] | 43/50 = 86.0% [73.8%, 93.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 34/40 = 85.0% [70.9%, 92.9%] | 35/40 = 87.5% [73.9%, 94.5%] | 30/40 = 75.0% [59.8%, 85.8%] | 211/240 = 87.9% [83.2%, 91.5%] |
| seat2: seat model alone, one pass: OpenAI mid | 30/30 = 100.0% [88.6%, 100.0%] | 43/50 = 86.0% [73.8%, 93.0%] | 35/40 = 87.5% [73.9%, 94.5%] | 39/40 = 97.5% [87.1%, 99.6%] | 32/40 = 80.0% [65.2%, 89.5%] | 31/40 = 77.5% [62.5%, 87.7%] | 210/240 = 87.5% [82.7%, 91.1%] |
| seat3: seat model alone, one pass: Google mid | 30/30 = 100.0% [88.6%, 100.0%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 36/40 = 90.0% [76.9%, 96.0%] | 29/40 = 72.5% [57.2%, 83.9%] | 23/40 = 57.5% [42.2%, 71.5%] | 208/240 = 86.7% [81.8%, 90.4%] |
| seat4: seat model alone, one pass: DeepSeek mid | 27/30 = 90.0% [74.4%, 96.5%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 38/40 = 95.0% [83.5%, 98.6%] | 38/40 = 95.0% [83.5%, 98.6%] | 233/240 = 97.1% [94.1%, 98.6%] |

## Paired differences in accuracy (95% bootstrap interval, tasks present in both conditions)

- c minus a: -4.8 points [-10.6, +1.0] over 104 tasks (interval includes zero)
    - code: +0.0 [-21.4, +21.4] over 14
    - data: -5.6 [-16.7, +0.0] over 18
    - logic: +0.0 [+0.0, +0.0] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: +4.5 [+0.0, +13.6] over 22
    - multi4: -17.9 [-32.1, -3.6] over 28
- c minus d: -1.0 points [-7.7, +5.8] over 104 tasks (interval includes zero)
    - code: -7.1 [-21.4, +0.0] over 14
    - data: -5.6 [-16.7, +0.0] over 18
    - logic: +28.6 [+0.0, +71.4] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: +0.0 [+0.0, +0.0] over 22
    - multi4: -3.6 [-25.0, +17.9] over 28
- c2 minus c: -2.9 points [-10.6, +3.8] over 104 tasks (interval includes zero)
    - code: +0.0 [-21.4, +21.4] over 14
    - data: +0.0 [-16.7, +16.7] over 18
    - logic: -14.3 [-42.9, +0.0] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: -4.5 [-13.6, +0.0] over 22
    - multi4: -3.6 [-25.0, +17.9] over 28
- c2 minus d: -3.8 points [-11.5, +3.8] over 104 tasks (interval includes zero)
    - code: -7.1 [-21.4, +0.0] over 14
    - data: -5.6 [-16.7, +0.0] over 18
    - logic: +14.3 [-28.6, +57.1] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: -4.5 [-13.6, +0.0] over 22
    - multi4: -7.1 [-28.6, +14.3] over 28
- d minus a: -3.8 points [-9.6, +1.9] over 104 tasks (interval includes zero)
    - code: +7.1 [+0.0, +21.4] over 14
    - data: +0.0 [+0.0, +0.0] over 18
    - logic: -28.6 [-71.4, +0.0] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: +4.5 [+0.0, +13.6] over 22
    - multi4: -14.3 [-32.1, +3.6] over 28
- c minus seat4: -1.9 points [-8.7, +4.8] over 104 tasks (interval includes zero)
    - code: +14.3 [-14.3, +42.9] over 14
    - data: -5.6 [-16.7, +0.0] over 18
    - logic: +0.0 [+0.0, +0.0] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: +4.5 [+0.0, +13.6] over 22
    - multi4: -14.3 [-32.1, +0.0] over 28
- d minus seat4: -1.0 points [-7.7, +5.8] over 104 tasks (interval includes zero)
    - code: +21.4 [+0.0, +42.9] over 14
    - data: +0.0 [+0.0, +0.0] over 18
    - logic: -28.6 [-71.4, +0.0] over 7
    - math: +0.0 [+0.0, +0.0] over 15
    - multi: +4.5 [+0.0, +13.6] over 22
    - multi4: -10.7 [-25.0, +3.6] over 28
- a minus seat4: -1.2 points [-4.6, +1.7] over 240 tasks (interval includes zero)
    - code: -10.0 [-30.0, +10.0] over 30
    - data: +0.0 [+0.0, +0.0] over 50
    - logic: +0.0 [+0.0, +0.0] over 40
    - math: +0.0 [+0.0, +0.0] over 40
    - multi: -2.5 [-10.0, +5.0] over 40
    - multi4: +2.5 [-5.0, +10.0] over 40
- seat4 minus seat1: +9.2 points [+5.0, +13.8] over 240 tasks (interval excludes zero)
    - code: -6.7 [-20.0, +6.7] over 30
    - data: +14.0 [+6.0, +24.0] over 50
    - logic: +0.0 [+0.0, +0.0] over 40
    - math: +15.0 [+5.0, +27.5] over 40
    - multi: +7.5 [+0.0, +17.5] over 40
    - multi4: +20.0 [+7.5, +35.0] over 40
- seat4 minus seat2: +9.6 points [+5.0, +14.2] over 240 tasks (interval excludes zero)
    - code: -10.0 [-20.0, +0.0] over 30
    - data: +14.0 [+6.0, +24.0] over 50
    - logic: +12.5 [+2.5, +22.5] over 40
    - math: +2.5 [+0.0, +7.5] over 40
    - multi: +15.0 [+2.5, +27.5] over 40
    - multi4: +17.5 [+5.0, +32.5] over 40
- seat4 minus seat3: +10.4 points [+6.2, +15.0] over 240 tasks (interval excludes zero)
    - code: -10.0 [-20.0, +0.0] over 30
    - data: +0.0 [+0.0, +0.0] over 50
    - logic: +0.0 [+0.0, +0.0] over 40
    - math: +10.0 [+2.5, +20.0] over 40
    - multi: +22.5 [+7.5, +37.5] over 40
    - multi4: +37.5 [+22.5, +52.5] over 40

## No-answer items (refused or failed after retries) and accuracy on answered items

| condition | no answer | of which code / data / logic / math / multi / multi4 | accuracy, no-answer counted wrong | accuracy on answered items |
|---|---|---|---|---|
| a | 6/240 | 6 / 0 / 0 / 0 / 0 / 0 | 95.8% | 230/234 = 98.3% |
| c | 0/104 | 0 / 0 / 0 / 0 / 0 / 0 | 91.3% | 95/104 = 91.3% |
| c2 | 0/104 | 0 / 0 / 0 / 0 / 0 / 0 | 88.5% | 92/104 = 88.5% |
| d | 0/104 | 0 / 0 / 0 / 0 / 0 / 0 | 92.3% | 96/104 = 92.3% |
| seat1 | 0/240 | 0 / 0 / 0 / 0 / 0 / 0 | 87.9% | 211/240 = 87.9% |
| seat2 | 0/240 | 0 / 0 / 0 / 0 / 0 / 0 | 87.5% | 210/240 = 87.5% |
| seat3 | 0/240 | 0 / 0 / 0 / 0 / 0 / 0 | 86.7% | 208/240 = 86.7% |
| seat4 | 5/240 | 3 / 0 / 0 / 0 / 1 / 1 | 97.1% | 233/235 = 99.1% |

A no-answer item is one where every attempt (7 per task) returned an empty or filtered reply, or failed outright; the error text in `results/<condition>/<task>.json` says which. Panel conditions can route around a seat that declines; single-model conditions cannot.

## Cost per item

| condition | mean tokens | mean cost | median seconds | calls per item | call errors |
|---|---|---|---|---|---|
| a | 3,147 | $0.0599 | 16 | 1.2 | 49 |
| c | 184,517 | $0.4215 | 323 | 39.1 | 72 |
| c2 | 188,747 | $0.4447 | 332 | 39.4 | 143 |
| d | 150,111 | $0.2131 | 244 | 33.4 | 34 |
| seat1 | 3,337 | $0.0258 | 14 | 1.0 | 1 |
| seat2 | 10,579 | $0.0052 | 15 | 1.0 | 0 |
| seat3 | 2,928 | $0.0080 | 12 | 1.0 | 3 |
| seat4 | 10,721 | $0.0314 | 57 | 1.3 | 69 |

Critique in condition c: first draft right on 99/104 (95.2%); of 5 wrong first drafts, 3 ended right after critique and revision (60.0%); of 99 right first drafts, 7 ended wrong (7.1%).

Critique in condition c2: first draft right on 95/104 (91.3%); of 9 wrong first drafts, 5 ended right after critique and revision (55.6%); of 95 right first drafts, 8 ended wrong (8.4%).

Critique in condition d: first draft right on 95/104 (91.3%); of 9 wrong first drafts, 6 ended right after critique and revision (66.7%); of 95 right first drafts, 5 ended wrong (5.3%).

## What the hub did (condition c)

- Answers submitted to the hub: 104; wrong before the hub: 9; right before the hub: 95
- Catch rate: 9/9 wrong answers were sent back (100.0%)
- Repair rate: 4/9 wrong answers ended right after interrogation (44.4%)
- False alarms: 87/95 right answers were sent back (91.6%)
- Harm: 4/95 right answers ended wrong after interrogation (4.2%)
- Panel deadlocks (no agreement within the round budget): 42/104 (40.4%)
- Released with all three gates met: 52/104; the rest shipped with a flag
- Mean hub questions per item: 5.1

Accuracy when all gates were met: 96.2%; when released with a flag: 86.5%. A large gap means the flag is informative.

## What the hub did (condition c2, second pass with the catalogue)

- Answers submitted to the hub: 104; wrong before the hub: 8; right before the hub: 96
- Catch rate: 7/8 wrong answers were sent back (87.5%)
- Repair rate: 0/8 wrong answers ended right after interrogation (0.0%)
- False alarms: 85/96 right answers were sent back (88.5%)
- Harm: 4/96 right answers ended wrong after interrogation (4.2%)
- Panel deadlocks (no agreement within the round budget): 47/104 (45.2%)
- Released with all three gates met: 41/104; the rest shipped with a flag
- Mean hub questions per item: 4.7

Accuracy when all gates were met: 95.1%; when released with a flag: 84.1%. A large gap means the flag is informative.

Condition d deadlocks: 53/104 (51.0%)

## Readout against the paper's falsification conditions

- Hub adding value (c beats d): not shown at this sample size (c-d = -1.0 points, interval [-7.7, +5.8])

Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): a: 6, seat4: 5
