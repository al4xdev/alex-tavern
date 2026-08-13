# Task 41 — An omniscient Director + canon reconciliation (URGENT)

**Origin:** the user's finding (2026-07-18, real session c2e5107b): the Director saw NO
thought at all — the player's thought ("estou atrasado, o evento já deve ter começado")
was dead data, and the prose invented "Link entered the hall" while the confirmed event
said he was running through the city.

## Goal (decided by the user)
- The Director is OMNISCIENT: it receives every private thought (labelled).
- The prose stays BLIND (only confirmed observable events) — structural, already true.
- Thoughts guide timing/pressure/dramatic intent; they never become public fact or another
  character's knowledge (deterministic guard).

## Evidence (isolated replays on the REAL T1 payload of c2e5107b, deepseek)
- V0 blind: 3/3 WRONG premise ("Link leaves the hall" — he was never there).
- V1 omniscient: 2/3 correct + dramatic irony for free; 1/3 teleports.
- V2 + a reconciliation rule: 3/3 correct premise, BUT 2/3 change the GLOBAL `location`
  (dragging the other 20 into the wrong canon) — a typed lever is missing.
- V3 + dynamic zone creation: run0 PERFECT (location intact + zone_moves creates "ruas da
  cidade" for C1 + the right event); 3/3 correct premise.

## The ownership rule (design decision)
| About what | Who wins |
|---|---|
| The character's OWN state (where I am, what I am doing) | the declarer — the Director RECONCILES the canon through a typed decision |
| Facts of the world / other characters | canon — a declaration becomes a claim (task 24's rule) |
| Genuine ambiguity | a DIEGETIC question through return_control, never a meta one |

## Implementation
1. `narrator.py`: thoughts enter the Director's HISTORY as `TYPE=PRIVATE THOUGHT (only you
   perceive this)` (without revealing that a human exists); omniscience + reconciliation
   rules in the system prompt.
2. Dynamic zones: `zone_moves` may CREATE a new zone (born isolated); when materialising
   the first zone in a scene with no zones, everyone else present is placed in a stage zone
   (= location) — otherwise "the unplaced perceive everything" and the isolation does not
   happen. The perception clamp then protects for free.
3. A deterministic anti-leak guard: rare tokens present ONLY in thoughts (minus those
   already public) are redacted from the content of perception_events — the same machinery
   as whisper confidentiality.
4. An ordering fix: scene_update/zone_moves apply BEFORE the prose renders (the prose was
   receiving old canon + a new event → and inventing a reconciliation).

## Acceptance
- [x] The Director receives labelled thoughts (from every owner); a real replay adjudicates
  without leaking (validated V1-V3). — replay in the original delivery; the label now has a
  test: `test_thought_containment.py::test_the_thought_reaches_the_director_labeled`
- [x] prose/character/summarizer/ledger still do NOT see others' thoughts (explicit
  structural tests). — **this was missing**, written 2026-07-27:
  `tests/test_thought_containment.py`, see the section at the end
- [x] Guard: a thought-exclusive token never appears in perception_events. —
  `test_omniscient_director.py::test_thought_only_token_redacted_from_events`
- [x] Dynamic zone: moving to a new zone creates it isolated + a stage for the others;
  witnesses clamped by construction. — `TestRunnerZoneMaterialization`
  (`test_first_split_creates_stage_and_audible_zone`,
  `test_a_declared_gap_seals_the_new_zone_in_the_same_beat`) + `TestPartialMoveLocationClamp`
- [x] The prose renders with reconciled canon (ordering fixed). —
  `test_omniscient_director.py::test_prose_renders_with_reconciled_canon`
- [x] xfailed3 (the leak families) re-validated — done 2026-07-26/27, see "xfailed3
  revalidation" at the end of the file.

## DELIVERED 2026-07-18 — caveat RESOLVED on 2026-07-27 (see the end of the file)

Implemented, tested (9 new tests in `tests/test_omniscient_director.py`; suite 619) and
validated by replay with the production BUILDER on the real case c2e5107b: **3/3 correct
premise** (zero teleports; run0 even acknowledged in the canon "everyone except Link, who
has not arrived"; runs 1-2 created the zone and moved C1).

### Delivered
- An omniscient Director: thoughts in HISTORY labelled `PRIVATE THOUGHT (only you perceive
  this)`; omniscience + reconciliation rules CLOSING the system prompt (position validated —
  in the middle, buried under the directives, they failed 3/3; the lesson is codified in
  AGENTS.md §6).
- A deterministic guard: `hidden_thought_tokens` (confidentiality) redacts from
  perception_events the tokens that exist ONLY in thoughts; the payload calibration already
  exempts generic feelings ("estou atrasado" → 0 tokens).
- Dynamic zones: `zone_moves` creates a new zone (sanitised, born isolated); when
  materialising one in a scene with no zones, everyone else present gets the stage zone
  (otherwise "the unplaced perceive everything" would cancel the isolation).
- A location clamp: a PARTIAL movement never changes the global location (zones express the
  split; location only changes when the whole scene moves) — this kills the model's 2/3 wart
  of emitting zone+location together.
- Ordering fixed: canon (scene_update/zone_moves) applies BEFORE the prose — the prose
  renders the reconciled scene (this was the cause of "Link entered the hall"). An
  intentional side effect: whoever moves speaks FROM the destination in the same beat (the
  record's audience is physical; the Director's witness clamps stay pre-move).

### Caveat (why this is not a 100% confident close)
- The xfailed3 leak families need re-validating under full omniscience (NPC thoughts now
  reach the Director) when the xfail clock runs (`-m llm`).

## CAVEAT RESOLVED → CLOSED WITH CONFIDENCE (2026-07-19, early hours)

Full xfailed3 (24 turns, 2 tiers) post-41: ZERO violations of the leak families (a private
thought in prose/character; a secret in an unauthorised prompt). The deterministic guard +
the validated end-position hold omniscience without leaking. Migrated to closed/.


---

# xfailed3 revalidation (2026-07-27) — the caveat that was missing

This task's only caveat was "re-validate xfailed3 when the xfail clock runs". It ran, four
times, on the 2026-07-26 tree — which already has `SESSION_SCHEMA_VERSION` 14 and all of
that day's prompt changes (the Director's rule 5 rewritten, `UPCOMING EVENT IS MANDATORY`,
the zone default inverted, the roster of those present in the Character).

**No leak family appeared.** The violations classified across the four runs were:

| Run | Violations |
|---|---|
| 1 and 2 | (no artifact export) |
| 3 | `unearned_identity_familiarity` — a regression introduced that same day by the roster of those present, fixed in `604dfab` |
| 4 (post-fix) | `WT-10-created-not-creator`, `WT-12-ribbon-retention` |

None of them belongs to the class this task protects (a private thought leaking into
`perception_events`, teleportation, the global canon dragged along). The two from run 4 are
`world_truth_contradiction` and `compaction_loss` — the noise distribution task 29 already
documented.

Worth recording what run 3 proves about this benchmark: it **discriminates**. An identity
regression introduced that same day showed up named by rule, in one run, with the two
previous ones clean. That is the opposite of undifferentiated noise.

The 13 turns with compaction and restore completed in all four runs, with no infrastructure
failure. The deterministic `hidden_thought_tokens` guard stays green in the suite (876
tests).

**Caveat closed.** Nothing remains pending in this task.


---

# The structural criterion, finally structural (2026-07-27)

Five blank acceptance boxes. Four only needed a read — the tests existed, and they are
pointed at inline above. The second was a real gap, and the word that matters in it is
*structural*.

Thought secrecy is not implemented in one place. It is four independent implementations of
the same invariant:

| agent | how it filters |
|---|---|
| Character | `character.py:414` keeps only the caller's own |
| Director | `narrator.py:460` keeps **all** of them, labelled — on purpose |
| Prose | never asks for the `thought` type |
| Summarizer / ledger | `capture_memory` only sweeps `speech`/`action` |

No test sat above all four. A fifth agent, or a refactor unifying history formatting
(exactly what Wave 4.1's `src/prompting.py` started doing), could knock out one of the
filters with the suite green.

`tests/test_thought_containment.py` tests no filter at all. It plants **one** meaningless
token (`veludo-quirografo-8812`) inside a character's thought and verifies, in the real
prompt each builder produces, that it reaches the Director and reaches nobody else. All the
builders are pure, so the verification is exact: no mock, no network, no inspecting
intermediate state.

Ten cases. The two that are not obvious:

- **The controlled character is not a privileged reader.** A human operates one character,
  and that character reads exactly what the others read. That was the plausible asymmetry
  for someone to introduce "for UI convenience".
- **Not even the thinker keeps the thought in the ledger.** The ledger survives compaction
  and goes on feeding prompts afterwards; a thought recorded there would outlive the record
  that produced it and re-enter through a channel never built to carry it. That is why `C2`
  is in the parametrize.

Two corrections the test forced on me, worth keeping as documentation: the Director receives
`SPEAKER=C2`, not `SPEAKER=Marta` (`speaker_label` only translates the `Player` marker; the
`ID=C2 | NAME=Marta` roster in the same prompt resolves it), and `project_text_for_viewer`
projects identity in free prose — it is not the ledger's guardian. The guardian is
`capture_memory`, and that is what the test hits.
