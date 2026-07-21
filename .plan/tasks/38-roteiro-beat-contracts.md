> ⚠️ **KEPT IN tasks/ (not in closed/) — delivered WITH RESERVATIONS, without a confident close.**
> The screenplay (roteiro) is opt-in (OFF by default) and helps drive in ACTION scenes, but is
> a **coin-flip in large procedural scenes** (portals 2W/2L). The ENGINE gains are
> reliable (beat ceiling, character guard, lexical backstop, stall disruption) and are banked; the SCREENPLAY itself is not a universal win.
> Convention (user, 2026-07-17): a task closed without confidence stays in tasks/
> with the reservations, it does not migrate to closed/. Full report:
> `docs/cases/11-roteiro-drive-scene-stagnation-2026-07-17.md`.

# Task 38 — Roteiro with Typed Beat Contracts and Algorithmic Replanning

**Depends on:** Task 36 (a Director box must exist to consume the roteiro).
Task 37 benefits but is not a hard dependency.

## Goal

Give the story a DIRECTION compiled before the first word (the user's
map-reduce insight applied to narrative): a hierarchical roteiro — stable
premise + act skeleton, rolling next-beat detail — consumed by the Director
and replanned by CODE, never by model self-assessment.

## Beat contract (design frozen in exploration, 2026-07-16)

```json
{
  "beat_id": "act1-beat3",
  "intent": "Van Helsing pressiona a delegacao a abrir o corredor solar",
  "expected_actors": ["C6", "C8"],
  "expected_anchors": ["corredor solar", "venezianas"],
  "exit_condition": "a delegacao decide sobre as venezianas",
  "budget_turns": 6
}
```

## Replan signals (in preference order; hysteresis + cooldown everywhere)

1. exit condition met → advance beat (normal);
2. turn budget exhausted without anchor coverage → stalled, replan rolling beat;
3. actor/anchor/location overlap below threshold for M consecutive turns →
   drifted, replan rolling beat (fuzzy similarity as fallback signal — measured
   0.79 vs 0.23 discrimination on real pairs);
4. act-level exit broken hard → regenerate act skeleton.

Only the rolling beat is rewritten routinely; premise and act skeleton stay
stable (cache-friendly prefix, spoilers contained).

## Confidentiality rule

The roteiro reaches ONLY Director-side calls. Never a character prompt, never
the prose renderer (it contains future secrets). Assertable from debug.jsonl.

## Acceptance Criteria (headline)

- [ ] Roteiro generator produces valid typed beats from a scenario config.
- [ ] Deterministic replan triggers with unit-tested hysteresis; zero
  model-self-assessment triggers.
- [ ] Roteiro text never appears in character/prose requests (debug scan).
- [ ] Real-run A/B: same scenario with and without roteiro; blind critic
  compares narrative drive without knowing which is which.

## CLOSED 2026-07-17 (sessão autônoma) — honest, scoped

Full report: `docs/cases/11-roteiro-drive-scene-stagnation-2026-07-17.md`.

Roteiro delivered as an OPT-IN feature (roteiro_enabled, OFF by default),
consumed only Director-side, with deterministic replanning. It was closed once
prematurely (b23a9e7), reopened after the portais generalization test the user
proposed, then closed again with an honest scoped verdict.

### Headline criteria — MET
- [x] Roteiro generator produces valid typed beats (premise + 3-act skeleton +
  rolling beat), schema v7, Director-only.
- [x] Deterministic replan with unit-tested hysteresis; ZERO model-self-
  assessment triggers (every A/B logged advance/coverage_complete/
  coverage_sufficient/in_progress/stalled/drifted/cooldown, all code signals).
- [x] Roteiro text never in character/prose requests: confidentiality scan NONE
  in every A/B run (character/prose builders have no roteiro parameter at all).
- [x] Real-run A/B with blind comparative critic (deepseek, shuffled arms) —
  run many times across two scenarios.

### The scoped verdict (the honest part)
- On tight ACTION scenes (estalagem, 3-4 chars, physical genre) the roteiro
  reliably WINS narrative drive (est. ~5 wins across the loops).
- On a large PROCEDURAL/ceremony scene (turma-dos-portais academy, 6 chars) the
  roteiro is a COIN-FLIP: 2 wins / 2 losses across four A/B runs. The value of
  "direction" is offset there by topic-pinning (procedural beats) and, once the
  disruption fix was added, by disconnected-disruption pile-up, plus high
  variance vs a free Director that sometimes finds cleaner emergent conflict.
  No single fix made it a reliable win there; that is architectural + variance,
  not a bug a loop closes. Feature stays OFF by default.
