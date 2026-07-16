# Task 33 — Autonomous Suggest Scheduler (randomness injection)

## Goal

Fire the existing suggest mechanism automatically on an algorithmic cadence, so the
story receives periodic "picadas de aleatoriedade" without the player having to drive
every event manually. Validated manually by the user (2026-07-16, session `091b11c6`
era): injecting a suggest event "muda tudo completamente" in a stalled scene.

This is the smallest shippable piece of the Drive layer
(`.plan/tasks/explore-29.2-subjective-state.md` §10) and does not depend on the 29.2
core work.

## Current Problem

The Narrator is passive: it waits for player input, even on skip turns
(evidence in Task 26, session `091b11c6`). The game state stalls unless the player
invents events or manually triggers suggestions.

## Proposed Direction

- **Escalating probability (hazard function), owned by code**: each turn without an
  injected event increases the firing probability; firing resets it. Parameters
  (base probability, growth, hard cap in turns) live in config with sane defaults.
  Deterministic seeding per session for replayability of the schedule decision.
- **Reuse the existing suggest pipeline unchanged** — the scheduler only decides WHEN.
- **Queue discipline**: an autonomous suggest never collides with a player-initiated
  suggest or an in-flight turn; it waits its turn (per-session lock already serializes).
- Scheduler decisions logged to `debug.jsonl` (fired/skipped, probability, seed) so
  playtests can correlate injections with narrative movement.
- Kernel/plugin boundary: the scheduling mechanism is kernel; consider exposing the
  cadence policy as configuration (not a plugin requirement for v1).

## Acceptance Criteria

- [ ] Unit tests: probability escalates per quiet turn, resets on fire, respects the
  hard cap, never fires while a player suggest/turn is in flight.
- [ ] Config validation for the new parameters, with defaults that fire roughly every
  4-8 turns of inactivity.
- [ ] Debug log records every scheduler decision.
- [ ] Real-LLM playtest: a scenario with several skip turns shows injected events
  advancing the scene (compare against a scheduler-disabled control run).

> **CLOSED 2026-07-16.** Delivered as `src/drive.py`: deterministic hazard
> (p = min(base + growth × quiet_turns, cap), seeded per session+turn),
> firing only on bare skip turns (never overrides a manual hint), injecting a
> WORLD-event seed (`drive:event_seed` structured call) as narrator_hint —
> never a player move (agency invariant; this is the one deliberate deviation
> from "reuse the suggest pipeline"). Config keys optional-with-defaults so
> stored configs keep loading; schema v5 adds the quiet-turn counter; every
> decision logged as `drive_scheduler` in debug.jsonl; harness gained skip
> turns. A/B real run (plans/artifacts/drive-ab): ON = 2 injections in 4 skips
> (stone through the window, carriage arriving) with narration visibly
> reacting; OFF = four turns of circular ambience, nothing happens. The A/B
> also caught a real robustness bug: the skip-turn narrowed enum made the
> local validator reject responses 3× before the lenient normalization could
> absorb them — exclusion is now normalization policy, full enum guides the
> model. 7+2 tests; suite 440 passed.
