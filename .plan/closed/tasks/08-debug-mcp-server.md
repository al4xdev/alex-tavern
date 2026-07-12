# Task: Debug toolkit, deterministic LLM replay, and MCP server

**Status:** Completed and closed
**Closed:** 2026-07-12
**README evidence:** `README.md`, section `MCP Debugging and Deterministic Replay`

## Goal

Create a local debugging stack that can exercise the real Roleplay backend and frontend without
running llama.cpp, then expose the application's debug operations to external development
clients through MCP.

The stack has three separate layers:

1. **Replay LLM (`127.0.0.1:8888`)** — an OpenAI-compatible fake server that consumes recorded
   LLM outputs in sequence.
2. **Roleplay application (`127.0.0.1:8889`)** — the existing real FastAPI application, Runner,
   persistence, compaction, undo, and frontend.
3. **Debug driver / MCP server** — tools that call the Roleplay HTTP API to create and drive
   sessions, inspect state, and perform debugging operations.

## MCP scope from the README

- Build an MCP server for external development/debugging clients, not for the roleplay
  turn loop.
- Expose tools to enumerate API routes.
- Inspect live session state.
- Drive the application through operations such as submitting a turn, forcing a speaker,
  and triggering compaction.
- Keep Narrator and Character model calls on their existing plain HTTP path.

## Deterministic LLM replay scope

- Load successful LLM outputs from `.data/sessions/{id}.debug.jsonl` once at startup.
- Preserve their original sequential order across Narrator, Character, suggestion, and
  summarizer calls.
- Expose `POST /v1/chat/completions` with the response envelope expected by
  `src.llm.client.chat_completion`.
- Skip non-LLM markers such as `undo`, `compact`, and `restore_compaction`; failed calls with no
  response are not replay outputs.
- Detect obvious sequence drift by comparing structured-output versus plain-text requests before
  consuming an entry.
- Provide local-only status, reset, and seek controls so one fixture can be replayed repeatedly.
- Return a clear exhausted-fixture error instead of silently recycling or inventing responses.
- Bind to `127.0.0.1` by default. Exposing recorded prompts or responses outside the local machine
  must require an explicit host override.

The server ignores semantic differences in player input by design. The real application still
processes and persists those inputs; the fake LLM only supplies the next recorded model output.
Call count and response kind must remain aligned with the fixture.

## Replay fixture and conversation driver

- The raw `response` field is sufficient to replay model content, including structured Narrator
  JSON and plain Character dialogue.
- Exact API replay uses the `turn_input` marker written before the first LLM call of every turn.
  It contains player `speech`, `action`, requested `force_speaker`, and the validated effective
  override.
- The maintained `tests/fixtures/current_replay.debug.jsonl` fixture exercises the current format
  with nine turns and one summarizer output. Logs without `turn_input` are rejected deliberately;
  no prompt/HISTORY inference or legacy compatibility layer is maintained.
- The driver should be able to start a preset session, submit the fixture turns sequentially,
  inspect state after each turn, trigger compaction, and report mismatches without a browser.

## MCP tools to expose

- Enumerate Roleplay API routes.
- List sessions and inspect a live session state.
- Start or fork a session.
- Submit a turn with speech, action, and optional forced speaker.
- Request suggestions.
- Undo/retry a turn where supported by the HTTP API.
- Trigger and restore compaction.
- Read replay status and reset/seek the replay cursor.

Mutation tools must be clearly separated from read-only inspection tools. Session deletion and
other destructive operations require an explicit confirmation design before exposure.

## Current repository state

- **MCP server & dependencies:** Implemented in [`tools/mcp_server.py`](../../../tools/mcp_server.py) using `FastMCP`.
- **Tool registry:** Exposes exactly 15 tools matching the specification (separating `inspect_` and `mutate_`).
- **Destructive confirmation:** `undo`, `compact`, and `restore_compaction` require
  `confirm=true` before the adapter sends an HTTP request; MCP annotations remain additive UI
  metadata rather than the only safety mechanism.
- **MCP tests:** Implemented in [`tests/test_mcp_server.py`](../../../tests/test_mcp_server.py),
  including a real stdio initialize/list-tools handshake.
