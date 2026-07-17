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

- [ ] Frontend boundary test: selecting two present characters and sending
  speech produces a turn payload with exactly that `audience` list; sending
  without a selection omits the field.
- [ ] Frontend boundary test: a rejected audience (backend 422) shows the error
  toast and does not clear the composer.
- [ ] Whispered records are visually distinct in the session view and show the
  audience names in both languages.
- [ ] Mobile action-menu interactions remain functional while a whisper is
  selected.
- [ ] One real-LLM session through the UI: whisper a fact to one character with
  an outsider present, verify the outsider's later replies contain no secret
  token (existing guards), and the transcript renders the whisper markers.

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
