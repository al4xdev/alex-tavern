# Debug tools

These tools run outside the normal Alex Tavern runtime. They can reproduce a recorded session
through the real Roleplay HTTP API without running llama.cpp.

## Curl-replay via MCP

The debug MCP server (`mcp_server.py`) exposes the curl-first validation method as two typed
tools: `replay_extract_call` locates one recorded LLM call in a session's debug log (exact agent
name, optional turn and occurrence) and `replay_llm_call` re-fires it at the ACTIVE provider up
to five times with small prompt edits (an append that lands at the end of the instruction body —
the validated position for new rules — or a replace that must match exactly once). Extraction
reads the log straight from disk, so it works with the application stopped.

## Experimental 33b watcher

`watcher_experiment.py` packages the exploration-validated stall probes (material-delta audit,
causal-intervention contract, deterministic stall ladder) without touching the runner.
`acceptance/watcher_abc.py` runs the A/B/C battery from the stagnation program (free baseline /
arbitrary disruption / clock+causal watcher) with isolated per-arm data dirs, arm-neutral offline
audits, and a blind critic.

## Prompt-cache probe

`prompt_cache_probe.py` proves provider-native prefix reuse through the same adapter, shared
client, and JSONL logger used by normal roleplay calls. It sends one warm request, three identical
repeats, and an early-prefix negative control:

```bash
uv run python -m tools.prompt_cache_probe --provider deepseek
uv run python -m tools.prompt_cache_probe --provider llama_cpp
```

The selected provider must already be reachable. Settings and the DeepSeek key come from
`.data/config.json`; credentials are neither printed nor logged. The command exits with status 0
only when a repeat reports non-zero cached tokens and the negative control reports fewer hits.
Its secret-free JSON result is printed to stdout, and complete calls remain in
`.data/sessions/cache-probe-<provider>-<nonce>/debug.jsonl`.

See [`docs/cases/06-prompt-caching-evidence-2026-07-12.md`](../docs/cases/06-prompt-caching-evidence-2026-07-12.md) for the verified DeepSeek and
llama.cpp runs, exact counters, server build, model, limitations, and inspection commands.

---

## 1. Start the recorded LLM replay

Stop llama.cpp so port 8888 is free, then run:

```bash
uv run python tools/replay_llm.py .data/sessions/<source-id>/debug.jsonl
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
uv run python tools/replay_session.py .data/sessions/<source-id>/debug.jsonl
```

The driver:

1. reads exact speech, private thought, action, and force-speaker values from required
   `turn_input` markers (older markers default missing `thought` to an empty string);
2. resets the replay cursor;
3. starts a fresh `thorn-lyra` session through the API;
4. submits every recorded turn and immediately reads the resulting session state;
5. verifies that both the turn response and latest persisted history record match that input's
   turn number, retaining history length/location observations in `turn_states`;
6. triggers compaction when the source contains a world/private summarizer output;
7. compares successful `{turn_number, agent, response}` entries in exact order.

It prints the new session id and preserves `state.json`, `debug.jsonl`, and active compaction checkpoints
under `.data/sessions/<new-id>/` for inspection.

When the original state files still exist, stricter state comparison can also be enabled:

```bash
uv run python tools/replay_session.py \
  .data/sessions/<source-id>/debug.jsonl \
  --source-checkpoint .data/sessions/<source-id>/backups/compaction.c000001.json \
  --source-final .data/sessions/<source-id>/state.json
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
request suggestions, undo, compact/restore, and inspect/reset/seek replay state. Session and scenario
deletion are intentionally not exposed. `inspect_debug_log` is local but sensitive: its bounded
output can contain complete prompts, model responses, and user-authored roleplay content.

The three session operations which can discard or replace state require an explicit confirmation
argument in addition to their MCP `destructiveHint` annotation:

```text
mutate_undo_turn(session_id="abc12345", confirm=true)
mutate_compact_session(session_id="abc12345", confirm=true)
mutate_restore_compaction(session_id="abc12345", confirm=true)
```

Omitting the argument or passing `false` returns a `ToolError` before any HTTP request is sent.
This keeps the safety rule consistent even in MCP clients that do not display annotation-based
confirmation UI. Reset/seek affect only the in-memory replay cursor and do not require this gate.

### Tool inventory

| Category | Tools |
|---|---|
| Inspection | `inspect_api_routes`, `inspect_sessions`, `inspect_session_state`, `inspect_session_history`, `inspect_debug_log`, `inspect_replay_status` |
| Session mutation | `mutate_start_session`, `mutate_fork_session`, `mutate_submit_turn`, `mutate_request_suggestions` |
| Confirmed destructive session mutation | `mutate_undo_turn`, `mutate_compact_session`, `mutate_restore_compaction` |
| Replay cursor mutation | `mutate_reset_replay`, `mutate_seek_replay` |

The adapter uses one shared asynchronous client per target service. It translates connection
failures, timeouts, HTTP errors, and invalid JSON into `ToolError` messages. History and debug-log
reads accept limits from 1 through 1,000. The stdio lifespan closes both clients when the MCP
client disconnects.

## Test data isolation

Pytest sets `ROLEPLAY_DATA_DIR` to a fresh temporary directory before importing application code.
All session JSON, backups, raw logs, config, and scenarios created by tests stay under that
directory. A session-wide safety guard aborts collection if storage ever resolves to the real
repository `.data` directory or one of its children.

## Replay fixture status

One checked-in fixture is maintained:

[`current_replay.debug.jsonl`](../tests/fixtures/current_replay.debug.jsonl): A three-field replay fixture containing nine Narrator-only turns plus one legacy summarizer response, with explicit `thought` fields (including non-empty thoughts) in the `turn_input` markers.

Strict three-field validation is enforced: `thought` must be a string key in every `turn_input` marker. There is no legacy fallback or compatibility layer for missing fields.

The older `7cb448da`/`614f2910` logs remain historical debugging evidence but contain no
`turn_input` markers. They are intentionally not accepted by the current conversation driver.

## Automated queued playtests

`playtest_harness.py` runs repeatable conversations directly through the real `Runner`, against
any live OpenAI-compatible endpoint. It is intended for bulk debugging and model comparisons,
not as a production request queue.

Start the model server first, then run all maintained scenarios twice:

```bash
uv run python tools/playtest_harness.py \
  --model-label gemma-4-26B-A4B-Q4_K_XL \
  --repeat 2 \
  --max-in-flight 1 \
  --llm-timeout 60
