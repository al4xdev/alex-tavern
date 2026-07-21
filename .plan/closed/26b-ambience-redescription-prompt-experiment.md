# Task 26b — Ambience redescription: attack via PROMPT (experimental)

> **Status: CLOSED NEGATIVE (2026-07-21) — parked direction, documented in article No. 13.**
> 24 calls, 3 variants in 2 iterations: ALL worsened the band (16.4%→21-23%) —
> the line about setting becomes an attention magnet. Prompt-based attack closed
> as a dead end. The owner-prescribed fallback was reached, so this experiment is
> complete rather than active. Future evidence belongs to Task 26 at the event
> level (material delta from 33b), not to another prompt variant.

**Origin:** owner decision (2026-07-19): "via prompt, if it doesn't work, fallback to park it". Experimental task, child of lane 26.

## Motivating evidence (offline measurement 2026-07-19)

4 real sessions, 549 narration sentences compared with prior narrations (script `measure26.py`):

- Near-verbatim echo (≥0.8): 2 cases out of 549 — and both because compaction hid the prior sentence from the guard. The deterministic prose guard is working.
- The dominant family is DIFFERENT: **ambience paraphrase** in the 0.7–0.8 band (~9% of sentences). Real examples: "the silver case on the pedestal remains sealed" → "the silver case lies forgotten, its seal intact"; "the blue ribbon does not move" re-observed turn after turn.
- Fuzzy threshold does not solve this: >0.85 never fires; lowering to 0.7 would kill legitimate callbacks.

## Hypothesis

The prose renderer re-describes unchanged objects/states because nothing in the prompt says that ambience only deserves ink when it changes. A small rule at the END of PROSE_SYSTEM (position validated in tasks 41/42) can redirect this ink to what happened NOW.

## Method (mandatory: AGENTS.md §6, same as 42)

1. Extract 2+ real prose payloads from turns with measured redescription (use the new `replay_extract_call` MCP tool; sessions xf-full T9/T12/T19 have measured cases).
2. Test ONE-line variants via `replay_llm_call`, 3 runs each, double metric: (a) rate of sentences 0.7–0.8 vs prior narrations (reuse `measure26.py`), (b) size — must NOT drop below the floor from 42 (both rules will coexist; measure together).
3. Initial candidates (tune via curl):
   - "Spend your words on what changed or happened this beat; setting already described stays as silent backdrop unless it changes."
   - variant with explicit permission for intentional callback.
4. The validated variant IS the shipped one, same position tested.

## Acceptance Criteria

- [ ] 0.7–0.8 band falls consistently in measured payloads (target: ~9% → <4%) without breaking the verbosity floor of 42 (not met: every variant worsened it).
- [x] Zero new prompt rules shipped; never cap.
- [x] Not achieved in 2 variant iterations: **parked** per owner decision and negative result logged here and in article No. 13.

## RESULT (2026-07-19): NEGATIVE in 2 iterations → PARKED (owner fallback)

24 calls on 3 real prose payloads (T9/T12/T19 from ce87167b, turns with measured redescription), 2 runs per variant per turn; metric: % of sentences in the ≥0.7 band vs prior narrations + words (42 floor):

| Variant | band ≥0.7 | words med |
|---|---|---|
| V0 baseline | **16.4%** (9/55) | 146 |
| V1 "silent backdrop" | 22.4% (15/67) | 179 |
| V2 V1+callback | 21.3% (16/75) | 213 |
| V3 direct prohibition ("zero words") | 22.8% (13/57) | 192 |

ALL variants WORSENED the band. Analysis: any line mentioning setting/redescription acts as an attention magnet — the model re-asserts the static state by contrast ("the case remains sealed") precisely because the rule made it think about the established objects. The verbosity floor of 42 was not violated (min 118-151), but the lines also INFLATE the size.

Future direction (if it wakes up again): not prompt — it's the EVENT level. The blind renderer only adorns what the Director emits; residual redescription enters when events re-enact a static state. Real candidate: material delta auditing of 33b marking event-without-delta before prose. Postponed until after watcher integration.

## Closure decision (2026-07-21)

The success target is deliberately left unchecked: this is a measured negative,
not a retroactive success. The task is nevertheless complete because its
pre-registered fallback was to stop after two failed iterations. No code or
prompt rule from this experiment remains to validate or ship.
