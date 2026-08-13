# Task 40 — The narrative clock (tick system): time always moves

**Origin:** the user's idea (2026-07-17), mechanising the "world clock" from
`docs/cases/12-scene-state-transition-theory-2026-07-17.md`.
**Relation:** a foundational primitive consumed by Task 33 (drive) and Task 33b (the
scene-transition controller).
**Status:** ✅ CLOSED (2026-07-20) — the tick is always on (code-owned); the deadline is
gated by `roteiro_enabled`. Acceptance fully test-locked (see the Acceptance section).

## The problem it solves

The LLM is "frozen in time": the story is static, the model has no clock and does not
notice that *continuing* has stopped being *progressing*. The two clocks (conversation vs
world) decouple and the procedural scene stagnates (portals/raffle).

> The LLM cannot stop time if time does not belong to the LLM.

## The idea

A **monotonic narrative tick, owned by the CODE, that always advances** (never 0, never
backwards). The roteiro, when generated, marks **each act (and optionally each beat) with
a tick span/deadline** and the `world_event` that fires at the deadline. When the clock
crosses an act's deadline, the code **forces** the world transition — enacting the
`world_event` + advancing the act — regardless of what the conversation did. The LLM never
holds the clock.

That is the deterministic authority the document argues for: **the code demands the
concrete causal transition** at the right moment; a human GM does not blow up the gates,
they simply run the raffle when the bell rings.

## Design questions to freeze in the task

- **The unit of time.** An abstract tick ≥1 per committed turn (base candidate: reuse or
  derive from `turn_number`, which is already monotonic)? Or a variable advance, which
  allows *time compression* (the human GM: "after a few minutes, the bell rings" — one
  turn consumes many ticks)? In-fiction time (minutes/hours) can be a derived annotation;
  ENFORCEMENT is on the monotonic tick.
- **The roteiro's annotation.** Each act declares `start_tick` + `duration_ticks` (or
  `deadline_tick`) + `world_event_on_deadline` (tied to the "procedure beat", §6.5 of the
  document: `world_owner`, `next_world_event`). Beats likewise, optional.
- **Enforcement.** The runner advances the clock on every committed turn; on crossing an
  act's deadline, force-advance + enact the `world_event` (the same mechanism that broke
  the loop 3/3 in Task 38's curl, but SCHEDULED by the clock, not reactive to a stall). It
  replaces/hardens 38's `budget_turns` (soft) with a hard deadline, and 33's
  `turns_since_injected_event` with a clock-derived signal.
- **Confidentiality.** The schedule (deadlines + future world_events) reaches ONLY the
  Director (like the roteiro; never the character/prose — it contains spoilers). Scan it.
- **Player freedom.** Time passing is a FACT OF THE WORLD, not a dictation of the player's
  will — consistent with the free-action contract (the Director has authority over the
  world's response; it hands control back). A consequential player attempt is still
  adjudicated; the clock only guarantees the world does not freeze.
- **Compression/skip.** The clock must support a "time skip" (advancing many ticks in one
  turn) to implement the human summary mode (document §4.2) — leave dramatic mode, advance
  the clock, come back at the next decision point.

## Starting method: curl-replay first

Before any code, validate the concept (AGENTS.md §6): take a real Director payload from a
stalled procedural turn and annotate "it is NOW tick N; the world advanced to <the
deadline's world_event>". Measure whether the Director stages the world transition (as the
concrete disruptive beat did 3/3) versus an abstract instruction (0/3). Only then design
the tick schema + the act annotation + the enforcement.

## Acceptance — ✅ ALL MET (marked 2026-07-20, evidence below)

- [x] A monotonic, code-owned clock, always +≥1 per turn; never regresses;
  undo/fork/restore preserve the clock exactly.
  → `test_tick_advances_per_committed_turn`, `test_tick_and_act_fields_roundtrip`
  (restore), `test_undo_does_not_regress_the_clock` (undo keeps the tick, does not
  regress). Fork uses the same serialisation as restore.
- [x] The roteiro annotates each act with a tick deadline + world_event; confidential to
  the Director (scan NONE).
  → `test_acts_validation_clamps_clock_fields` (duration_ticks/world_event in the schema,
  clamps); `test_prose_and_character_builders_have_no_roteiro_surface` (the prose/character
  builders have NO roteiro parameter — scan NONE by construction).
