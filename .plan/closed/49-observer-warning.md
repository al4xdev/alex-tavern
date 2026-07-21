# Task 49 — Observer warning in the speech box

**Status:** CLOSED (2026-07-21)

## Goal

Before the player has spoken in a session, use the speech input placeholder to
make the skip behavior explicit: continuing silently lets the world and its
characters carry the story without the player's intervention.

## Frozen contract

- This is informational UI only. It does not block skip, speech, thought or
  action and does not change turn behavior.
- The warning lives in the existing speech textarea placeholder.
- It remains while the canonical session history has no non-empty public
  `Player` speech, including after one or many skip-only turns.
- It disappears after the first successful turn that persists effective player
  speech. Undoing that speech makes it appear again.
- The state is derived from current history and successful turn output. It adds
  no backend field, session schema, storage, memory or compatibility path.
- English and Brazilian Portuguese receive equivalent copy. The wording says
  that **Continue** lets the world proceed; it does not claim that turns happen
  automatically.

## Acceptance

- [x] Empty and skip-only sessions show the warning in the speech box.
- [x] Successful speech removes it; reload and undo derive the correct state.
- [x] Thought/action-only turns keep it; failed turns do not remove it.
- [x] Locale changes update the active placeholder.
- [x] Frontend checks pass and the task is moved to `.plan/closed/`.

## Delivery evidence

`renderHistory()` derives the flag only from non-empty canonical records with
`speaker="Player"` and `content_type="speech"`. The successful turn path changes
it only after non-empty `effective_input.speech`; skip, thought/action-only and
failed calls therefore cannot dismiss the warning. Reload and undo both pass
through the same authoritative history renderer. Locale changes re-render the
placeholder. No backend, schema, localStorage or session field was added.

Focused Task 49 regressions cover history derivation, successful effective
speech and EN/PT locale updates; they passed as part of the 42-test frontend
slice. Desktop visual inspection confirmed the warning in the expanded speech
box. On narrow screens the existing collapsed composer deliberately retains its
short “Write message...” label; opening the composer reveals the warning in the
actual speech field.
