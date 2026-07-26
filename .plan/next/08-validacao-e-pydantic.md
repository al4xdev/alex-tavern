# 08 — Uma validação de turno, e um shim de pydantic menor

**Escopo:** `src/main.py`, `src/runner.py`, `src/pydantic_compat.py`
**Esforço:** M · **Risco:** baixo · **Quebra contrato:** nenhuma (status HTTP muda de 422 para 422)

## Sintoma

A mesma regra de negócio está escrita duas vezes, em duas linguagens diferentes.

**Em pydantic** (`src/main.py:232-244`):

```python
@after_validator
def require_content(self) -> PlayerTurnRequest:
    if self.skip:
        if self.speech.strip() or self.thought.strip() or self.action.strip():
            raise ValueError("skip=True cannot be combined with speech, thought, or action")
        return self
    if not any(value.strip() for value in (self.speech, self.thought, self.action, self.narrator_hint)):
        raise ValueError("A turn needs speech, thought, action, or narrator_hint")
    if self.audience is not None and not self.speech.strip() and not self.action.strip():
        raise ValueError("audience (whisper) requires speech or action")
    return self
```

**Em Python puro** (`src/runner.py:404-424`):

```python
if not skip and not any(value.strip() for value in (speech, thought, action, narrator_hint)):
    raise ValueError("A turn needs speech, thought, action, narrator_hint, or skip")
...
if audience is not None:
    if not speech.strip() and not action.strip():
        raise ValueError("audience (whisper) requires speech or action")
    if not audience:
        raise ValueError("audience cannot be an empty list")
    ...
```

Repare que já **divergiram**: a mensagem do runner cita `skip`, a do pydantic
não; e a regra "skip não combina com conteúdo" só existe no lado HTTP — quem
chamar `Runner.player_turn(skip=True, speech="oi")` por dentro (playtest
harness, MCP, plugin) passa batido.

## Por que isso importa mais do que parece

Esse validador é o **único** motivo pelo qual `src/pydantic_compat.py` precisa de
`after_validator` — e o `after_validator` é responsável por ~50 das 99 linhas do
shim, incluindo a classe `_ValuesProxy` inteira (`pydantic_compat.py:62-98`), que
existe para fazer um validador escrito no estilo v2 (`self.campo`) rodar sobre o
dict do `root_validator` v1 do Android.

Ou seja: uma regra de negócio duplicada sustenta uma classe de compatibilidade
de framework que só roda no APK e que **nenhum teste cobre**
(`# pragma: no cover - exercised only on the Android build`).

## Proposta

1. **A validação vive no Runner** (é regra de domínio, não de transporte). Ele já
   valida o resto: audiência vazia, IDs desconhecidos, personagens ausentes.
   Mover a regra de `skip` para lá e unificar as mensagens.
2. `PlayerTurnRequest` mantém só o que é *forma*: tipos, `extra="forbid"` do
   `StrictModel`. Sem `@after_validator`.
3. `Runner.player_turn` levanta `ValueError` (já levanta) e `main.py` mapeia
   `ValueError` → 422 num handler — mesmo status que o pydantic devolvia, então
   o frontend não muda.
4. Com isso, `after_validator` e `_ValuesProxy` **saem do shim**, que fica com
   `dump`, `validate` e `StrictModel`: ~35 linhas, todas exercitadas nas duas
   versões.

Antes de apagar, `grep -rn "after_validator" src tests` para confirmar que
`PlayerTurnRequest` é o único usuário — no estado atual, é.

## Efeito colateral bom

Hoje só a rota HTTP valida. Depois, **todo** caminho que chega no turno
(HTTP, `tools/playtest_harness.py`, MCP `tools/mcp_server.py`, comando de
plugin) recebe a mesma regra. Isso é o inverso da duplicação: uma regra, um
lugar, todos os chamadores.

## Sobre o resto do shim (não remover)

`pydantic<2` é restrição **dura** do Android, documentada em
`.ci-cd/android/app/build.gradle:58-63`: Chaquopy não compila `pydantic-core`
(Rust) e não há wheel. Enquanto o backend for FastAPI, `dump`/`validate`/
`StrictModel` continuam necessários. O que esta tarefa faz é reduzir o shim ao
mínimo irredutível — não fingir que dá para eliminá-lo (ver doc 11).

## Passos

1. Mover as três regras para `Runner.player_turn`, mensagens unificadas.
2. Handler `ValueError` → 422 em `main.py`.
3. Remover `@after_validator` de `PlayerTurnRequest`.
4. Remover `after_validator` e `_ValuesProxy` de `pydantic_compat.py`.
5. Atualizar `tests/test_api_limits.py` / `test_integration.py` onde afirmam a
   mensagem exata do 422.

## Como validar

- `uv run pytest tests/test_api_limits.py tests/test_integration.py tests/test_pydantic_compat.py`;
- `curl` os quatro casos inválidos (turno vazio; `skip` + fala; whisper sem
  fala/ação; audiência vazia) esperando 422 com mensagem legível;
- **no aparelho**: instalar o APK e mandar um turno inválido pelo app — é o único
  caminho que exercita o lado v1 do shim (`.claude/skills/android-apk-lab`).

## Não fazer

- **Não** mover a validação para o frontend "porque o botão já bloqueia". O
  frontend valida por UX (`app.js:1632`); o servidor valida por contrato.
</content>
