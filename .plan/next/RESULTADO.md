# Resultado da faxina pré-1.0

Branch `refactor/pre-1.0-cleanup`, 15 commits sobre `969b939`, 2026-07-26.
**Não foi feito push.**

## Números medidos, antes e depois

| | Antes (`9387bdc`) | Depois | |
|---|---:|---:|---|
| Testes | 785 | **817** | +32, nenhum removido |
| ruff | limpo | limpo | |
| mypy (escopo do AGENTS.md) | limpo | limpo | 56 arquivos |
| `Runner.player_turn` | 245 statements / 80 branches | **fora da lista** | 13 estágios nomeados |
| Imports fora do topo | 80 | 46 | `main.py` foi de 35 a **0** |
| Statements demais | 15 funções | 12 | |
| Branches demais | 19 funções | 15 | |
| Escritas atômicas de JSON | 6 cópias | **1** | +1 em `tools/` também migrada |
| Registries de lock | 4 cópias | **1** | genérico, 3 domínios |
| Blocos de transporte LLM | 18 | **1** | `call_agent` |
| Envelopes de log escritos à mão | 15 | **1** | `_emit` |
| `if self.plugins is not None` | 19 | **0** | |
| `_char` duplicado em teste | 15 arquivos | **1** fábrica | −127 linhas líquidas |
| `app.js` | 2.424 linhas | 2.050 | 4 módulos extraídos |

## O que quebrou de propósito

- **Config v1**: `LEGACY_CONFIG_SCHEMA_VERSION` e a conversão sumiram. Config v2
  (a sua, com a chave da API) continua válida — verificado com boot real.
- **Hooks `session.*`**: deixaram de ser síncronos. Handlers síncronos de plugin
  continuam funcionando; o hub precisa regenerar o contrato exportado.
- **`context.command`**: não passa mais por `unsafe`. Verificado em servidor real
  com os 3 plugins curados ativos: **zero** eventos `permission: "unsafe"` no
  journal (antes, todo plugin com comando emitia um).
- **`GET /bootstrap_log`**: removido (ninguém consumia; o MainActivity lê o
  arquivo nativamente).
- **Sessões**: `SESSION_SCHEMA_VERSION` continua **13**. Nada aqui invalida
  sessão sua.

## Três coisas que a suíte pegou e que valem registro

1. **`log_compaction_status` grava `"error": None` de propósito.** Eu tinha lido
   como resto e "corrigido". A mensagem de uma falha do sumarizador carrega o
   resumo privado do mundo, e essa entrada é lida por ferramentas e pelo drawer
   de debug. `tests/test_compaction.py` reprovou na hora. Está documentado agora,
   ao lado do teste que trava.
2. **As chaves `presence.*` do i18n não são mortas.** Não têm leitor neste
   repositório porque quem as usa é o plugin curado de presença. Removi,
   `test_frontend_architecture.py` reprovou, restaurei todas. O cabeçalho de
   `i18n.js` agora avisa que o catálogo é contrato de plugin.
3. **`drive`/`watcher` e `roteiro` nunca renderizaram o mesmo contexto.** Pareciam
   idênticos na leitura; a comparação byte a byte antes/depois mostrou que os
   dois primeiros rotulam personagens por ID ("C2") e o terceiro por nome
   ("Marta"). Virou um parâmetro explícito com comentário: unificar é experimento
   de prompt (regra curl-first), não refatoração.

## Portões que dependem de você

1. **Playtest manual** pelo roteiro de
   `.plan/backlog/02-readme-media/manual-playtest-script.md`. O Playwright aqui
   valida carga e render com zero erro de console, mas não consegue clicar (os
   overlays interceptam a checagem de actionability do Playwright), então
   interação é olho humano.
2. **Turno real contra o provider ativo.** Não tenho sua chave; tudo que exercitei
   foi com LLM mockado, mais o boot real com os 3 plugins curados.
3. **APK e aparelho** (`.claude/skills/android-apk-lab`). Os docs 10 e 11 mexem
   justamente no que só falha no celular: `android-bridge.js`, o shell do service
   worker, `build_info`, as strings nativas de boot e o lado v1 do
   `pydantic_compat` (que nenhum teste de desktop cobre).

## O que ficou para depois

- **Doc 10 (parcial)**: faltam `transcript.js`, `composer.js`,
  `sessions-modal.js`, `compaction-ui.js`, `opening-picker.js`, `dom.js` — os
  cinco com acoplagem de 6 a 11 funções e todos no caminho do turno ao vivo.
- **Doc 12 (parcial)**: falta o `FakeDirector` único no lugar dos ~10 duplos de
  LLM ad-hoc.
- Fora de escopo desde o plano: `config: dict` → dataclass tipada, divisão de
  `main.py` em routers, `style.css`.
