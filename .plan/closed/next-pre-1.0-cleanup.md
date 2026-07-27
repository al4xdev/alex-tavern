# Faxina de código pré-1.0 — fechada

> ✅ **COMPLETA** em 2026-07-26, branch `refactor/pre-1.0-cleanup`, 33 commits
> sobre `9387bdc`. Os 13 apontamentos da revisão de 2026-07-25 foram aplicados.
> A pasta `.plan/next/` e o `to_the_next.md` foram removidos: este artigo é o
> que sobra deles.

## O que era

Uma revisão linha a linha de `src/`, `tools/`, `tests/` e `.ci-cd/android/`,
feita porque o desenvolvimento acabou e a 1.0 ia congelar a base. O objetivo
declarado não era caçar bug — 785 testes passavam, ruff e mypy limpos — e sim
**não entrar na versão inicial com dívida estrutural**: o mesmo helper escrito
seis vezes, o mesmo `if` defensivo dezenove vezes, um método de 245 statements.

Regra da casa em tudo: forward-only. Nada aqui criou shim, conversor ou leitura
dupla; onde a limpeza quebrou o SDK de plugins, os dois lados mudaram juntos.

## Números medidos, antes e depois

| | Antes (`9387bdc`) | Depois | |
|---|---:|---:|---|
| Testes | 785 | **847** | +62, nenhum removido |
| ruff / mypy | limpos | limpos | 58 arquivos |
| `Runner.player_turn` | 245 statements / 80 branches | fora da lista | 13 estágios nomeados |
| Imports fora do topo | 80 | 45 | `main.py` foi de 35 a **0** |
| Escritas atômicas de JSON | 6 cópias | **1** | +1 em `tools/` |
| Registries de lock | 4 cópias | **1** | genérico, 3 domínios |
| Blocos de transporte LLM | 18 | **1** | `call_agent` |
| Envelopes de log à mão | 15 | **1** | `_emit` |
| `if self.plugins is not None` | 19 | **0** | |
| `_char` duplicado em teste | 15 arquivos | **1** fábrica | |
| Dicts do Director à mão | 43 em 18 arquivos | **1** fábrica | |
| `document.getElementById` | 161 espalhados | **1** `dom.el` | falha alta, com o id |
| `app.js` | 2.424 linhas | **620** | 10 módulos extraídos |

## O que quebrou de propósito

- **Config v1**: `LEGACY_CONFIG_SCHEMA_VERSION` e a conversão sumiram. Config v2
  continua válida — verificado com boot real.
- **Hooks `session.*`**: deixaram de ser síncronos. Handlers síncronos de plugin
  continuam funcionando; o hub precisa regenerar o contrato exportado.
- **`context.command`**: não passa mais por `unsafe`. Verificado em servidor real
  com os 3 plugins curados: **zero** eventos `permission: "unsafe"` no journal
  (antes, todo plugin com comando emitia um).
- **`GET /bootstrap_log`**: removido. Ninguém consumia; o `MainActivity` lê o
  arquivo nativamente.
- **`tools/frontend_inspector.py`** e os dois tools de MCP de frontend:
  removidos em favor do plugin de Playwright do editor. Ver `50-playwright-*`.
- **Sessões**: `SESSION_SCHEMA_VERSION` continua **13**. Nada aqui invalidou
  sessão existente.

## Cinco coisas que a suíte (ou uma medição) pegou, e que valem registro

1. **`log_compaction_status` grava `"error": None` de propósito.** Eu li como
   resto e "corrigi". A mensagem de uma falha do sumarizador carrega o resumo
   privado do mundo, e essa entrada é lida por ferramentas e pelo drawer de
   debug. `tests/test_compaction.py` reprovou na hora. Está documentado ao lado
   do teste que trava.

2. **As chaves `presence.*` do i18n não são mortas.** Não têm leitor neste
   repositório porque quem as usa é o plugin curado de presença. Removi,
   `test_frontend_architecture.py` reprovou, restaurei todas. O cabeçalho de
   `i18n.js` agora avisa que o catálogo é contrato de plugin.

3. **`drive`/`watcher` e `roteiro` nunca renderizaram o mesmo contexto.**
   Pareciam idênticos na leitura; a comparação byte a byte antes/depois mostrou
   que os dois primeiros rotulam personagens por ID ("C2") e o terceiro por nome
   ("Marta"). Virou parâmetro explícito com comentário: unificar é experimento
   de prompt, não refatoração.

4. **Nenhum duplo de Director escrito à mão carregava o contrato inteiro.** Ao
   escrever o teste que compara `director_beat()` com o schema shippado,
   descobri que `scene_blocking`, `time_skip_ticks` e `time_skip_summary` eram
   obrigatórios no schema e estavam ausentes dos 43 dicts. A fábrica também
   tinha defaults mutáveis compartilhados — dois bugs achados pelo teste da
   própria fábrica.

5. **Eu afirmei que "o Playwright não consegue clicar" e era falso.** Os alvos
   que falhavam ficam dentro de `#setup-overlay`, um modal fechado
   (`opacity: 0`, `pointer-events: none`). Ele recusava certo. Abrindo o modal
   na ordem correta, dirige a UI inteira — incluindo gesto de swipe em viewport
   de celular.

## Como cada portão foi fechado

- **Suíte, ruff, mypy** a cada commit.
- **Prompt idêntico byte a byte** onde a refatoração tocou contexto de prompt
  (doc 13): capturado do `debug.jsonl` antes e depois.
- **Boot real** nos dois cenários: `.data/` vazio (Experience padrão aplicada,
  marcador escrito) e config v2 existente (chave da API preservada).
- **`curl`** nos contratos de erro: 404 sessão inexistente, 422 turno inválido,
  409 opening depois da conversa começar.
- **Sessão real contra a DeepSeek**, jogada pelo frontend em viewport 390×844:
  criar sessão, gerar aberturas, swipe no carrossel, turno, sugestão,
  compactação forçada, undo, drawer de debug. Zero erro de console.
- **Playtest manual do dono** (task 02), que produziu as tasks 53 a 57.

## O que ficou fora de escopo, declarado

- `config: dict` → dataclass tipada (atravessa adapters, SDK, `runtime-config.js`
  e ~40 testes: supertask própria).
- Dividir `main.py` em routers por domínio.
- Mover os prompts grandes para arquivos `.txt` — destruiria a rastreabilidade
  dos comentários que citam qual replay validou cada posição do texto.
- `style.css` (2.852 linhas), não revisado.

## O portão que continua sendo seu

**APK e aparelho** (`.claude/skills/android-apk-lab`). Os docs 10 e 11 mexeram
justamente no que só falha no celular: `android-bridge.js`, o shell do service
worker (hoje `rpt-shell-v31`), `build_info`, as strings nativas de boot e o lado
v1 do `pydantic_compat`, que nenhum teste de desktop cobre.
