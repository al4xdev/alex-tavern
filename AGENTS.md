# Project guidelines for agents

> **New here? Read `.plan/guides/GUIDE.md` first** — it is the hour before this file:
> read order, what each `.plan/` folder means, the house method, and the three ways an
> agent has actually gone wrong in this repository. This file is the contract and it
> is long; the guide is how to enter it. **Where the two disagree, this file wins.**
>
> This is the tool-neutral contract. `CLAUDE.md` is a pointer to it and holds no rules
> of its own; if your tool loads a different file by default, make that one a pointer
> too rather than a second copy.

Alex Tavern is a state-driven multi-agent roleplay application. A Narrator governs the physical
world and routes the scene; Character agents speak and think with restricted context; the Runner
preserves human agency, persists every session and coordinates calls to LLM providers.

This file is the working contract for any agent modifying the repository. It describes the
architecture and the decisions in force. History, audits and completed implementations live in
`.plan/closed/`; active work lives in `.plan/tasks/`; future ideas with no active work in
`.plan/backlog/`; living architecture docs in `.plan/reference/`; items awaiting the owner in
`.plan/para-o-dono/`. The full map is in `.plan/README.md` (the monolithic `ROADMAP.md` was removed
on 2026-07-20: state lives distributed across those folders).

## 0. The hard rules, and what actually enforces them

This file is long. If you read nothing else, read this table. It lists the rules that
are not negotiable by measurement, argument or convenience — and, honestly, which of
them a failing test will catch for you and which of them only exist as prose.

**A rule enforced by a test is one you cannot break by accident. A rule that is prose
only is one you break by forgetting.** Treat the second group as the ones that need
your attention, not the first.

| rule | section | enforced by |
|---|---|---|
| No agent learns a human drives a character — no "Player", no named exclusion, no structural marker | §3 | `tests/test_prompt_operator_ontology.py`, `src/prompt_contract.py` |
| A private thought reaches the Director and nobody else | §3 | `tests/test_thought_containment.py` |
| Internal ids never reach a prompt or the prose | §3 | `tests/test_internal_ids_in_prompts.py` |
| The Director does not author persisted dialogue | §3 | `tests/test_audible_speech_{persistence,echo,deterministic_guards}.py` |
| A whisper or zone audience is never widened | §3 | `tests/test_zone_audibility_default.py`, `tests/test_whisper_ui.py` |
| Narration is projected per viewer | §3 | `tests/test_per_viewer_narration.py` |
| A new schema field means a new `SESSION_SCHEMA_VERSION`; no `.get(field, default)` | §2 | `tests/test_session_schema_version.py` |
| Tests never read, write or clean the real `.data/` | §3 | `tests/test_data_isolation.py` |
| **No AI authorship trailer in any commit, tag or PR** | §9.10 | ⚠ **prose only** — nothing will stop you |
| **Do not commit or push without explicit authorisation** | §9.9 | ⚠ **prose only** |
| **A claim about LLM behaviour is a hypothesis until a `curl` on a real payload confirms it** | §6 | ⚠ **prose only** |
| **A new finding goes to `.plan/backlog/`, not `.plan/tasks/`** | `.plan/README.md` | ⚠ **prose only** |
| **Pre-register the decision rule before running the experiment** | §6 | ⚠ **prose only** |

The five prose-only rules are the ones this project has broken most often, and every
one of them was broken by an agent acting in good faith and in a hurry.

> [!IMPORTANT]
> **Basic execution rule for agents:**
> Before creating any new code or feature, you **must always check `.plan/tasks/`** for an existing spec or plan already under way, to avoid rework and keep the architecture consistent.
> The **`S`** prefix marks a **Supertask**: a planned structural, high-impact change. Completed supertasks, such as `S01-plugin-system.md`, live in `.plan/closed/`; the ones not yet started (e.g. `S02`) live in `.plan/backlog/` until the owner prioritises them.

## 1. Current view

The project is leaving its experimental phase and consolidating a small, explicit, adaptable
architecture:

- FastAPI backend and Runner independent of any LLM vendor;
- one backend adapter and one frontend adapter per provider;
- configuration and secrets belong to the server;
- state persisted as JSON with transactional locks and atomic writes;
- structured contracts between program and model;
- vanilla frontend in ES modules, no application globals;
- trusted in-process Python/JavaScript plugins, no sandbox, with an explicit SDK;
- Experiences as ordered compositions of plugins/configuration;
- observability, replay, MCP and playtests as tools outside the normal turn;
- the extensive documentation is part of the case study, not a problem to be reduced.

