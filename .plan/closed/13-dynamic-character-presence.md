# Task 13: Dynamic character presence

**Status:** Closed — implemented in two phases (core + curated plugin), verified
end-to-end (real backend + browser), full quality gates in both repositories.
**Delivery format:** Curated hybrid plugin (`dev.alex-tavern.dynamic-character-presence`)
**Requested by the user:** simple manual control of who takes part in the scene, with optional Narrator control

## 1. Objective

Add dynamic presence without creating a second character list. All characters keep
existing in `GameState.characters`, with their full data preserved, while
`Scene.present_characters` now indicates only who is in the current scene.

When the plugin is active:

- each character in the current setup UI gets a presence toggle;
- on means the character starts present in the scene;
- off means it stays saved in the session but starts outside the scene;
- the Narrator can add or remove characters during the turn when the plugin's optional
  setting allows it;
- absent characters stop consuming detailed context in calls they don't take part in.

The feature does not remove, disable, or recreate characters. Presence is scene state,
not registration state.

## 2. User experience

### Toggle in the current character UI

The control must be embedded in the header of each existing `.char-card` in setup. It
must not open a parallel screen or duplicate the character editor.

The toggle uses a short, translated label, like `In scene`, and must communicate its
state through text, appearance, and accessible semantics. Clicking the label also
changes the value. The control must work via keyboard, screen reader, and touch, with
an appropriate minimum target size for mobile.

When saving a scenario or starting a session, the IDs that are on, followed by the
internal `Player` marker, form `scene.present_characters`. IDs that are off remain in
`characters` with no loss of `mind`, `body`, notes, or history. When a scenario is
loaded again, the UI restores the toggles from the persisted list; `Player` doesn't get
its own toggle.

The human-controlled character must be present. If the user turns off the controlled
character, the UI must ask them to pick another present character before saving or
starting. The backend repeats this validation and never silently corrects the value.

### Conditional plugin configuration

Once the plugin is activated, its configuration area shows:

```json
{
  "allow_narrator_presence_changes": true
}
```

Suggested label: `Narrator can change who is in the scene`.

- `true`: the Narrator can propose entrances and exits in its structured response;
- `false`: only the human toggles set presence, and the Narrator receives the list as
  read-only context;
- the field only appears while the plugin is active;
- the value belongs to the plugin's configuration and can be set by an Experience;
- initial activation materializes the `true` default before first use;
- missing or invalid configuration fails explicitly; there is no legacy-format read
  path.

That configuration's UI must use a frontend contribution declared by the plugin. If the
SDK doesn't yet offer a configuration slot, this task includes creating a generic,
machine-readable contract for plugin configuration, instead of adding a branch keyed on
the plugin ID in `plugin-center.js`, `setup.js`, or `index.html`.

## 3. Canonical state and invariants

`Scene.present_characters` remains the single source of truth for presence. The plugin
does not keep a mirror list in `plugin_state` or in its own configuration.

Contract rules:

- each character entry is an ID that exists in `GameState.characters`;
- IDs are unique and preserve the canonical order of `characters`;
- the controlled character is always present;
- the internal `Player` marker stays present exactly once, at the end of the list, never
  becomes an additional character, and is never exposed to agents as an external
  operator;
- adding or removing someone doesn't change their profile, memory, mood, or body;
- absent characters can return later with the same ID and state;
- invalid data is rejected, never silently filtered or completed.

The current path that recomposes `present_characters` with every character in
`Runner.start_session` must be replaced by the current input contract. Producers and
consumers change together, with no fallback to the previous behavior.

## 4. Human control during a session

Besides the initial setup state, the plugin must contribute a compact control for the
active session UI. The same character list uses `In scene` toggles and allows adding or
removing NPCs without editing their profiles.

Each human change:

- uses a plugin endpoint/contribution that resolves the session by ID;
- acquires the same session lock used by turn, undo, compaction, and delete;
- validates the expected revision so it doesn't overwrite a concurrent turn;
- performs a single atomic write and advances the revision once;
- records the human origin and the IDs actually changed in the journal;
- participates in the undo/audit policy defined for administrative session mutations.

The human control doesn't generate a narrative turn, doesn't call an LLM, and doesn't
add a message to the history.

## 5. Narrator control

When `allow_narrator_presence_changes` is active, the normal Narrator call receives an
optional structured extension:

```json
{
  "presence_update": {
    "present_character_ids": ["C1", "C3"]
  }
}
```

The response declares the complete desired list. This avoids ambiguity around partial
operations, duplicates, and application order.

The result is validated before commit and applied to the same turn's draft. There is no
second LLM call, textual parser, regex, or provider-specific branch. The change is
persisted together with narration, speech, thought, snapshots, and
`plugin_state_snapshot`, under the session lock.

The Narrator cannot remove the controlled character, insert an unknown ID, or select an
absent character as the next speaker. An invalid proposal is discarded and journaled
without corrupting the state; the rest of the valid narrative response can still go
through.

When the setting is off, the schema doesn't offer `presence_update`, and any unexpected
field fails normal structured validation.

### SDK gap to resolve

The plugin must not replace the entire `narrator.call` just to add presence. If the SDK
doesn't yet have the necessary contract, this task includes a narrow contribution point
to:

- add Narrator context;
- extend its JSON Schema with an optional output belonging to the plugin;
- validate and apply the result to the turn's transactional draft.

The contract must stay provider-independent and preserve `session_id`, `turn_number`,
`agent`, debug log, local validation, human agency, and deterministic plugin ordering.
The machine-readable contract, the authoring MCP, and the hub documentation must be
updated together with core.

## 6. Context and token economy

The Narrator receives full profiles only for present characters. For absent ones, it
receives a minimal, deterministic list containing only ID and name — enough to know who
could enter the scene, without loading personality, knowledge, physical description, or
outfit.

Character calls remain limited to the character itself and can only happen for a
present character. Absent characters receive no autonomous calls.

World summary, private memories, and history remain responsible for continuity. The
plugin doesn't create another memory system and doesn't turn the absent-characters
minimal list into a parallel summary.

## 7. Responsive frontend requirements

The main criterion is preserving the current density and design on both mobile and
desktop. Activating the plugin must not make the cards feel cluttered, unnecessarily
increase their height, or break the setup flow.

### Desktop

- toggle aligned in the card header, alongside the existing actions;
- name keeps occupying the main flexible space;
- text never overlaps the badge, toggle, or remove button;
- on/off states stay legible under the current theme and contrast.

### Mobile

- no horizontal scrolling at supported widths;
- the header can wrap intentionally, keeping name and actions usable;
- the touch target doesn't depend solely on the small visual indicator;
- the toggle doesn't shrink text fields to an impractical width;
- safe areas, visible focus, and the virtual keyboard keep working;
- the plugin's configuration uses the same responsive pattern as the Plugin Center.

The plugin's elements are only mounted while it's active. Deactivating it removes the
controls without leaving empty gaps, duplicate listeners, or CSS that alters the base
UI.

## 8. Ownership and plugin format

Expected format in the curated hub:

```text
plugins/dynamic_character_presence/
├── plugin.toml
├── backend.py
├── frontend.js
└── tests/
```

Expected permissions:

- `session.state.write` to change `Scene.present_characters` under the authorized flow;
- `config.read` / `config.write` for `allow_narrator_presence_changes`;
- `frontend.dom.mount` for the toggles and the conditional configuration.

Must not require `model.call`, `network`, or `unsafe`. The Narrator's existing call is
itself extended through the SDK contract.

## 9. Non-goals

- deleting characters or removing their data from the session;
- automatically changing personality, body, mood, knowledge, or notes;
- creating a parallel presence list in `plugin_state`;
- keeping compatibility with sessions that depend on recomposing every character;
- creating a Llama.cpp-, DeepSeek-, or other-provider-specific prompt or parser;
- letting an absent character speak, or letting an LLM control the human character;
- redesigning the character editor or adding a heavy panel to the main screen;
- editing `.data/plugins/hub` as the plugin's source.

## 10. Implementation sequence

1. Define current fixtures for `present_characters`, including controlled present,
   invalid IDs, and a partial list.
2. Remove the automatic recomposition at session start and validate the received list
   at the boundary.
3. Add the SDK's generic points for frontend configuration and structured Narrator
   extension, if they don't already exist.
4. Scaffold the curated plugin in the sibling checkout via the hub MCP.
5. Implement the toggle on the current setup cards and restoration from scenarios.
6. Implement the compact control in the active session with lock, revision, and atomic
   write.
7. Implement the conditional configuration and the structured Narrator control.
8. Reduce absent-character context and prevent Character calls/speaker selection
   outside the scene.
9. Validate undo, concurrency, debug/journal, replay, and plugin failures.
10. Run frontend tests on desktop and mobile, the real HTTP boundary, plugin
    validation/packaging, and core's full quality gates.

## 11. Acceptance criteria

- Each card's toggle correctly sets the initial presence without deleting the
  character.
- Saving and reloading a scenario preserves the presence selection exactly.
- The backend rejects an unknown ID, duplicate, invalid order, and an absent controlled
  character.
- With the plugin inactive, there are no toggles, configuration, empty space, or visual
  change in the UI.
- With the plugin active, the `Narrator can change who is in the scene` option appears
  in the plugin's configuration and persists its value.
- With the option off, only the human changes presence and the Narrator's schema
  doesn't accept an update.
- With the option on, a valid Narrator change is applied atomically in the same turn.
- The Narrator never removes or takes over the controlled character and never picks an
  absent character as the next speaker.
- An absent character keeps all its state and can return later with no data loss.
- Full profiles of absent characters never enter the Narrator's prompt; the minimal
  list contains only ID and name.
- An absent character never receives an LLM call.
- A human mutation concurrent with a turn, undo, compaction, or delete never produces a
  lost update.
- Undo restores the exact presence of the step, and the debug/journal identifies the
  origin of the change.
- Setup and the session control stay legible, accessible, and free of overflow at
  supported mobile and desktop widths.
- Repeatedly activating/deactivating never duplicates controls, listeners, or styles.
- Frontend tests load every module, register the plugin, parse the HTML, and cover
  keyboard/touch; backend tests cover success, error, empty/invalid input, and
  concurrency.
- The plugin passes `plugin_validate`, `plugin_test`, and `plugin_pack`, and core passes
  the full quality gates before this task moves to `.plan/closed/`.
