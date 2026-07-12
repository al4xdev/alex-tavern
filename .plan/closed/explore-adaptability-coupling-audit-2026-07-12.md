# Explore: Adaptability and coupling audit

**Date**: 2026-07-12
**Scope**: Read-only review of backend, LLM integration, persistence, and vanilla frontend, with a concurrent review of the uncommitted provider work in `src/config.py` and `src/llm/providers.py`.

## Executive finding

The codebase is small and most direct dependencies are proportional to that size. The new provider adapter is a real separation at the HTTP compatibility boundary, not a cosmetic abstraction. The main extensibility gap is that provider discovery, configuration, validation, and UI metadata remain separate hardcoded catalogs. The most concrete correctness risks are concurrency boundaries around runtime configuration and filesystem mutations, rather than the number of modules or absence of a large dependency-injection framework.

## Findings

### High: persisted configuration and active runtime configuration are not one transaction

- `merge_config_update()` serializes read/merge/validate/write under `_config_lock`, but releases that lock before the server replaces `STORED_CONFIG`, `SERVER_CONFIG`, and `runner`: `src/config.py:169-179`, `src/main.py:404-417`.
- Two concurrent `PUT /config` calls can interleave as follows: request A writes A, request B writes B, request B installs runner B, then request A installs runner A. Disk contains B while subsequent LLM calls use A.
- The three globals plus `llm_client` are initialized and mutated directly by the FastAPI module: `src/main.py:27-42`. Every route reaches the current global `runner` rather than application-scoped state: `src/main.py:134-370`, `src/main.py:463-470`.
- Replacing the Runner is otherwise safe for already-running method calls: Python retains the bound Runner for the active await. The inconsistency concerns concurrent config updates and which configuration later calls observe.

### Medium-high: provider adapters are centralized, provider metadata is not

- Transport differences are correctly concentrated in `LlamaCppAdapter` and `DeepSeekAdapter`: completion URL, headers, structured-output request adaptation, and DeepSeek thinking payload live in `src/llm/providers.py:20-105`.
- Adapter lookup itself is a single registry: `src/llm/providers.py:108-119`.
- A separate provider catalog exists in configuration (`PROVIDER_NAMES` and `DEFAULT_CONFIG`), with DeepSeek branches for model requirements, key handling, redaction, and thinking: `src/config.py:15-44`, `src/config.py:69-125`, `src/config.py:169-201`.
- The same two-provider catalog is repeated in the browser field map and conditional key handling: `src/static/runtime-config.js:8-43`, `src/static/runtime-config.js:56-110`.
- Provider cards and provider-specific forms are separately encoded in HTML: `src/static/index.html:42-128`.
- Therefore a third provider is “one adapter” only at the outbound HTTP layer. Making it selectable requires coordinated changes to at least the adapter registry, backend config catalog/validation/redaction, browser mapping, and HTML. Nothing enforces that these catalogs stay aligned; a config-supported provider can lack an adapter or vice versa.
- Some duplication is intentional: distinct providers genuinely need different forms and secret fields. The coupling problem is the absence of a shared source of provider identity/capability metadata, not the mere presence of provider-specific UI.

### Medium: JSON completion prepares the same request through the adapter twice

- `chat_completion_json()` calls `adapter.prepare_request()` with the JSON Schema, then passes the prepared messages/format to `chat_completion()`: `src/llm/client.py:454-485`.
- `chat_completion()` resolves the adapter again and calls `prepare_request()` a second time, this time without the schema: `src/llm/client.py:326-348`.
- Current adapters happen to tolerate this. For DeepSeek, the first pass inserts the schema instruction and converts the format; the second pass preserves that message and supplies the thinking payload. Llama.cpp copies the request twice without semantic change.
- The adapter protocol does not state that preparation must be idempotent or safe in multiple phases: `src/llm/providers.py:20-38`. A future adapter with an unconditional message or payload transform could apply it twice.

### Medium: provider/config details are threaded through every agent as an untyped dict