```

With llama.cpp configured as `--parallel 1`, keep `--max-in-flight 1`. The semaphore covers a
whole scenario rather than an individual HTTP request: each conversation retains its ordered
context, while later conversations wait in the harness instead of entering the server and
spending their HTTP timeout in an implicit queue. A server with multiple genuinely independent
slots can use the same number for `--max-in-flight` and `--parallel`.

To run the same suite through the active provider in the server-owned config (including a
DeepSeek key without placing it on the command line), use:

```bash
uv run python tools/playtest_harness.py \
  --config-file .data/config.json \
  --model-label deepseek-v4-flash \
  --repeat 2 \
  --max-in-flight 1
```

`--provider llama_cpp` or `--provider deepseek` can override only the provider selected by that
file. The complete key remains in `.data/config.json`; results record the provider/base URL but
never serialize the key. DeepSeek runs require `--config-file` rather than a secret CLI flag.
For reproducible A/B runs, the harness deliberately takes language, context, output limits,
compaction window, and timeout from its experiment defaults/CLI instead of from the server file;
the file supplies only provider transport, credentials, and model selection.

When no scenario paths are supplied, the harness discovers every JSON file under
`tools/playtests/`. The maintained suite currently separates four concerns:

| Scenario | Purpose |
|---|---|
| `micro_character_role.json` | Isolate the Character speech/thought boundary with little physical pressure |
| `micro_consequence_pov.json` | Check immediate physical consequences, viewpoint, and stable location |
| `natural.json` | Exercise a gradual conversation, automatic routing, compaction, and recall |
| `stress.json` | Reproduce the long, adversarial regression path, including suggestions, compaction, restore, and undo |

Specific files can be selected explicitly:

```bash
uv run python tools/playtest_harness.py \
  tools/playtests/natural.json \
  tools/playtests/micro_character_role.json \
  --model-label candidate-model \
  --repeat 3
```

Every invocation creates a fresh `/tmp/roleplay-playtest-suite-*` data directory, copies only the
default scenarios, and refuses to use the repository's real `.data` directory or any descendant.
Use `--output-dir` to choose a new, nonexistent directory elsewhere. The real `.data` tree is
never needed for a playtest run.

The output directory contains:

- `playtest-results.json`: complete inputs, outputs, before/after state snapshots, queue timings,
  raw deterministic metrics, and per-scenario aggregates;
- `playtest-report.md`: a compact run table for quick inspection;
- `sessions/*.json` and `sessions/*.debug.jsonl`: the same persisted state and raw LLM evidence
  produced by normal runtime sessions.

The built-in analysis counts errors, retries, prompt sizes, latency, `Player` prompt leaks,
nested `physical_facts`, second-person narration, likely Character physical actions, redundant
mood writes, exact sentence duplication, and forbidden Unicode dashes. These are deliberately
simple deterministic signals. Regex hits are candidates for manual review, not semantic proof;
the full state snapshots must also be inspected for incorrect `null` removals, invented events,
or other errors whose meaning depends on the scenario.

For an A/B model comparison, keep the scenario files, repetition count, language, context size,
and server sampler settings identical. Change only the endpoint/model and `--model-label`, then
compare both JSON manifests. A repeated prose/instruction-following failure suggests a
model/prompt interaction. State corruption, schema acceptance, queueing, persistence, and API
failures remain system concerns even when only one model happens to trigger them.