- [x] At the deadline, the code FORCES the world_event/act advance — a procedural scene
  reaches the world's next event by the clock, with NO arbitrary disruption.
  → `test_act_deadline_stages_world_event_and_advances`; enforcement in `_maintain_roteiro`
  (code-owned act advance, the model's act_completed ignored on a deadline replan).
- [x] Supports a time-skip (compression) within one turn.
  → `test_time_skip_fields_are_required_in_narrator_schema`,
  `test_director_skip_request_is_clamped_and_witnessed` (clamp 0..8, the summary as a
  witnessed observation). Curl (increment 2): a live scene never skips, 6/6.
- [x] A/B/C (from the document's §7): measure material delta, threads, re-intervention,
  blind coherence.
  → battery RUN (article No. 13, `docs/cases/13-...`): arm C (clock+causal) sustained 6
  productive turns without the watcher firing. Honest note: the blind critic scored B
  higher (drama with agency), but EVERY incoherence it flagged came from seeds with no
  anchor — addressed by the causal contract (33b/Decision B).

**CLOSING (2026-07-20):** every criterion met and test-locked; increment 1 (tick +
deadline) + increment 2 (time-skip) + the A/B/C battery delivered. The tick is always on
(code-owned, +1/turn); deadline enforcement is gated by `roteiro_enabled`. No technical
loose ends. Migrated to `closed/`.

## Increment 1 DELIVERED (2026-07-19, early hours)

Replay first (production builder, stalled procedural session ccb521ab): the deadline's
world_event injected as an UPCOMING EVENT → staged 2/3 even AGAINST a story that had
already moved (the conflict was an artifact of the synthetic injection; in the real
mechanism the event comes from the roteiro itself). The channel was already proven by drive
(33) and by the disruption (38).

Delivered:
- `GameState.narrative_tick` (+1 per committed beat, owned by the CODE; never regresses —
  decision: undo does NOT rewind the clock; the redone turn happens at a later tick,
  consistent with "time always moves").
- `RoteiroAct.duration_ticks` (0=no deadline; clamp 0..12) + `world_event` (clamp 300
  chars); `Roteiro.act_started_tick`; the architect generates both (required in the schema)
  under the rule "the world never waits for the conversation".
- Deterministic enforcement in `_maintain_roteiro`: a passed deadline → the world_event
  becomes this beat's UPCOMING EVENT (the same channel as drive), the act advance belongs
  to the CODE (a replan only writes the opening beat; the model's act_completed is ignored
  on deadline replans — no double-advance), all of it logged (`roteiro_replan`
  action=act_deadline).
- Time-skip (v2) and the A/B/C experiment remain pending (33b/the user).

Tests: roundtrip, clamps, tick per turn, the deadline fires + advances + hint. Suite 619.

## Increment 2 (time-skip) DELIVERED (2026-07-19, morning)

Curl first (12 calls, real payloads):
- Safety: a live scene (the T20 confrontation) NEVER skips — 6/6 zero ticks, even when
  INVITED to compress. Invitation-proof.
- A stalled scene (the raffle): free 1/3; when invited, 2/3 skipped (2-3 ticks, coherent
  summaries: "os alunos seguem ao pátio central..."). The model UNDER-uses the proactive
  power (the same pattern as 38/drive) → the skip cannot depend on the LLM's initiative;
  the CODE issues the invitation.
- The invitation over the hint channel does not become a staged event (verified).

Shipped design (validated variant = shipped variant, text and position):
- The Director's schema: `time_skip_ticks` (0-8) + `time_skip_summary`, both required; the
  TIME COMPRESSION rule at the END of the system prompt.
- The invitation (`CLOCK_SKIP_INVITE`) fires when the player SKIPS the turn and neither
  drive nor a deadline occupied the hint — the player's skip is the human signal for
  "summary mode" (document §4.2). A trigger on semantic stagnation is left to the 33b
  watcher.
- Application belongs to the CODE: clamp 0..8, `narrative_tick += ticks` on top of the
  beat's +1; the summary enters as an observation witnessed by everyone present
  (prose/perspectives/history inherit it through the normal channels); logged (`time_skip`
  in the debug JSONL). An honest division: the deadline GUARANTEES the advance; the skip
  COMPRESSES when offered.

Tests: schema required, the invitation on a skipped turn, clamp 99→8 + witnessed
observation. Suite 627. Pending: the A/B/C unified with 33b (owner).


## The A/B/C battery (2026-07-19): the clock carried the scene

In arm C of the battery (article No. 13), clock+roteiro sustained 6 consecutive productive
turns with NO watcher intervention — the increment 1+2 mechanism was sufficient in this
run. Time compression, active in every arm, absorbed part of the stagnation (ticks 16/15/17
over 10 turns). The task's A/B/C pending item: MET.