- Character, Narrator, Suggest, and Summarizer each extract the same provider fields and pass them individually into the low-level client: `src/agents/character.py:99-136`, `src/agents/narrator.py:246-273`, `src/agents/narrator.py:382-415`, `src/agents/summarizer.py:159-183`.
- Repeated fields include model, language, timeout, provider, API base, API key, and thinking state. Token-limit extraction is also repeated with local defaults.
- `Runner` retains a raw mutable `dict` as its configuration and passes it to agents: `src/runner.py:35-40`, `src/runner.py:404-437`.
- Adding a provider capability that agents must expose expands all four call sites. A transport-only provider difference remains isolated by the adapter and does not.

### Medium: session mutation locking is enforced by convention and bypassed by endpoints

- `save_game()`, `load_game()`, and backup restoration document that callers must hold the per-session lock, but do not enforce it: `src/store/sessions.py:43-91`, `src/store/sessions.py:137-188`.
- Runner turn, undo, compact, and restore operations do hold the lock: `src/runner.py:164`, `src/runner.py:259`, `src/runner.py:333`, `src/runner.py:395`.
- State/history reads, suggestions, session deletion, and session forking operate outside it: `src/runner.py:232-241`, `src/runner.py:287-314`, `src/store/sessions.py:191-199`, `src/store/sessions.py:242-258`, with direct API exposure at `src/main.py:473-496`.
- Atomic rename protects readers from partially written JSON, but it does not serialize higher-level operations. A delete can race with an in-flight turn and be followed by that turn recreating the session; a fork can capture either side of a concurrent turn.
- The direct filesystem store is intentional and appropriately lightweight for a personal single-process app. The issue is inconsistent use of its own mutation boundary, not the choice of JSON persistence.

### Medium: preset locking is declared but never used

- The module claims “per-name lock” and defines `_preset_locks`/`_get_lock()`: `src/store/presets.py:1-21`.
- No source caller uses `_get_lock()`; save and delete execute without it: `src/store/presets.py:34-54`, `src/store/presets.py:73-80`.
- Atomic replacement prevents a half-written JSON document, but concurrent save/delete remains last-operation/interleaving dependent. The dead lock registry also makes the module’s stated concurrency guarantee inaccurate.

### Medium-low: presets have two character representations across storage/API/UI

- Built-in presets use canonical nested `mind`/`body` characters. Current `.data/defaults/thorn-lyra.json` and `thorn-lyra-pt.json` both have that representation.
- User presets are saved from `StartSessionRequest`, whose characters are flat `CharacterInput` objects: `src/main.py:62-82`, `src/main.py:442-449`.
- Session start consequently parses both nested and flat character shapes: `src/main.py:160-214`.
- The browser separately flattens built-in characters, while user presets can be populated directly: `src/static/setup.js:165-217`, `src/static/setup.js:298-314`.
- `Runner.start_session()` contains another built-in-preset conversion path: `src/runner.py:63-107`.
- This is active format duplication, not solely historical compatibility. It creates multiple conversion paths for the same domain object and makes preset behavior depend on origin.

### Low-medium: the LLM client combines transport, output policy, validation, retry, and persistence

- `src/llm/client.py` is 502 lines and contains debug JSONL persistence (`101-258`), global writing-style injection (`303-324`), provider dispatch/HTTP (`326-360`), response parsing/schema checks (`30-85`, `361-366`), and retry/backoff (`406-502`).
- The provider adapter isolates outbound compatibility but response extraction remains fixed to OpenAI’s `choices[0].message.content`: `src/llm/client.py:360`. This is consistent with the module’s stated scope of OpenAI-compatible APIs, so it is not a defect for llama.cpp or DeepSeek.
- The module docstring still describes only llama.cpp and localhost:8888: `src/llm/client.py:1-4`. That is stale ownership language after introduction of multiple providers.
- Debug records include provider, base URL, and thinking state but do not include the API key: `src/llm/client.py:172-196`. Secret containment is preserved at this boundary.

### Low-medium: local JSON Schema validation is deliberately partial and silently accepts unknown types/keywords

