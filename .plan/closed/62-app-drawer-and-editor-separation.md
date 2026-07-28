# Task 62 — App drawer and 1.0 content ownership

> **Status:** completed 2026-07-27. Rewritten after owner review and
> `.plan/closed/62-explore-adventure-scenario-character-model.md`. The earlier frontend-only split encoded
> the wrong product model and is superseded completely.

## Product model

There are three layers:

1. **Character library** — reusable source records (the existing internal preset contract) with canonical `mind`/`body`, avatar, revision,
   and immutable built-in or mutable user ownership.
2. **Scenario library** — reusable world/directive/scene records whose ordered cast contains only
   references to character records. A scenario never embeds character definitions.
3. **Session** — an independent runtime snapshot materialized from one scenario. Editing the
   session does not mutate either source library. Explicit save-to-source actions are the only
   reverse path.

This is forward-only. Existing `.data/presets`, `.data/scenarios`, setup localStorage, and sessions
may be discarded. There is no compatibility reader or migration.

## App ownership

- **Adventure:** state of the active session. It has no Start button. Administrative edits are
  revision-checked, session-locked, persisted, and isolated from source records.
- **Characters:** character library CRUD, avatar, converter drafts, and built-in viewing/copying.
- **Scenarios:** scenario library CRUD. Its cast picker links ordered character IDs from the
  character library and chooses the controlled character.
- **Settings:** application and server-owned engine configuration.
- **Sessions:** list/fork/delete plus the only New Adventure flow. New selects a scenario,
  previews its world and cast, then starts.
- **Plugins** and **Help:** existing independent surfaces.

The drawer is core-first: Adventure, Characters, Scenarios, Settings, Sessions, Plugins, Help,
then deterministic plugin entries.

## Canonical contracts

### Character record

```json
{
  "schema_version": 1,
  "preset_name": "thorn",
  "character": {"mind": {}, "body": {}},
  "avatar": null,
  "revision": 1,
  "created_at": "...",
  "updated_at": "..."
}
```

Built-ins live in `src/characters/`; mutable records retain the existing `.data/presets/` store. User records
shadow no built-in ID. Mutation uses optimistic revision and explicit replace/delete.

### Scenario record

```json
{
  "narrator_directives": "",
  "scene": {
    "location": "...",
    "time_of_day": "...",
    "present_characters": ["C1", "C2", "Player"],
    "physical_facts": {}
  },
  "character_preset_ids": {"C1": "thorn", "C2": "lyra"},
  "controlled_character_id": "C1"
}
```

Built-ins remain immutable under `src/scenarios/`; mutable records live in `.data/scenarios/`.
Every reference is validated before saving through the editor and again before session
materialization. Character definitions are resolved only when materializing a session or preview.

### Session

`POST /session/start` accepts the existing `scenario_name` and materializes full characters plus
the existing `character_preset_ids`. `GameState` persists `scenario_source_id` and character source identities.
The session schema advances forward-only. No source revision is live-linked after materialization.

An administrative session update accepts the editable snapshot plus `expected_revision`. It runs
under the session lock, validates stable character IDs and controlled character, increments the
revision, saves atomically, and logs the operation. It does not write source libraries.

## UI requirements

- Four-column mobile drawer with 44 px targets and existing sheet/safe-area/focus behavior.
- Character library uses product language; “preset” is not exposed to users.
- Scenario editor makes linked cast visible and selectable from the character library.
- Adventure clearly says changes affect only the current session and exposes explicit
  save-character/save-scenario source actions.
- Sessions → New is a scenario picker with cast preview and Start.
- Empty state with no active session routes to Sessions.
- Character Converter opens a character-library draft and never auto-saves.
- Draft/state values survive Back/Close without hidden writes.

## Public plugin launcher

Keep the strict `sdk.registerAppEntry({name,title,icon}, handler)` contract already developed:
strict keys, kebab-case plugin-local name, both locales, bounded text icon, safe `textContent`,
core-first deterministic order, activation cleanup, and handler failure containment. Settings and
slash actions do not create tiles.

## Acceptance

- Defaults contain no embedded `characters`; every reference resolves.
- Character CRUD covers conflict, stale write, delete, and immutable built-in behavior; scenario
  CRUD and session materialization cover missing character references.
- Starting from each built-in scenario materializes the same canonical character and scene data as
  its former embedded form.
- Active edits are revision-checked, locked, persisted, logged, and source-isolated.
- Playwright at 320, 360, 393×852 and 1280×800 traverses every destination, creates a character,
  links it into a scenario, starts from Sessions, edits the active snapshot, and observes zero
  console errors or failed requests.
- Core dark and Creme use the same UI without theme-specific patches.
- Node parses/imports all frontend modules; HTML, registries, and service worker validate.
- Ruff, format-check for touched Python, mypy, and `pytest -x` pass.
- README and SDK/hub docs describe the shipped model; the task moves to `.plan/closed/`.

## Delivered verification

- Real Chrome/Playwright at 320, 360, 393×852, and 1280×800 for both core dark and Creme.
- Character creation, scenario linking, Sessions-only start, active snapshot editing, explicit
  scenario save, source isolation, controlled-character change, and every drawer destination.
- Four columns, no horizontal overflow, no undersized tiles, correct focus return, and zero
  console/network failures.
- `uvx ruff check .`, mypy, Node module parsing, JSON validation, and `pytest -x` pass.
- The repository-wide format check still reports pre-existing formatting drift in unrelated dirty
  Task 58 files; Task 62 did not rewrite those user-owned changes.
