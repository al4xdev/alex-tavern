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
