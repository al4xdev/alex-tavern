# Task: Dynamic character presence and removal (Narrator control & token optimization)

**Status:** Explicit future work  
**README evidence:** N/A (Requested by User)

## Stated behavior

- Allow characters to be dynamically removed or added to the active conversation context during play.
- The Narrator should have the agency to decide who is present in the scene. In its JSON schema response, it should be able to output presence updates (e.g. `scene_update: { present_characters: [...] }`).
- For characters not present in the current scene:
  - Do not pass their full profiles (personality, physical description, outfit) to the Narrator or Character LLM calls to optimize token usage.
  - Retain their full profiles in the session's overall `characters` list so they can return to the scene later without losing their definition.
- Address context-preservation challenges: how does the Narrator remember details about a character who has left the scene without keeping their complete raw profile inside the active prompt context at all times?

## Current repository state

- Currently, `present_characters` is re-initialized by the Runner to always include all characters: `scene.present_characters = [*characters, "Player"]`.
- The Narrator's system prompt constructor unconditionally appends the profiles of all characters defined in the session, consuming tokens for inactive characters.
- There is no mechanism in the REST endpoints, Runner, or Narrator agent to update, add, or remove characters dynamically from the active scene.

## Open questions

- **Prompt Optimization:** If a character is absent, should we completely exclude them from the Narrator's prompt, or pass a minimal summary (e.g., just name and status/location) to preserve continuity?
- **Narrator Schema:** How should the Narrator output presence changes? Should it be a list of modifications (e.g. `{"remove_characters": ["C3"]}`) or a declaration of the new list of present characters?
- **Frontend Sync:** How should the UI reflect that a character is "absent" (e.g., grayed out, hidden, or marked as "out of scene")?
