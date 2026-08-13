# Task 47 — UX: a reassuring loading message + a persistent retry on error

**Status:** ✅ CLOSED (2026-07-20) — delivered by a subagent, visually accepted by the
owner ("perfeito"), i18n/architecture tests green (suite 702). The follow-up (a
streaming signal for the exact roteiro text) is documented and does not block.
**Commits:** `446ecb0` (implementation), `0daef89` (note).

## 1. A persistent retry on a backend error

Today: when a turn fails (`app.js` ~248-254), a 6s toast appears and the retry stays
**hidden in the ⚡ actions popup** (`action-retry-btn`, shown by `updateActionPopup`
when `state.lastTurnFailed`). The user does not notice it.

The request: a **visible, persistent retry button** that waits for the click when
there is an error. Reuse `retryTurn()` (`app.js:573`, which resends
`state.lastInputs`). Keep the entry in the popup; add a visible affordance (a
banner/button near the input or in the chat) that stays until the click or until a
new turn starts. i18n PT/EN.

## 2. A reassuring message in the loading bar

Today: `setLoading(on)` (`app.js:127`) only turns on the generic spinner. A turn with
the roteiro enabled is slower and feels like lag.

The honest boundary: a message *specific to "generating the roteiro"* would require a
streaming signal from the backend (the roteiro is compiled inside a synchronous turn
— a single POST; compaction progress, by contrast, is streamed with `stage`).
**Out of scope for this polish.**

The small version (frontend-only): after ~3-4s of loading, show a progressive
reassuring message near the spinner ("the story is unfolding…"), with a roteiro
flavour when `roteiro_enabled` is ON (the frontend already has the config). Mirror
the style of `compact-progress-status`. It disappears when the turn ends. i18n PT/EN.

## Acceptance — ✅ MET
- [x] A turn error shows a visible/persistent retry (the `retry-banner`); clicking it
      resends through `retryTurn()`; it disappears on click or when a new turn starts.
- [x] Loading shows a reassuring message after ~3.5s; it disappears on completion
      (`loading.stillWorking`/`stillWorkingStory`).
- [x] i18n PT/EN at parity; `test_frontend_i18n` and `test_frontend_architecture`
      green (suite 702).
- [x] Visual verification by the owner ("perfeito", 2026-07-20).

## Follow-up (outside this polish)
- A backend streaming signal for "compiling the roteiro", so the message can be exact
  (not merely time-based). Connects to Task 44.