The goal is not to accumulate mechanisms. It is to keep boundaries clear so new features land in
the right owner, with tests and without widening coupling.

## 2. The forward-only rule

> **"Move, rather than build backwards compatibility and legacy. The project is very new and must
> not depend on yesterday."**

This is a new project. When a contract changes, every producer and consumer changes with it.

Do not create:

- converters or fallbacks for earlier formats;
- double reads of config, scenario, session or log;
- old fields kept "just in case";
- files duplicated between runtime and source;
- permanent branches for removed behaviour;
- wrappers that only preserve an abandoned internal API;
- alternative caches or storage that hide a contract divergence.

Incompatible local data may be discarded during development. If a change ever demands a real
migration, that has to be an explicit product decision, isolated and tested; it must never appear
incidentally inside the current parser.

Removing the previous format entirely is preferable to turning the code into a stack of
compatibility layers.

### Session versioning: move forward without fear

The mechanism that makes the forward-only rule safe in practice is `SESSION_SCHEMA_VERSION`
(`src/models.py`): every session persists the schema version it was written with. When the
`GameState`/`TurnRecord` schema changes in a way old sessions do not honour (a new field with
behavioural semantics, an altered visibility rule, ...):

1. **Bump `SESSION_SCHEMA_VERSION` and document the change in the history comment.**
2. Do not write a migration, a fallback or a double read — the backend refuses sessions of a
   different version (`IncompatibleSessionError` → HTTP 409 `incompatible_session`) and the
   frontend lists those sessions locked with the incompatible symbol, without allowing them open.
3. Old sessions stay on disk (the user can delete them), but are never opened by an incompatible
   build — there is no risk of a corrupted conversation.

Consequence for agents: **do not hold back a core improvement out of fear of breaking existing
sessions.** Breaking session compatibility is cheap and planned for; just bump the version. The
real cost is in carrying compatibility shims, never in invalidating sessions.

**New field = new version. No "additive" exception.** There is no such thing as a "purely additive
field that can skip the bump": if `dict_to_game_state` (or any `dict_to_*`) needs
`.get(field, default)` to read a session, that default is a migration in disguise and it will
survive forever. Every field of the current schema is read by direct access (`data["field"]`) and a
`KeyError` means a corrupted file, not an old version — the loader already refused any different
version before reaching that point. Reading a field with a default is only legitimate when the
value is optional *in the current schema* (the `roteiro`, which is `None` with the feature off).

### Budgets: what this project treats as cheap

The forward-only rule says what we are willing to **break**. This one says what we are willing to
**spend**, and it exists for the same reason: new agents arrive saving the wrong resource and
asking permission to spend the right one.

**Three resources are cheap here. Do not protect them, do not ask for authorisation, and do not
propose a worse design to save them.**

1. **Backwards compatibility** — §2 above. Bump the schema version and move on.
2. **Token cost.** An extra call that improves the fiction is a call to be made. Do not budget in
   cents, do not pick a worse model on price, and do not write "that would be expensive" as an
   argument against a correct design. Prompt caching already carries most of it
   (`docs/cases/06`, `docs/cases/10`).
3. **Latency.** This is the most counter-intuitive and the most important:

> **"Latency is not a problem. If it takes 10 minutes and we land on good quality, that is a matter
> of time — the models improve every quarter and that is in our favour."**

Engineering spent making the engine fast is invested in an asset that depreciates on its own every
quarter. Engineering spent on the fiction does not depreciate. So the turn may be slow if the
slowness buys quality: more agent calls, real character routing, per-viewer projection, validation
that actually validates. The UX bill for this stance is paid in the interface — a captain's log, a
loading screen with content (`.plan/backlog/73-...`) — never by cutting quality.

**What stays expensive, and what this does NOT authorise:**

- **Unmeasured serial latency.** Spending latency is allowed; spending it without counting is not.
  Independent calls go in `asyncio.gather` — if they are independent and they are serial, that is a
  defect, not a budget choice. The real risk of this stance is not the user waiting: it is the
  engine accumulating serial waits nobody measured, and staying slow once the models get ten times
  faster.
- **Complexity and coupling.** Still expensive. One more call is cheap; one more subsystem to
  justify it is not.
- **A worse answer.** Nothing here authorises cutting quality to gain time — the whole vector of
  this rule points the other way.

## 3. Domain invariants

### Agency and immersion

The human controls a character in the world. The LLMs are never given the existence of a "Player",
a user or an external operator.

