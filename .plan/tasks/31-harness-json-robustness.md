# Task 31 — Structured-Output Robustness and Unified Retry Policy

## Goal

Stop losing real-LLM runs to single malformed-JSON responses, and unify the
scattered retry ownership so the policy is defined in exactly one place.

**Sequencing note:** this task is a practical prerequisite for Task 29.1. The
full `xfailed3` tier is ~60 provider calls and 0.7-1.2M tokens per run, and its
contract explicitly classifies malformed JSON as an *operational* failure that
must never satisfy the narrative xfail — so under the current flake rate a
large fraction of expensive baseline runs would be wasted on infrastructure.

## Current Problem

- Character agent calls pass `retries=0` (`src/agents/character.py:343`), while
  the Narrator and Summarizer use `chat_completion_json`'s default of
  `retries=2` (`src/llm/client.py:204`). One malformed DeepSeek response on any
  character call therefore raises
  `ValueError: Falha ao obter JSON válido após 1 tentativas` and aborts the
  whole turn — and, in the harness, the whole run.
- Measured impact during Tasks 22/24/25 acceptance (2026-07-14/15): roughly 1
  in 3 repetitions of the 33-turn `memory_focus_xyz` scenario died to this
  flake despite the engine behavior under test being healthy.
- Retry ownership is spread across three layers with different semantics:
  transport/format retries with backoff in `chat_completion_json`, the
  character 2-attempt *semantic correction* loop (action heuristic, whisper
  output guard), and per-agent `retries` overrides. The interaction is easy to
  get wrong: raising the client retry count naively multiplies with the
  correction loop.

## Proposed Direction

- One retry policy owned by the client layer (`src/llm/client.py`),
  distinguishing error classes: transport errors and HTTP 5xx (retry with
  backoff), malformed/empty JSON and schema violations (retry with backoff —
  the model is stochastic, a fresh attempt usually parses), HTTP 4xx
  (fail fast — retrying cannot help).
- Remove the `retries=0` character override; every structured agent call gets
  the same budget. If character latency is a concern, tune the shared default,
  not a per-agent exception.
- Keep semantic correction loops (action heuristic, whisper guard) strictly
  separate from format retries and document the boundary: format retries repeat
  the *same* request; correction retries append a CORRECTION message. Bound the
  worst-case total call count explicitly.
- `debug.jsonl` already records `attempt_number` per call; extend harness
  analysis counters if needed so flake pressure stays observable
  (`provider_retries` per run).

## Acceptance Criteria

- [ ] Unit test: a character `act()` whose fake provider returns malformed JSON
  once and valid JSON on the second attempt completes the turn successfully.
- [ ] Unit test: HTTP 4xx from the provider fails fast without retries.
- [ ] Worst-case call count per character turn is asserted (format retries ×
  correction attempts bounded, no multiplication blow-up).
- [ ] Three consecutive repetitions of `memory_focus_xyz` against the real
  provider complete with zero runs lost to `Falha ao obter JSON válido`
  (narrative failures, if any, are out of scope here).
- [ ] `rg 'retries='` in `src/` shows no per-agent overrides left.
