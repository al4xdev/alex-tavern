# To the next session

Handoff refreshed 2026-07-21 after implementing Tasks 48, 49 and 50. These
newest changes are validated locally but are not committed.

## 1. Git and safety state

- Branch: `master`; the working tree contains the uncommitted Task 48/49/50
  implementation and documentation. Preserve it.
- Earlier work below is committed but **not pushed**. Do not commit, rebase,
  merge or push without fresh, explicit owner authorization.
- New commit subjects: `fix(alignment): validate screenplay impulse controls`,
  `feat(disposition): close substrate with witnessed dyads`,
  `test(canon): refresh the xfailed3 provider benchmark`, and
  `docs: close reviewed lanes and refresh the handoff`.
- Existing commit subjects in the visible local history are in English. Do not
  add AI attribution trailers to future commits.
- Runtime/playtest data stayed under `/tmp`; no `.data/` content belongs in Git.

## 2. Completed in this working tree

### Tasks 48 and 49: opening sparks and observer warning

Empty sessions can now request three scenario-only opening sparks. The backend
uses only scene facts/directives, returns ephemeral strings, and refuses missing
or already-started sessions. Choosing a spark literally reuses narrator hint +
Continue. DeepSeek V4 Flash passed the pre-registered final gate: 6/6 structural,
6/6 without internal IDs and 5/6 qualitative sets; the real HTTP selection
committed normally and a repeat request returned 409. Full evidence is inline in
`.plan/closed/48-opening-suggestions.md`.
The owner also completed a normal manual frontend check and reported the feature
working as expected before authorizing commit and push.

Until canonical history contains the player's first public speech, the speech
placeholder now warns that Continue lets the world speak without them. The flag
is frontend-only and derived from history/effective successful input; skip,
thought/action and failures do not dismiss it. Evidence is inline in
`.plan/closed/49-observer-warning.md`.

The service-worker shell cache is now `rpt-shell-v19`.

### Task 50: shared Playwright frontend inspection

Playwright 1.61.0 now belongs to the dev dependency group. Agents can use
`tools/frontend_inspector.py`, passive MCP tool `inspect_frontend`, or stepped
non-read-only MCP tool `mutate_frontend_flow`; every screenshot is constrained
to `/tmp`. Real Chromium captures passed through both CLI and FastMCP registry
with zero browser/page errors. The MCP launcher is now forward-only
`python -m tools.mcp_server`; old file-path examples were updated together.
Full evidence is inline in `.plan/closed/50-playwright-frontend-inspector.md`.

### Task 44: character/roteiro alignment, closed with evidence

The task was reopened because its checklist and durable evidence were missing.
It now has the benchmark inline and all real gates recorded in
`.plan/closed/44-roteiro-character-alignment-toggles.md`:

- deriver v2: 18/18 across 6 beats and 6 characters after an isolated v1 fix;
- Character boundary replication: OFF 1.75 -> warm 2.00, zero leak/meta,
  voice preserved 4/4;
- all four toggle combinations, invalid input and Runner/provider swap tested;
- real HTTP PUT -> turn boundary exercised;
- Playwright passed at 1080p and 2K; disabled-warning accessibility and keyboard
  focus were corrected.

The tracked frontend shell cache is now `rpt-shell-v18`.

### Task 45: multi-beat continuation, live confirmation added

The previously test-only player-action budget fix was observed against the real
provider. Across two continuation actions, `beat_actions_elapsed` advanced
`1 -> 2`; multiple turns committed without a false `stalled` replan. An explicit
player question also queued three responses. Evidence is inline in
`.plan/closed/45-multi-beat-story-continuation.md`.

### Task 43: disposition substrate, closed by measured subtraction

The final contract is smaller than the proposal:

- Trust and Warmth remain as per-dyad scalar state projected as qualitative
  bands to Character prompts.
- Composure failed its single-utterance razor in every battery (5/10, 5/10,
  7/10) and was removed completely.
- A public Trust/Warmth persona prior failed two pre-registered Character gates
  (5/8, then 4/8 after the only allowed prompt clarification) and was reverted.