- `Player.controlled_character_id` is the Runner's knowledge, not the agents';
- internal records with `speaker="Player"` are rendered with the character's name before reaching
  any prompt;
- when the Narrator picks the controlled character as next speaker, the Runner hands control back
  to the human and does not generate their speech;
- there is no separate name, persona or prompt for the player;
- no new call may bypass that agency lock;
- **a structural marker is leakage too.** A prompt that formats the controlled character
  differently from all the others identifies them without naming anything — and that violates this
  section exactly as the word "player" would. A label, an ordering, an extra field, a named
  exclusion: if the formatting rule separates out exactly one character, it encodes
  `controlled_character_id` into the text. Found twice on 2026-07-27: the Director's routing
  constraint (fixed in `5002f11`) and the drive/watcher context, which rendered the controlled
  character by name and the rest by ID in the same list (task 58).

> **Why this is not negotiable by measurement.** Both fixes above have a recorded A/B, and that is
> good — but the A/B measures *what it costs*, never *whether it ships*. An invariant that accepts
> being failed by a quality metric is not an invariant. The practical rule: when a finding falls
> under this section, the experiment decides the shape of the fix, not its existence.
> `src/prompt_contract.py` covers the lexical part (`operator_ontology_hits`) and the structural
> part (`singled_out_speakers`); neither replaces reading the prompt the server actually sent.

### Role responsibilities

| Role | Responsibility | Context allowed |
|---|---|---|
| Narrator | Physical world, consequence, transition, scene, mood and next speaker | Scene, all characters, `mind`, `body`, summary and active window |
| Character | Only first-person speech and subjective thought | Their own `mind`, their own note, the Narrator's context, public speech and their own thoughts |
| Runner | Agency, call ordering, state, locks, persistence and routing | The application's full state, never heuristic narrative decisions |
| Historian | Compact old events without crossing private boundaries | The world summary receives public events; each private memory receives public events, its own note and its own thoughts |

A Character neither performs nor describes physical action. A thought about another person is
subjective interpretation, not objective description. `body`, the scene, historical narration,
someone else's personality and other characters' notes never enter a Character prompt.

### Canonical state

- A character uses a single shape: `{"mind": {...}, "body": {...}}`.
- Personality uses only `personality`.
- The scene uses reserved fields (`location`, `time_of_day`, `present_characters`) and
  `physical_facts` for free-form facts.
- Immutable built-in scenarios live in `src/scenarios/`.
- Config, user scenarios, sessions, backups and logs live exclusively in `.data/` or in the
  deployment's `ROLEPLAY_DATA_DIR`.
- Each session lives in `.data/sessions/{id}/`, with `state.json`, `debug.jsonl` and `backups/`.
- Plugin cache, physical activation, config, environment and journal live in `.data/plugins/`.
- `.data/` is never tracked by Git nor reused by CI/CD.

## 4. Architecture and ownership

```text
Frontend ES modules
    ├── api.js
    ├── setup.js
    ├── runtime-config.js
    ├── plugin-runtime.js / plugin-center.js
    └── adapters/<provider>.js
                 │ HTTP
                 ▼
FastAPI ── RuntimeState ── PluginRuntime ── Runner ── role agents
                                  │
                                  ▼
                         shared LLM client
                          ├── adapters/<provider>.py
                          ├── schema.py
                          └── debug_log.py
```

### Runner and concurrency

`src/runner.py` does not hold `GameState` on `self`. Every operation resolves the session by ID.

Turns, suggestions, snapshots, history, preview, fork, delete, undo, compaction and restore share
the same per-session lock. Do not introduce an endpoint that reads or changes a session outside
that transactional boundary.

- a critical save uses a temp file, flush, `fsync` and rename;
- delete waits for active operations and removes state, log and backups together;
- scenarios have a per-name lock;
- the debug JSONL has its own lock for append and read;
- lock registries use weak references;
- the current locks are process-local: the supported deployment uses a single Uvicorn process.

`RuntimeState`, owned by FastAPI, gathers persisted config, resolved config, the HTTP client and
the active Runner. Switching provider persists and replaces the Runner under the same lock. Do not
recreate parallel mutable globals.

### Plugins and Experiences

Plugins are trusted in-process code and may replace core behaviour. There is no sandbox and no
permission gate: `permissions` documents access for review and the journal. The `unsafe` escape is
deliberate. The curated repository provides trust through full source review and a pinned SHA-256;
a third-party ZIP is the responsibility of whoever installs it.

