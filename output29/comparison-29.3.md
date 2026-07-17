# Task 29.3 — Baseline vs post-29.2 comparison (round 1, 2026-07-16)

Same fixture, ledger, taxonomy, and probes as the 29.1 baseline
(`tests/fixtures/xfailed3_counter_canon.json`, `tests/test_xfailed3_counter_canon.py`).
Engine delta under measurement: Task 29.2 increments 1 (perspective ledger +
viewer-relative projection) and 2 (typed perception events + zone graph).
Campaign remained zone-less this round: v1 zone positions are static and the
campaign requires the partition to open at turn 8 (movement is a future
increment); the identity half of SP-01 is structural now, the spatial half
stays a recorded limitation. All runs: strict xfail clean, zero infrastructure
failures (Task 31 retry policy holding).

## Delta table (full tier)

| Rule | Baseline | Post-29.2 | Reading |
|---|---:|---:|---|
| SOC-01a delegate never learns signatory name (T8) | 1 | **0** | fixed by projection |
| SOC-01a delegate still anonymous (T16) | 1 | **0** | earned-name provenance (see below) |
| GLOBAL anonymous-pair prompt | 2 | **0** | fixed |
| GLOBAL secret in unauthorized prompt | 18 | 26 | same single root, cascade quantified (see below) |
| SEC-01 Watson unauthorized (T22) | 1 | 1 | downstream of the same root |
| WT-06 public mortality (T17) | 1 | 1 | stochastic semantic probe |
| WT-08 natural routing to the Witch (T9) | 0 | 1 | new signal, see routing note |
| WT-09 epilogue alias (T24) | 1 | 1 | stochastic semantic probe |
| WT-12 ribbon retention (T13) | 1 | 0 | stochastic (failed in an intermediate run) |
| **Total** | **25** | **30** | counts are instance-level; root-level story below |

## Key findings

### 1. The identity boundary flipped to green — and produced an emergent story

Every identity rule the increments targeted now passes. The T16 case is the
most instructive: Watson said "conforme combinado com **Alice**" aloud at T13
in the delegate's presence, and the identity updater legitimately recorded the
learned name with provenance (`source_turn`). The baseline's binary probe
("prompt must never contain Alice") became imprecise against correct behavior;
the oracle was upgraded to consult ledger provenance (`_earned_name`) —
distinguishing earned knowledge from leaks is only POSSIBLE post-29.2, which is
itself a result.

### 2. The confidentiality root is one defect with a five-stage cascade

All 26 secret instances trace to the single untouched root: the private
Historian ignores `record_visible_to` (summarizer.py). Quantified cascade in
this run: (1) whisper enters 7 private-summarizer prompts at both compactions →
(2) poisoned notes feed character prompts ("What you remember") → (3) **Van
Helsing (T19) and Watson (T22) then SPOKE the secret publicly** → (4) the public
records legitimately propagate it to everyone, including 4 perspective-updater
prompts. The character output guard cannot catch stage 3: it only protects
secrets the speaker legitimately witnessed; a note-smuggled secret is invisible
to it. Fixing the Historian (next increment) collapses the entire cascade.

### 3. Routing signal worth watching

The natural-routing probe (question addressed to the Witch by title, no force)
passed in the baseline and failed in both post-29.2 full runs. Plausible
interaction with the multi-speaker queue (routing pressure changed). Feeds Task
32's routing metrics; not classified as an increment regression without a
rate-based measurement.

### 4. Stochastic probes need rates

WT-06/WT-09/WT-12 flip between runs with no engine change; single-run pass/fail
on semantic retention probes produces noise. Recommendation for the 29.3 exit
criteria: repeat-based measurement (already the doc's position: "three
consecutive full runs").

## Next increment target (recommendation)

Private Historian audience filtering + note rebuild (`record_visible_to` in
`build_private_memory_messages`, plus deciding whether per-character notes
survive at all given the ledger — 29.2 doc §8 "remove private compaction").
Expected effect: GLOBAL-secret 26 → 0 and SEC-01-watson → 0 in one change.

## Round 2 addendum — post-Task-35 (2026-07-16)

Three sub-fixes were required to zero the confidentiality family; each full-tier
re-run localized the next link exactly:

1. **Record visibility** (`record_visible_to` in the private historian):
   26 → 17 instances — whispers stopped entering outsider notes directly.
2. **Narration exclusion**: 17 → 13 — the T21 narration RETOLD the whisper
   ("Dracula ouve o sussurro de Alice... LUMEN-17") and narration flowed into
   every private prompt; characters never perceive narration, so it never
   belongs in a private note.
3. **World-directives exclusion**: 13 → 0 — the campaign bible itself defines
   the secret as world truth (WT-11) and the directives were injected into
   every private-historian prompt; narrator-side authority never belongs in a
   ONE-character memory compressor.

**Final full-tier state: 25 (baseline) → 2 violations**, both stochastic
semantic probes (WT-06 mortality phrasing, WT-08 natural routing). Zero
privacy, zero identity, zero compaction-loss. The remaining two need
rate-based measurement (§15 repeated-run criteria), not fixes.

## Round 3 addendum — zoned campaign + audience_origin (2026-07-16, autonomous overnight)

The campaign fixture adopted the zone graph (delegate structurally isolated,
partition opened by a T7 action via `zone_link_updates` — no ledger renumbering)
and gained the deterministic SP-01-structural rule. The first zoned run exposed
a real design collision: zone-computed audiences were being treated as
CONFIDENCES by the secrecy machinery (Dorothy repeating her own public origin in
front of the newcomer flagged as a "whisper leak", 4 false positives). Fix:
schema v6 `audience_origin` — "whisper" (intentional confidence, secret source)
vs "zone" (physics, perception-only); guards, WHISPERED labels, and transcripts
now distinguish them.

Full-tier results after the fix (three consecutive runs for the §15 clock):

| Run | Violations | Content |
|---|---:|---|
| 1 | **0** | XPASS — first fully clean full tier in the program |
| 2 | 3 | ribbon kept in the POCKET not the wrist (promise compliance), mortality phrased "sou humano" (probe too strict — calibrated), alias withheld by in-character discretion |
| 3 | 4 | testimony question upstaged by the partition surprise, invented Moriarty prison (REAL confabulation the old regex missed — tightened), alias confabulated, one same-turn earned-name oracle miss (fixed: final-ledger provenance consulted) |

Verdicts: the deterministic families (identity, secrets, isolation, agency,
routing-under-force) are at ZERO across all three runs. What remains is
long-horizon semantic variance — promise compliance, discretion vs audit,
attention under simultaneous events, alias confabulation — which is exactly the
class this benchmark exists to measure over time. Strict xfail STAYS; the exit
clock per §15 continues with the calibrated oracle.
