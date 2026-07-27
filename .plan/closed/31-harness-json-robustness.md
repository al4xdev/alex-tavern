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
- [x] `rg 'retries='` in `src/` shows no per-agent overrides left. — **conferido
  2026-07-27**: só o repasse do parâmetro em `client.py:328`, nenhum override.


---

# As três repetições, executadas (2026-07-27)

O critério era estreito e por isso mensurável: três repetições consecutivas de
`memory_focus_xyz` contra o provider real, **zero runs perdidos por "Falha ao
obter JSON válido"**.

**3/3 completaram o cenário inteiro. Nenhum run perdido por JSON.**

E o run trouxe a evidência positiva de que a política de retry desta task faz
trabalho real: **9 `JSONSchemaValidationError` ocorreram e todos foram
recuperados**. O Diretor mandou booleano onde o schema pede string ou nulo (6
vezes, sempre em chaves de `scene_update` inventadas pelo próprio modelo, tipo
`porta_arrombada: true`), `location: null`, e a prosa mandou chaves fora do
schema (`actions`, `events`, `scene_change`). Antes desta task, cada um desses
era um turno perdido; aqui nenhum sequer apareceu para o jogador.

## O que o run revelou sobre o instrumento, não sobre o produto

O harness marcou 2 dos 3 runs como falhos — mas não por JSON. Por
`RecallCheckFailed: whispered secrets leaked into records`, com estes tokens:

| run | token acusado |
|---|---|
| 1 | `onde` |
| 2 | `cabeça` |

"Onde" e "cabeça" não são segredos. O detector (`_is_rare` + `PAYLOAD_WINDOW`
em `src/confidentiality.py`) aceita qualquer token com 4+ caracteres que caia na
vizinhança da âncora do sussurro, e numa língua onde "onde", "casa", "porta",
"mesa" e "cabeça" são o vocabulário básico da cena, isso gera falso positivo com
facilidade. A reaparição dessas palavras numa fala posterior não é evidência de
vazamento.

Não é bug desta task e **não é conserto para hoje**: mudar o filtro é
recalibração de um instrumento que outras tasks usam como oráculo (a família
`secret` do xfailed3 depende dele), e recalibrar sem medir a precisão antes e
depois só troca um viés por outro. Fica registrado como a próxima pergunta a
medir: qual a taxa de falso positivo do detector de vazamento em português, e uma
lista de parada por idioma resolve ou só desloca o problema?
