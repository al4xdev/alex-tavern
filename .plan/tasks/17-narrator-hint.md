# Task: Narrator Hint (God-Mode Suggestions as a Plugin)

**Status:** Open (Refactored to Plugin Architecture)  
**Replaces:** Old implementation plan modifying core REST endpoints and system parameters

## 1. Description & Plugin Fit
Instead of hardcoding a `narrator_hint` parameter across the FastAPI route, `Runner.player_turn`, and `narrator.py`, the God-mode narrator hint will be implemented as a **Trigger Plugin** (`narrator-hint`).

At execution time, the frontend can pass arbitrary extra parameters inside a generic `plugin_data` dictionary in the turn payload. The `narrator-hint` plugin will intercept this payload and append the hint directly to the Narrator's instructions before the model call is initiated.

---

## 2. Plugin Execution Flow

1. **Frontend Dispatch:** The user enters a narration hint in a dedicated "Event" input box.
2. **Payload Structure:** The frontend sends a POST request with `plugin_data`:
   ```json
   {
     "speech": "...",
     "action": "...",
     "plugin_data": {
       "narrator_hint": "Suddenly, a loud thunderclap shakes the tavern."
     }
   }
   ```
3. **Core Interception:** The runner executes the `before_narrator` hooks, passing the `plugin_data` and prompt messages.
4. **Plugin Logic:** The `narrator-hint` plugin extracts `"narrator_hint"` and modifies the system instructions by appending:
   ```text
   UPCOMING EVENT (incorporate this into your narration):
     Suddenly, a loud thunderclap shakes the tavern.
   ```
5. **Execution:** The Narrator receives the prompt and decides how the scene updates or who acts next naturally, keeping full agency.

---

## 3. Benefits of the Plugin Approach
- **Core Decoupling:** Neither `Runner` nor `Narrator` needs to know what a "hint" is.
- **Payload Flexibility:** Other mechanics (like dice rolls or card draws) can use the same `plugin_data` envelope without modifying backend schemas.
- **Clean Architecture:** If the user disables this plugin, the Narrator prompts remain clean without empty condition checks.

---

## 4. Implementation Steps
1. **API Schema Update:** Ensure the `POST /sessions/{id}/turn` payload accepts an optional `plugin_data: dict[str, Any]` field.
2. **Hook Execution:** Propagate `plugin_data` to the plugin execution pipeline.
3. **Hint Injection Trigger:** Code the `narrator-hint` plugin to modify messages during the `before_narrator` event hook.
4. **UI Update:** Add the "Narrator Hint / Event" pop-up in the frontend and bind its submit value to the `plugin_data.narrator_hint` field.
