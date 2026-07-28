# Explore: adventure, scenario, and character ownership

> Completed exploration supporting Task 62.

**Date**: 2026-07-27
**Scope**: Current persistence, API, runtime state, frontend flows, and the in-progress Task 62 UI split.

## Findings

### The current product has four different objects behind three labels

```text
Character preset (.data/presets)
    └── one reusable character definition + optional avatar + revision

Scenario (src/scenarios or .data/scenarios)
    └── complete start-session configuration
        ├── copied character definitions
        ├── optional character_preset_ids
        ├── controlled character
        ├── scene
        └── narrator directives

Setup draft (localStorage rpt_setup_v2)
    └── another complete start-session configuration

Session (.data/sessions/<id>/state.json)
    └── independent runtime copy of characters, scene, directives, history, and other state
```

- Native character presets are the only current character database. Each record contains a
  canonical `mind`/`body` character, optional avatar, optimistic revision, and timestamps
  (`src/store/presets.py`; `src/main.py:763-824`).
- A scenario is not currently a world-only object. The HTTP shape reuses
  `StartSessionRequest`, which accepts complete characters, scene, directives, controlled
  character, scenario name, and character-to-preset mapping (`src/main.py:287-293`,
  `src/main.py:869-874`).
- Every built-in scenario currently embeds all character definitions. None of the four built-ins
  has `character_preset_ids`.
- The setup draft also owns the complete characters and scene payload
  (`src/static/setup.js:274-310`).
- The active session owns another full copy in `GameState`
  (`src/models.py:367-384`).

### The existing “link” is identity metadata, not source resolution

- `character_preset_ids` maps session-local IDs such as `C1` to preset names
  (`src/models.py:382-383`).
- Session creation validates that mapped presets exist, but it does not load character fields
  from them. Character definitions must already be supplied directly or embedded in the scenario
  (`src/runner.py:314-390`).
- The frontend uses the mapping to fetch current avatar URLs
  (`src/static/app.js:362-370`).
- Loading a scenario in setup copies its complete character definitions into cards, then
  separately hydrates any preset identities (`src/static/setup.js:313-339`).
- Saving a user scenario serializes the complete setup draft, including copied characters
  (`src/static/setup.js:698-712`).
- Therefore changing a character preset does not change a scenario's copied character fields or
  an active session's copied character fields. The avatar may change because it is fetched from
  the currently named preset.

### A reference-only scenario cannot start under the current backend

- `/session/start` resolves characters from the explicit request first, then from the scenario's
  embedded `characters` (`src/main.py:445-451`).
- It does not resolve `character_preset_ids` into character definitions.
- If a named scenario contained only character references, `main.py` would pass no character
  definitions to the Runner. The Runner would then try to borrow characters from the first
  built-in scenario (`src/runner.py:307-332`) and reject preset mappings whose local IDs do not
  match that borrowed cast (`src/runner.py:373-381`).

### “Adventure” currently edits a pre-session draft, not the active adventure

- In the in-progress Task 62 frontend, the Adventure entry opens the setup draft and exposes the
  Start button (`src/static/setup.js:735-782`).
- The actual active adventure is `GameState`, loaded with `GET /session/{id}/state`; the main
  transcript ingests its characters and scene (`src/static/app.js:326-349`).
- `GameState` does not persist the scenario name or scenario revision. It persists only
  `character_preset_ids` (`src/models.py:367-384`).
- Consequently the UI cannot currently identify which scenario source produced an active session.
- Sessions → New closes the session list and opens the Adventure setup editor
  (`src/static/sessions-modal.js:35-44`; `src/static/app.js:566-570`).

### Active-session editing has only one narrow mutation today

- The only administrative state editor is presence. It uses the session lock, checks the whole
  session revision, writes an explicit undo entry, increments revision, saves atomically, and
  logs the mutation (`src/runner.py:1905-1945`).
- There is no endpoint for editing active character definitions, narrator directives, controlled
  character, location, time, or physical facts.
- `Player.controlled_character_id` is documented as fixed in the session
  (`src/models.py:72-76`).
- Turn undo snapshots scene, moods, plugin state, perspectives, dispositions, narrative clock,
  and roteiro state. It does not snapshot whole character definitions.
- Adding or removing an active character also intersects presence, perspective ledgers,
  dispositions, roteiro actors, history identity, avatar mapping, and controlled-character
  validity.

### Saving an active edit back to a source is not represented

- Character preset writes already support explicit replacement and stale-revision conflict.
- An active session stores a preset name but not the preset revision from which the character was
  copied.
- User scenarios have no schema version, revision, timestamps, or conflict check. Saving is a
  last-write-wins atomic replacement.
- An active session stores neither scenario identity nor source revision.
- There is therefore no current contract for distinguishing “save only in this session” from
  “update the source scenario” or for detecting a stale scenario source.

### The in-progress Task 62 assumptions no longer match the clarified product model

- Task 62 currently declares the split frontend-only, keeps scenarios as complete payloads,
  places Start in Adventure, excludes active-session character mutation, and forbids session
  schema changes.
- The clarified model requires source references, active-session editing, source identity, and
  session creation from Sessions. Those needs cross persistence, API, Runner, session schema, and
  frontend boundaries.

## Open Questions

- Whether a scenario reference chooses an ordered cast with stable local IDs, or an unordered set
  from which session-local IDs are generated.
- Whether scenario records refer to mutable character heads by name or pin exact character
  revisions.
- Which active fields are administratively editable: existing character sheets only, or also
  add/remove, controlled character, directives, and all scene fields.
- How active administrative edits interact with turn undo and whether they need their own LIFO
  edit history like presence.
- Whether “save scenario” updates only world/directives and cast references, or can also overwrite
  the referenced character records.
- Whether built-in characters become immutable reusable character assets or are installed into
  the mutable character database on first use.