- DeepSeek relies on prompt-enforced JSON Object mode followed by local validation: `src/llm/providers.py:73-105`, `src/llm/client.py:44-85`.
- `_matches_json_type()` returns true for an unknown schema type, and unsupported schema keywords are ignored rather than rejected: `src/llm/client.py:30-41`, `src/llm/client.py:44-85`.
- All currently generated agent schemas use only the implemented subset: object, array, primitive/null unions, enum, required, additionalProperties, items, minItems, and maxItems (`src/agents/narrator.py:62-101`, `src/agents/narrator.py:332-357`, `src/agents/summarizer.py:50-67`). Current behavior is therefore covered.
- The extensibility hazard appears only if later schemas add constraints such as string lengths, numeric bounds, combinators, or references; those constraints would look present but would not be enforced locally.

### Low: process-global lock registries have inconsistent lifecycle

- Session locks are acknowledged as indefinitely growing, though explicit deletion removes one: `src/store/sessions.py:17-26`, `src/store/sessions.py:191-199`.
- Debug-log locks grow by every logged session and have no corresponding removal when a session is deleted: `src/llm/client.py:21-23`, `src/llm/client.py:101-117`; `delete_session()` removes only `_session_locks`: `src/store/sessions.py:191-199`.
- Preset locks would be removed on deletion, but are currently never created because `_get_lock()` is unused: `src/store/presets.py:14-21`, `src/store/presets.py:73-79`.
- These are process-local registries. They do not coordinate multiple Uvicorn workers or processes.

### Low: explicit legacy/special cases remain despite the forward-only direction

- `resolve_personality()` still combines `personality_summary` and `personality_full` when `personality` is absent: `src/models.py:131-139`.
- The session-start preset parser supports nested and flat characters: `src/main.py:160-192`. As noted above, flat user presets are still actively generated, so this branch cannot currently be classified as dead legacy.
- Default ordering special-cases the literal `thorn-lyra`: `src/store/presets.py:93-104`. Browser error fallback repeats that default name: `src/static/setup.js:262-293`.
- `PRESETS_KEY` and `BUILTIN` are declared but unused remnants of earlier browser preset handling: `src/static/setup.js:8-10`.
- Runtime LLM config and keys do follow the user’s server-owned requirement: `runtime-config.js` calls `/config` and does not use browser storage (`src/static/runtime-config.js:1-150`). `setup.js` still stores the last game setup in localStorage (`src/static/setup.js:246-255`), which is separate from LLM provider configuration and API secrets.

### Low: frontend modules depend on script load order and shared globals

- `api.js`, `runtime-config.js`, `setup.js`, and `app.js` are loaded as classic scripts in a fixed order: `src/static/index.html:355-358`.
- They communicate through globals (`api`, `RuntimeConfig`, `Setup`, `toast`) rather than explicit imports; for example Setup probes `RuntimeConfig` and `toast`: `src/static/setup.js:257-260`, `src/static/setup.js:347-353`.
- This is a common and proportionate choice for a dependency-free vanilla frontend. It becomes a coupling concern mainly when modules are tested or loaded independently; it is not presently evidence that a frontend framework or build system is needed.

## Coupling that appears intentional and proportionate

- `Runner` directly importing the three known roleplay agents is its core orchestration responsibility, not provider coupling: `src/runner.py:15-18`.
- `Player` and `Narrator` string sentinels are repeated across model, runner, prompts, and UI because they are persisted domain protocol values: `src/models.py:55-63`, `src/models.py:112-123`, `src/runner.py:173-210`, `src/static/app.js:271`, `src/static/app.js:362-367`.
- `src/paths.py` successfully centralizes all runtime filesystem roots and honors `ROLEPLAY_DATA_DIR`: `src/paths.py:1-13`.
- `src/static/api.js` centralizes HTTP error parsing and route calls; direct knowledge of backend paths is expected in this thin API client rather than scattered through UI handlers: `src/static/api.js:8-125`.
- The adapter registry uses immutable singleton adapters with no mutable instance state: `src/llm/providers.py:41-119`. This global registry is not equivalent to the mutable runtime globals in `main.py`.
- File-local atomic write implementations are repeated in config, sessions, presets, and playtest reports. Their details are similar, but they write different formats/ownership domains; at current size this is duplication, not strong evidence for a generalized persistence framework.