- goal-per-NPC-per-scene (user-added criterion): a GLOBAL character-prompt
  improvement, arc-dependent, not a guaranteed roteiro differentiator.
- lexical variation (user-added criterion): guaranteed by construction (the
  narration backstop); metric <0.8 with 0 near-dups every run.

### Engine improvements banked (help BOTH arms, independent of the roteiro)
- Hard per-beat turn cap (6d6e9b8): no beat can pin the scene into static
  repetition (min(budget, 3) turns).
- Character anti-repetition guard (5c40276): verbatim self-echo / parroting
  eliminated deterministically (0/0), retry then drop-if-other-survives.
- Prose lexical backstop (06bb963): a sentence still echoing after the retry is
  stripped; lexical variation guaranteed.
- Roteiro replan into a concrete DISRUPTION on stall (490f1d5): validated 3/3 at
  the generator and 3/3 at the Director via curl-replay.
- Coverage measured on AUTHORITATIVE evidence (35a9a2f), partial-coverage
  advance (bdda81f), architect escalation + no-exposition (cedbb1a).

### Key methodological finding (the durable payoff, curl-replay technique)
Topic-looping is NOT a character problem and NO character-prompt rule fixes it
(even an explicit topic ban failed 0/3 on the isolated call). It is scene
stagnation: the fast model follows the established scene history hard. The only
levers that broke it: injecting a fresh scene event (2/3) and, decisively, a
concrete DISRUPTIVE beat fed to the Director (3/3). The Director has authority
to break the scene but exercises it only with a concrete "this happens NOW"
beat. Method documented in AGENTS.md; it also frames the player-attempt
adjudication rule (world-response + return_control, never dictating will).

### Routed
- General anti-stagnation trigger -> DRIVE LAYER (Task 33): give the hazard
  function a topic-stagnation input so it injects novelty in BOTH arms.
- Disconnected-disruption pile-up + procedural-arc weakness -> future roteiro
  work (make disruptions advance the planned arc, not interrupt loosely).
  **↑ RESERVATION ADDRESSED (2026-07-20, authorized by the owner) — via layer 33b,
  not via the screenplay prompt.** Two fronts tested via curl:
  1. **Rewrite the `stalled` prompt of the screenplay for a causal contract (A/B):**
     DID NOT win. OLD (loose "arrival/bursting in") 5/6 vs NEW (causal) 5/6 in
     real locked windows, blind causality judge. FIRE does not discriminate (scene
     on fire = any disruption grows from it, 3/3 in both); in LOTTERY
     (procedural, weak thread) each arm missed 1 — OLD with messenger-out-of-nowhere,
     NEW with FORCED escalation contradicting the scene ("already dissipated smoke
     explodes"). Pre-registered rule required NEW>OLD → reverted, not shipped
     (`plans/artifacts/roteiro-causal-stall-ab/`). Confirms the verdict of the task:
     procedural weakness is architecture + variance, not a prompt.
  2. **Route the stall recovery through the watcher's causal intervention (33b
     piece 3):** THIS is the resolution. The causal contract `source_thread→event_now`
     validated **9/9 grounded** by a blind judge (vs the disconnected pile-up). Delivered and
     wired behind `watcher_enabled` (see task 33b). When the watcher is
     on, the recovery disruption grows from an open thread (9/9), instead
     of the loose screenplay disruption. The A/B/C battery had already pointed out that ALL
     critic incoherence came from seeds without anchors — the causal contract closes
     that source.
- Re-narrated whole beats (cross-turn event dup) + semantic character echo +
  action_intent repetition -> Task 26.
- Perspective-ledger init overflow at 20+ present chars (fixed 1024 budget) ->
  Task 29.2 (large-cast scaling).
- Player-attempt adjudication (the portal example) -> new follow-up.

Suite: 550 passed. Artifacts + all blind-critic rounds:
`plans/artifacts/roteiro-ab*/`. Commits: 9761f31, 35a9a2f,
3f4c014, bdda81f, 9f073e0, 06bb963, cedbb1a, 86df261, 7b39304, 6d6e9b8,
5c40276, c3863ae, 490f1d5 (+ the b23a9e7 revert 52f5f88).
