# Task 48 — Scenario-only opening suggestions

**Status:** CLOSED (2026-07-21)

## Goal

When a session has no history, offer three short ways to open the story without
making the player design the first event. Generation uses only the resolved
scenario (`scene` plus `narrator_directives`), never character sheets or history.
Choosing one composes the existing native flow: queue it as `narrator_hint`, then
call the existing skip/continuation action.

## Frozen contract

- `POST /session/{id}/opening-suggestions` returns exactly three strings.
- Only an empty session may call it; missing session is 404, started session is 409.
- Input to the model excludes characters, character IDs, controlled identity and
  history. Output is not persisted, cached or added to session state.
- Each option is one brief external opening event ending in `...`; it does not
  decide a character's action and gives whoever naturally notices it a reason to
  comment. It never requires everyone to react or chooses who reacts; the
  controlled character may simply watch without being identified to any agent.
- The empty state shows an explicit generation button. Results live only in a
  one-card carousel with bounded arrows, dots/count, swipe, "Start this way" and
  "Generate others".
- Selection performs only `state.narratorHint = option; await skipTurn()`.
- Options are cleared on session load/start, after the first record and after reload.

## Real-provider gate (pre-registered before calls)

Run the exact production builder three times for each of two materially different
scenarios (small tavern and large academy): six calls total.

- Structural pass: 6/6 responses contain exactly three schema-valid, one-line
  strings of 20-240 characters ending in literal `...`.
- Qualitative pass: at least 5/6 sets contain three distinct, scenario-grounded
  openings; every option leaves character choice open, names no character/ID and
  gives natural witnesses a reason to comment without requiring everyone.
- If the qualitative gate fails, change only the opening prompt and rerun the same
  six-call production-builder battery. The tested variant is the shipped variant.

## Acceptance

- [x] Backend contract, lock, error semantics, debug identity and zero persistence tested.
- [x] Frontend carousel, regenerate, keyboard/swipe, failure recovery and ephemeral reset tested.
- [x] English/Portuguese parity, responsive layout and reduced motion validated.
- [x] Real-provider gate and real HTTP opening -> existing turn boundary recorded here.
- [x] README updated and task moved to `.plan/closed/`.

## Delivery evidence

### Prompt iterations and decision rule

The pre-registered two-scenario battery was kept fixed. The first variant
returned three valid events in all six calls but gave no reliable reason for a
Character response (0/6 sets). The second prompt-only variant improved this to
roughly 3/6 sets. The shipped variant changed the internal structured item to
`{event, conversation_hook}` and made the hook a bounded 6-to-12-word clause.
DeepSeek receives that schema through its existing adapter as JSON Object mode
plus the full schema instruction; the shared client validates `minLength` /
`maxLength` locally and retries invalid output.

Final real-provider battery (DeepSeek V4 Flash, Brazilian Portuguese, production
builder, 2026-07-21):

- 6/6 calls returned exactly three one-line public strings ending in `...`;
- all 18 strings were 107-182 characters and 6/6 calls contained no character
  ID or `Player` marker;
- 5/6 sets passed the qualitative gate: three distinct scenario-grounded
  events, free character choice and a natural-witness conversation hook. The
  one failing set used question-like hooks (`alguém quer comentar?` /
  `alguém mais notou?`) and one merely reflective hook. The pre-registered gate
  was at least 5/6, so no post-hoc iteration was made after passing;
- debug entries identify every attempt as `agent="opening_suggest"`, with the
  real session ID and `turn_number=0`.

### HTTP and persistence boundary

The first returned option was submitted to the existing `POST /turn` boundary
as `skip=true` plus `narrator_hint`. It committed normally (six history records
across the generated continuation). A second opening request returned HTTP 409.
The authoritative state contained no `opening_suggestions` field. All runtime
config, sessions and raw evidence stayed under
`/tmp/alex-tavern-task48-20260721/`; no `.data` artifact entered Git.

### Frontend and deterministic validation

- Focused Task 48/49, i18n and frontend architecture slice: 42 passed.
- Native hint composition is literal: selection assigns `state.narratorHint`
  and awaits the existing `skipTurn()`.
- Firefox headless inspection at 1365x900 and 390x844 confirmed readable card
  wrapping, bounded arrows, count/dots, coherent actions and responsive layout.
  The temporary query-string preview used for screenshots was removed before
  validation; screenshots remain only in `/tmp`.
- The owner then exercised the new opening flow manually in the normal frontend
  and confirmed that it worked as expected before authorizing the remote push.