- `plugin.toml` is strict/forward-only and uses `schema_version = 1`;
- installed packages are immutable by `id/version/hash`;
- files in `.data/plugins/started/` are the active global set;
- dependencies use semver constraints and the exact environment is rebuilt with uv;
- ordering is a deterministic DAG, and the order declared by the Experience becomes default edges;
- pre-commit filters receive isolated drafts; a failure discards the draft and disables the plugin
  at boot;
- post-commit actions never redo work already persisted;
- the `narrator.call` and `character.call` wrappers may replace the whole operation;
- the supervisor must be Uvicorn's real parent in order to swap the Python process.

The SDK and the machine-readable contracts live in `src/plugins/`. Examples and the authoring CLI
live in `plugins/examples/` and `tools/plugin_author.py`. The curated hub/MCP is a separate
repository; the MCP has no Git or publishing tools.

### The hub workspace, for agents

When a task involves creating, reviewing, testing or publishing a curated plugin, the agent working
in the main repository must work across both repositories, without copying the SDK and without
turning the runtime snapshot into source:

1. Use `src/plugins/`, `src/static/plugin-runtime.js` and `tools/plugin_author.py` from this
   checkout as the source of truth for the core and its extension points.
2. Look first for the sibling checkout `../alex-tavern-plugins`. If it does not exist, request the
   Git authorisation the environment requires and create a partial clone:

   ```fish
   git clone --filter=blob:none --sparse \
     git@github.com:al4xdev/alex-tavern-plugins.git \
     ../alex-tavern-plugins
   git -C ../alex-tavern-plugins sparse-checkout set docs plugins experiences
   ```

   Sparse mode includes the root files, the MCP, the tools and the three declared folders, but does
   not materialise the blobs in `artifacts/` or `assets/`. Do not replace that flow with a full
   clone just to read documentation or write source.
3. Inside the hub, read `AGENTS.md`, `docs/manifest.md`, `docs/sdk.md`, `docs/hooks.md` and
   `docs/mcp.md` before selecting hooks. For plugins with LLM calls, also read
   `docs/model-calls.md`. The contract exported by the current core beats any old example.
4. Configure the hub's MCP with the hub as working directory and the main checkout as
   `--core-root`. In a fish terminal, the equivalent form is:

   ```fish
   set core_root (pwd)
   cd ../alex-tavern-plugins
   uv sync
   uv run python mcp_server.py --core-root "$core_root"
   ```

   Use the MCP tools `plugin_contract`, `plugin_scaffold`, `plugin_validate`, `plugin_test`,
   `plugin_pack` and `plugin_trace`; do not hand-replicate contracts the SDK already exports.
5. Plugin source belongs in `../alex-tavern-plugins/plugins/`. To review or regenerate published
   media and packages, ask for authorisation to expand the sparse checkout before touching those
   paths:

   ```fish
   git -C ../alex-tavern-plugins sparse-checkout add artifacts assets
   ```

6. Never edit `.data/plugins/hub`: it is an ephemeral, validated, replaceable snapshot used by the
   application. Do not `pull`, commit, push, change a remote or publish in the sibling repository
   without explicit and specific Git authorisation.

### Providers

Built-in adapters live in `src/llm/adapters/`; additional providers should preferably be plugins
registering the same `ProviderAdapter` during boot. Each adapter has:

- identity and defaults;
- secret fields and activation requirements;
- forced settings;
- URL and authentication;
- request adaptation;
- response envelope extraction.

The shared client owns HTTP, timeout, retry, text policy and parsing. Local validation belongs to
`src/llm/schema.py`; observability persistence belongs to `src/llm/debug_log.py`. Vendor
differences do not enter the Runner or the agents.

Built-in frontend adapters live in `src/static/adapters/`; plugins register the same contract
through the browser SDK before `RuntimeConfig.init`. Each declares its card, fields, secret, forced
settings, parsing and serialisation. `index.html` contains containers only; do not add a hardcoded
per-provider form or provider branches in `runtime-config.js`.

Adding a provider requires both adapters plus tests for config, redaction, request, response and
UI. The extensible backend registry is the source of truth for the server contract; the UI refuses
divergent catalogues at runtime.

### Structured contracts

Narrator, Character, suggestions and Historian use JSON. Llama.cpp receives a native JSON Schema.
DeepSeek V4 Flash receives `json_object`, the technical schema instruction added by the adapter,
and local validation afterwards. That is capability adaptation, not a provider-specific narrative
prompt.

