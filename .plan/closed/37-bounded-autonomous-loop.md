# Task 37 — Bounded Autonomous Loop

**Depends on:** Task 36 (Director/Resolver split). Do not start before it.

## Goal

Let the world play several beats without the human driving every step: the
Director picks an event or next agent → Character produces speech/thought/
intent → Resolver adjudicates → blind renderer narrates → repeat, until a stop
condition returns control to the player.

## Stop conditions (user spec, 2026-07-16)

- someone addresses or reacts directly to the player's character;
- a relevant strategic choice appears;
- the player's character is in danger and must decide;
- a small dramatic beat completes;
- the autonomous-action budget is exhausted (hard cap);
- the player interrupts or forces a speaker.

## Product decisions this task owns (were deliberately deferred)

- **Undo semantics across a burst**: one beat vs the whole burst (the map's
  open question #2). Recommendation to evaluate first: undo pops one beat;
  a "undo burst" affordance pops to the pre-burst checkpoint.
- **Transactionality**: whole burst under one session lock with per-beat
  commits, or one atomic commit; crash mid-burst must not leave partial beats.
- **Latency UX**: 3 sequential calls per beat ≈ 6-8s; bursts need progressive
  rendering (stream each beat to the frontend as it commits).

## Direct evidence this attacks

Sessions 091b11c6/ef6b5b90: skips still wait for the player; the game state
stalls without manual invention (Task 26 evidence, "passive narrator").
Nina/silent-character findings from the blind critics.

## Acceptance Criteria (headline)

- [ ] A skip turn can trigger an autonomous burst that advances the scene ≥2
  beats and stops on a listed condition (logged which one).
- [ ] Hard cap enforced; player interrupt honored between beats.
- [ ] Undo behavior implemented per the decision above, with tests.
- [ ] Real-run: a stalled-scene scenario visibly advances without player
  input; blind critic confirms the beats read as intentional storytelling.

## CLOSED 2026-07-17 (autonomous session)

All headline acceptance criteria delivered and measured:
- [x] A bare skip turn triggers a bounded burst (`autonomous_burst_max_beats`,
  default 1 = old contract): three live runs advanced 4 beats each, every
  stop condition logged (`autonomous_burst` debug records: beat_count,
  stop_reason, first_turn). Observed live: `budget_exhausted` (runs 1-2) and
  `protagonist_decision` (run 3 — the Director's typed `return_control` flag
  handed control back exactly when the hooded rider crossed the threshold).
- [x] Hard cap enforced (budget stop); a manual force always means exactly
  one beat; player interrupt is structural — each beat commits under the
  session lock before the next starts.
- [x] Undo decision taken and tested: **undo pops one beat** (each beat is a
  full committed turn); crash mid-burst leaves only complete beats
  (transactionality = per-beat commits, no partial state possible).
- [x] Stop conditions beyond the cap, all deterministic in the runner:
  player routed into the queue (`player_addressed`), Director `return_control`
  (`protagonist_decision`), zero-novel-events narrator beat or two-beat
  narrator-only streak (`beat_settled`).
- [x] Real-run + blind critic x2: run-1 critic (C-) found an event re-told 3x,
  a recap beat, phantom "says something", narrated player silence. Structural
  fixes: per-burst event dedupe (fuzzy >0.8, `repeats_event_text`), prose
  renderer never receives `audible_speech` events, anti-phantom/anti-silence
  prose rules, and empty-event burst beats render NO narration at all (the
  null-recap turn is impossible by construction). Run-2 critic confirmed all
  structural classes gone (real escalation chain, zero phantom speech, zero
  contradiction); its residual findings (epithet recycling, sentence-level
  verbatim copying, reactive-chorus NPC) are prose-craft, routed to Task 26
  with a refined mitigation candidate (per-sentence fuzzy guard).
- Latency UX decision (owned here): v1 returns the whole burst in one
  response (`beats[]` + `burst_stop_reason`; frontend renders beat-by-beat);
  progressive per-beat streaming (SSE) deliberately deferred as a UI-lane
  follow-up — the per-beat commit architecture already supports it.
Suite: 503 passed. Artifacts: `plans/artifacts/burst-live{,2,3}/`.
