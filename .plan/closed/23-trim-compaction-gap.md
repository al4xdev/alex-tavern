# Task 23 — Close the Trim/Compaction Gap (Silent Long-Session Memory Hole)

## Goal

Guarantee that no speech record leaves a character's context window without first being
folded into `story_summary` / `character_notes` — compaction must fire *before* the
token trim, never after.

## Current Problem

Three defaults interact into a silent memory hole for long sessions or small-context
providers:

1. `trim_history_by_tokens` (`src/models.py`) drops the oldest records at
   ~`0.7 × context_max − max_tokens_*`, silently and with no summary fallback.
2. `automatic_compaction_enabled` defaults to `False`
   (`src/config.py`), so nothing preserves evicted content.
3. Even when enabled, the thresholds are inverted — compaction triggers at 80% of
   `context_max` while trimming already starts at ~70% — and
   `compaction_keep_recent_turns = 200` returns `blocked_by_retention_window`
   (`src/runner.py`, `_compact_loaded_game`) for any session under 200 turns.

Once a session outgrows the trim budget, characters lose their oldest memories with no
trace: this is the mechanism that will reproduce the "character forgot an early fact"
symptom investigated in `docs/cases/multi-character-memory-retention-2026-07-14.md`
(where it was ruled out only because the DeepSeek budget ≈ 367k tokens was never reached).

## Evidence

Two strict xfail specification tests in `tests/test_memory_retention.py`
(`TestTrimCompactionGapFinding`) encode the desired behavior and fail today:

- `test_trim_preserves_early_fact_or_summarizes_it`
- `test_automatic_compaction_unblocked_under_context_pressure`

## Proposed Direction

- Flip defaults: enable automatic compaction, set its threshold *below* the trim point
  (e.g. 60% < 70%), and lower the default retention window to something a real session
  can reach (e.g. 40 turns).
- Under automatic trigger with context pressure, treat the retention window as a
  preference, not a blocker: use an adaptive cutoff (e.g.
  `max(MIN_KEEP, len(turns) // 2)`) instead of returning `blocked_by_retention_window`.
  Manual compaction keeps today's semantics.
- Surface trimming: when `_format_history_for_character` drops records, log a debug
  entry (count, budget, whether a summary exists) so the playtest analysis can count it.

## Acceptance Criteria

- Both xfail tests turn green (remove the markers in the same commit).
- Existing compaction tests (`tests/test_compaction.py`) still pass; manual compaction
  behavior is unchanged.
- A playtest run with `--context-max 2048` on `memory_focus_xyz.json` passes recall
  check 1 via `character_notes`/`story_summary` even after the early turns leave the
  window.

> **CLOSED 2026-07-16 (autonomous overnight).** Both strict-xfail spec tests
> flipped to green as normal tests:
> 1. **Code-anchor pinning in the character trim**: records carrying a
>    code-like identifier (uppercase word fused to digits — ORQUÍDEA-741,
>    LUMEN-17) are pinned through `trim_history_by_tokens` (capped at the last
>    12), so recency discards atmosphere but never a confided code. Plain
>    digits ("Rota 3") do not pin — noise stays trimmable.
> 2. **Adaptive automatic retention**: when automatic compaction fires under
>    real context pressure (estimate above threshold) and the configured
>    `compaction_keep_recent_turns` would block it, the window shrinks to the
>    most recent half (never below 4 turns, only above 8 total) so the session
>    compacts instead of silently trimming. Manual compaction still honors the
>    configured window untouched.
> Suite: 495 passed, zero xfails remaining anywhere. The principled long-term
> home for trimmed private memory remains Task 39 (ledger memory dimension).
