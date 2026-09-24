# Task 69: the cohort comparison does not resolve capacity

2026-09-05. Decision: keep capacity and attention mechanisms undiagnosed. The pre-registered read found no unequivocal re-staging of a completed physical event among the earliest flagged pairs from 16 below-threshold sessions. This does not show those sessions have no defect: the fixed positive-only sample contains repeatable gestures, continuing conditions and uncertain object identities. The rule in [PREREGISTRATION.md](PREREGISTRATION.md), written before scanning on 2026-09-05, was: one clear physical repeat below the recorded threshold would show threshold attainment is not necessary for that example; zero confirmed cases leaves the question unresolved, not falsified. This fixed sample did not satisfy the positive criterion. This read cannot support the earlier claim that capacity is excluded, nor estimate how often genuine restaging happens.

## Reading, one selected pair per session

OBSERVED, unblinded manual read of both event records and the repeating prompt's relevant intervening transcript and complete facts bag. Selection was fixed before scanning: earliest lexical flag in each below-40 session; repeated turn, source turn and text break ties. No second candidate was substituted to obtain a clearer positive. Table judgments are conservative case readings, not detector accuracy estimates.

| session | prompt peak | turns | reading and reason |
|---|---:|---|---|
| 00997daa | 29 | 12→15 | Indeterminate: messenger enters carrying a sealed scroll twice, but T13 explicitly has him leave. Return or another messenger remains possible. |
| 05e0dffc | 10 | 14→16 | Continuation: Bruna remains in the center with buzzing bracelets. No completed transition is repeated. |
| 07218133 | 9 | 6→7 | Indeterminate object: Maelis flips a nameplate twice; sixteen plates exist and the chosen name/plate is not identified. |
| 11028536 | 26 | 7→8 | Indeterminate repeated gesture: Riven laughs/crosses his arms again; laughter can recur. |
| 21f7c4e1 | 29 | 18→19 | Indeterminate progression: the same crack widens with stone chips; it can widen further after its earlier widening. |
| 22b27d6e | 30 | 14→15 | Continuation/intensification: runic glow persists and sulfur smell strengthens. |
| 377582f0 | 31 | 4→5 | Continuation: Garran descends and positions himself, then remains there. |
| 54bcdace | 36 | 11→13 | Different action: the creature advances toward Asword, then retreats toward the fissure. |
| 55d03896 | 36 | 19→20 | Progression: Doran engraves a rune which lights, then completes it and stabilizes the floor. |
| 5d60575d | 30 | 12→13 | Indeterminate repeatable inspection: Doran taps/tests hollow flooring again; earlier narration tests multiple spots. |
| 63deac61 | 19 | 9→10 | Indeterminate departure: Riven starts toward the door twice without an intervening arrival. Repeated staging is plausible, a completed transition is not established. |
| 7fd84e9a | 17 | 2→4 | Continuation possible: Garran's palm strike causes a buzz, and later its effect is described; intervening narration retains the hum. |
| 834f91e5 | 27 | 5→6 | Continuing examination: Doran notices soot and then examines soot/door. No new physical creation of soot. |
| a3e1ceda | 25 | 7→10 | Different target: Cassian's monocle gesture changes its focus from the director to the crack. |
| c76037ff | 28 | 13→15 | Indeterminate object: a crack opens on the north-stand-to-pulpit route, persists at T14, then a new crack follows that route. Suspicious repetition, but identity is not established. |
| d0cc98e5 | 35 | 16→17 | Progression: Cassian takes another step back on each turn. |

## Diagnostic counts, not a restaging rate

The original 33-session inventory is pinned by debug path and SHA in `results.json`; the two later post-79 sessions are excluded. Eighteen sessions never reach 40 keys in any recorded Director request, fifteen reach at least 40. Two below-threshold sessions (045e431b, 8e3971ab) have no candidate events after turn 3 and remain in the inventory but not rate summaries. The scan inspected 1,135 Director records from the 33 sessions and reported zero missing/unparseable Physical facts blocks. This verifies recorded request coverage, not absence of unlogged processing.

The scanner reuses the archived Unicode-normalized SequenceMatcher >=0.6 detector within the prior three turns. Both sides are restricted to physical_outcome/observation; those labels still do not guarantee semantic physical events. Each event contributes at most one flag. Last parseable Director response per turn is used, not every retry; parseability is not proof of runtime acceptance/persistence. There were 53 earlier parseable responses discarded and 15 unparseable responses, counted across 33 sessions; full per-session provenance remains in `results.json`.

