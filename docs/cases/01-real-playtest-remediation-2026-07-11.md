# From a real playtest to verified remediation: a four-stage engineering loop

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 01 |
| **Dates** | 2026-07-11 to 2026-07-12 |
| **Sessions** | `7cb448da` and post-remediation live session |
| **Model** | Gemma 4 26B A4B QAT via local llama.cpp |
| **Status** | Historical evidence; later contracts supersede implementation details (see notes) |

## Abstract

A 20-turn real playtest with one manual compaction surfaced six objective defects and a set of qualitative weaknesses in the early engine. This article preserves the complete loop as evidence: the original findings (Part I), the execution plan derived exclusively from them (Part II), the verified closure of every objective defect (Part III), and the independent post-remediation live exploration that validated the fixes under real play, including two compactions with a restore between them and an undo (Part IV). The loop established the house method later formalized for every task: findings recorded before fixes, plans derived from recorded evidence only, and closure claimed only on verified behavior.

---

## Part I — Findings of the real playtest (2026-07-11, session 7cb448da)

**Date:** 2026-07-11
**Session:** `7cb448da`
**Scope:** 20 real turns, 1 manual compaction, and inspection of the state, the backup and the
sequential raw log.

> **Contract note (2026-07-14):** this report preserves the paths and the behaviour observed in
> the 2026-07-11 playtest. The current runtime uses directory-based sessions, manual or automatic
> compaction, measured SSE progress, and incremental LIFO checkpoints that preserve later turns.
> See [Context Compaction](../../README.md#-context-compaction).

### Artifacts audited

- State after compaction: `.data/sessions/7cb448da.json`
- Full pre-compaction backup: `.data/sessions/7cb448da.kb_0.json`
- Raw calls and responses: `.data/sessions/7cb448da.debug.jsonl`
- Relevant flows: `src/runner.py`, `src/llm/client.py`, `src/agents/narrator.py`,
  `src/agents/character.py` and `src/agents/summarizer.py`

The script used was the project's private manual playtest script. Some `force_speaker` values were
chosen freely during the test, so not every deviation from the expected text is attributable to the
agents.

### Summary

The main flow worked end to end: there was no `Player` leak to the model, all 20 turns were
persisted, Thorn's agency was respected, the Narrator produced valid JSON after its retries, and
the compaction retained the expected 8 turns. The session did, however, reveal two state bugs with
direct impact, an observability problem, a likely degradation from context growth, and several
strange agent behaviours.

The highest-priority problems are:

1. location changes never update `Scene.location`;
2. the character notes produced by compaction are saved under keys the runtime never consults;
3. from turn 14 to 20, every first Narrator call failed and the log recorded only an empty error
   message;
4. the session's exact replay cannot be reconstructed from the log alone, because `force_speaker`
   is not recorded.

### Clear bugs

#### 1. Location changes are written as physical facts, not as `Scene.location`

**Suggested severity:** high

The Narrator emitted coherent location updates:

- turn 13: `{"location":"The Old Watchtower"}`;
- turn 15: `{"location":"The Old Watchtower — interior entrance"}`;
- turn 17: `{"location":"The Old Watchtower — interior"}`.

Even so, the final state still contains:

```text
scene.location = "Old Mork's Tavern — main hall, dim lighting"
scene.physical_facts.location = "The Old Watchtower — interior"
```

The cause is in `Runner._update_scene`: every `scene_update` pair is written exclusively into
`game.scene.physical_facts`. The prompt then presents the tavern as the official location and the
tower as a physical fact, simultaneously. The UI and any logic reading `Scene.location` stay stale
throughout every change of setting.

#### 2. Compaction notes use identifiers incompatible with the runtime

**Suggested severity:** high

The Historian returned, and the state saved:

```json
{
  "C1 — Thorn": "...",
  "C2 — Lyra": "..."
}
```

But `Runner._call_character` consults `game.character_notes.get(character_id, "")`, where
`character_id` is `C1` or `C2`. So both notes exist in the JSON and will never be delivered to
Thorn or Lyra.

The prompt asks for a map keyed by character id, but shows the input lines as `C1 — Thorn:`. The
schema accepts any key (`additionalProperties`) and does not restrict the properties to existing
ids. The integration tests use mocks that already return `C1` and `C2`, so they do not cover the
variation observed with the real model.

#### 3. LLM failures are recorded as `error: ""`

**Suggested severity:** medium

There were 7 failing first attempts, one on each turn from 14 to 20. All were followed by a
successful attempt, but the error lines contain only an empty string. `_log_llm_call` receives
`str(e)`, which loses all information when the exception has an empty text representation.

From the behaviour and the fixed 60-second timeout, `httpx.ReadTimeout` is a strong hypothesis, but
the log itself does not preserve the exception's type or `repr` to confirm it. That weakens the
main observability tool exactly when the context grows.

#### 4. A forced character can receive context written for another speaker

**Suggested severity:** medium

In `Runner.player_turn`, the Narrator first generates `next_speaker` and
`context_for_character`. Then `force_speaker` may replace only the speaker. If the forced
character differs from the one originally chosen, `_call_character` receives the same
`context_for_character`, still written for the original speaker.

This playtest produced no Lyra call that contradicted the Narrator's original choice, so the effect
did not appear in the final text. The incorrect path is, however, direct and reproducible from the
code.

#### 5. The log records neither `force_speaker` nor the turn payload

**Suggested severity:** medium for replay; low for normal use

Turn 13 demonstrates the gap: the Narrator chose `C2`, but there was no Lyra call — a result
consistent with the override to `Narrator` indicated by the script. `debug.jsonl` records only the
LLM calls and does not record the payload received by `POST /session/{id}/turn`.

Consequences:

- it is impossible to distinguish `Auto` from an override that happened to match the Narrator's
  decision;
- it is impossible to reconstruct with certainty the overrides chosen freely;
- a replay tape based only on the responses knows the order of the outputs, but does not know which
  UI actions should provoke one or two calls.

For the future fake server on port 8888, the log's `response` is enough to return the model's
content, but the sequence of inputs/overrides has to be stored separately.

#### 6. The test suite uses and deletes artifacts from the real sessions directory

**Suggested severity:** high, for the safety of development data

After running `uv run pytest -x`, the manual files `7cb448da.json` and `7cb448da.kb_0.json`
disappeared from `.data/sessions`, while the original `debug.jsonl` remained and several files from
sessions created by the tests were left in the same directory. That proves at least part of the
suite shares the real storage instead of injecting an isolated temporary directory.

The effect destroyed the state and the backup used in this audit. Reproduction could only continue
because the full HISTORY still existed in the raw log's requests. The exact cause and the isolation
fix were left pending, but no test should read, clean or write the real `.data/sessions`.

### Strange or fragile behaviours

#### Context growth coincides with retries on every final turn

The Narrator's prompt grew continuously:

- turn 1: 1,416 characters;
- turn 13: 16,221 characters;
- turn 14: 17,427 characters, first failure;
- turn 20: 26,443 characters.

From turn 14 onward, every first attempt failed and every following retry worked. That does not
prove causality, but it creates a strong correlation between growing context, latency and timeout.
Compaction was only triggered after turn 20.

#### The physical state accumulates duplicate, identity-less keys

The final state contains, simultaneously:

```text
weather_outside = heavy rain
weather = torrential rain
```

The generic key `door` also represented, at different moments, the tavern door, the kitchen exit
and the tower door. Its values went through `closed`, `open`, `pushed open`, `ajar` and finally
removal. Since facts are a flat dictionary created freely by the model, synonymous names accumulate
and objects from different places collide.

#### Excessive mood churn

The Narrator emitted `mood_updates` on 18 of the 20 turns. Thorn passed, among other states,
through `cautious`, `alert`, `grim`, `vigilant`, `determined`, `cautious`, `determined`, `focused`,
`intense`, `alert`, `ready`, `heavy-hearted`, `vulnerable`, `determined`, `alert`, `determined` and
`resolute`.

Some changes are justifiable, especially on turns 15–17, but the frequency indicates the field is
working as a snapshot description of pose rather than durable emotional state. That contradicts the
instruction to update only when the mood actually changed.

#### Lyra invented a fact and compaction turned it into durable memory

On turn 5, Lyra claimed the medallion was found "in the old ruins while we were trekking to the
edge of the corrupted forest". The preset said only that the medallion had been found and that the
forest to the north was corrupted; that turn's context did not supply the ruins either.

The Historian later folded "medallion found in the old ruins near a corrupted forest" into the
`story_summary`. That shows how a Character's invention can become persistent canon at compaction.

#### Lyra repeated a whole sentence from her own history

On turn 20, Lyra repeated the first line of turn 18 literally:

```text
If you are trying to be brave is working, you should know that the noise is making it very hard
to focus on your stoic silence, Thorn.
```

The repetition preserved even the grammatical error. The Character receives previous dialogue in
the prompt, which makes a direct copy from the history plausible.

#### The Narrator frequently describes the controlled character's mind

Examples include "his mind calculating", "the burden of a man leading a charge", "the hollow ache
in his chest" and the assertion that the truth could "break him or forge him". The sensory
narration works, but it sometimes stops showing observable signals and instead defines Thorn's
thoughts, intentions and internal emotions. That erodes the separation between the Narrator and the
controlled character.

#### Actions are retold, but do not always produce consequence

- turn 6: Thorn orders Mork to bar the door, but Mork never acts;
- turn 3: the hooded figure starts to rise, but the thread is left unresolved;
- turn 19: Thorn asks Lyra to break the ward, but the answer only raises the tension;
- turn 20: the script introduces the map and changes the focus before clearly resolving what was
  behind the wall.

The script also contributes to the last two jumps, so they are not isolated model bugs. Even so,
the Narrator tends to expand the input sensorially instead of closing its consequence before moving
on.

#### Recurring language defects

Examples observed in the raw outputs:

- `as他 evaluates her restless energy`;
- `sliding own the surface`;
- `hoodie` instead of `hood`/`cloak` in a fantasy setting;
- `or am just meant`;
- `am i`;
- `huming`;
- `theissen in the parchment`;
- `If you are trying to be brave is working`;
- `casting long, casting his features`;
- `vanishingness of the old trails`.

The Narrator also used an em dash on 3 of the 20 turns, despite the explicit instruction not to use
em or en dashes. The system prompt itself contains those characters in other instructions and
examples, which may weaken the prohibition.

#### The summary preserved facts, but also flattened uncertainty

The `story_summary` retained the medallion, the Iron Guard, Thorn's brother, the symbol in the
drain, the magical trail and the journey north. However, it:

- consolidated the invented origin in the ruins as fact;
- called Thorn's brother deceased, a probable inference but not stated literally in the preset;
- summarised the hooded figure as a tense encounter, without clearly preserving that his identity
  and intent remain open.

### Behaviours confirmed correct

- None of the log's 43 events contains `Player` in the prompts sent to the LLM.
- The Narrator produced a valid JSON response for all 20 turns, after retries.
- Lyra was called 14 times and, in every one, the original `next_speaker` was also `C2`.
- When the Narrator chose the controlled character (`C1`), the runner did not generate their
  speech.
- The pre-compaction backup contains 74 records spread across turns 1–20.
- Compaction removed 45 records from turns 1–12 and retained 29 records from turns 13–20, exactly
  the configured 8-turn window.
- The world summary was saved and the `compact` marker was appended to the log.
- There was no Historian retry or error during compaction.

### Coverage that remained absent

- There was no turn after the compaction; so this playtest did not confirm live whether the
  Narrator uses `story_summary` correctly, nor demonstrate that the invalid notes stop reaching the
  Characters.
- There was no undo marker, compaction restore or suggest in this session.
- Since the `force_speaker` choice is not persisted, it is not possible to fully audit which
  selections were manual using the session artifacts alone.


## Part II — Remediation plan derived exclusively from Part I

> **Merge note.** This part was originally a separate file. References to
> `01-real-playtest-remediation-2026-07-11.md` inside it mean the ORIGINAL findings
> report (now Part I) when cited as source, and the final remediation report (now
> Part III) when cited as planned output - the merge renamed all three to this
> article's filename.


**Date:** 2026-07-12
**Sole source:** [`01-real-playtest-remediation-2026-07-11.md`](./01-real-playtest-remediation-2026-07-11.md)
**Status:** ready for autonomous execution
**Expected output:** [`01-real-playtest-remediation-2026-07-11.md`](./01-real-playtest-remediation-2026-07-11.md)

> **Contract note (2026-07-14):** the references to backup and restore in this plan describe the
> implementation audited on 2026-07-12. The current contract uses incremental LIFO checkpoints,
> preserves later turns, and may compact automatically on estimated context pressure. See
> [Context Compaction](../../README.md#-context-compaction).

### Goal

Fix and verify the problems found in the Thorn/Lyra playtest without pulling in the private task
backlog. The file `01-real-playtest-remediation-2026-07-11.md` stays unchanged as the original
evidence. At the end, a traceable report will be produced, with changes, tests, playtest results
and residual risks.

### Confirmed baseline

On 2026-07-12, the non-LLM suite passed with:

```text
101 passed, 5 deselected
```

The five excluded tests are marked `llm`. Inspecting the current code confirmed:

| ID | Report finding | Current state |
|---|---|---|
| B1 | `location` ends up in `physical_facts` | Active in `Runner._update_scene` |
| B2 | compaction notes may use incompatible keys | Active; the schema accepts any key and there is no normalisation |
| B3 | an LLM error may be logged as an empty string | Active; the log uses only `str(e)` |
| B4 | a forced speaker may receive another character's context | Active; the override happens after the Narrator call |
| B5 | the log records neither the payload nor `force_speaker` | Active; replay still has to infer that data |
| B6 | pytest uses the real sessions directory | Already fixed by `ROLEPLAY_DATA_DIR` and regression tests |

The report's qualitative behaviours remain possible because they depend mainly on the prompts and
the model: physical facts with no stable identity, excessive mood churn, inventions promoted to
canon, repetition, description of the characters' minds, missing consequence and language defects.
The relationship between context size and timeout remains unproven.

### Scope limits

- Do not implement items from the private backlog, including a grammar-correction agent, automatic
  compaction, RAG, internationalisation or README media.
- Do not alter or rewrite `01-real-playtest-remediation-2026-07-11.md`.
- Do not commit, push or perform any other git mutation.
- Do not use, clean or modify real sessions in `.data/` during tests or playtests.
- Do not declare a qualitative problem resolved merely because a prompt was changed.
- Do not change the timeout or the compaction policy based only on the original playtest's
  correlation.

### Rules for autonomous execution

1. Preserve the user's pre-existing changes and limit the diff to the files needed for this plan's
   findings.
2. Use a temporary `ROLEPLAY_DATA_DIR` for all validation. Before and after the full suite, compare
   the inventory/hash of `.data/` to prove the real data did not change.
3. Keep compatibility with old sessions and logs. New log fields will be additive, and replay will
   continue accepting logs without the new turn marker.
4. When the local LLM server is unavailable, complete every deterministic fix and verification and
   mark only the real playtest as `BLOCKED`, with evidence of the attempt.
5. Classify each finding in the final report as `RESOLVED`, `MITIGATED`, `NOT REPRODUCED`,
   `BLOCKED` or `DEFERRED`, always with a justification and evidence.

### Phase 1 — Fix the scene state (B1 and fragile physical facts)

#### Implementation

- Make `location` and `time_of_day` reserved keys of `scene_update` in the Narrator's
  prompt/schema; they represent `Scene` fields, never physical facts.
- In `Runner._update_scene`, apply those keys directly to `game.scene.location` and
  `game.scene.time_of_day`.
- When the location actually changes, clear physical facts belonging to the previous scene before
  applying the remaining delta. That stops the tavern's doors, lighting and objects from surviving
  into the tower.
- Preserve the delta behaviour for the other fields: a `None` value removes the key and a string
  creates/updates the fact.
- Do not let `None` erase the mandatory `location` or `time_of_day` fields.
- Strengthen the prompt to reuse a stable `snake_case` key for the same fact and avoid simultaneous
  synonyms such as `weather`/`weather_outside`.

#### Verification

- Test a location change, a time change, a fact removal, an update in the same location, and the
  clearing of old facts on a location switch.
- Test that `physical_facts` never contains `location` or `time_of_day` after application.
- Test persistence, reload and undo after a location switch.
- Verify that the UI re-reads the state and shows the new location within the same turn.

#### Acceptance criterion

A response equivalent to `{"location": "The Old Watchtower", "door": "ajar"}` leaves
`Scene.location == "The Old Watchtower"`, contains only the relevant door in `physical_facts`, and
can be correctly reverted by undo.

### Phase 2 — Make compaction notes usable (B2)

#### Implementation

- Build the Historian's schema with the session's real IDs as the only accepted properties of
  `character_notes`; the properties stay optional, because only changed notes should come back.
- Change how characters are presented in the prompt so that ID and name are unambiguously
  separated.
- Normalise the response defensively before the merge:
  - accept the exact canonical key (`C1`);
  - recover observed formats such as `C1 — Thorn`, without confusing `C1` with `C10`;
  - ignore unknown keys;
  - if a canonical key and an alias coexist, the canonical one wins.
- Keep compatibility with already-saved notes. Do not migrate or delete old data automatically;
  only new compactions produce the canonical map.

#### Verification

- Cover exact keys, the alias observed in the playtest, an unknown ID, ambiguous prefixes and a
  collision between the canonical key and an alias.
- Run an integrated `compact -> save -> reload -> call character` test and assert that only the
  character's own note reaches their prompt.
- Confirm that no other character's note is leaked.

#### Acceptance criterion

A Historian output with `"C1 — Thorn"` results in `game.character_notes["C1"]`, and that note
appears in Thorn's later call without appearing in Lyra's.

### Phase 3 — Fix routing and exact replay (B4 and B5)

#### Forced-speaker implementation

- Validate `force_speaker` right after loading the session, before calling the Narrator.
- Pass the valid override to the Narrator as an internal routing constraint, with no mention of a
  player or an interface.
- When a character is forced, restrict `next_speaker` to that ID and require
  `context_for_character` to be filtered specifically for them.
- When `Narrator` is forced, require empty context and do not call a Character.
- Invalid overrides remain equivalent to `Auto`.

#### Turn-log implementation

- Add an append-only `turn_input` marker before the turn's first LLM call, containing
  `turn_number`, `speech`, `action`, the requested `force_speaker` value and the validated
  effective value.
- Keep that marker out of the prompts and the fictional state; it exists only in the debug log.
- Make the replay driver prefer `turn_input` for exact reconstruction, keeping the current
  inference as a fallback for legacy logs.
- Ensure tape loaders ignore the marker as an LLM response.

#### Verification

- Simulate the Narrator choosing C1 while C2 is forced, and prove that the context C2 received was
  created for C2.
- Cover overrides to the controlled character, to an NPC, to `Narrator`, to an invalid value and to
  none.
- Cover log ordering, a first-call failure, and a retry without consuming markers as replay
  outputs.
- Reconstruct a small session using only the new log, with no auxiliary backup and no `HISTORY`
  heuristic.

#### Acceptance criterion

No Character receives context intended for another ID, and the log alone contains enough data to
repeat each turn call and its override exactly.

### Phase 4 — Improve observability and investigate the final retries (B3)

#### Implementation

- Preserve the textual `error` field for compatibility, but use `str(e) or repr(e)` so an empty
  message is never written.
- Add structured fields: exception type, `repr`, attempt duration, attempt number and approximate
  prompt size.
- Record the same duration/size fields on successful calls, to allow comparison.
- Add a timeout option to the configuration, only to make it explicit and adjustable; keep the
  current default behaviour until there is measurement justifying another value.

#### Verification

- Force an `httpx.ReadTimeout` with an empty text representation and check that the type and `repr`
  are available in the JSONL.
- Cover an HTTP status error, invalid JSON followed by a retry, and success on the second attempt.
- Confirm the new fields do not break the UI, the MCP, the replay loader or old logs.

#### Evidence-based decision

After the instrumentation, repeat the 20-turn script in temporary storage:

- if `ReadTimeout` is confirmed, record the latency and prompt size and adjust only the timeout
  configuration needed for the environment tested;
- if the failure is schema/JSON or transport, fix the observed cause and add a regression;
- if there is no reproduction, do not invent a performance fix; classify it as `NOT REPRODUCED` and
  keep the new telemetry.

Automatic compaction stays out of scope, because the report did not prove it is the solution.

### Phase 5 — Reduce agent fragility

These items get prompt/validation fixes and a comparative evaluation. They will not be marked
`MITIGATED` without a measurable failure rate of zero over a sufficient sample.

#### Narrator

- Require a concrete consequence for the last action before adding atmosphere or opening another
  narrative thread.
- Forbid asserting thoughts, intentions or internal emotions as fact; use only observable signals,
  explicitly provided perception, or speech/thought already present in the history.
- Treat mood as persistent state: emit `mood_updates` only after a significant emotional change,
  not for synonyms of pose or momentary disposition.
- Make explicit the difference between canonical fact, a character's claim, and an attempted
  action.

#### Character

- Reinforce that knowledge, notes and context are the only sources of facts; missing information
  must be omitted or presented as doubt, never as invented past.
- Ask for a brief review before answering, and forbid literal repetition of a recent sentence by
  the character themselves.

#### Historian

- Include `content_type` alongside every event handed to compaction.
- Treat dialogue as an attributed claim and a character's action as an attempt until the Narrator
  confirms it; preserve uncertainty in the summary instead of promoting it to canon.
- Explicitly preserve open threads, unknown identities and unconfirmed facts.

#### Language and punctuation

- Remove the U+2014/U+2013 characters themselves from the prompts' instructions and separators,
  using names/codes or ASCII separators.
- Keep the raw log with the model's real response, but normalise those two characters in the
  persisted/displayed output, to guarantee the rule the product already states.
- Do not build the optional grammar-correction agent. Other language errors will be measured in the
  playtest and reported as residual risk if they persist.

#### Verification

- Prompt tests prove the rules are present and that events are marked with their provenance.
- Deterministic tests prove punctuation normalisation without altering the raw log.
- An evaluation of the same script counts: mood updates, literal repetition, mind assertions,
  unsupported facts, actions without consequence and language defects.

### Phase 6 — Close the original playtest's coverage gaps

- Run at least one turn after the compaction and verify the use of `story_summary` and of the
  Character's canonical note.
- Deliberately exercise an override that differs from the Narrator's free choice.
- Exercise `undo`, `restore_compaction` and `suggest` in temporary storage.
- Confirm that no prompt contains the internal `Player` marker.
- Confirm the compaction window counts, and that backups/restores remain intact.
- If the real LLM is unavailable, run deterministic/replay equivalents and separate that evidence
  from live validation in the final report.

### Phase 7 — Final technical validation

Run, in this order:

```bash
uvx ruff check .
uvx ruff format --check .
uvx mypy .
uvx pytest
```

Then:

- run the `llm` tests only if the local endpoint is healthy;
- repeat the isolated playtest described above;
- compare `.data/` hashes/inventory before and after;
- review the diff for scope, compatibility, locks, atomicity and error paths;
- check every ID B1-B6 and every qualitative behaviour against concrete evidence.

### The mandatory final report

Create `01-real-playtest-remediation-2026-07-11.md` with:

1. an executive summary;
2. the hash/base commit analysed and the diff's scope;
3. a matrix of every finding from `01-real-playtest-remediation-2026-07-11.md`, with status, files
   changed, tests and evidence;
4. complete results from Ruff, the format check, mypy and pytest;
5. the real playtest's result, or a verifiable reason for the blockage;
6. a quantitative comparison of the original playtest versus the new one;
7. proof that the real `.data/` was not altered;
8. residual risks, mitigated items, and items requiring a human decision;
9. an explicit list of any step of this plan that was not completed.

The report must not call prompt changes a "resolution" without an evaluation, and must not hide
failures, skips or unavailable validations.

### Definition of done

The work is done when:

- B1-B5 have automated regressions and corrected behaviour;
- B6 has been revalidated without any modification of the real data;
- every qualitative fragility has evidence of mitigation or a declared residual risk;
- the deterministic suite is green;
- the real playtest is complete, or formally marked blocked by endpoint unavailability, without
  preventing the other deliverables;
- `01-real-playtest-remediation-2026-07-11.md` allows a finding-by-finding audit.


## Part III — Verified closure of the six objective defects

> **Merge note.** This part was originally a separate file. References to
> `01-real-playtest-remediation-2026-07-11.md` inside it mean the ORIGINAL findings
> report (now Part I) when cited as source, and the final remediation report (now
> Part III) when cited as planned output - the merge renamed all three to this
> article's filename.


**Date:** 2026-07-12

**Sole source:** [`01-real-playtest-remediation-2026-07-11.md`](./01-real-playtest-remediation-2026-07-11.md)

**Result:** the six objective bugs were fixed and verified; the qualitative problems were
mitigated, but remain model-dependent.

> **Contract note (2026-07-14):** the results below remain historical evidence of the 2026-07-12
> runtime. Compaction today uses measured SSE progress, an opt-in automatic trigger, and
> incremental LIFO checkpoints that preserve later turns. See
> [Context Compaction](../../README.md#-context-compaction).

### Result per finding

| ID | Original finding | State | Evidence |
|---|---|---|---|
| B1 | `location` written into `physical_facts` | **RESOLVED** | `Runner._update_scene` treats `location` and `time_of_day` as reserved fields, clears the previous location's facts and preserves undo. Tests cover the switch, persistence, removal and restore. In the final playtest, opening the door changed the location to `Outside Old Mork's Tavern, alleyway`. |
| B2 | compaction notes with unusable IDs | **RESOLVED** | The schema accepts only the session's IDs, the response is filtered by canonical IDs, and the prompt separates ID/name. The playtest produced `C1` and `C2` notes; Lyra's note appeared in the post-compaction turn's prompt. |
| B3 | LLM errors recorded as an empty string | **RESOLVED** | The JSONL now records `str(e) or repr(e)`, `error_type`, `error_repr`, the duration, the attempt and the prompt size. Structured JSON errors are also recorded and excluded from the tape. The timeout is configurable, defaulting to 60 s. |
| B4 | `force_speaker` could reuse another character's context | **RESOLVED** | The override is validated before the Narrator and restricts schema/prompt to the effective ID; `Narrator` forces empty context. Tests and the playtest covered `C2`, `Narrator`, invalid and automatic. |
| B5 | log without payload/override, preventing exact replay | **RESOLVED (current format)** | Every turn writes `turn_input` before the first call, with speech, thought, action, and the requested and effective override. Replay requires those markers and does not try to infer old logs. That decision follows the guidance not to create a legacy compatibility layer. |
| B6 | tests altered the real `.data` | **RESOLVED** | `tests/conftest.py` sets a temporary `ROLEPLAY_DATA_DIR` before the imports and refuses the real directory or its descendants. The hash and file count of `.data` stayed identical throughout the final validation. |

### Qualitative mitigations

- The Narrator was given rules to resolve the immediate consequence first, avoid mind-reading,
  preserve uncertainty, stabilise moods and reuse physical keys.
- The Character limits its sources of facts, forbids repeating a recent sentence in full, and asks
  for a short grammatical review.
- The Historian receives `TYPE`, distinguishes a claim/attempt from a confirmed fact, and uses a
  closed schema.
- Generated responses normalise U+2014/U+2013 only after the raw log. In the final playtest there
  was 1 em dash in the raw response and 0 in the persisted content.

These items are **MITIGATED**, not declared eliminated: invention, repetition, grammar, mood churn
and narrative quality remain probabilistic. A short playtest does not replace a statistical
evaluation, nor does it repeat the original 20 turns.

### Validation performed

- `uvx ruff check .`: passed.
- `uvx ruff format --check .`: passed, 26 files already formatted.
- `uvx mypy src/`: passed, 14 modules with no errors.
- `uv run pytest -x`: **116 passed, 5 deselected**.
- `uv run pytest -m llm -x`: **5 passed, 116 deselected**, using local Gemma 4.
- `node --check src/static/app.js` and `src/static/api.js`: passed.
- Isolated real playtest in `/tmp/roleplay-report-live-ayqs4vpq`: 5 turns, 10 LLM attempts, 0
  errors, 3 suggestions, a compaction, a post-compaction turn, an undo, a safe refusal to restore
  with a new turn present, and a successful restore after the undo.
- No playtest prompt contained `SPEAKER=Player`.
- `.data`: 38 files and aggregate hash
  `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f` before and after.

The seven timeouts/retries from turns 14–20 of the original report did not reappear in the five LLM
tests or in the final playtest. So observability was fixed, but there is no evidence to change the
default timeout or to introduce automatic compaction.

### Additional fixes found on resuming

After updating to the new `HEAD`, the review found three regressions outside the original findings,
but blocking for the project's health:

- multi-exception syntax incompatible with MyPy in `src/store/presets.py` and
  `src/store/sessions.py`;
- a disordered local import, a long comment and a missing type on the bootstrap endpoint in
  `src/main.py`.

They were fixed and are included in the validations above.

### Out of scope and residual risks

- `01-real-playtest-remediation-2026-07-11.md` stayed unchanged as the original evidence.
- The Android/Docker work was not altered. There is a potential incompatibility to watch in the
  APK: Gradle pins Python 3.11, FastAPI 0.99 and Pydantic 1, while the project declares Python
  3.14+ and FastAPI 0.115+.
- The playtest directory in `/tmp` was preserved for inspection.
- No commit, push or other Git mutation was performed by this remediation.


## Part IV — Post-remediation live exploration (20 turns, compaction, restore, undo)

**Date:** 2026-07-12
**Scope:** 20 turns of the Thorn/Lyra script, a suggestion, two compactions with a restore between
them, a post-compaction turn and an undo
**Model:** Gemma 4 26B A4B QAT, served by local llama.cpp
**Isolated storage:** `/tmp/roleplay-report-playtest.DmyEbG`
**Session:** `89c21c6c`

> **Contract note (2026-07-14):** this playtest records the backup/restore that existed on the date
> of execution. The current runtime replaced that format with incremental LIFO checkpoints, keeps
> the checkpoints until the session is deleted, and preserves later turns during an undo. See
> [Context Compaction](../../README.md#-context-compaction).

### Artifacts

- Structured result: `/tmp/roleplay-report-playtest.DmyEbG/playtest-results.json`
- Final state: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.json`
- Pre-compaction backup: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.kb_0.json`
- Raw log: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.debug.jsonl`
- Script: the project's private manual playtest script

### Execution summary

| Metric | Result |
|---|---:|
| Main turns | 20 |
| Post-compaction turns | 1 |
| LLM records | 40 |
| Successes | 40 |
| Errors/retries | 0 |
| Narrator calls | 21 |
| Character/Lyra calls | 16 |
| Historian calls | 2 |
| Suggest calls | 1 |
| Largest prompt | 32,550 characters |
| Longest call | 10,582 ms |
| Records before compaction | 75 |
| Records removed/kept | 45 / 30 |
| `turn_input` markers | 21 |

The Narrator's prompt grew from 4,066 characters on turn 1 to 32,550 on turn 20. Even so, every
call finished on the first attempt. The longest duration, 10.6 seconds, sat far below both the
playtest's timeout (90 s) and the product default (60 s). The retries observed from turn 14 onward
in the original playtest did not reappear.

### Objective bugs

#### 1. `physical_facts` can become a key containing serialised JSON

**Observed severity:** high, for state integrity.

On turn 20, the Narrator returned:

```json
{
  "location": "Watchtower Base",
  "physical_facts": "{\"atmosphere\": \"stifling, vibrating, and freezing\", \"dust\": \"falling ash-like particles\", \"scent\": \"cloying, rotting lilies\"}"
}
```

The state persisted, literally:

```json
{
  "atmosphere": "stifling, vibrating, and freezing",
  "physical_facts": "{\"atmosphere\": ...}"
}
```

So `dust` and `scent` did not become queryable facts on turn 20; the container appeared inside
itself as a string. On turn 21 the model went back to emitting both keys flat, but the incorrectly
serialised key remained beside them.

The shape is accepted because `scene_update.additionalProperties` allows any key with a string/null
value (`src/agents/narrator.py:79-86`). The runner copies every key other than `location` or
`time_of_day` straight into `game.scene.physical_facts` (`src/runner.py:514-520`).

#### 2. Dash normalisation causes a false location change

**Observed severity:** medium; there was a real mutation, with no loss in this case.

The preset started at `Old Mork's Tavern — main hall, dim lighting`. On turn 1, the raw output
repeated that location exactly. Before the state was applied, normalisation converted the dash into
a comma (`src/agents/narrator.py:298-303` and `src/llm/client.py:32-34`).

The runner compared the normalised string against the original, read the punctuation difference as
a location change, and ran `physical_facts.clear()` (`src/runner.py:503-508`). No fact was lost,
because the model also repeated the lighting, the audience, the weather and the door in that
output. The state, however, changed the location's name and walked the scene-transition path
without the scene having changed semantically.

#### 3. The Character performs/describes physical action in every observed response

**Observed severity:** high, relative to the documented role model.

`AGENTS.md` states that a Character may only speak and think, never perform or describe physical
action, their own or anyone else's. Across the 20 turns there were 15 Lyra responses, and all of
them included her own physical action or description. The post-compaction response repeated the
pattern.

Examples:

- turn 2: `I say, leaning closer to the pulsing metal`;
- turn 8: `I mutter, frantically stuffing my scrolls into my satchel`;
- turn 14: `my fingers trembling slightly as I pull a minor illumination stone from my belt`;
- turn 19: `I stammer, my eyes wide as I stare at the vibrating wall`.

The formatter's own docstring confirms that only dialogue should reach the Character, because only
the Narrator narrates/describes/acts (`src/agents/character.py:47-52`). The prompt forbids
narrating actions as fact, but also asks for first person and dialogue only
(`src/agents/character.py:20-36`). The free-text output has no subsequent validation separating
speech, thought and action.

#### 4. The location changed with no narrative transition on turn 17

**Observed severity:** medium.

On turn 16 the state was at `Watchtower Interior`. On turn 17, Thorn stated the plan for dawn, put
away the dispatch and searched the room for supplies. The narration had already started calling the
setting the `tower base`, and `scene_update.location` changed to `Watchtower Base`, with no exit,
descent or other spatial transition described.

The change also cleared `light_level`, since every location switch discards the previous scene's
facts. The new state retained only `atmosphere`.

### Qualitative fragilities reproduced

#### The second-person point of view implicitly switches to Lyra

Nine of the 21 narrations contain `you`/`your` while Thorn is described in the third person. In
several cases, the second person can only be Lyra:

- turn 18: `The illumination stone in your hand ... as your hands shake`, while Thorn has his ear
  against the wall and the stone belongs to Lyra;
- turn 19: `your pale blue light`;
- turn 20: `your illumination stone`;
- turn 21: `your fingers ... around the staff`.

There was no leak of the word `Player`, but the narration shown to the human controlling Thorn
shifts focus to Lyra's body and objects without marking the change of point of view.

#### Immediate consequences can still be deferred

- turn 6: Thorn orders Mork to bar the door. Mork pauses with the cloth in his hand but does not bar
  the door; `door` stays `closed` only because it already was in the preset;
- turn 19: Thorn counts down and orders Lyra to break the ward. The narration swaps the scratching
  sound for banging and Lyra says she is ready, but the ward is not broken;
- turn 20 moves on to the map without resolving the ward or what is behind the wall.

The rule to resolve the consequence before widening the atmosphere exists in the Narrator's prompt,
but both patterns from the original report reappeared.

#### The Character still invents an absent origin

On turn 5, Lyra answers `We found it tucked away in a ruin`. Her knowledge contains only that the
medallion was found and gives off a faint aura; the script, the state and the turn's context supply
no ruin. It is the same kind of invention observed in the original playtest.

Neither compaction promoted the ruin into the summary, a sign the Historian's provenance rules
worked better than in the original report.

#### The Narrator still asserts internal states

Examples observed:

- turn 5: `desperate, piercing intensity`;
- turn 17: `grim, mechanical purpose` and `his focus remaining on the task`;
- turn 20: `Thorn ignores it, his focus entirely consumed by the paper`.

These passages attribute emotion, purpose or internal focus, despite the rule to describe only
observable evidence.

#### Redundant mood updates

The Narrator emitted eight mood-update objects. Three did not change the persisted value:

- turn 10: C2 `anxious` to `anxious`;
- turn 14: C2 `anxious` to `anxious`;
- turn 19: C2 `terrified` to `terrified`.

There were five real transitions: C1 to `determined`, C2 to `anxious`, C1 to `devastated`, C1 back
to `determined` and C2 to `terrified`. The frequency is far lower than the original report's 18
updates across 20 turns, but the instruction to omit characters with no change is still not
consistently obeyed.

### Behaviours confirmed correct

- No prompt contains `Player` or `SPEAKER=Player`.
- All 21 requested overrides were recorded and correctly validated in `turn_input`.
- All 40 calls have metrics and `attempt_number=1`; there was no empty error and no retry.
- Real location changes cleared the previous scene's facts: the tavern, the corridor, the alleyway,
  the streets and the tower did not leak doors/weather/lighting into one another.
- The compaction notes used only `C1` and `C2`.
- Turn 21 received `STORY SO FAR`, Lyra's canonical note, and only her own note.
- Lyra was able to list the medallion, the dispatch and the forest after the compaction.
- The first compaction removed 45 records and kept 30, corresponding exactly to the eight turns
  13-20 of this run.
- The restore recovered the previous 75 records; a new compaction brought it back to 30.
- The undo of turn 21 restored the history, the scene and the moods of the post-compaction state.
- No complete sentence was repeated literally between narrations or between Lyra's responses.
- The raw log contains one em dash (in turn 1's location); the persisted generated content was
  normalised with no em/en dash.
- The real `.data` directory stayed at 38 files and aggregate hash
  `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f`.

### Observations not classified as bugs

Compacting, restoring and compacting the same state again produced two semantically close but not
identical summaries. The notes were also reworded. The behaviour is consistent with generation at
temperature 1.0, but it demonstrates that repeated compaction is not semantically idempotent even
when the input state is identical.

None of the five turns with automatic routing chose C1, the controlled character. That branch's
agency lock remains covered by earlier tests and playtests, but it was not exercised live in this
particular run.

### Open Questions

- Should the narration always stay in the third person, or is there an intent to allow second
  person directed at a character who is not the controlled one?
- Should `physical_facts` be treated as a reserved container name in the schema/delta, or is its
  literal use as a fact considered valid?
- Is the variation between two compactions of the same state acceptable for the restore/retry flow,
  or should it be treated only as an observable characteristic of the model?
