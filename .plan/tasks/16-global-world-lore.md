# Task 16: Global World Lore

**Status:** Open — product definition expanded; implementation intentionally pending
**Delivery shape:** Curated hybrid plugin (`dev.alex-tavern.global-world-lore`)
**Depends on:** Task 07 for slash-command dispatch, discovery, autocomplete, and suggestions
**Related future work:** Task 06 may later provide semantic retrieval when lore volume justifies it

## 1. Product intent

Global World Lore is a plugin-owned memory for objective facts and ongoing events whose scope is
the wider world, not only the current scene. It gives the Narrator durable knowledge such as:

- “The northern kingdom destroyed the old coastal republic.”
- “The war continues beyond the mountains.”
- “Iron ships cannot cross the Glass Strait during winter.”
- “The imperial capital has prohibited unlicensed magic.”

Here, **global** describes narrative scope. It does not mean one mutable database shared by every
Alex Tavern session. Each roleplay/session owns its own world-lore state so different worlds never
leak into one another.

The plugin must not add `world_lore` to `GameState`, `Runner`, Character, or Scene. Runtime lore
lives under the plugin namespace in `GameState.plugin_state`; reusable templates live in
plugin-owned preset/config storage.

## 2. Ownership and knowledge boundary

### Narrator

The Narrator receives the active global lore as objective world context. It may:

- use a distant event when it becomes relevant to the current scene;
- narrate indirect consequences such as refugees, shortages, rumors, law changes, or travel risk;
- propose additions, changes, or removals as the world evolves;
- never change an entry marked `fixed`.

Lore is context, not an instruction to force a plot beat. The Narrator decides whether it is
currently relevant while continuing to respect player agency and the normal scene contract.

### Characters

The plugin does **not** inject the global lore directly into Character prompts. Doing so would turn
objective world state into universal character knowledge and violate knowledge isolation.
Characters learn it only through their own `mind.knowledge`, public narration/dialogue, or a future
explicit knowledge-granting mechanism.

### Runner and core

The Runner continues to own locks, revision, persistence, undo, compaction, and the authoritative
turn transaction. The plugin cannot write a session from a side route without the same session lock.

## 3. Canonical plugin state

Proposed version-1 state inside `game.plugin_state[plugin_id]`:

```json
{
  "schema_version": 1,
  "active_preset_id": "war-torn-continent",
  "entries": {
    "war.north-south": {
      "key": "Northern war",
      "value": "The war between Arven and Solkar continues along the mountain border.",
      "tags": ["war", "politics", "north"],
      "fixed": false,
      "source": "preset",
      "updated_turn": null
    }
  }
}
```

Contract rules:

- entry IDs are stable lowercase dotted/dashed identifiers and are never array positions;
- `key` is a short human-facing label;
- `value` is the objective fact/event supplied to the Narrator;
- `tags` are editable labels used by the UI, presets, and future retrieval;
- `fixed = true` blocks automated Narrator mutation, but an explicit human edit may still unlock or
  replace the entry;
- `source` records `preset`, `human`, or `narrator` provenance;
- `updated_turn` records the durable turn responsible for a Narrator mutation and is `null` for a
  preset or direct human edit;
- unknown fields and incompatible schema versions fail instead of receiving compatibility fallback.

`fixed` means narratively immutable until the human changes it. It is not the same as physical
scene state: locations, bodies, present characters, and immediate physical facts remain owned by
Scene/Narrator core contracts.

## 4. Narrator read/write flow

The target flow is one structured Narrator call, not a hidden second LLM request:

```text
session plugin_state
        │
        ▼
serialize active global lore within a token budget
        │
        ▼
augment Narrator context + structured optional lore operations
        │
        ▼
Narrator returns normal output and zero or more lore proposals
        │
        ▼
validate IDs, fields, fixed protection, and operation limits
        │
        ▼
apply proposals to the isolated turn draft at turn.before_commit
        │
        ▼
single atomic session save + normal revision/undo/plugin-state snapshot
```

Narrator operations should be explicit structured data:

```json
{
  "operations": [
    {
      "operation": "update",
      "entry_id": "war.north-south",
      "value": "A winter ceasefire now holds along the mountain border.",
      "tags": ["war", "politics", "north", "ceasefire"]
    }
  ]
}
```

Allowed operations are `add`, `update`, and `remove`. Validation rejects duplicate operations,
unknown entry IDs for update/remove, replacement of stable IDs, changes to fixed entries, oversized
values, invalid tags, and excessive operations in one turn. Rejected lore operations must not fail
the narrative turn; they are journaled with a reason and discarded from the draft.

### SDK gap to resolve before implementation

The current SDK exposes `narrator.call` as a full wrapper but does not yet provide a narrow way to
augment Narrator messages and extend its response schema with plugin-owned output. The task must not
solve this through `unsafe`, prompt-string patching, provider branches, or a second invisible model
call.

Before building the plugin, extend the machine-readable SDK with a provider-neutral Narrator
context/schema contribution contract. It must preserve the normal structured call, validation,
debug log, session ID, turn number, and agency rules. The exported MCP contract and hub docs must be
updated alongside that SDK change.

## 5. Prompt budget and retrieval

The first release targets a compact world ledger. It uses deterministic serialization and an
explicit token budget visible in plugin settings. It must never cut an entry by characters or
silently omit arbitrary fields.

