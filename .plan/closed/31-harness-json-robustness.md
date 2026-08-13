# Task 31 — Structured-Output Robustness and Unified Retry Policy

> **CLOSED 2026-07-15.** Delivered: `_is_unretryable` in `src/llm/client.py`
> (definitive 4xx fails fast, 408/429 stay retryable, everything transient keeps
> the backoff budget), removed the `retries=0` override in
> `src/agents/character.py`, and `tests/test_llm_retry_policy.py` (7 tests:
> malformed-once recovery, 4xx fail-fast, 408/429/503 retry, client-budget bound
> of 3 provider calls, correction loop bound of 2 without multiplication).
> Suite: 381 passed, 2 xfailed. Real acceptance
> (`plans/artifacts/task31-acceptance/`, 3x `memory_focus_xyz`): 3/3 runs
> completed, 9/9 recall checks green, zero `Falha ao obter JSON válido`; runs 2
> and 3 each hit a previously-fatal flake (`character JSONSchemaValidationError`,
> `narrator RemoteProtocolError`) and recovered on attempt 2 — the exact failure
> class that used to kill ~1 in 3 runs. Per user decision the blind critic loop
> was not used for this task (reserved for 29.2). Forward note: every future
> structured call (e.g. the 29.2 perspective updater) inherits this policy by
> construction because it lives in the client layer.

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

- [x] Unit test: a character `act()` whose fake provider returns malformed JSON
  once and valid JSON on the second attempt completes the turn successfully.
- [x] Unit test: HTTP 4xx from the provider fails fast without retries. —
  `test_definitive_client_error_fails_fast`
- [x] Worst-case call count per character turn is asserted (format retries ×
  correction attempts bounded, no multiplication blow-up).
- [x] Three consecutive repetitions of `memory_focus_xyz` against the real
  provider complete with zero runs lost to `Falha ao obter JSON válido`
  (narrative failures, if any, are out of scope here).
- [x] `rg 'retries='` in `src/` shows no per-agent overrides left. — **checked
  2026-07-27**: only the parameter being passed through in `client.py:328`, no
  override.


---

# The three repeats, executed (2026-07-27)

The criterion was narrow and therefore measurable: three consecutive repeats of
`memory_focus_xyz` against the real provider, **zero runs lost to "Falha ao obter
JSON válido"**.

**3/3 completed the whole scenario. No run lost to JSON.**

And the run brought positive evidence that this task's retry policy does real
work: **9 `JSONSchemaValidationError`s occurred and every one was recovered**. The
Director sent a boolean where the schema wants a string or null (6 times, always
in `scene_update` keys the model invented itself, such as
`porta_arrombada: true`), `location: null`, and the prose sent keys outside the
schema (`actions`, `events`, `scene_change`). Before this task, each of those was a
lost turn; here not one even reached the player.

## What the run revealed about the instrument, not about the product

The harness marked 2 of the 3 runs as failed — but not for JSON. For
`RecallCheckFailed: whispered secrets leaked into records`, with these tokens:

| run | accused token |
|---|---|
| 1 | `onde` |
| 2 | `cabeça` |

"Onde" and "cabeça" ("where" and "head") are not secrets. The detector (`_is_rare`
+ `PAYLOAD_WINDOW` in `src/confidentiality.py`) accepts any token of 4+ characters
falling in the neighbourhood of the whisper's anchor, and in a language where
"onde", "casa", "porta", "mesa" and "cabeça" are the scene's basic vocabulary, that
produces false positives easily. Those words reappearing in a later line is not
evidence of a leak.

It is not a bug of this task and it is **not a fix for today**: changing the filter
means recalibrating an instrument other tasks use as an oracle (xfailed3's `secret`
family depends on it), and recalibrating without measuring precision before and
after only swaps one bias for another. It is recorded as the next question to
measure: what is the false-positive rate of the leak detector in Portuguese, and
does a per-language stop list solve the problem or only move it?