## Open questions

- Whether runtime provider changes are intended to affect every existing session on its next operation or only newly created sessions. Current behavior changes all subsequent operations because provider config belongs to the global Runner, not the persisted session.
- Whether multiple Uvicorn workers are an intended deployment mode. Current locks, globals, and adapter/config state are process-local.
- Whether user presets are expected to remain a frontend-shaped contract or converge on the nested persisted domain shape. Both are active today.

## Post-audit status in the provider change set

The audit was read-only and captured a moving uncommitted implementation. The primary agent
subsequently addressed four findings inside the provider scope:

- runtime persistence and the in-memory Runner swap now share `_runtime_config_lock`;
- backend provider identity/defaults/secrets/forced settings are discovered from the adapter
  registry rather than a separate `PROVIDER_NAMES` catalog;
- JSON requests pass through `prepare_request()` once;
- agents use one `llm_request_options()` projection rather than repeating provider transport
  fields.

The provider-specific HTML remains explicit because the two forms genuinely expose different
fields; a new selectable UI provider still requires a deliberate interface addition. The
preexisting session/preset locking, dual preset representation, legacy personality conversion,
and global lock-lifecycle findings were not changed as part of the provider task.

## Final remediation closure

The initial provider task was reopened because “closed” in this project means its actionable
review findings are resolved, not merely recorded. The follow-up removed every actionable item:

- backend providers now live under `src/llm/adapters/`, split into contract, registry, llama.cpp,
  and DeepSeek modules;
- each backend adapter owns request adaptation and response-envelope extraction;
- frontend providers now live under `src/static/adapters/`; their cards, fields, secrets, forced
  values, parsing, and serialization are declarative adapter responsibilities;
- the browser entrypoint uses ES modules with explicit imports; setup, runtime config, API, and
  application behavior no longer communicate through shared application globals;
- `RuntimeState` moves Runner/config/client ownership from mutable module globals to FastAPI
  application state and retains the transactional config swap;
- session state/history reads, prompt previews, suggestions, turns, fork, delete, undo,
  compaction, and restore share one per-session transaction lock;
- deletion waits for active work and removes the session, debug log, and all backups together;
- preset mutation uses real per-name locks; debug append/read is separately locked;
- session, preset, and debug lock registries use weak references instead of unbounded identity
  accumulation;
- built-in presets moved from mutable `.data/defaults` to versioned `src/defaults` assets;
- built-in presets, user presets, API requests, browser state, and Runner now use only the nested
  `mind`/`body` character representation;
- the flat preset branch, personality migration fields, literal default ordering, dead frontend
  constants, duplicate `app.js2`, and runtime copies of built-in presets were removed rather than
  migrated;
- the JSON Schema validator moved to `src/llm/schema.py`, implements its declared subset, and
  rejects every unknown type, keyword, or malformed constraint;
- debug persistence moved to `src/llm/debug_log.py`, reducing `src/llm/client.py` to shared HTTP,
  output policy, parsing, and retry behavior.

The only explicit architectural boundary left is intentional: runtime coordination is
single-process. Multi-worker Uvicorn would require inter-process locking and shared runtime
configuration and is not a supported deployment mode. This is a declared deployment constraint,
not an untracked remediation item.

Final evidence:

- Ruff lint and format checks passed;
- MyPy passed for 26 Python source files;
- 137 Pytest cases passed, including lock blocking, concurrent preset writes, adapter envelope
  extraction, unsupported schema rejection, canonical preset shape, and frontend module structure;
- every frontend module passed Node syntax checks and the adapter registry loaded both providers;
- isolated HTTP smoke test passed built-in load, canonical preset save/read, session start/state,
  fork, session deletion, and preset deletion;
- no test server remained active and repository `.data` was not used.