If the active ledger exceeds the budget, the plugin reports the overflow in its UI and requires the
human to edit, remove, or move entries into another preset before the full set can be injected.
Semantic RAG is not required for version 1.

Task 06 may later add retrieval over a large lore library. If adopted, retrieval selects complete
entries with provenance and a token budget; it does not become a second authoritative memory and
does not replace the session’s plugin state.

## 6. `/global-lore` command and UI

`/global-lore` is an administrative/transient command. It opens the plugin panel and does not:

- become a roleplay turn;
- enter narrative history;
- call the Narrator;
- mutate state by itself.

The panel shows the complete ledger and supports:

- add, edit, and remove entries;
- edit `key`, `value`, and tags;
- toggle `fixed` with a clear explanation that fixed facts cannot be changed by the Narrator;
- filter/search by key and tag;
- show provenance and last updated turn;
- review a diff before applying destructive edits or loading a preset;
- surface the current prompt-budget usage and overflow;
- load, save, import, and export lore presets.

Every mutation is validated server-side and performed under the session lock with one revision.
Edits must participate in the project’s chosen undo/audit policy for stateful commands; that policy
is finalized by Task 07 rather than invented locally by this plugin.

### Slash-command dependency kept open

Task 07 is still designing the real command system. This plugin must register `/global-lore` through
the final `commands` contribution contract and must not add a one-off parser to `app.js`.

The final Task 07 contract should let this plugin declare enough metadata for the current input UI:

- command ID and literal `/global-lore`;
- localized title and description;
- transient/administrative classification;
- whether arguments are accepted (version 1 accepts none);
- autocomplete keywords;
- suggestion text and icon;
- availability rule: active session plus active plugin;
- handler result: open the contributed Global Lore panel.

Autocomplete and command suggestions remain deliberately open until Task 07 settles its parser,
keyboard behavior, mobile presentation, escaping, discovery, and dispatch API. This task consumes
that contract after it exists; it does not freeze a competing version.

## 7. Presets

Presets make it easy to move between roleplays without copying one world’s mutable state into
another.

- bundled presets are immutable templates shipped in the reviewed plugin package;
- user presets live in plugin-owned config/storage, not in source or the runtime hub snapshot;
- loading a preset copies validated entries into the selected session’s plugin state;
- save-as-preset copies the current ledger into a reusable template without linking future edits;
- replace versus merge is an explicit choice with a previewed diff;
- merge conflicts are resolved by stable entry ID and never silently overwrite;
- Experiences may select a bundled preset through plugin configuration, but the resulting session
  still owns its independent mutable copy.

Preset loading never switches provider, Character memory, Scene state, or unrelated plugin config.

## 8. Plugin shape and permissions

Expected package:

```text
plugins/global_world_lore/
├── plugin.toml
├── backend.py
├── frontend.js
├── presets/
│   └── war-torn-continent.json
└── tests/
```

Expected declared permissions:

- `session.state.write` for its namespaced session state;
- `config.read` / `config.write` for plugin settings and user presets;
- `frontend.dom.mount` for the panel.

It should not require `model.call`, `network`, or `unsafe` for the primary feature.

## 9. Explicit non-goals

- no new core `GameState.world_lore` field;
- no application-global mutable lore shared across unrelated sessions;
- no automatic Character knowledge injection;
- no regex/text parser for Narrator lore updates;
- no provider-specific prompt implementation;
- no hidden LLM call or unlogged autonomous background agent;
- no required RAG/indexer in the first release;
- no direct edits under `.data/plugins/hub`;
- no private slash-command implementation inside this plugin.

## 10. Implementation sequence

1. Finalize Task 07’s dispatcher, autocomplete/suggestion metadata, stateful-command transaction,
   and panel-opening result.
2. Add the narrow Narrator context/schema contribution to the core SDK and export it through the
   authoring MCP/docs.
3. Define strict lore state, operation, preset, and panel contracts with fixtures.
4. Scaffold the curated hybrid plugin through the hub MCP.
5. Implement read-only Narrator context injection and token-budget reporting.
6. Implement validated Narrator operations applied at `turn.before_commit`.
7. Implement `/global-lore`, panel CRUD, fixed toggle, provenance, and preset workflows.
8. Validate undo, compaction snapshots, concurrent UI/turn writes, replay/debug evidence, failure
   containment, frontend accessibility, mobile command discovery, and curated package review.

## 11. Acceptance criteria

- Two sessions can load different lore/presets without sharing mutable state.
- The Narrator receives active world facts while Character prompts receive none directly.
- A relevant global event can influence narration without forcing a scripted scene.
- Valid Narrator add/update/remove operations commit atomically with the turn.
- A Narrator attempt to mutate a fixed entry is rejected and journaled without failing the turn.
- Undo restores the exact previous namespaced lore snapshot.
- Compaction preserves current global lore and does not summarize it into another authority.
- `/global-lore` opens the panel through the shared command dispatcher.
- The command appears in autocomplete and suggestions using Task 07’s final metadata contract.
- UI edits use the session lock, advance one revision, and never race an active turn.
- Preset replace/merge shows a diff and never silently overwrites ID conflicts.
- Prompt budget is measured; overflow is visible and deterministic.
- Debug evidence identifies injected entry IDs and accepted/rejected lore operations without leaking
  secrets or private Character context.
- Plugin validation, tests, packing, curated review, HTTP/frontend boundaries, and the full core
  quality gates pass before the task can move to `.plan/closed/`.
