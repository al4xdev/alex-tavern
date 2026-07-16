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