- **Test data isolation:** Set up in [`tests/conftest.py`](../../../tests/conftest.py) using
  `ROLEPLAY_DATA_DIR` and verified in
  [`tests/test_data_isolation.py`](../../../tests/test_data_isolation.py).
- **LLM replay server & conversation driver:** Implemented in
  [`tools/replay_llm.py`](../../../tools/replay_llm.py) and
  [`tools/replay_session.py`](../../../tools/replay_session.py), with tests in
  [`tests/test_replay_llm.py`](../../../tests/test_replay_llm.py) and
  [`tests/test_replay_session.py`](../../../tests/test_replay_session.py).
- **Documentation:** The main README contains the feature-level architecture and safety model;
  [`tools/README.md`](../../../tools/README.md) contains operational commands and verification data.

## Running the implemented replay server

With llama.cpp stopped so port 8888 is free:

```bash
uv run python tools/replay_llm.py .data/sessions/<session-id>.debug.jsonl
```

Useful control endpoints:

```text
GET  http://127.0.0.1:8888/health
GET  http://127.0.0.1:8888/replay/status
POST http://127.0.0.1:8888/replay/reset
POST http://127.0.0.1:8888/replay/seek/{position}
POST http://127.0.0.1:8888/v1/chat/completions
```

The maintained fixture loads 10 successful responses: nine structured Narrator calls followed by
one summarizer call. Its nine `turn_input` markers make the conversation self-contained.

The final end-to-end run used the real Roleplay application on port 8889 and replay server on
port 8888, with storage isolated under `/tmp` and no llama.cpp process. All nine turns were
submitted, state was read and validated after each turn, compaction evicted 2 of 18 records, all
10 outputs matched exactly, and the replay cursor ended exhausted (`10/10`, `matches: true`).

## Acceptance criteria

- [x] A recorded session can be loaded and served on port 8888 without llama.cpp.
- [x] The existing Roleplay backend can consume structured and plain replay entries through its unchanged `llm_host` configuration.
- [x] Replay status reports total entries, current cursor, remaining entries, and the next expected agent without exposing response content.
- [x] Reset and seek are concurrency-safe; concurrent completion requests never consume the same entry.
- [x] Exhaustion and request/fixture mismatches return explicit non-2xx errors without advancing the cursor incorrectly.
- [x] Unit tests cover loading, filtering, order, empty/exhausted fixtures, mismatch, reset/seek, and concurrent consumption.
- [x] A debug driver can execute a complete machine-readable conversation against the real Roleplay API and replay LLM.
- [x] The driver validates response/state turn numbers and records state evidence after every submitted turn.
- [x] MCP tools can perform the same supported operations and preserve the plain HTTP model path.
- [x] The MCP server completes a real stdio initialize/list-tools handshake.
- [x] Every exposed destructive session operation requires an explicit server-side confirmation.

## Open questions

- **MCP transport and startup lifecycle:** Resolved. Communication runs over stdio via the `tools/mcp_server.py` process.
- **Authentication and safe exposure of raw/private session data:** Resolved for the local debug
  threat model. Transport is stdio, target URLs default to loopback, reads are bounded, and raw-log
  sensitivity is documented. Remote targets require explicit CLI configuration.
- **Destructive-operation confirmation:** Resolved. Deletion/retry remain absent; undo,
  compaction, and restore require `confirm=true` before any HTTP request.
- **Whether turn payload recording belongs in the append-only debug log or in a separate replay
  fixture format:** Resolved. Current logs use append-only `turn_input` markers; legacy inference
  is intentionally unsupported.
- **Whether the driver should control a browser for visual assertions or restrict itself to HTTP API/state assertions:** Resolved. Restricted to fast, lightweight HTTP assertions on state schemas and fields without browser dependencies.

## Closure evidence

- `uvx ruff check .`: passed.
- `uvx ruff format --check .`: passed.
- `uvx mypy src/ tools/mcp_server.py tools/replay_llm.py tools/replay_session.py`: passed.
- `uv run pytest -x`: 123 passed, 5 LLM tests deselected.
- Real MCP stdio handshake: initialized `Alex Tavern Debug`, negotiated protocol, listed 15 tools.
- End-to-end replay: 9 turns, 9 per-turn state observations, 1 compaction, 10/10 outputs,
  zero remaining entries, `matches: true`.
- Real repository `.data` was not used by the end-to-end run.
