# Server-owned multi-provider architecture and the DeepSeek V4 Flash integration

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 02 |
| **Date** | 2026-07-12 |
| **Status** | Adopted architecture; DeepSeek remains the active provider |

## Abstract

Model and API discovery, a server-owned provider-adapter architecture (the browser never holds credentials), configuration and UI surfaces, tests, and live validation of DeepSeek V4 Flash against the local Gemma baseline. The adapter boundary introduced here is the one every later agent call, security policy and cache measurement flows through.

---

## Original report
**Date**: 2026-07-12
**Scope**: exact model/API discovery, provider architecture, server-owned configuration, UI,
tests, and live validation.

### Confirmed API contract

- Account model inventory: `deepseek-v4-flash`, `deepseek-v4-pro`.
- Selected model: `deepseek-v4-flash`.
- Base URL: `https://api.deepseek.com`.
- Non-reasoning request: `thinking: {"type": "disabled"}`.
- `response_format: json_object`: accepted; response contained no `reasoning_content`.
- `response_format: json_schema`: rejected with HTTP 400, “This response_format type is
  unavailable now”.

The local Deep Code clone independently uses the same model name and disabled-thinking payload.

### Architecture delivered

- `src/llm/adapters/`: separate contract, registry, llama.cpp, and DeepSeek modules. Each adapter
  owns transport capabilities, response extraction, defaults, secret metadata, forced settings,
  URL/auth, and request adaptation.
- `src/llm/client.py`: provider-neutral HTTP, retry, output policy, and JSON parsing;
  `src/llm/schema.py` owns strict local validation and `src/llm/debug_log.py` owns concurrent log
  persistence.
  DeepSeek JSON Schema requests become JSON Object requests plus the schema instruction and local
  validation; invalid schema responses enter the existing retry path.
- `src/config.py`: one canonical `.data/config.json`, per-provider settings, validation, atomic
  writes, secret preservation/redaction, active-provider resolution, and shared agent call
  options.
- `src/main.py`: `GET /config` and `PUT /config`; config persistence and Runner replacement share
  one runtime lock. The shared HTTP client has no provider-bound base URL.
- Frontend: `src/static/adapters/` declaratively owns each provider's cards, fields, secrets,
  forced values, and serialization. The setup modal renders those adapters without provider HTML
  or application globals. Provider settings never use localStorage. The API key input is
  write-only; GET exposes only `api_key_configured`.
- Service worker: `/config` is network-only and `runtime-config.js` is part of the versioned app
  shell.
- Playtest harness: `--config-file .data/config.json` uses the configured provider/credential
  without exposing a secret CLI parameter, while preserving identical experiment parameters for
  A/B comparisons.

### Live application validation

Using an isolated temporary data root:

- config GET/PUT succeeded;
- DeepSeek remained selected after a full Uvicorn restart;
- the API key remained configured but absent from every config response;
- a real forced-C2 turn completed through the actual HTTP API;
- the turn made one Narrator and one Character request through the DeepSeek adapter;
- narration, Character response, state persistence, and routing all completed successfully.

### Test-suite cleanup in parallel

- Default suite reduced from 133 to 121 cases before provider tests.
- Old stochastic LLM tests were replaced by the maintained harness.
- The historical llama probe was preserved as `tools/legacy_llama_api_probe.py` *(contract note: later deleted; it survives in git history)*.
- Retry coverage no longer waits through real backoff.
- Six provider/config/adapter cases were added, bringing the current suite to 127 fast tests.

### A/B playtest

The first 8-run DeepSeek integration suite completed with zero failed runs but inherited the
server's Portuguese/larger-token settings, so it is evidence of compatibility rather than a fair
model comparison.

The fair suite used the exact Gemma baseline language (English), 65,536-token context, output
limits, timeout, four scenarios, two repetitions, and a single in-flight scenario. Both providers
therefore received the same 8 scenario runs.

| Signal | DeepSeek V4 Flash | Gemma 4 26B local | Interpretation |
|---|---:|---:|---|
| Character outputs containing action markers | 39/69 (56.5%) | 59/69 (85.5%) | DeepSeek followed the dialogue-only role more often, but still violated it frequently. |
| Narrations containing second-person language | 51/86 (59.3%) | 8/86 (9.3%) | DeepSeek was substantially worse at the requested third-person narrator POV. |
| Nested `physical_facts` outputs | 0 | 3 | DeepSeek was cleaner. |
| Redundant mood updates | 0 | 5 | DeepSeek was cleaner. |
| Raw em dashes | 6 | 14 | DeepSeek violated the style rule less often. |
| Schema failures/retries | 2/2 | 0/0 | Both DeepSeek failures were caught and recovered by local validation. |
| Full suite wall time | 507.3 s | 680.3 s | DeepSeek completed about 25% faster in this run. |

The two rejected DeepSeek responses contained real contract violations: one `next_speaker`
outside the allowed enum and one boolean where `scene_update` allowed only string or null. Neither
invalid response reached application state.

Manual inspection exposed an additional failure that the existing regex metrics do not measure:
DeepSeek narrations sometimes wrote Lyra's physical actions and dialogue, after which the Character
agent responded again. Character outputs also still used roleplay action markers. Consequently,
DeepSeek V4 Flash is **not a strict quality upgrade** over the local Gemma model; it changes the
failure profile. It is better on state shape, mood stability, punctuation, speed, and Character
action frequency, but materially worse on Narrator POV and role ownership under the English test.

The earlier Portuguese compatibility suite had only 8 second-person narrations and 7 Character
action hits, but it also used different context/output settings. That is a useful indication of a
language/prompt interaction, not a valid model comparison. The next prompt study should therefore
measure narrator role ownership explicitly and compare English and Portuguese independently.

Artifacts retained for inspection:

- DeepSeek fair suite: `/tmp/roleplay-playtest-suite-vekl52w5`
- Gemma baseline: `/tmp/roleplay-playtest-suite-7zkowcx7`

### Closure

All feature acceptance requirements are implemented. The provider task is closed; prompt-quality
refinement remains a separate experimental concern rather than an integration blocker.

Final repository validation after formatting:

- `uvx ruff check .`: passed;
- `uvx ruff format --check .`: 31 files already formatted;
- `uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py tools/replay_llm.py tools/replay_session.py`:
  passed for 20 source files;
- `uv run pytest -x`: 127 passed in 1.51 seconds;
- JavaScript syntax checks, HTML parsing, and `git diff --check`: passed.

Post-audit remediation subsequently expanded the suite to 137 passing tests and split adapters,
schema validation, debug logging, frontend modules, immutable built-ins, preset representation,
and session concurrency into their final ownership boundaries. The final canonical preset/session
HTTP smoke test passed through load, save, start, state read, fork, and deletion without an LLM.

### Security closure

`.data/` was already listed in `.gitignore`, but `.data/config.json` remained tracked from an
earlier commit. With explicit owner authorization, `git rm --cached .data/config.json` removed it
from the index while retaining the local file and configured key. `git check-ignore` confirms
that both configuration and session files are covered by the directory-wide rule. Runtime and
CI/CD environments must create and own their respective data directories.
