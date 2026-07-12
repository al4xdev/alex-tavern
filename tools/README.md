# Debug tools

These tools run outside the normal Alex Tavern runtime. They can reproduce a recorded session
through the real Roleplay HTTP API without running llama.cpp.

## 1. Start the recorded LLM replay

Stop llama.cpp so port 8888 is free, then run:

```bash
uv run python tools/replay_llm.py .data/sessions/<source-id>.debug.jsonl
```

The server binds to `127.0.0.1:8888` by default and implements the
`POST /v1/chat/completions` response shape used by the project. It loads successful responses
once, skips errors and non-LLM markers, and consumes outputs sequentially.

Controls:

```text
GET  /health
GET  /replay/status
POST /replay/reset
POST /replay/seek/{position}
```

## 2. Start the real Roleplay application

In another terminal:

```bash
./start.sh
```

The application runs on port 8889 and should have `llm_host` set to
`http://localhost:8888` in `.data/config.json`.

## 3. Recreate and compare the session

```bash
uv run python tools/replay_session.py .data/sessions/<source-id>.debug.jsonl
```

The driver:

1. reads exact speech, action, and force-speaker values from required `turn_input` markers;
2. resets the replay cursor;
3. starts a fresh `thorn-lyra` session through the API;
4. submits every recorded turn;
5. triggers compaction when the source contains a summarizer output;
6. compares successful `{turn_number, agent, response}` entries in exact order.

It prints the new session id and preserves the new `.json`, `.debug.jsonl`, and compaction backup
under `.data/sessions/` for inspection.

When the original state files still exist, stricter state comparison can also be enabled:

```bash
uv run python tools/replay_session.py \
  .data/sessions/<source-id>.debug.jsonl \
  --source-backup .data/sessions/<source-id>.kb_0.json \
  --source-final .data/sessions/<source-id>.json
```

The driver intentionally requires the current `turn_input` format. It does not infer inputs or
overrides from prompt text.

## 4. Connect the debug MCP server

The MCP server is a separate local development process. It does not participate in Narrator,
Character, suggestion, or summarizer model calls; those continue to use the existing plain HTTP
client. Start the Roleplay application on port 8889 and, when replay controls are needed, the
recorded LLM replay on port 8888. The MCP client should then launch:

```bash
uv run python tools/mcp_server.py
```

The server communicates over stdio and defaults to these local services:

```text
Roleplay API  http://127.0.0.1:8889
Replay API    http://127.0.0.1:8888
```

Override either URL when registering the process with an MCP client:

```bash
uv run python tools/mcp_server.py \
  --roleplay-url http://127.0.0.1:8889 \
  --replay-url http://127.0.0.1:8888
```

A generic client registration from the repository root is:

```json
{
  "mcpServers": {
    "alex-tavern-debug": {
      "command": "uv",
      "args": ["run", "python", "tools/mcp_server.py"],
      "cwd": "/absolute/path/to/roleplay"
    }
  }
}
```

Read-only tools are prefixed with `inspect_`; state-changing tools are prefixed with `mutate_`.
They enumerate live API routes, inspect sessions/history/state/raw logs, create and drive sessions,
request suggestions, undo, compact/restore, and inspect/reset/seek replay state. Session and preset
deletion are intentionally not exposed. `inspect_debug_log` is local but sensitive: its bounded
output can contain complete prompts, model responses, and user-authored roleplay content.

## Test data isolation

Pytest sets `ROLEPLAY_DATA_DIR` to a fresh temporary directory before importing application code.
All session JSON, backups, raw logs, config, presets, and defaults created by tests stay under that
directory. A session-wide safety guard aborts collection if storage ever resolves to the real
repository `.data` directory or one of its children.

## Verified fixture

Session `7cb448da` was replayed as session `614f2910`:

- 20 turns submitted through the real API;
- 35 successful outputs matched exactly;
- 20 Narrator, 14 Lyra, and 1 summarizer responses consumed;
- 45 history records evicted and 29 retained by compaction;
- no replay entries remained;
- no LLM errors occurred.
