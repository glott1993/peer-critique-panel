# Pilot results

Run started 2026-10-17T07:20:20Z; OpenRouter; tasks from `tasks/pilot2_tasks.json`.
Seats: anthropic/claude-sonnet-5, openai/gpt-5.6-luna-pro, google/gemini-3.8-flash, deepseek/deepseek-v4-pro-0813. Hub: anthropic/claude-opus-5. Baseline: anthropic/claude-opus-5. Rounds 3, hub budget 6, dissenter True.

## Accuracy (95% Wilson interval)

| condition | code | data | logic | math | multi | multi4 | all |
|---|---|---|---|---|---|---|---|
| a: single frontier model, one pass (temperature 0.3) | 24/30 = 80.0% [62.7%, 90.5%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 38/40 = 95.0% [83.5%, 98.6%] | 39/40 = 97.5% [87.1%, 99.6%] | 231/240 = 96.2% [93.0%, 98.0%] |
| c: panel with hub | 13/14 = 92.9% [68.5%, 98.7%] | 17/18 = 94.4% [74.2%, 99.0%] | 7/7 = 100.0% [64.6%, 100.0%] | 15/15 = 100.0% [79.6%, 100.0%] | 22/22 = 100.0% [85.1%, 100.0%] | 22/28 = 78.6% [60.5%, 89.8%] | 96/104 = 92.3% [85.6%, 96.1%] |
| c2: panel with hub, second pass, hub reads the catalogue built by the first | 13/14 = 92.9% [68.5%, 98.7%] | 17/18 = 94.4% [74.2%, 99.0%] | 6/7 = 85.7% [48.7%, 97.4%] | 15/15 = 100.0% [79.6%, 100.0%] | 21/22 = 95.5% [78.2%, 99.2%] | 21/28 = 75.0% [56.6%, 87.3%] | 93/104 = 89.4% [82.0%, 94.0%] |
| d: panel without hub | 14/14 = 100.0% [78.5%, 100.0%] | 18/18 = 100.0% [82.4%, 100.0%] | 5/7 = 71.4% [35.9%, 91.8%] | 15/15 = 100.0% [79.6%, 100.0%] | 22/22 = 100.0% [85.1%, 100.0%] | 23/28 = 82.1% [64.4%, 92.1%] | 97/104 = 93.3% [86.8%, 96.7%] |
| seat1: seat model alone, one pass: Anthropic mid | 29/30 = 96.7% [83.3%, 99.4%] | 43/50 = 86.0% [73.8%, 93.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 34/40 = 85.0% [70.9%, 92.9%] | 36/40 = 90.0% [76.9%, 96.0%] | 30/40 = 75.0% [59.8%, 85.8%] | 212/240 = 88.3% [83.7%, 91.8%] |
| seat2: seat model alone, one pass: OpenAI mid | 30/30 = 100.0% [88.6%, 100.0%] | 43/50 = 86.0% [73.8%, 93.0%] | 35/40 = 87.5% [73.9%, 94.5%] | 39/40 = 97.5% [87.1%, 99.6%] | 33/40 = 82.5% [68.0%, 91.3%] | 31/40 = 77.5% [62.5%, 87.7%] | 211/240 = 87.9% [83.2%, 91.5%] |
| seat3: seat model alone, one pass: Google mid | 30/30 = 100.0% [88.6%, 100.0%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 36/40 = 90.0% [76.9%, 96.0%] | 29/40 = 72.5% [57.2%, 83.9%] | 23/40 = 57.5% [42.2%, 71.5%] | 208/240 = 86.7% [81.8%, 90.4%] |
| seat4: seat model alone, one pass: DeepSeek mid | 27/30 = 90.0% [74.4%, 96.5%] | 50/50 = 100.0% [92.9%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 40/40 = 100.0% [91.2%, 100.0%] | 39/40 = 97.5% [87.1%, 99.6%] | 38/40 = 95.0% [83.5%, 98.6%] | 234/240 = 97.5% [94.7%, 98.8%] |

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
- seat4 minus seat3: +10.8 points [+6.7, +15.4] over 240 tasks (interval excludes zero)
    - code: -10.0 [-20.0, +0.0] over 30
    - data: +0.0 [+0.0, +0.0] over 50
    - logic: +0.0 [+0.0, +0.0] over 40
    - math: +10.0 [+2.5, +20.0] over 40
    - multi: +25.0 [+10.0, +40.0] over 40
    - multi4: +37.5 [+22.5, +52.5] over 40

## No-answer items (refused or failed after retries) and accuracy on answered items

| condition | no answer | of which code / data / logic / math / multi / multi4 | accuracy, no-answer counted wrong | accuracy on answered items |
|---|---|---|---|---|
| a | 6/240 | 6 / 0 / 0 / 0 / 0 / 0 | 96.2% | 231/234 = 98.7% |
| c | 0/104 | 0 / 0 / 0 / 0 / 0 / 0 | 92.3% | 96/104 = 92.3% |
| c2 | 0/104 | 0 / 0 / 0 / 0 / 0 / 0 | 89.4% | 93/104 = 89.4% |
| d | 0/104 | 0 / 0 / 0 / 0 / 0 / 0 | 93.3% | 97/104 = 93.3% |
| seat1 | 0/240 | 0 / 0 / 0 / 0 / 0 / 0 | 88.3% | 212/240 = 88.3% |
| seat2 | 0/240 | 0 / 0 / 0 / 0 / 0 / 0 | 87.9% | 211/240 = 87.9% |
| seat3 | 0/240 | 0 / 0 / 0 / 0 / 0 / 0 | 86.7% | 208/240 = 86.7% |
| seat4 | 5/240 | 3 / 0 / 0 / 0 / 1 / 1 | 97.5% | 234/235 = 99.6% |

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

Critique in condition c: first draft right on 100/104 (96.2%); of 4 wrong first drafts, 3 ended right after critique and revision (75.0%); of 100 right first drafts, 7 ended wrong (7.0%).

Critique in condition c2: first draft right on 96/104 (92.3%); of 8 wrong first drafts, 5 ended right after critique and revision (62.5%); of 96 right first drafts, 8 ended wrong (8.3%).

Critique in condition d: first draft right on 96/104 (92.3%); of 8 wrong first drafts, 6 ended right after critique and revision (75.0%); of 96 right first drafts, 5 ended wrong (5.2%).

## What the hub did (condition c)

- Answers submitted to the hub: 104; wrong before the hub: 8; right before the hub: 96
- Catch rate: 8/8 wrong answers were sent back (100.0%)
- Repair rate: 4/8 wrong answers ended right after interrogation (50.0%)
- False alarms: 88/96 right answers were sent back (91.7%)
- Harm: 4/96 right answers ended wrong after interrogation (4.2%)
- Panel deadlocks (no agreement within the round budget): 42/104 (40.4%)
- Released with all three gates met: 52/104; the rest shipped with a flag
- Mean hub questions per item: 5.1

Accuracy when all gates were met: 98.1%; when released with a flag: 86.5%. A large gap means the flag is informative.

## What the hub did (condition c2, second pass with the catalogue)

- Answers submitted to the hub: 104; wrong before the hub: 7; right before the hub: 97
- Catch rate: 6/7 wrong answers were sent back (85.7%)
- Repair rate: 0/7 wrong answers ended right after interrogation (0.0%)
- False alarms: 86/97 right answers were sent back (88.7%)
- Harm: 4/97 right answers ended wrong after interrogation (4.1%)
- Panel deadlocks (no agreement within the round budget): 47/104 (45.2%)
- Released with all three gates met: 41/104; the rest shipped with a flag
- Mean hub questions per item: 4.7

Accuracy when all gates were met: 97.6%; when released with a flag: 84.1%. A large gap means the flag is informative.

Condition d deadlocks: 53/104 (51.0%)

## Readout against the paper's falsification conditions

- Hub adding value (c beats d): not shown at this sample size (c-d = -1.0 points, interval [-7.7, +5.8])

Items that failed with an error (excluded from hub metrics, counted as wrong in accuracy; rerun to retry): a: 6, seat4: 5

## Panel stages, flags and checks (added for v1.3)

First draft = the assembled answer before any critique (pre_critique_correct); pre-hub = after critique and revision (pre_hub_correct); final = correct. In d there is no hub, so pre-hub and final coincide.

### First draft, after critique, final

- c: first draft right 100/104 (96.2%); after critique 96; final 96. Wrong first drafts: multi2-11, multi4-06, multi4-17, multi4-33
- c2: first draft right 96/104 (92.3%); after critique 97; final 93. Wrong first drafts: multi2-21, multi2-34, multi4-06, multi4-18, multi4-25, multi4-26, multi4-31, multi4-35
- d: first draft right 96/104 (92.3%); after critique 97; final 97. Wrong first drafts: data2-07, data2-10, multi4-04, multi4-17, multi4-24, multi4-26, multi4-33, multi4-35

### Critique alone (first draft to pre-hub) and the hub alone (pre-hub to final)

- c critique: right first draft to wrong pre-hub 7 (code2-14, code2-27, data2-17, data2-49, multi2-35, multi4-05, multi4-31); wrong first draft to right pre-hub 3 (multi2-11, multi4-17, multi4-33); net -4
- c hub: right pre-hub to wrong final 4 (multi4-24, multi4-28, multi4-35, multi4-37); wrong pre-hub to right final 4 (code2-14, data2-17, multi2-35, multi4-31); net +0
- c2 critique: right first draft to wrong pre-hub 4 (data2-34, logic2-06, multi4-11, multi4-39); wrong first draft to right pre-hub 5 (multi2-21, multi4-06, multi4-18, multi4-26, multi4-31); net +1
- c2 hub: right pre-hub to wrong final 4 (code2-14, multi4-05, multi4-34, multi4-38); wrong pre-hub to right final 0 (none); net -4
- d critique: right first draft to wrong pre-hub 5 (logic2-01, logic2-34, multi4-19, multi4-31, multi4-39); wrong first draft to right pre-hub 6 (data2-07, data2-10, multi4-04, multi4-17, multi4-26, multi4-35); net +1

### Pairwise flips between panel conditions (tasks present in both)

- c vs c2 over 104: first draft differs on 10 (right in c only: multi2-21, multi2-34, multi4-18, multi4-25, multi4-26, multi4-31, multi4-35; right in c2 only: multi2-11, multi4-17, multi4-33); final differs on 15 (right in c only: code2-14, data2-34, logic2-06, multi2-34, multi4-11, multi4-25, multi4-34, multi4-38, multi4-39; right in c2 only: code2-27, data2-49, multi4-06, multi4-24, multi4-28, multi4-37)
- c vs d over 104: first draft differs on 8 (right in c only: data2-07, data2-10, multi4-04, multi4-24, multi4-26, multi4-35; right in d only: multi2-11, multi4-06); final differs on 13 (right in c only: logic2-01, logic2-34, multi4-19, multi4-31, multi4-33, multi4-39; right in d only: code2-27, data2-49, multi4-05, multi4-06, multi4-28, multi4-35, multi4-37)
- c2 vs d over 104: first draft differs on 12 (right in c2 only: data2-07, data2-10, multi4-04, multi4-17, multi4-24, multi4-33; right in d only: multi2-21, multi2-34, multi4-06, multi4-18, multi4-25, multi4-31); final differs on 16 (right in c2 only: logic2-01, logic2-34, multi4-19, multi4-24, multi4-31, multi4-33; right in d only: code2-14, data2-34, logic2-06, multi2-34, multi4-05, multi4-11, multi4-25, multi4-34, multi4-35, multi4-38)

### Accuracy by agreement

- c: deadlocked 35/42 (83.3%), agreed 61/62 (98.4%); Fisher's exact p = 0.0070 one-sided (deadlocked more often wrong), 0.0070 two-sided, odds ratio 12.20. Wrong when deadlocked: code2-27, data2-49, multi4-05, multi4-06, multi4-24, multi4-28, multi4-37; wrong when agreed: multi4-35
- c2: deadlocked 37/47 (78.7%), agreed 56/57 (98.2%); Fisher's exact p = 0.0014 one-sided (deadlocked more often wrong), 0.0022 two-sided, odds ratio 15.14. Wrong when deadlocked: code2-14, data2-34, multi2-34, multi4-05, multi4-11, multi4-25, multi4-34, multi4-35, multi4-38, multi4-39; wrong when agreed: logic2-06
- d: deadlocked 48/53 (90.6%), agreed 49/51 (96.1%); Fisher's exact p = 0.2346 one-sided (deadlocked more often wrong), 0.4374 two-sided, odds ratio 2.55. Wrong when deadlocked: multi4-19, multi4-24, multi4-31, multi4-33, multi4-39; wrong when agreed: logic2-01, logic2-34

### Flagged releases by reason (a task can fail more than one gate)

- c: flagged 52 (7 wrong), all gates met 52 (1 wrong); Fisher's exact p = 0.0299 one-sided (flagged more often wrong), 0.0599 two-sided, odds ratio 7.93
    - deadlock: 42 tasks, 35 right (83.3%); wrong: code2-27, data2-49, multi4-05, multi4-06, multi4-24, multi4-28, multi4-37
    - hub questions open: 23 tasks, 19 right (82.6%); wrong: code2-27, data2-49, multi4-28, multi4-37
    - failed check: 2 tasks, 1 right (50.0%); wrong: code2-27
    - overlaps: deadlock only: 28 (25 right); deadlock+hub questions open: 12 (9 right); hub questions open only: 10 (10 right); deadlock+hub questions open+failed check: 1 (0 right); deadlock+failed check: 1 (1 right)
- c2: flagged 63 (10 wrong), all gates met 41 (1 wrong); Fisher's exact p = 0.0263 one-sided (flagged more often wrong), 0.0467 two-sided, odds ratio 7.55
    - deadlock: 47 tasks, 37 right (78.7%); wrong: code2-14, data2-34, multi2-34, multi4-05, multi4-11, multi4-25, multi4-34, multi4-35, multi4-38, multi4-39
    - hub questions open: 32 tasks, 29 right (90.6%); wrong: multi2-34, multi4-11, multi4-39
    - failed check: 2 tasks, 2 right (100.0%); wrong: none
    - overlaps: deadlock only: 29 (22 right); deadlock+hub questions open: 17 (14 right); hub questions open only: 15 (15 right); failed check only: 1 (1 right); deadlock+failed check: 1 (1 right)
- d: flagged 53 (5 wrong), all gates met 51 (2 wrong); Fisher's exact p = 0.2346 one-sided (flagged more often wrong), 0.4374 two-sided, odds ratio 2.55
    - deadlock: 53 tasks, 48 right (90.6%); wrong: multi4-19, multi4-24, multi4-31, multi4-33, multi4-39

### Hub questions used

- c: questions per task {0: 8, 2: 2, 3: 12, 4: 3, 6: 79}; mean 5.06; at the most used (6): 79 tasks, 72 right; no question asked: code2-28, data2-45, math2-10, multi2-31, multi4-08, multi4-10, multi4-17, multi4-33
- c2: questions per task {0: 12, 2: 3, 3: 14, 4: 1, 5: 3, 6: 71}; mean 4.74; at the most used (6): 71 tasks, 65 right; no question asked: code2-13, data2-17, data2-40, math2-04, multi2-07, multi2-31, multi2-35, multi4-06, multi4-19, multi4-26, multi4-32, multi4-35

### Checks ordered by the hub and run outside the panel

- c: 286 checks on 96 tasks; arithmetic invalid fail: 4; arithmetic valid fail: 4; arithmetic valid pass: 264; code valid fail: 1; code valid pass: 13. Failed: 5 on 4 tasks (code2-27 code: pre-hub wrong, final wrong, release blocked; multi2-20 arithmetic: pre-hub right, final right, release blocked; multi4-31 arithmetic: pre-hub wrong, final right, release not blocked; multi4-31 arithmetic: pre-hub wrong, final right, release not blocked; multi4-34 arithmetic: pre-hub right, final right, release not blocked)
- c2: 263 checks on 89 tasks; arithmetic valid fail: 5; arithmetic valid pass: 244; code valid pass: 14. Failed: 5 on 5 tasks (code2-11 arithmetic: pre-hub right, final right, release not blocked; code2-28 arithmetic: pre-hub right, final right, release blocked; data2-10 arithmetic: pre-hub right, final right, release not blocked; multi4-27 arithmetic: pre-hub right, final right, release not blocked; multi4-37 arithmetic: pre-hub right, final right, release blocked)
