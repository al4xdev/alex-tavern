# 10 — `app.js`: quebrar o monólito e fechar os bypasses

> 🟡 **PARCIAL** (branch `refactor/pre-1.0-cleanup`, 2026-07-26).
>
> **Feito:** `android-bridge.js` (8bfa8ce), `markdown.js` + `onboarding.js`
> (79f8529), `debug-drawer.js` (6319304); `checkVersionSync` arrumado com i18n e
> toast compartilhado; comentários "Antigravity" e código comentado removidos;
> `sw.js` com shell completo (agora travado por teste que exige TODO módulo na
> lista) e cache em `rpt-shell-v24`. `app.js`: 2.424 → 2.050 linhas.
>
> **Falta:** `transcript.js`, `composer.js`, `sessions-modal.js`,
> `compaction-ui.js`, `opening-picker.js`, `dom.js`. Motivo declarado: a
> acoplagem medida desses cinco é de 6 a 11 funções externas cada (contra 1 do
> debug drawer), e todos ficam no caminho do turno ao vivo. O portão que tenho
> aqui — Playwright — valida carga e render com zero erro de console, mas **não
> consegue clicar**: o `pointer-events` dos overlays intercepta a checagem de
> actionability, então uma regressão de interação passaria batido. Esses cinco
> pedem o playtest manual do dono como portão, não um teste headless.
>
> **Chaves de i18n órfãs: NÃO remover.** Foram removidas e restauradas no mesmo
> commit: `presence.*` e `character.inScene` são o contrato do plugin curado de
> presença (ver `tests/test_frontend_architecture.py`). O cabeçalho de `i18n.js`
> agora diz isso.

**Escopo:** `src/static/app.js` (2.424 linhas), `i18n.js`, `api.js`, `index.html`
**Esforço:** M/L · **Risco:** médio (é a view do jogo) · **Quebra contrato:** nenhuma

## Sintoma A — um módulo, treze responsabilidades

`app.js` tem ~70 funções cobrindo: toasts, loading, empty state, carrossel de
opening, lista de sessões, render de histórico, typewriter, cena, sugestões,
hint popup, compactação com SSE, drawer de debug, whisper, force speaker,
**um parser de markdown próprio** (`parseMarkdown:2163`,
`parseInlineMarkdown:2204`), banner de dicas, help drawer, gestos de swipe,
install prompt de PWA e version check.

O projeto já é modular por toda parte — `api.js`, `setup.js`, `i18n.js`,
`runtime-config.js`, `plugin-center.js`, `plugin-runtime.js`, `slash-*.js`,
`adapters/*` — e `AGENTS.md` §4 declara "frontend vanilla em módulos ES, sem
globals de aplicação". `app.js` é o único lugar que não seguiu.

Métricas do arquivo:

- **75** `const x = document.getElementById(...)` no escopo de módulo (79 no
  total), todos resolvidos no import — antes de qualquer checagem de existência;
- **17** `let` soltos no escopo de módulo, ao lado de um objeto `state` com 13
  campos (`app.js:25-43`). Não há regra dizendo o que vai em `state` e o que
  vira `let`: `openingIndex` e `openingBusy` são estado de UI tanto quanto
  `state.busy`;
- **34** guards `if (elemento)` antes de `addEventListener`, para elementos que
  estão fixos em `index.html` — defensividade que nunca dispara e que esconde um
  typo de id (o listener simplesmente não é registrado, em silêncio).

### Corte proposto

| Módulo novo | Sai de |
|---|---|
| `transcript.js` | `addMessage`, `renderHistory`, `revealTypewriter`, `messageSegments`, `speakerInfo`, `colorFor`, `updatePlayerEcho`, `buildPlayerEcho` |
| `sessions-modal.js` | `openSessionsModal`, `renderSessionList`, `loadSession`, `timeAgo` |
| `composer.js` | inputs, whisper, force speaker, hint popup, `sendTurn`, `skipTurn`, `retryTurn`, `undoLastTurn` |
| `compaction-ui.js` | `compactSession`, `restoreCompaction`, `renderCompactionProgress`, `compactionProgressPercent`, `setCompactionBusy` |
| `debug-drawer.js` | `renderDebugBlock`, `renderRawLog`, `refreshDebugLog`, `previewPrompt`, `makeCopyBtn`, `messagesToText` |
| `markdown.js` | `parseMarkdown`, `parseInlineMarkdown` (+ teste unitário, hoje inexistente) |
| `onboarding.js` | `showTipBanner`, help drawer, `showHelpArticle`, `checkVersionSync` |
| `opening-picker.js` | carrossel de opening (6 funções + 4 `let`) |
| `dom.js` | um `el(id)` com falha alta em id inexistente, no lugar dos 75 `getElementById` |

`app.js` fica com: `state`, wiring dos módulos, `startSession`, `ingestState` e
`initializeApplication`. Estimativa: ~300 linhas.