| cohort | measurable sessions | flags/events | pooled lexical rate | session median | population SD | session range |
|---|---:|---:|---:|---:|---:|---:|
| recorded peak below 40 | 16 | 145/1394 | 10.40% | 10.66% | 4.13 pp | 1.72–18.63% |
| recorded peak at least 40 | 15 | 149/1558 | 9.56% | 8.62% | 4.15 pp | 3.37–17.80% |

These are descriptive lexical frequencies in this archive, not estimates of genuine repeats. Shared represented turn indices are 4–40; restricting to them changes neither count. That restriction does not balance opportunity or match individual sessions. Oldcode sessions 45dac069/976e9d42 peak at 58/70 keys, so threshold attainment does not certify a cap operated. Cohorts also differ in engine revision, history and scene trajectory. Similar frequencies cannot establish equivalence or exclude eviction, retrieval or attention mechanisms. Historical 703/5064 used a different denominator and remains separate.

## Reproduce and inspect

`uv run python plans/artifacts/69-session-cohorts/compare_cohorts.py` refuses to overwrite an existing result. Local artifact mtimes are 2026-09-05 16:21:21 UTC for PREREGISTRATION.md and 16:22:38 UTC for results.json; they document this run order, not an immutable third-party timestamp. `dossier.json` preserves each selected pair with full prompt messages/facts for review. Raw JSON follows the repository's existing artifact ignore policy; raw files remain local unless explicitly synchronized.

## Review disposition

The isolated critic accepted the unresolved-mechanism conclusion and the separation of lexical counts from completed-event readings. It requested the exact prospective rule, record denominator and chronology; these are now supplied above. Its strongest reservation remains: a completed-event criterion does not cover repeated starts or repetitive prose. No broader no-defect conclusion follows. Recounting the pinned sources or identifying one unequivocal reset in the fixed sample would falsify the corresponding inventory or reading claim. The lexical metric remains REPORT, DO NOT GATE.

## Per-session diagnostic inventory

| session | peak request keys | flags/events after T3 | lexical rate | discarded earlier parses | invalid responses |
|---|---:|---:|---:|---:|---:|
| 00997daa | 29 | 11/89 | 12.36% | 2 | 0 |
| 045e431b | 9 | 0/0 | not measurable | 0 | 0 |
| 05e0dffc | 10 | 5/47 | 10.64% | 0 | 0 |
| 07218133 | 9 | 6/48 | 12.50% | 1 | 0 |
| 09aabf25 | 40 | 14/105 | 13.33% | 2 | 0 |
| 11028536 | 26 | 15/102 | 14.71% | 10 | 1 |
| 17ec48d5 | 40 | 6/101 | 5.94% | 2 | 0 |
| 21f7c4e1 | 29 | 5/61 | 8.20% | 0 | 0 |
| 22b27d6e | 30 | 2/69 | 2.90% | 0 | 0 |
| 34390b86 | 40 | 10/116 | 8.62% | 0 | 0 |
| 377582f0 | 31 | 11/111 | 9.91% | 1 | 0 |
| 4351ed30 | 40 | 6/86 | 6.98% | 0 | 1 |
| 45dac069 | 58 | 7/108 | 6.48% | 7 | 1 |
| 513cb09f | 40 | 12/111 | 10.81% | 1 | 0 |
| 54bcdace | 36 | 7/112 | 6.25% | 1 | 0 |
| 55d03896 | 36 | 13/117 | 11.11% | 0 | 1 |
| 5c994c42 | 40 | 6/84 | 7.14% | 0 | 0 |
| 5d60575d | 30 | 1/58 | 1.72% | 1 | 0 |
| 63deac61 | 19 | 14/106 | 13.21% | 8 | 0 |
| 75d9f36f | 40 | 21/118 | 17.80% | 1 | 0 |
| 7fd84e9a | 17 | 9/70 | 12.86% | 1 | 0 |
| 834f91e5 | 27 | 11/103 | 10.68% | 0 | 0 |
| 87157fa1 | 40 | 4/109 | 3.67% | 0 | 1 |
| 8bd4d0f1 | 40 | 10/123 | 8.13% | 0 | 2 |
| 8e3971ab | 9 | 0/0 | not measurable | 0 | 0 |
| 976e9d42 | 70 | 11/115 | 9.57% | 3 | 1 |
| a3e1ceda | 25 | 19/102 | 18.63% | 8 | 1 |
| b11b38dc | 40 | 8/85 | 9.41% | 2 | 0 |
| c76037ff | 28 | 7/89 | 7.87% | 1 | 3 |
| d0cc98e5 | 35 | 9/110 | 8.18% | 0 | 1 |
| d5a2ccf0 | 40 | 16/97 | 16.49% | 0 | 0 |
| d8310b8b | 40 | 15/111 | 13.51% | 0 | 1 |
| ec84b31e | 40 | 3/89 | 3.37% | 1 | 1 |
