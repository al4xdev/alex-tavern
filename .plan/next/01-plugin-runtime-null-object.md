# 01 — `PluginRuntime` como null object

> ✅ **Aplicado em `f2e5e3d`** (branch `refactor/pre-1.0-cleanup`, 2026-07-26) — aplicado integralmente

**Escopo:** `src/runner.py`, `src/plugins/hooks.py`, `src/plugins/runtime.py`
**Esforço:** S · **Risco:** baixo · **Quebra contrato:** SDK (só remoção de variantes internas)

## Sintoma

`Runner.__init__` aceita `plugins: PluginRuntime | None = None`
(`src/runner.py:149`) e o resto da classe paga por isso **19 vezes**:

```
$ grep -c "self.plugins is not None\|self.plugins is None" src/runner.py
19
```

O caso mais caro é o duplo caminho da chamada do Director
(`src/runner.py:692-721`): o mesmo `_call_narrator` é montado duas vezes, uma
direta e outra via `call_wrapped`, com um `partial` de 9 argumentos no ramo com
plugin. O mesmo padrão se repete para Character em `src/runner.py:917-935`, ali
com uma lambda de captura por default-arg
(`lambda g=character_game, s=speaker, c=ctx, st=step, ra=reply_audience: ...`)
em vez de `partial` — duas soluções diferentes para o mesmo problema, a 200
linhas de distância.

Sobrou também asserção morta nos dois ramos:

```python
narrator_game = game
assert narrator_game is not None      # runner.py:705
character_game = game
assert character_game is not None     # runner.py:923
```

`game` é `GameState` não-opcional naquele ponto (o `return` do `None` acontece
em `runner.py:411`), então as duas asserções nunca podem falhar.

## Por que é dívida

O `None` não representa nenhum estado real: `main.py:68-79` **sempre** constrói
um `PluginRuntime()` e chama `plugins.boot()`. O único produtor de
`Runner(..., plugins=None)` são os testes. Ou seja: 19 branches em produção
existem para servir a conveniência de um construtor de teste.

Um `PluginRuntime()` recém-criado já é um no-op perfeito: `HookRegistry.ordered()`
devolve lista vazia, `filter` devolve o valor de entrada, `action` não faz nada e
`call_wrapped` chama a operação original. O null object já existe — só não está
sendo usado.

## Proposta

1. `plugins: PluginRuntime = field(default_factory=PluginRuntime)` (ou
   `plugins or PluginRuntime()` no `__init__`), tipo não-opcional.
2. Apagar os 19 `if self.plugins is (not) None`, ficando com a chamada direta ao
   hook nos dois lados.
3. Unificar Director e Character em **um** padrão: `partial` para os dois, sempre
   via `call_wrapped`.
4. Apagar as duas asserções mortas e as variáveis `narrator_game`/`character_game`.
5. Remover `HookRegistry.action_sync` e `HookRegistry.filter_sync`
   (`hooks.py:141-162`) tornando `Runner.start_session` assíncrona.

O ponto 5 merece justificativa: as variantes `_sync` existem só porque
`start_session` é síncrona, e elas carregam um contrato irritante — se um plugin
registrar um handler `async` em `session.start`, ele **levanta `TypeError`** em
`hooks.py:146` e é desabilitado no boot. Tornando `start_session` async (o
endpoint em `main.py:352` já é `async def` e o chama de dentro de um `await`
handler), as duas variantes somem e handlers sync continuam funcionando, porque
`_await()` (`hooks.py:33`) já aceita valor não-awaitable. Some também
`_failed_sync` e o `TypeError` de "Async plugin error handlers cannot run from
synchronous hooks".

## Passos

1. `Runner.__init__`: tipo não-opcional + default.
2. `sed` mental nos 19 guards; rodar `pytest tests/test_plugins.py` a cada bloco.
3. Unificar os dois wrappers com `partial`.
4. `start_session` → `async def`; atualizar `main.py:435`, `tools/playtest_harness.py`
   e os testes que a chamam direto.
5. Remover `action_sync`/`filter_sync`/`_failed_sync` de `hooks.py`.
6. Atualizar `src/plugins/contracts.py`: `session.start` e
   `session.before_commit` deixam de ser `"sync filter"`, `session.after_commit`
   deixa de ser `"sync action"` (ver doc 09).

## Como validar

- `uv run pytest` (785 verdes; `test_plugins.py` e `test_integration.py` são os
  que mais exercitam hooks);
- um plugin do hub curado com handler `session.start` continua ativando e
  aparecendo em `/plugins` sem entrar em `disabled_for_boot`;
- `uvx ruff check . && uvx mypy src/`.

## Não fazer

- **Não** criar uma classe `NullPluginRuntime` separada: `PluginRuntime()` vazio
  já é o null object, e uma segunda classe recria a bifurcação em outro lugar.
- **Não** manter `filter_sync` "por segurança" para plugins antigos — isso é
  exatamente o shim que o `AGENTS.md` §2 proíbe. O hub é revisado por fonte
  integral; se algum plugin curado depender da forma síncrona, ele muda junto.
</content>
