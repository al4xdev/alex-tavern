# Task: Replace prompt preview with JSONL-based debug view

**Status:** Open

## Approach

The `previewPrompt` button currently hits a backend endpoint that builds hypothetical prompt
messages from the current state. This is redundant — the JSONL debug log already captures the
**real** request messages from every LLM call. Replace the preview with a direct JSONL read.

## What to remove

### Backend
- `POST /session/{session_id}/preview_prompt` endpoint (`main.py:450-458`)
- `PreviewPromptRequest` model (`main.py:150`)
- `preview_narrator_prompt` method (`runner.py:482-541`)

### Frontend
- `api.previewPrompt` in `api.js`

## What to change

### Frontend `app.js`
- Replace `previewPrompt()` function: instead of calling the old endpoint, call
  `api.getDebugLog(sessionId)`, filter for the **last** `agent: "narrator"` entry,
  and render its request messages.
- Fallback: if no narrator entry found, show a placeholder message.
- Rename button label from "Prompt preview" to something like "Last call" or keep
  the icon.

## Files affected

| File | Action |
|---|---|
| `src/main.py` | Remove endpoint + model |
| `src/runner.py` | Remove `preview_narrator_prompt` |
| `src/static/api.js` | Remove `previewPrompt` |
| `src/static/app.js` | Rewrite `previewPrompt` → JSONL-based |
| `tests/test_integration.py` | Remove `test_preview_narrator_prompt*` tests |

## Tests

- Remove old preview tests
- Verify debug log read still works
- Verify no orphaned imports
