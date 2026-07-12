# Explore: test suite redundancy and legacy audit

**Date**: 2026-07-12
**Scope**: `tests/`, pytest configuration, related persistence/model compatibility paths, and
the boundaries exercised by the current suite.

## Suite shape

- Pytest collects 138 cases, deselects 5 `llm` cases by default, and runs 133.
- The default suite passes in about 3.1 seconds.
- `tests/test_integration.py` contains 98 tests in 2,199 lines (74% of the default cases).
- The remaining default cases are split across data isolation (3), MCP (8), playtest harness
  (10 parameterized cases), replay server (7), and replay driver (12 parameterized cases).
- `tests/test_llama_api.py` defines six `test_*` functions but sets `__test__ = False`; it is a
  standalone diagnostic script and contributes zero pytest cases.

## Clearly stale or legacy coverage

### Standalone llama API script

`tests/test_llama_api.py` is not part of pytest and describes an older model and older protocol:

- metadata names `supergemma4-26b-uncensored-fast-v2-Q4_K_M`;
- the complex JSON probe exposes `Player` and `player_options`, which are absent from the current
  blind-Narrator contract;
- it tests generic tool calling, while the roleplay runtime uses structured HTTP responses and
  MCP is deliberately external;
- it uses `json_object`, while the current Narrator uses `json_schema`;
- it writes a bespoke `/tmp/llama_test_results.json` report and duplicates the role now served
  by the queued scenario harness.

### Old live-LLM class

`TestRunnerWithLLM` in `tests/test_integration.py:1111` contains five tests deselected by the
default pytest expression. The assertions are intentionally loose and stochastic (nonempty
narration, a valid speaker, some history), and the class uses obsolete per-agent temperature
config keys. The queued playtest harness now exercises richer real Runner flows with preserved
artifacts, repetitions, scenarios, and deterministic metrics.

### Explicit persisted-session compatibility

`test_game_state_load_legacy_without_compaction_fields` at
`tests/test_integration.py:185` explicitly preserves sessions saved before compaction fields
existed. Its production counterpart is the empty defaults for `story_summary` and
`character_notes` in `src/models.py:216`.

`resolve_personality` at `src/models.py:131` is another explicit migration path for the removed
`personality_summary`/`personality_full` shape. No test directly exercises that migration, but
both persistence and preset parsing still call it.

## Tests with little or misleading signal

- `test_imports` (`tests/test_integration.py:138`) asserts that an already-imported dataclass is
  not `None`; collection/import itself proves this.
- `test_scene_shallow_copy_fails` (`:158`) proves that normal Python assignment aliases an
  object. It executes no product helper.
- `test_game_state_round_trip_empty_history` (`:216`) is contained by the broader round-trip test,
  whose fixture already has empty history.
- `test_atomic_write_integrity` (`:283`) claims to simulate a failed save, but performs only a
  successful save and checks that no temporary file remains. It does not execute the exception
  cleanup path described by its docstring.
- `test_generate_session_id_unique` (`:295`) samples UUID randomness 100 times. It does not test a
  deterministic product invariant beyond the implementation library's behavior.
- `test_concurrent_save_same_session` (`:266`) acquires `_get_lock` inside the test operation. It
  proves that the test's explicit lock serializes read-modify-write, not that `save_game` or
  arbitrary callers enforce locking themselves.
- `test_structured_retry_logs_http_json_and_success_attempts` (`:2127`) is valuable retry/logging
  coverage but spends about 1.5 seconds in real retry backoff even though elapsed time is not an
  assertion. It accounts for roughly half of default suite runtime.

## Overlapping groups

The following groups cover related paths repeatedly. They are not exact duplicates, but their
assertions could be expressed with fewer scenario-style tests without losing distinct outcomes:

- start/session persistence: `test_start_session_returns_id`, `test_start_session_creates_file`,
  `test_get_state_after_start`, `test_start_session_custom_player`, and
  `test_start_session_custom_round_trip`;
- undo: `test_undo_restores_mood_and_full_step`, `test_undo_simple_turn`,
  `test_undo_with_character`, and the first step of `test_undo_multiple_turns`;
- model persistence: general round trip, history round trip, empty-history round trip, then
  save/load and history persistence at the store layer.

Some apparent repetition is intentional boundary coverage and remains distinct:

- prompt-builder tests versus Runner argument-plumbing tests;
- MCP adapter mapping versus registry annotations versus real stdio initialization;
- replay entry parsing versus replay HTTP cursor behavior versus state comparison;
- shared pytest data isolation versus the playtest harness refusing the real `.data` path.

## Coverage imbalance

- `src/main.py` exposes 19 FastAPI routes, but no test drives the actual Roleplay FastAPI app via
  ASGI. Runner/store behavior is heavily tested while request validation, response models, status
  codes, lifespan wiring, and endpoint-to-Runner translation are largely untested.
- The static frontend has no automated JavaScript/UI coverage.
- The new live findings (reserved nested `physical_facts`, unjustified bulk `null` removal, and
  punctuation-only location rewrites) are observed by playtests but are not current enforced
  invariants, so unit tests cannot yet protect them.
- The harness tests its parser, queue, analyzer, aggregation, and report independently, but no
  default test invokes its complete CLI against a fake OpenAI-compatible endpoint.

## Factual conclusion

The suite is fast and its size is not an operational problem. It does contain a small group of
clear no-signal tests, an old live-model layer superseded by the playtest harness, and explicit
legacy compatibility inconsistent with a forward-only data policy. The larger issue is
allocation: persistence and Runner internals have dense overlapping coverage, while the public
FastAPI boundary has none.
