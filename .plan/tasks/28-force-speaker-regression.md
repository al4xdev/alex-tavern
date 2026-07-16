# Task 28 — Force Speaker Regression

**Status:** Open
**Reported:** 2026-07-15
**Type:** Bug

## Goal

Restore the Force Speaker control across every supported turn path. The reported
behavior is that the selected override is no longer honored at all: for example,
forcing `Narrator` can still produce a Character response.

The cause is not known yet. Do not limit the investigation or the fix to skip
turns, and do not treat a passing backend-only test as proof that the UI flow is
working.

## Scope

- Reproduce the regression through the real frontend before changing the code.
- Trace the selected value through the frontend request, `turn.input` plugin hook,
  FastAPI boundary, Runner validation, Narrator prompt, routing decision, response,
  and `debug.jsonl` evidence.
- Cover ordinary sends and skip turns independently.
- Preserve the mobile long-press/gesture action menu. Its secondary actions,
  including **Suggest**, must remain reachable and functional while Force Speaker
  is selected and after the fix.
- Keep the agency guard: forcing the human-controlled character must return control
  to the human and must never generate their speech.

## Acceptance criteria

### Isolated automated coverage

- [ ] A frontend boundary test selects `Narrator`, performs an ordinary send, and
  proves that the HTTP turn payload contains `force_speaker: "Narrator"`.
- [ ] A separate frontend boundary test selects `Narrator`, activates **Skip turn**,
  and proves that the same request contains both `skip: true` and
  `force_speaker: "Narrator"`.
- [ ] A Runner/API test makes the Narrator model return an NPC as `next_speaker`
  while `Narrator` is forced, then proves that `next_speaker` remains `Narrator`,
  `character_response` is absent, and no Character model call occurs.
- [ ] Tests cover invalid/absent character IDs and the controlled character without
  weakening the current presence and human-agency guards.
- [ ] A mobile interaction test exercises the long-press/gesture action menu and
  proves that Force Speaker remains selectable and the **Suggest** action still
  calls the suggestion flow. Test Force Speaker from this menu with ordinary send
  and keep the skip-turn case isolated from it.

### Final real-LLM acceptance run

- [ ] Run a real LLM conversation with **more than four characters present** (at
  least five total, including the human-controlled character).
- [ ] Execute at least four consecutive rounds with `force_speaker` set only to
  `Narrator`; do not force an NPC during this acceptance run.
- [ ] Every round produces Narrator output only, even when the raw model response
  chooses an NPC. No Character call or Character response may occur.
- [ ] For every round, `debug.jsonl` shows `force_speaker: "Narrator"` in
  `turn_input`, `effective_force_speaker: "Narrator"` in
  `turn_input_effective`, and the expected Narrator request/response with matching
  `session_id`, `turn_number`, and `agent`.
- [ ] Run the skip-turn acceptance separately with `skip: true` and forced
  `Narrator`, proving the same routing outcome without player speech, thought, or
  action.

## Delivery evidence

- Record the original reproduction, identified root cause, isolated test commands,
  frontend/mobile boundary evidence, and real-LLM session/debug-log evidence here
  before moving this task to `.plan/closed/`.
- Update the Force Speaker documentation if its actual user-visible contract changes.

## Additional Evidence (2026-07-16, live session `091b11c6`)

User replayed with the character-alteration plugin active and reports the bug
persists: characters did not speak even when explicitly forced
(`plans/artifacts/session-091b11c6-live-findings/`). Investigate whether the
plugin's `turn.input` hook interferes with `force_speaker`, and compare
`turn_input` vs `turn_input_effective` records in that session's debug log.
