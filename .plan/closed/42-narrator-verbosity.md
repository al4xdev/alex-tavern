# Task 42 — The Narrator says too little (URGENT, pure curl)

**Origin:** the user (2026-07-18). The narrator's prose is far too short. It is NOT
`max_tokens` (the budget is enormous); it is the prompt. The prompts are already
large — the solution has to be a **SHORT SENTENCE** that unlocks deepseek, not
another wall of rules.

## Suspects (to confirm over curl)
1. `PROSE_SYSTEM`: "vivid but **economical**" — an explicit instruction to be
   economical.
2. Events arrive as "ONE short sentence" each — the renderer may be mirroring the
   size of its input.
3. The anti-repetition/anti-invention rules push toward safety = brevity.

## Method (pure curl; the lesson of 41: position is part of the variant)
1. Measure a real baseline: narration length in real sessions (c2e5107b, the
   roteiro-ab artifacts) — evidence of "says too little".
2. Take REAL prose payloads; replay 3× per variant, measuring chars/sentences +
   quality (no repetition, no invention).
3. Variants = short sentences at the END of `PROSE_SYSTEM` (and/or replacing
   "economical"); NEVER a sentence cap (AGENTS.md rule); a floor/richness is fine.
4. The validated variant is the shipped one; suite; commit.

## Acceptance
- [x] Baseline measured in real sessions. (median 240-390 chars)
- [x] Winning variant: lengthens the prose consistently (3/3) without
  reintroducing repetition/invention (checked against the existing guards).
- [x] Minimal prompt diff (a short sentence), position validated.
      **Confirmed in production 2026-07-27**, see the section at the end.

## DELIVERED 2026-07-18 (pure curl, same session)

Baseline measured (real sessions): median 240-390 chars (~2-4 sentences) per
narration; in replay, payload A yielded a median of 118 chars.

Experiment (2 real payloads from different scenes, 3× per variant):
- V0 baseline: 118 / 271 chars (median).
- V1 swapping "economical"→"generous": 702 / 301 — high variance (194-1813).
- V2 a qualitative sentence ("let the scene breathe"): 567 / 351.
- **V3 a numeric floor (1 line, end of the prompt): 1247 / 568 — the largest and
  the most consistent, 3/3 on BOTH payloads. WINNER, shipped exactly as
  validated** ("Narrate at least 150 words; a beat deserves full paragraphs").

Notes: it is a FLOOR, not a cap (the AGENTS rule forbids limiting by a fixed
quantity — a floor is pressure, and the model delivers less on a small beat, which
is the desired behaviour). "vivid but economical" stayed (a counterweight against
rambling; the floor dominates — tested). The anti-repetition/anti-invention guards
remain active at runtime. Watch item: a turn with no events (the atmospheric
fallback outside a burst) now yields ~150 words of atmosphere — if that becomes
annoying, handle it in 26.

## CLOSED WITH CONFIDENCE (2026-07-19, early hours)

Pure curl method (AGENTS.md §6) on 2 real prose payloads: suspect #1 ("vivid but
economical") was real, but swapping it alone was not enough; the winning variant
was ONE FLOOR line at the END of `PROSE_SYSTEM` ("Narrate at least 150 words; a
beat deserves full paragraphs") — median 118→1247 and 271→568 chars, 3/3 on both
scenes. A floor, never a cap (house rule). The validated variant IS the shipped one
(commit "feat(prose): verbosity floor").


---

# Confirmed in production (2026-07-27)

The three acceptance boxes stayed unchecked even with the task delivered: the
18/07 experiment was a curl replay on 2 payloads, 3x per variant. Nine days of
prompt changes later — the Director rewritten, the roteiro, zones, the hint guard,
the roster of those present — nobody had checked whether the floor still holds in a
real session.

It does. 15 real sessions from today (the A/B/C arms of task 55's measurement), 122
narrations:

| | July (baseline) | July (V3 replay) | today (production) |
|---|---|---|---|
| median chars | 240-390 | 1247 / 568 | **1130** |
| median words | ~40-65 | — | **191** |
| range | — | — | 559 - 2501 chars |

18 of 122 narrations (14%) fall below 150 words, minimum 92. That is **not a
failure of the floor, it is the floor working as specified**: the task deliberately
recorded that it is a floor and not a cap ("it is a FLOOR, not a cap (the AGENTS
rule forbids limiting by a fixed quantity — a floor is pressure, and the model
delivers less on a small beat, which is the desired behaviour)"). A small beat
yielding 92 words is the original decision, not a regression of it.

**Correction of 2026-07-27 (critical review).** The "minimum 92" holds for THIS
population and is not a general property of the system. Measuring `.data/sessions`
— a different population, which includes the disposable sessions from my own
acceptance scripts — gives 71 narrations: median 1213 chars / 204 words (the
medians hold across both samples), but the tail drops to **21 words** and 24% fall
below the floor, against 15% here. The shortest narrations come from 2-character
sessions created by script, not from normal play — even so, writing "minimum 92"
as if it described the system was generalising from a sample. The reading "it is a
floor, not a cap" still stands and is in fact reinforced; the number that
accompanied it is sample-dependent, and now that is said.

The task's watch item ("a turn with no events yields ~150 words of atmosphere — if
it becomes annoying, handle it in 26") did not materialise as a problem either: no
production narration came close to being pure floor-filler, and the observed
minimum is **below** it.

One methodological caveat, for whoever re-reads this: the data comes from sessions
generated to measure *something else* (alignment/roteiro in 55), not from a
collection designed for length. That is in favour of the conclusion, not against it
— length was not what was being optimised there.