## Sintoma B — `checkVersionSync` fura três convenções de uma vez

```js
// app.js:2396-2418
const isPt = (localStorage.getItem('language') || 'en') === 'pt-BR';
if (isPt) {
    textSpan.innerHTML = `⚠️ <strong>Nova versão disponível!</strong> ...`;
} else {
    textSpan.innerHTML = `⚠️ <strong>Update available!</strong> ...`;
}
```

1. **Bypassa o i18n**: o projeto inteiro usa `t('chave')` e `data-i18n`; aqui há
   um `if (isPt)` com as duas strings hardcoded;
2. **Lê `localStorage` direto** em vez de `getLocale()` (`i18n.js` já exporta);
3. **Monta uma segunda implementação de toast** (`showVersionWarningToast:2396`)
   com `innerHTML`, em vez de usar `toast()` (`app.js:142`), que já existe 2.250
   linhas acima e usa `textContent`.

Some a isso que a função faz `fetch('https://api.github.com/repos/al4xdev/alex-tavern/commits/master')`
com o repositório **hardcoded no meio da view**, num app que roda offline no
celular. Vale decidir explicitamente se este check entra na 1.0; se entrar, ele
merece: chave de i18n, `toast()` compartilhado, URL em constante junto do resto
da config de build, e um `catch` que não polua o console em modo avião.

## Sintoma C — restos visíveis

- `src/static/api.js:5` e `src/static/index.html:4`:
  `WARNING (Antigravity AI): Modified to switch BASE_URL...` — comentários de
  outra ferramenta de IA que sobraram no código de produção. O conteúdo é
  legítimo e importante (o `BASE_URL` de `file://` e os caminhos relativos são o
  que fazem o WebView funcionar); só a atribuição precisa virar um comentário
  normal explicando *por quê*, sem o "WARNING" nem o nome da ferramenta.
- `app.js:2372`: `// openSessionsModal(); // show the sessions list on first load`
  — código comentado.
- **11 chaves de i18n órfãs** (17 entradas contando os dois locales; verificado
  com busca em todos os `.js` e no `index.html`, descontando as compostas
  dinamicamente como `compaction.stage.*`/`engine.*Band.*` e as consumidas por
  dados como `help.warning.*`, que vêm de `help/warning.json`):
  `presence.panelTitle`, `presence.controlled`, `presence.saving`,
  `presence.loading`, `presence.undoButton`, `presence.nothingToUndo`
  (`i18n.js:144-149` e `:523-528` — o painel de presença virou plugin, ver
  `setup.js:181`), mais `character.inScene`, `empty.open`,
  `debug.previewNarrator`, `plugins.noCatalog` e `commands.startFirst`.
  Atenção: os endpoints `POST /session/{id}/presence` e `/presence/undo`
  continuam existindo e são usados por `api.js:221,232` — o que morreu foi a UI
  no core, não a feature.
- `sw.js:9-35`: a lista `SHELL` é mantida à mão e **não inclui**
  `help/warning.json` nem os 14 `help/**/*.md` — o banner de dicas e os artigos
  de ajuda não funcionam offline, embora sejam parte do onboarding. Ou entram no
  precache, ou o `showTipBanner` some no offline por decisão declarada (hoje ele
  cai no `catch` e esconde o banner, o que é sorte, não desenho).

## Passos

1. `dom.js` + `markdown.js` primeiro (isolados, com teste).
2. Um módulo por commit, sempre com `tests/test_frontend_architecture.py` e
   `tests/test_frontend_i18n.py` verdes.
3. Limpar chaves órfãs e comentários (rápido, faça junto).
4. Decidir `checkVersionSync` (manter com i18n / mover para o modo debug /
   remover) — é decisão de produto, não de código.
5. Fechar `SHELL` do service worker + bump do `rpt-shell-v21`.

## Como validar

- `uv run pytest tests/test_frontend_architecture.py tests/test_frontend_i18n.py
  tests/test_whisper_ui.py`;
- `tools/frontend_inspector.py` (Playwright) com **zero** erros de console e de
  página, nos dois locales;
- inspeção manual do fluxo completo: criar sessão, turno, whisper, sugestão,
  compactar, undo, debug drawer, help — o `.plan/backlog/02-readme-media/manual-playtest-script.md`
  já descreve o roteiro;
- no celular: `.claude/skills/android-apk-lab` para confirmar que o WebView
  carrega os módulos novos por caminho relativo (é o ponto onde um import
  absoluto quebra e o desktop não acusa).

## Não fazer

- **Não** introduzir framework nem bundler. A regra "vanilla em módulos ES" é do
  `AGENTS.md` §4 e o custo do WebView `file://` é real.
- **Não** trocar o parser de markdown por biblioteca: ele serve 7 artigos de
  ajuda controlados por nós; uma dependência aqui pesaria mais do que resolve.
</content>