`src/llm/schema.py` implements an explicit subset. An unsupported type, keyword or constraint must
fail before the response is accepted. Never silently ignore part of a schema, and never replace a
structured contract with a regex parser.

### Configuration and secrets

`.data/config.json` is the only runtime configuration. It holds the common config, the active
provider and one complete object per provider.

- `GET /config` returns a redacted representation only;
- a blank secret on PUT preserves the stored value;
- a key never enters localStorage, the service worker cache, a log or a CLI argument;
- `/config` is network-only;
- deployments create their own config; they do not copy the development config.

## 5. The flow of a turn

1. The Runner acquires the session lock and loads the state.
2. `turn.input` may transform a draft of the input.
3. Human speech, private thought and action are persisted separately under a single `turn_number`.
4. The Narrator receives the canonical state and returns validated JSON; wrappers/filters may
   replace the call/output.
5. The Runner applies `force_speaker` when requested and preserves the controlled character's
   agency.
6. If needed, the Character receives only its permitted context and generates structured
   `speech`/`thought`.
7. The Runner applies `scene_update` and `mood_updates` and runs `turn.before_commit` on an
   isolated draft.
8. State is saved atomically, the revision advances once and `turn.after_commit` is emitted.

All records of the step share `turn_number`, `scene_snapshot`, `mood_snapshot` and
`plugin_state_snapshot`. Undo removes the whole step and restores those snapshots.

Any new model call must propagate `session_id`, `turn_number` and `agent` to the log. There are no
invisible LLM calls.

## 6. Prompts and context

Prompts are shared across providers and describe role rules declaratively.

> **The curl-first rule (do not guess — test first).** Every claim about LLM behaviour (a prompt, a
> contract, a schema, a confidentiality boundary, "this will leak / improve / collide") is a
> hypothesis until a `curl` against a REAL payload confirms it. Do not decide by hypothesis and do
> not write "probably X"; isolate the call, replay it via `curl` (method below), count the rate
> over 3-4 runs and decide with the number. Pre-register the decision rule BEFORE running (e.g.
> "if 4b ≈ 4a → I keep it"), so the goalposts cannot move afterwards. It is cheap: one flash-model
> call per variant. Guessing wrong costs far more.

- do not create a special narrative prompt for one vendor;
- do not repeat the same rule across several layers;
- do not introduce macros, depth injection or a text parser;
- do not cap narration by a fixed number of sentences;
- keep attributed facts as claims until the Narrator confirms them;
- immediate consequence comes before sensory expansion;
- mood is persistent state and changes only on a real change;
- generated text uses no em dash/en dash; normalisation is global, in the client;
- history is bounded by a token budget, never by cutting characters.

### Debugging a defect that looks like a prompt problem (isolated replay before the battery)

When an agent's output repeats or breaks in a real scene, do NOT iterate by running the whole A/B
battery (slow and expensive). Isolate the faulty call and fix it first, then validate on the
battery:

