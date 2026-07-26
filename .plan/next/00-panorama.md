# 00 — Panorama da revisão

**Base:** `9387bdc` (master, working tree limpo) · **Data:** 2026-07-25

## Baseline verificado antes de propor qualquer coisa

```
uv run pytest -q            → 785 passed, 2 deselected (14.7s)
uvx ruff check .            → All checks passed!
uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py
                            → Success: no issues found in 52 source files
```

O repositório está **saudável** pelos critérios que ele mesmo definiu. Tudo o que
segue é dívida *estrutural*, invisível para ruff/mypy: repetição, acoplamento por
`None`, métodos longos e restos de decisões antigas.

## Tamanho real do que foi varrido

| Superfície | Linhas | Observação |
|---|---:|---|
| `src/**/*.py` | 7.496 | 32 arquivos |
| `src/static/*.js` + adapters | 6.444 | `app.js` sozinho: 2.424 |
| `src/static/style.css` | 2.852 | fora de escopo desta revisão |
| `tests/` | ~14.000 | 53 arquivos, 785 testes |
| `tools/` | 3.613 | 12 scripts |

## Os números que motivam a pasta

Medidos com `uvx ruff check --select PLR0913,PLR0917,PLR0915,PLR0912,PLC0415 --statistics src tools`:

- **80** imports fora do topo do módulo (35 só em `src/main.py`);
- **45** funções com argumentos demais, **30** com posicionais demais;
- **19** funções com branches demais, **15** com statements demais;
- `Runner.player_turn` isolado: **245 statements, 80 branches, 760 linhas**.

E, por inspeção manual:

- **6** implementações quase idênticas de escrita atômica de JSON
  (`config.py:219`, `store/sessions.py:61`, `store/presets.py:63`,
  `store/scenarios.py:44`, `plugins/sdk.py:115`, `plugins/hub.py:187`);
- **4** registries de lock com o mesmo corpo `WeakValueDictionary` + guard
  (`store/sessions.py:31`, `store/presets.py:50`, `store/scenarios.py:19`,
  `llm/debug_log.py:18`);
- **18** chamadas a `chat_completion_json` repetindo o mesmo bloco de 8 kwargs,
  em 11 módulos;
- **15** funções `log_*` repetindo o mesmo envelope `ts/session_id/turn_number/agent`;
- **19** ocorrências de `self.plugins is (not) None` em `runner.py`;
- **19** arquivos de teste declarando o próprio `SCENE`/`CHARACTERS`/`_char()`.

## O que NÃO encontrei

Você disse que achava que não havia bug, e a varredura concorda: **não há
nenhum defeito funcional confirmado** nesta revisão. Em particular procurei e
não achei:

- vazamento de fronteira de confidencialidade (whisper/thought/roteiro) — os
  guards determinísticos em `confidentiality.py`, `narrator.redact_whisper_leaks`
  e `character._leaked_secret_tokens` cobrem os caminhos que importam;
- caminho que escape do lock de sessão (todo endpoint mutante passa por
  `_get_lock`);
- `TODO`/`FIXME`/`HACK` — zero ocorrências em todo o repositório;
- segredo em log, cache, localStorage ou payload de plugin;
- código morto de vulto: só `src/disposition.py:73 axis_label()` (nunca chamada)
  e 12 chaves de i18n órfãs (ver doc 10).

Dois achados ficam **entre higiene e defeito latente**, ambos com evidência
reproduzível — estão detalhados nos docs 07 e 06:

1. `src/main.py:845` usa `body.dict(exclude_none=True)`, API depreciada do
   pydantic v1. Verificado: emite `PydanticDeprecatedSince20` e some no
   pydantic v3. É o **único** ponto de `src/` que fura o shim `pydantic_compat`.
2. `src/config.py` ainda carrega e migra config `schema_version = 1`
   (`LEGACY_CONFIG_SCHEMA_VERSION`), exatamente a "leitura dupla de config" que
   o `AGENTS.md` §2 proíbe.

## Método

Leitura arquivo a arquivo de `src/` (100% dos `.py` e dos `.js` de aplicação),
`tools/`, `tests/conftest.py` + amostragem dirigida dos testes, `.ci-cd/android/`
e a raiz; depois greps de confirmação para cada número citado e execução real de
ruff/mypy/pytest. Nenhuma métrica neste diretório é estimada.

## Princípio que guiou o corte

Nem toda repetição merece abstração. O filtro usado foi:

> Abstrair quando o mesmo trecho existe **≥3 vezes** *e* uma mudança futura
> obrigaria a editar todas as cópias.

Por isso ficaram **de fora** propostas do tipo "extrair os prompts para arquivos
`.txt`" (perde grep e revisão junto do código), "criar uma camada de repositório
sobre `store/`" (indireção sem ganho num app single-process) ou "tipar
`config: dict` como dataclass" — este último é tentador, mas atravessa plugins,
adapters e 40 testes; anotei como possibilidade no doc 03 e não como tarefa.
</content>
