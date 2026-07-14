# Task: Replace prompt preview with JSONL-based debug view

**Status:** Completed and closed  
**Closed:** 2026-07-13

## Delivered behavior

The debug panel's preview action now displays the last real Narrator request recorded in the
session JSONL log. It does not synthesize a hypothetical prompt or make a new LLM call.

## Closure evidence

- `src/static/app.js` fetches `api.getDebugLog(sessionId)`, finds the most recent entry with
  `agent === "narrator"` and request messages, and renders that request/response through the
  standard debug renderer.
- When no Narrator invocation exists, the UI renders the translated empty-state placeholder and
  reports the condition without treating it as a backend failure.
- `src/static/api.js` exposes only `getDebugLog` for this behavior; `previewPrompt` was removed.
- The old `POST /session/{session_id}/preview_prompt` endpoint, its request model, the Runner's
  synthetic prompt builder, and their integration tests were removed.
- The forward-only replacement was delivered in `fa064ae`.
