# Explore: slash command experience

**Date**: 2026-07-15
**Scope**: Task 20, current slash frontend/backend contracts, local runtime state, open S02 overlap, and every source plugin in the sibling curated hub.

## Findings

### Task 20 follows the first command implementation

- Task 07 shipped the current session-bound plugin command registry and was closed on 2026-07-14.
- Task 20 was added later the same day and explicitly asks for a redesigned slash experience, contextual actions, autocomplete metadata, contextual suggestions, and migration of every public plugin (`.plan/tasks/20-slash-command-experience.md:1`).
- S02 independently records that the current contract cannot represent a global action such as `/chat`, because execution requires a session (`.plan/tasks/S02-agentic-configuration-command-center.md:281`, `.plan/tasks/S02-agentic-configuration-command-center.md:552`).

### The observed missing autocomplete is an empty-catalog experience

- The only locally installed and active plugin is `dev.alex-tavern.dynamic-character-presence`; it registers no command. The Character Converter was previously uninstalled according to `.data/plugins/events.jsonl`.
- `SlashCommands.refresh()` loads only `GET /commands`, whose contents are commands registered by active backend plugins (`src/static/slash-commands.js:250`).
- With an empty catalog, typing `/` produces an empty match list and the suggestion surface is hidden (`src/static/slash-commands.js:47`, `src/static/slash-command-parser.js:9`). There is no empty-state or link to the Plugin Center.
- With a non-empty catalog, matching is a case-normalized prefix comparison against the canonical command name only (`src/static/slash-command-parser.js:9`).
- An unknown command is blocked on send and shown in the panel/toast, but the message only mentions suggestions and `//`; it does not expose available commands or the Plugin Center (`src/static/slash-commands.js:183`, `src/static/i18n.js:340`).
- The catalog is refreshed at application initialization and locale changes. `PluginCenter` does not call `SlashCommands.refresh()` directly; ordinary activation paths currently reload the page.

### Slash mode has no pre-resolution visual state

- The `command-mode` class is added only after a canonical command name resolves exactly (`src/static/slash-commands.js:96`).
- While the user is typing a slash query, the speech input retains the same text, color, border behavior, and surrounding Speech/Thought/Action layout as ordinary dialogue.
- The source control is an `<input type="text">`; it cannot style only the slash token or command substring without a different rendering technique. Whole-control and wrapper state can be styled with the existing structure.

### Descriptor information is validated but not rendered

- The backend requires `usage`, localized argument labels, and localized argument hints (`src/plugins/commands.py:47`).
- The suggestion list renders only canonical name and summary (`src/static/slash-commands.js:47`).
- The active command card renders only `fields`; it never renders `usage` or `arguments` (`src/static/slash-commands.js:96`).
- Positional arguments are recovered later by splitting the remainder of the speech input on whitespace (`src/static/slash-commands.js:203`). There is no quoting or escaping model.
- Backend field errors carry a `field` identifier, but the frontend reduces the response to one message and does not focus or annotate the named argument/field (`src/static/slash-commands.js:176`).

### Character Converter exposes the descriptor/UI mismatch

- `/convert-character` requires positional `preset-name`, plus exactly one of a source textarea or source file.
- Selecting the command opens the textarea and file controls but does not show the required preset name, its validation hint, or `/convert-character <preset-name>` usage.
- The converter creates a global preset draft but the current command and model-call contracts require an already-open session. The frontend rejects it before execution when no session exists (`src/static/slash-commands.js:198`).
- The command result is handled through a Character Converter-specific callback and a hardcoded `character_preset_draft` branch in the shared slash module (`src/static/slash-commands.js:21`, `src/static/slash-commands.js:230`). Other result kinds have no generic presentation path.

### The current catalog cannot express discovery or availability

- The strict command descriptor accepts only `name`, `summary`, `usage`, `arguments`, `fields`, and `result_kind` (`src/plugins/commands.py:47`).
- It has no aliases, localized search terms, category, icon, owner display name, scope, current availability, disabled reason, ranking, contextual relevance, or launcher target.
- Public entries add plugin ID and version, but not the plugin's human-facing name (`src/plugins/commands.py:176`).
- The browser SDK exposes hooks and DOM mounting, but no application-action, contextual-action, command-discovery, focus-target, route, or workspace registration (`src/static/plugin-runtime.js:17`).

### Core already has useful actions outside the command registry

- Global shell actions exist for Help, Plugin Center, Settings/setup, Sessions, and New Session.
- Session actions exist for suggest, narrator hint, undo, skip, compaction, restore compaction, debug, and presence management.
- These actions have different ownership and effects: some only open frontend surfaces, some call locked session endpoints, some start a narrative turn, and some invoke a model.
- The current command registry represents only session-bound plugin utilities that receive an isolated `GameState` and cannot advance narrative history. It does not represent the existing shell/session action set.

### Public plugin review

| Plugin | Current interaction | Slash-relevant fact |
|---|---|---|
| Character Converter | Backend command returning an editable preset draft | It is the only published executable slash command; it exposes hidden positional arguments, a hardcoded result path, and a session requirement despite operating on global preset data. |
| Dynamic Character Presence | Setup toggle, session tool panel, generic plugin setting, Narrator schema/context/result filters | Its existing human interaction is a contextual panel. The browser SDK has no public action that can declare and focus that mounted panel. |
| Grammar Tools | Automatic `turn.input` filter | It has no direct user operation or setting and does not inherently require a slash command. Its active/passive status is not visible in the slash surface. |
| OpenRouter Provider | Backend/frontend provider adapter rendered in configuration | It is application configuration, not a session utility. The current slash command contract cannot open or target provider configuration. |

### Test coverage confirms parser mechanics, not the complete experience

- The frontend test verifies prefix matching, exact resolution, unknown-command null resolution, and `//` escaping (`tests/test_frontend_architecture.py:64`).
- There is no DOM-level test for an empty catalog, no-match state, slash-mode styling, descriptor argument rendering, usage rendering, field-focused errors, plugin provenance, contextual availability, or mobile selection.
- The backend tests cover command validation, locking, non-mutation, and logs; those guarantees are separate from discovery UX.

## Open Questions

- What vocabulary distinguishes executable plugin tools, global application actions, session actions, contextual panel launchers, and future workspaces?
- Which built-in shell/session actions belong in the slash catalogue, and which should remain visible only in their existing controls?
- Does a slash palette operate before a session exists, and how does it expose disabled session-only items?
- Is localized discovery based on aliases, keywords, display titles, fuzzy ranking, or a constrained combination?
- Are positional arguments still part of the product UX, or are all descriptor inputs rendered as typed controls?
- What generic result/lifecycle contract replaces the Character Converter-specific result branch?
- How do plugins refer to a panel/workspace target without DOM reach-through or a plugin-ID branch in shared frontend code?
- How are empty catalog, no matches, catalog load failure, plugin disabled, and command unavailable represented as distinct user states?
- How should Task 20's application-action work be bounded so it remains compatible with, but does not prematurely implement, S02's full workspace/agent SDK?
