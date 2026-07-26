# 04 — Envelope único no `debug_log`

> ✅ **Aplicado em `b7ba81c`** (branch `refactor/pre-1.0-cleanup`, 2026-07-26) — aplicado integralmente

**Escopo:** `src/llm/debug_log.py` (496 linhas) e seus 18 chamadores
**Esforço:** S · **Risco:** baixo · **Quebra contrato:** formato JSONL (só aditivo, se feito certo)

## Sintoma

15 funções `log_*` e todas abrem com o mesmo literal:

```python
_append(session_id, {
    "ts": datetime.now(UTC).isoformat(),
    "session_id": session_id,
    "turn_number": turn_number,
    "agent": "<nome>",
    ...campos próprios...
})
```

`log_turn_input:58`, `log_effective_turn_input:88`, `log_command_input:110`,
`log_command_result:137`, `log_llm_call:170`, `log_whisper_output_guard:232`,
`log_undo:261`, `log_compact:274`, `log_drive_decision:303`, `log_time_skip:330`,
`log_burst:353`, `log_unanswered_player:376`, `log_roteiro_decision:395`,
`log_compaction_status:422`, `log_restore_compaction:456`, `log_presence_change:469`,
`log_presence_undo:486`.

A repetição já produziu **deriva silenciosa**:

- `log_compact:285`, `log_restore_compaction:457`, `log_presence_change:472` e
  `log_presence_undo:487` **não gravam `turn_number`** — as outras 11 gravam.
  Nenhuma dessas quatro tem motivo declarado para omitir; `log_compact` inclusive
  recebe `cutoff_turn_number` e poderia informar o turno.
- `log_compaction_status:445` grava **`"error": None` fixo** enquanto recebe
  `error: BaseException | None` e o usa só para `error_type`/`error_repr`. Ou a
  chave é lixo, ou o valor deveria ser `str(error)` como em `log_llm_call:221`.
- `log_llm_call` tem **17 parâmetros posicionais** (`PLR0917`), chamada de dois
  lugares em `client.py:152` e `client.py:173` com as 17 posições repetidas —
  trocar duas de lugar é um bug que nenhum teste pega.

## Por que é dívida

`debug.jsonl` é a matéria-prima de `tools/replay_session.py`,
`tools/analyze_memory_run.py`, `tools/render_transcript.py`, do MCP e do método
curl-first do `AGENTS.md` §6. Um campo faltando numa família de eventos é uma
análise impossível meses depois — e é exatamente o tipo de erro que a repetição
manual produz.

## Proposta

```python
def _emit(session_id: str, agent: str, *, turn_number: int = 0, **fields: Any) -> None:
    """Envelope canônico: ts + session_id + turn_number + agent + campos do evento."""
```

As 15 funções viram uma linha cada:

```python
def log_undo(session_id: str, turn_number: int, removed_records: int) -> None:
    _emit(session_id, "undo", turn_number=turn_number, removed_records=removed_records)
```

Ganhos concretos: `turn_number` passa a existir em **todas** as entradas
(aditivo — nenhum consumidor quebra); a lista de campos de cada evento vira
legível de relance; e novos eventos não têm mais como esquecer o envelope.

Para `log_llm_call`, converter os 17 posicionais num par de dataclasses já
existentes no espírito do módulo — `LlmCallRequest` (messages, model, max_tokens,
response_format, provider, api_base, thinking_enabled) e `LlmCallOutcome`
(content, error, duration_ms, attempt_number, usage, cache_hit/miss) — e chamar
com dois objetos nos dois sítios de `client.py`. Some a possibilidade de trocar
posições e a assinatura passa a caber na tela.

Aproveitar para decidir o caso `log_compaction_status`: gravar
`"error": str(error) if error else None`, igual ao `log_llm_call`, ou remover a
chave. Hoje ela mente.

## Passos

1. Introduzir `_emit`; migrar as 15 funções (mecânico).
2. Adicionar `turn_number` nas quatro que o omitiam.
3. Corrigir `"error"` em `log_compaction_status`.
4. Refatorar `log_llm_call` para os dois objetos de request/outcome.
5. Conferir os consumidores: `tools/replay_session.py`,
   `tools/analyze_memory_run.py`, `tools/render_transcript.py`,
   `tools/mcp_server.py` e o painel de debug em `src/static/app.js:1361`
   (`renderRawLog`).

## Como validar

- `uv run pytest tests/test_replay_session.py tests/test_analyze_memory_run.py
  tests/test_render_transcript.py tests/test_mcp_server.py`;
- rodar um turno real e comparar `debug.jsonl` antes/depois: mesmas entradas, na
  mesma ordem, com os mesmos `agent`, mais `turn_number` onde faltava;
- abrir o drawer de debug no frontend e conferir que as entradas continuam
  renderizando.

## Não fazer

- **Não** versionar o JSONL nem escrever conversor: o log é diagnóstico
  descartável, e `AGENTS.md` §2 já resolve isso — dado local incompatível se
  apaga.
- **Não** trocar por `logging` do stdlib. O formato estruturado append-only com
  lock por sessão é deliberado e os `tools/` dependem dele.
</content>
