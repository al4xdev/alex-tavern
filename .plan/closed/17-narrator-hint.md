# Task: Narrator Event Hint

**Status:** Completed and closed  
**Closed:** 2026-07-13

## Delivered behavior

The Narrator Event Hint is a core turn feature. The player can queue an external event from the
frontend modal and send it with the next turn. The Narrator receives it as an `UPCOMING EVENT`
section and decides its narrative consequences, scene update, and next speaker.

## Closure evidence

- `src/static/index.html` and `src/static/app.js` provide the event-hint control and modal, retain
  a queued value across retry/undo UI state, and submit `narrator_hint` with the turn.
- `PlayerTurnRequest` in `src/main.py` accepts `narrator_hint`; a hint-only turn is valid.
- `Runner.player_turn` persists the supplied value in the `turn_input` debug marker and forwards it
  to the Narrator call under the session lock.
- `src/agents/narrator.py` appends a non-empty hint to the Narrator context as `UPCOMING EVENT`.
- Integration tests cover prompt inclusion/omission, HTTP propagation, hint-only turns, skip,
  thought, action, and forced-speaker combinations.

## Architecture note

The original proposal to make this a `plugin_data`/`before_narrator` plugin was not adopted. The
application has no generic `plugin_data` turn field or `narrator-hint` plugin. The final, supported
contract is the explicit core `narrator_hint` field, introduced in `a878bb2` and subsequently
covered through the complete turn flow.