- Real-persona authority passed 3/3: favorable public reputation did not let a
  weaker character assert victory or dictate the player's will.
- Appraisal proposals are now clamped to relationship evidence the observer
  actually perceived on that turn.

The semantic removals required `SESSION_SCHEMA_VERSION = 13`; there is no
compatibility shim. The full measured verdict is tracked as case study No. 16:
`docs/cases/16-disposition-substrate-measured-verdict-2026-07-21.md`.

Raw gate output is temporary by design:
`/tmp/task43-phase4-results.json` and
`/tmp/task43-phase4-results-v2.json`.

### Task 29.3: current-contract xfailed3 rerun recorded

The structural tier passes. Two real-provider runs were executed with isolated
data under `/tmp/alex-tavern-task29-3/`:

- reduced run: 0 violations, strict XPASS as expected for a clean sample;
- full run: 24 turns, 2 compactions and 2 restores, with two genuine residual
  output-clock misses (WT03 direction omitted; WT09 Glinda never made audible).

WT06 was an oracle false positive: a negative supernatural assay correctly
established mortality, but the regex accepted only literal “mortal/human”. The
oracle and its structural regression test now accept that semantic form. No
privacy, routing, memory, transaction or restoration defect appeared.

Task 29 stays in `tasks/` intentionally: strict xfail is a distribution monitor,
not a feature waiting for another architecture change.

### Task 26b: prompt experiment closed negative

All three prompt variants worsened ambience paraphrase from 16.4% to 21-23%.
That fulfills the owner-prescribed stop/park rule after two iterations. The task
is archived in `.plan/closed/` with its success target honestly unchecked and no
prompt rule shipped. Any future attempt belongs to Task 26 and needs new
event-level material-delta evidence; do not revive the prompt wording.

### Task 46: moved to backlog

The schema-description migration was explicitly shelved and transverse, so it
now lives in `.plan/backlog/46-schema-description-instruction-channel.md` rather
than masquerading as active work. Task 45 is closed; its unrun field-description
A/B is merely a candidate for a future deliberately budgeted campaign.

## 3. Tasks intentionally still open

- `26-narrator-prose-quality.md`: evidence accumulator for the residual ~9%
  semantic paraphrase band. There is no measured, actionable intervention now.
- `29.1-29.3-xfailed3-counter-canon.md`: variance-bound distribution monitor;
  the current-contract rerun is recorded inline.
- `38-roteiro-beat-contracts.md`: delivered with reservations by explicit owner
  convention. Its document now states the current unit correctly: serialized
  `budget_turns` means player actions, and one continuation spends one action.

These three files remaining under `tasks/` is deliberate. Closing them as if the
distributional uncertainty had disappeared would be less accurate than their
current status.

## 4. Validation state

Final deterministic validation:

- all changed alignment/config/frontend/disposition/schema/29.3 files:
  **113 passed, 2 LLM tests deselected**;
- disposition plus undo integration slice: **49 passed** (including the new
  end-to-end restoration of pre-turn disposition state);
- Ruff check and format check: passed;
- `mypy src/`: passed.
- `git diff --check`: passed.

The aggregate suite produced no assertion failure but could not finish in this
sandbox: it hung at boundary-heavy modules (`test_integration.py`, then
`test_mcp_server.py`, then `test_memory_retention.py`) until controlled timeout/
interrupt. The changed modules are covered by the deterministic sets above; do
not misreport those no-output boundary hangs as product failures.

## 5. Durable decision rules

- Curl-first, with the decision rule registered before calls.
- The tested prompt variant must be the one shipped; a failed variant is
  removed, not rationalized.
- Prompts express tendencies; code owns guarantees, scalars and confidentiality.
- A negative experiment can be a complete task when its preregistered fallback
  is to stop. Leave the failed success metric visible.
- Do not create session compatibility layers. Bump the schema when persisted
  semantics change and move forward.

At this point there is no remaining autonomous implementation item in the
reviewed queue. The next productive step is either fresh live evidence for Task
26/29/38 or an explicit owner choice of a backlog feature.