1. Take the REAL payload of the bad call from `<data>/sessions/<sid>/debug.jsonl` (the agent's
   record has that turn's exact `request.messages`).
2. Replay via `curl` against the provider, varying ONLY the prompt. For deepseek:
   `POST {api_base}/chat/completions`, `Authorization: Bearer <key>`, body
   `{"model","messages","response_format":{"type":"json_object"},"thinking":{"type":"disabled"}}`
   (the adapter already embeds the schema in the system message). Run it 3-4x per variant — the
   output is stochastic; count the defect rate, not a single case.
3. Iterate the prompt until the isolated call comes out clean; ONLY then run the battery.
   **The validated variant has to be the shipped variant**: the final replay must use the
   production BUILDER (or mirror exactly the position/order of the text in the final prompt —
   including long scenario directives that come afterwards). Measured lesson (2026-07-18, task 41):
   rules validated at the END of the prompt worked 3/3; the same rules implemented in the MIDDLE,
   buried under 5k chars of directives, failed 3/3. Position is part of the variant.
4. A rule this technique has already proved (2026-07-17, the raffle loop in turma-dos-portais): if
   an instruction in the CHARACTER prompt does not fix the isolated call — not even an explicit ban
   on the topic — the defect is NOT a prompt defect; the cause is upstream (a scene stagnant on the
   same topic). Confirm it by varying the INPUT instead of the prompt: injecting a new scene event
   into the context broke the loop 2/3 without touching the prompt, while the hard ban broke it
   0/3. In that case the lever is the Director/roteiro moving the scene on, not the agent's prompt
   — do not add a prompt rule the evidence has shown does not work.

Compaction is a transactional event: it prepares summaries in an isolated draft, writes a numbered
incremental checkpoint, keeps the recent window and updates `story_summary`/`character_notes`.
Automatic compaction is opt-in, uses the full prompt estimate before the Narrator, and runs under
the same turn lock. Undoing a compaction is LIFO, may cross several checkpoints and preserves later
turns; a conflict in plugin state must be resolved by the plugin itself. Immutable checkpoints
remain until the session is deleted. RAG, if implemented, will be semantic retrieval over an
external volume and not a second memory system for facts already present in the session.

## 7. Observability and tooling

`.data/sessions/{id}/debug.jsonl` is the primary evidence of execution. It records:

- `turn_input` before the first call;
- the redacted request, the response, the attempt, the duration and the prompt size;
- error type and representation;
- undo, compaction and restore markers.

The log is append-only. Undo does not erase evidence.

Tools in `tools/` sit outside the narrative runtime:

- `replay_llm.py`: a deterministic server compatible with the LLM API;
- `replay_session.py`: replays current inputs against the real API;
- `mcp_server.py`: debug inspection and mutations over stdio;
- `playtest_harness.py`: repeatable scenarios, a queue and A/B comparisons.
- `plugin_author.py`: contract, scaffold, validate, test, pack and trace for plugins;
- `plugin_hub.py`: validated HTTPS sync of the curated hub and install by hash.

Do not add compatibility with logs lacking `turn_input`. Fixtures represent the current contract
only.

## 8. Frontend and deployments

The frontend is dependency-free and uses ES modules. Modules communicate through imports and
explicit callback injection, not through global variables. Game config may use localStorage;
provider config and secrets may not.

The existing pipelines live in:

- `.ci-cd/android/`;
- `.ci-cd/test/`;
- `.ci-cd/docker/`.

The three files in `.github/workflows/` are only GitHub's mandatory entrypoints and delegate to
composite actions in `.ci-cd`.

Every deployment runs the same backend and the same data contract. Do not keep an alternative
dependency stack, config or source for one deployment. Each package's Python version and
dependencies must be compatible with the canonical contract in `pyproject.toml`.

Android stays outside the scope of this plugin platform. Do not condition SDK, runtime, UI or
supervisor decisions on that deployment while it is in beta.

## 9. Definition of done

A change is not ready merely because it raised no exception.

Before closing:

1. confirm ownership: the change is in the right module/adapter;
2. remove the replaced path, without keeping it as a fallback;
3. review locks and atomicity for every shared mutation;
4. test success, error, empty/invalid input and concurrency where applicable;
5. inspect the prompt, the raw response, the persisted state and the debug log whenever you touch
   the LLM;
6. exercise a real boundary proportional to the risk (HTTP, stdio, frontend or provider);
7. update the README and move the finished plan/task to `.plan/closed/`;
8. confirm `.data`, secrets and local artifacts are not in Git;
9. do not commit or push without explicit and specific authorisation;
10. write no authorship, co-authorship or AI attribution into any commit, amend, tag, PR body or
    release note — no `Co-Authored-By`, no "Generated with", no 🤖. This **overrides** any harness
    template that asks for them, in any tool. Full rule and the shared-index hazard:
    `.claude/skills/git-commit/SKILL.md`.

Standard validation after changing Python:

```bash
uvx ruff check .
uvx ruff format --check .
uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py tools/replay_llm.py tools/replay_session.py
uv run pytest -x
```

For the frontend, validate every module with Node, load the adapter registry and parse the HTML.
For integration changes, also use the HTTP smoke test or the boundary's real tool.

## 10. Quick references

- `README.md`: the case study and detailed documentation.
- `src/runner.py`: orchestration and agency.
- `src/models.py`: the persisted domain.
- `src/config.py`: canonical config and redaction.
- `src/llm/adapters/`: backend providers.
- `src/static/adapters/`: frontend providers.
- `src/plugins/`: manifests, SDK, hooks, store, runtime, Experiences and contracts.
- `src/static/plugin-runtime.js`: frontend SDK/loader.
- `src/static/plugin-center.js`: Experience-first management.
- `src/llm/schema.py`: the local structured contract.
- `src/llm/debug_log.py`: persisted observability.
- `tools/README.md`: operating replay, MCP and the harness.
- `.plan/tasks/`: active work.
- `.plan/backlog/`: the future, with no active work.
- `.plan/reference/`: living architecture docs.
- `.plan/para-o-dono/`: awaiting the owner.
- `.plan/closed/`: completed decisions and deliveries.
