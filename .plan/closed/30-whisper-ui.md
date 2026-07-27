# Task 30 — Whisper / Audience Control in the Frontend

## Goal

Expose the audience (whisper) model to the human player. The backend already
supports it end to end; the frontend has no way to use it.

## Current Problem

Task 22 delivered the full audience model: `PlayerTurnRequest.audience`
(`src/main.py`), Runner validation (known + present IDs, dedup, speaker
membership), persisted `TurnRecord.audience`, reply-audience inheritance for the
responding confidant, deterministic narrator/character confidentiality guards,
and whisper labels in prompts and rendered transcripts. Today all of that is
reachable only through the HTTP API and the playtest harness. A player using the
web UI cannot whisper at all, so the engine's most interesting confidentiality
mechanics are invisible in the product.

## Proposed Direction

- Composer control to select an audience for the next speech/action: a
  multi-select over currently present characters (the player's controlled
  character is implicitly covered by the Player→controlled normalization).
  Clearing the selection returns to public speech; the selection must not
  silently persist across turns.
- Send `audience` in the turn payload only when a whisper is active; surface the
  backend 422 validation errors (absent/unknown IDs) as a toast instead of a
  silent failure.
- Render whispered records distinctly in the session view (marker + audience
  names), consistent with `tools/render_transcript.py` semantics ("perceived
  only by ...").
- i18n (en/pt) for every new label; keep the mobile long-press action menu fully
  functional with a whisper active (same constraint Task 28 protects for Force
  Speaker).

## Acceptance Criteria

- [x] Frontend boundary test: selecting two present characters and sending
  speech produces a turn payload with exactly that `audience` list; sending
  without a selection omits the field. — `test_whisper_ui.py::test_turn_payload_carries_audience_only_when_selected`
- [x] Frontend boundary test: a rejected audience (backend 422) shows the error
  toast and does not clear the composer. — **faltava**, escrito em 2026-07-27:
  `TestTheRejectedTurnKeepsWhatTheUserTyped` (5 casos)
- [x] Whispered records are visually distinct in the session view and show the
  audience names in both languages. — `TestWhisperedRendering` + `test_styles_exist`
  + `test_i18n_keys_exist_in_both_languages`
- [x] Mobile action-menu interactions remain functional while a whisper is
  selected. — **faltava**, escrito em 2026-07-27:
  `TestTheActionMenuIsNeverLeftStale` (3 casos)
- [~] One real-LLM session through the UI: whisper a fact to one character with
  an outsider present, verify the outsider's later replies contain no secret
  token (existing guards), and the transcript renders the whisper markers.
  **Metade cumprida por instrumento mais forte, metade bloqueada** — ver nota
  de 2026-07-27 no fim.

> **CLOSED 2026-07-16.** Composer gained the whisper control (🤫 button +
> checklist popup of present non-controlled characters, populated with the
> force-speaker options); the turn payload carries `audience` only when a
> selection exists; a whisper without speech/action is blocked client-side
> mirroring the backend rule; the selection is cleared on every committed turn
> (never silently persists). Player echo and history records with an audience
> render a localized badge ("🤫 whispered to / sussurrado para {names}"),
> including zone-scoped records. i18n en/pt; 9 static boundary tests
> (`tests/test_whisper_ui.py`); JS syntax verified; the whisper mechanics
> end-to-end (payload → runner → guards → prompts) were already exhaustively
> validated by the partition/perspective live runs. Residual: a human
> click-through in a real browser (cannot be automated here) — the payload the
> UI emits is byte-identical to the harness-validated shape.

> **Superseded rendering detail (2026-07-26, Task 56):** after
> `audience_origin` began distinguishing explicit whispers from zone-computed
> perception, zone-scoped records stopped receiving the `🤫` badge. Only
> `audience_origin="whisper"` is now labeled as whispered.


---

# Nota de 2026-07-27

## Dois critérios estavam implementados e sem teste

O caminho de erro do compositor sempre fez a coisa certa: preserva os campos
("Keep inputs in fields so user can edit and retry"), dispara
`notify(t('turn.failed'), 'error')` e **não** chama `clearWhisperSelection()`.
Nada impedia uma edição futura de mover essas limpezas para um `finally` — o que
destruiria em silêncio um sussurro que o usuário teria de redigitar, com a
audiência perdida junto. `TestTheRejectedTurnKeepsWhatTheUserTyped` trava isso
partindo o corpo do submit no `catch` e exigindo que as limpezas fiquem só antes.

O quarto critério tem a mesma forma. O menu de ação é onde sussurro, desfazer,
repetir e pular vivem no celular; um turno que termine sem `updateActionPopup()`
deixa o botão de repetir escondido justamente depois de um sussurro falhar — o
estado em que o menu é mais necessário. Os dois caminhos refrescam o menu, e
agora há teste dizendo isso.

## O critério de sessão real: metade feita, metade bloqueada

A **substância** — sussurrar um fato a um personagem com um estranho presente e
o estranho jamais repetir o segredo — foi verificada hoje por um instrumento
mais forte que uma sessão manual: a campanha xfailed3 de 24 turnos com provider
real inclui o sussurro `LÚMEN-17` e pontua a família *secret* explicitamente.
**Deu 0**, tanto em `GLOBAL-whisper-leak` quanto em
`GLOBAL-secret-in-unauthorized-prompt`.

O que continua bloqueado é só a parte de **UI**: confirmar pelo navegador que a
transcrição desenha os marcadores. O plugin do Playwright não sobe. Diagnóstico
de hoje, com log:

```
TimeoutError: async initializeServer: Timeout 180000ms exceeded.
  - <launching> /opt/google/chrome/chrome ... --remote-debugging-pipe about:blank
  - <launched> pid=24342
```

O Chrome **inicia** (o processo nasce e reporta versão); o que nunca completa é o
handshake do `--remote-debugging-pipe`. Não é o repositório, não é a página, e
não é algo que eu resolva daqui — o mesmo bloqueio segura o item de 1080p/2K da
task 45.
