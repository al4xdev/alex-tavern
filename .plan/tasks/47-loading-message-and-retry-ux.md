# Task 47 — UX: reassuring loading message + persistent retry on error

**Status:** 🟡 ABERTA (2026-07-20, pedido do dono). Frontend polish; delegado a
subagente.

## 1. Retry persistente no erro do backend

Hoje: ao falhar um turno (`app.js` ~248-254), aparece um toast de 6s e o retry fica
**escondido no popup de ações ⚡** (`action-retry-btn`, mostrado via
`updateActionPopup` quando `state.lastTurnFailed`). O usuário não percebe.

Pedido: um **botão de retry visível e persistente** que espera o clique quando há
erro. Reusar `retryTurn()` (`app.js:573`, que reenvia `state.lastInputs`). Manter a
entrada no popup; adicionar uma affordance visível (banner/botão perto do input ou
no chat) que fica até o clique ou até um novo turno começar. i18n PT/EN.

## 2. Mensagem tranquilizadora na barra de loading

Hoje: `setLoading(on)` (`app.js:127`) só liga o spinner genérico. Um turno com
roteiro ligado é mais lento e parece lag.

Fronteira honesta: uma mensagem *específica de "gerando roteiro"* exigiria sinal de
streaming do backend (o roteiro é compilado dentro de um turno síncrono — um POST
só; o progresso de compactação, esse sim, é streamado com `stage`). **Fora de escopo
pra este polish.**

Versão pequena (frontend-only): após ~3-4s de loading, mostrar uma mensagem
tranquilizadora progressiva perto do spinner ("a história está se desenrolando…"),
com sabor de roteiro quando `roteiro_enabled` estiver ON (o frontend já tem o config).
Espelhar o estilo de `compact-progress-status`. Some ao terminar o turno. i18n PT/EN.

## Aceite
- [ ] Erro de turno mostra retry visível/persistente (não só toast + popup); clicar
      reenvia via `retryTurn()`; some ao clicar ou iniciar novo turno.
- [ ] Loading mostra mensagem tranquilizadora após um atraso; some ao concluir.
- [ ] i18n PT/EN com paridade; `tests/test_frontend_i18n.py` e
      `tests/test_frontend_architecture.py` verdes.
- [ ] Verificação visual do dono (1080p/2K).

## Follow-up (fora deste polish)
- Sinal de streaming do backend "compilando roteiro" para a mensagem ser exata
  (não só temporal). Liga com Task 44.
