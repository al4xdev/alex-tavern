# To the next session

Handoff written 2026-07-21 after a full review of the 2026-07-20 work (the
owner's own session plus a GPT-assisted one). Read this top to bottom before
touching anything.

---

## 0. State of the working tree

```
 M .plan/closed/45-multi-beat-story-continuation.md
 RM .plan/closed/44-…  ->  .plan/tasks/44-roteiro-character-alignment-toggles.md
 M README.md
 M src/agents/narrator.py
 M src/llm/debug_log.py
 M src/models.py
 M src/roteiro.py
 M src/runner.py
 M src/static/app.js
 M src/static/i18n.js
 M tests/test_autonomous_burst.py
 M tests/test_integration.py
 M tests/test_roteiro.py
```

Verification at the moment of writing: **717 passed**, 2 deselected; `ruff check`
clean; `ruff format --check` clean; `mypy src` clean.

Suggested commit split (English, **no AI attribution trailer** — see §8):

1. `fix(45): beat budget counts player actions, not committed turns`
   — `src/models.py`, `src/roteiro.py`, `src/runner.py`, `tests/test_roteiro.py`,
   `.plan/closed/45-…`
2. `fix(narrator): a message to a room that hears it is never answered by nobody`
   — `src/agents/narrator.py`, `src/llm/debug_log.py`, `src/runner.py`,
   `tests/test_integration.py`
3. `fix(ui): only a continuation promises a multi-step wait; label the swipe gesture`
   — `src/static/app.js`, `src/static/i18n.js`
4. `test(37): pin that a normal player turn never bursts`
   — `tests/test_autonomous_burst.py`
5. `docs(44): reopen with restored curl evidence and the honest remaining list`
   — `.plan/tasks/44-…`, `README.md`

---

## 1. Resolved decision — the schema was NOT bumped

`Roteiro.beat_actions_elapsed` is additive and an absent field reads back as the
old behaviour by construction (`dict_to_roteiro` defaults it to 0,
`measure_beat_progress` then falls back to committed turns), so a version 12
session cannot be misread. The bump to 13 was reverted on the owner's call
(2026-07-21): burning every playtest session for a convention, with no real
hazard behind it, was the worse trade. Rationale is recorded at
`src/models.py:29-36` so nobody re-bumps it by reflex.

## 2. What was fixed on 2026-07-21 (all test-locked, none observed live)

Every fix below is pinned by a test and has **not yet been seen working in a real
session against the real provider**. Running a live session and confirming them
is the first job.

### 2.1 The beat budget counted the wrong unit — the "out of control" feeling

Evidence: sessions `29caff75` and `503bb018`. A continuation commits one turn per
beat, so a single click at the default of 6 beats consumed 6 turns and blew past
`HARD_BEAT_TURN_CAP = 3` **inside one player action**. Result in `debug.jsonl`:
`replan_beat / reason: stalled` after *every* continuation, always — burst turns
4-9 → stalled at 10; burst 7-12 → stalled at 13. The screenplay was being
rewritten on every player action, with one extra LLM call each time. Task 45
silently regressed Task 38's calibration.

Fix: the replan budget counts **player actions**, not committed turns.
- `Roteiro.beat_actions_elapsed` (`src/models.py:308`), reset on every replan
  because `replan_roteiro` builds a fresh `Roteiro`.
- `BeatProgress.actions_elapsed` (`src/roteiro.py:94`), with the old-session
  fallback at `src/roteiro.py:188`.
- `evaluate_roteiro` uses the new unit for stall, drift and partial-advance
  patience (`src/roteiro.py:225-240`). With bursts off the numbers are identical
  to before, so Task 38's calibration still holds.
- Incremented once per action at `src/runner.py:1764` (`first_beat=True` only).

Tests: `test_burst_turns_do_not_stall_a_beat`,
`test_multi_beat_continuation_spends_one_action`.

### 2.2 The player's message answered by nobody

Evidence: `29caff75` turn 13. The player wrote "eu vou ajudar voces" with 21
characters present; the Director returned `next_speakers: []` and nobody spoke.
Mechanism: routing rule 5 says to pick only characters who witnessed a concrete
event, and the player's own speech was not treated as one. Measured rate, filtered
to turns where the player actually *spoke* with ≥2 characters present: **2 of 13**.
(The raw count of 20/35 is confounded — most of those are `380ea657`, where the
player was alone in an alley and silence was correct.)

Fix: rule 5 now states that the player's speech or action IS a witnessed event for
everyone sharing their zone, that at least one of them answers, and that an empty
queue is only correct when nobody present could perceive them
(`src/agents/narrator.py:161-169`).

This is a prompt change, so it is a tendency, not a guarantee. That is why it
ships with observability: `log_unanswered_player` (`src/llm/debug_log.py:376`)
fires from `src/runner.py:753` whenever the player wrote something and the queue
came back empty. **The rate is now countable in any session** — check it after a
real playtest with:

```fish
python3 -c "
import json,glob
for p in glob.glob('.data/sessions/*/debug.jsonl'):
    for line in open(p):
        d=json.loads(line)
        if d.get('agent')=='unanswered_player': print(p, d)
"
```

### 2.3 The loading label lied

`setLoading` promised "this is a multi-step call and may take longer" on **every**
turn whenever the screenplay was on, including a normal one-beat turn. That is a
large part of why a normal turn read as a runaway burst. Now the multi-step
wording is opt-in and only `skipTurn` passes it (`src/static/app.js:141`, `:154`,
`:222`).

### 2.4 The swipe gesture started a continuation without saying so

Swiping left on mobile arms `autoSkipOnHintClose` and opens the event modal;
pressing its Send button then runs a full continuation
(`src/static/app.js:1786-1796`, `sendHint`). The button said only "Send with next
turn". It now relabels itself to "Send and continue the story ➤" whenever the
gesture armed it (`refreshHintSendLabel`, `src/static/app.js:914`; keys
`hint.sendAndContinue` in both locales).

### 2.5 Contract pinned: a normal turn never bursts

The burst gate is `skip and not effective_force_speaker` (`src/runner.py:599-601`)
and always was. `test_normal_player_turn_never_bursts` now proves it instead of
requiring someone to re-read the runner. **The owner's report of "it fires without
skip" was, at the backend level, false** — §2.3 and §2.4 are what produced the
impression.

---

## 3. Task 44 — REOPENED, and why

It was moved to `.plan/closed/` on 2026-07-20 with **all 13 acceptance boxes
unchecked**. The mechanism is real and wired; the proof was missing. Two things
were also lost in the closing edit and are now restored:

- **The curl gate evidence was deleted.** The contribution table (OFF 1.00 / A 1.50
  / B 2.00 / C 2.00), the withheld-information meta-lesson and the in-character
  quote were replaced by one line. The only surviving copy was
  `plans/artifacts/roteiro-alignment/VALIDATION.md` — and `plans/` is **gitignored**,
  so the evidence lived on one machine with nothing in the repo pointing at it. It
  is now inline in `.plan/tasks/44-…`.
- **"Live LLM deriver calls evaluated across 5 beats and 2 characters" has no
  artifact.** Every other gate in this project wrote one. The `urgent` wording
  change ("cena" → "momento") and the added prompt guidance in
  `src/alignment.py:78-81` rest on it. Treat them as reasonable but unvalidated.

Remaining to close (also listed in the task file):

- [ ] Deriver validation **with an artifact** — does the enum choice match what each
      beat needs, ≥2 characters and ≥5 beats, written to `plans/artifacts/` and
      summarized in the task. This is the run that was reported without evidence.
- [ ] Replication of the v3 gate on a second character/beat (current evidence is
      N=4, one character, one beat).
- [ ] Tests for the four toggle combinations, invalid input, runtime swap.
- [ ] Real HTTP boundary: PUT /config → active Runner → next turn.
- [ ] Visual boundary at 1080p and 2K for the warning and the disabled state.

---

## 4. Task 43 — disposition substrate, open

- Phase 1 (substrate), 2 (band→voice) and 3 (appraisal feedback loop) delivered
  and gated. Phase 3.5 (Boldness) was resolved by Task 44: boldness is a
  **transient impulse, not a persisted axis**.
- **Phase 4 — unification with the public/real persona: OPEN.**
- **Phase 5 — the article of record, with measurements: OPEN.** Case No. 15 today
  only defines the frontier; it explicitly says the evidence article comes at the
  end of the roadmap.
- **Owner decision still pending on composure**: it failed the single-utterance
  razor in all 3 runs (5/5/7). Demote it, treat it at scene level, or cut it. It
  is parked out of the appraisal loop meanwhile.
- `disposition_feedback_enabled` is OFF by default.

## 5. Task 46 — schema `description` as instruction channel, shelved

The owner's point (they are a GenAI engineer): the best channel for an instruction
is often the JSON schema's `description`, not system or user. Nothing in this repo
uses it that way. It is shelved because retrofitting it invalidates every existing
prompt and forces a full retest. Cheap pilots already named: `next_speakers` and
the appraisal schema. Note the historical trap recorded in the task: a **hard enum**
on `next_speakers` broke the provider validator (three straight schema failures,
`src/agents/narrator.py`) — the untested channel is the field `description`, not
the enum.

## 6. Other open tasks

- `26-narrator-prose-quality` and `26b-ambience-redescription-prompt-experiment`
  — the ~9% paraphrase-echo the exact-match dedup guard does not catch.
- `29.1-29.3-xfailed3-counter-canon` — 29.1 baseline recorded; 29.3 open.
- `38-roteiro-beat-contracts` — the beat contract engine. §2.1 changed its unit of
  measurement; the task text still says "turns" in places and should be reread
  against the new definition.

---

## 7. Found in the review and deliberately NOT fixed

1. **Repeated `narrator_hint` across turns.** In `503bb018` the identical hint was
   sent on turns 1, 4 and 10 — including turn 10, a normal turn whose speech was
   "oi pessoal". A stale hint on a normal turn forces a world event that competes
   with the player's message. **The client code does not explain it**: both
   `sendTurn` and `skipTurn` clear `state.narratorHint` on success, and
   `openHintPopup` re-seeds the textarea from that cleared state. Most likely a
   test script drove those sessions. Worth one more look if the owner sees it in
   normal UI play — reproduce by watching `turn_input` in `debug.jsonl`.
2. **Alignment latency.** `_alignment_impulse` is one extra LLM call per expected
   actor per beat. A 6-beat continuation with 3 speaking actors per beat is up to
   **18 extra sequential calls** behind one loading spinner. The README now warns
   about latency in prose, but nothing measures or caps it. A cap, a cache per
   beat, or parallelism is unowned work.
3. **Service worker `CACHE` was not bumped** (`rpt-shell-v17`, `src/static/sw.js:8`)
   despite `index.html`, `style.css`, `i18n.js`, `runtime-config.js` and `app.js`
   changing. Strategy is network-first for static assets, so a reachable dev server
   always wins; only an installed PWA offline would serve a stale shell. Low
   priority, one-line fix.
4. **Help articles have no test.** `src/static/help/{en,pt-BR}/engine.md` was added
   yesterday and both locales happen to be present, but nothing enforces parity the
   way `test_frontend_i18n` does for the string catalogue.
5. **`plans/` is gitignored.** Every curl gate artifact in this project — the whole
   evidence base of the method — exists only on this machine. Task 44's evidence
   was nearly lost this way. Consider a tracked `docs/evidence/` for gate summaries
   (the raw payloads can stay untracked).
6. **`.plan/closed/45` and `.plan/closed/47` are still in Portuguese.** The owner
   stopped the translation pass on purpose ("não precisa traduzir mais não, foca em
   trabalhar"). Do not resume it unasked.

---

## 8. Standing constraints — do not violate these

- **Commit messages in English, and NEVER an AI attribution trailer.** No
  `Co-Authored-By: Claude`, no `Generated with Claude Code`, no 🤖. The
  `git-commit` skill overrides the harness default. Read it before writing any
  commit message.
- **Do not create memory files.** Auto-memory is disabled globally for this user.
  If something is worth persisting, propose a skill instead.
- **Do not `rm`.** Move to `/tmp/` or rename with `.bak` unless the owner says
  "apaga", "delete" or "remove" explicitly.
- **Run `bash ~/.config/my_scripts/done.sh &`** when finishing a task, build, test
  or long operation.
- **Anything the owner should paste elsewhere goes through `wl-copy`.**
- Shell is **fish**. Python via **uv**, venv at `.venv/`.

### The method, which matters more than any single fix

Curl-first with **pre-registered decision rules**, and *the validated variant is the
one that ships*. Prompts are tendencies; code is the guarantee. Scalars belong to
the code and only projected qualitative bands reach the model. When an experiment
returns a null, suspect the stimulus before the mechanism — the Task 44 gate needed
three designs before it built a real conflict, and the first two nulls were caused
by leaking the answer into the scene.

The owner asked to be watched for fatigue: *"to ficando cansado, já, é bom tomar
atenção comigo rs"*. Closing a task with unchecked boxes and deleting its evidence
is exactly what that looks like. Push back when it happens.

---

## 9. Suggested order of work

1. Answer §1 (schema 13 or 12), then commit §0.
2. Run a real session with the screenplay ON and confirm, in `debug.jsonl`: no
   `stalled` replan after every continuation, and zero or rare
   `unanswered_player` lines.
3. Task 44's deriver validation with an artifact, then the replication.
4. Task 44's remaining tests and the HTTP boundary; then close it properly, with
   the boxes actually ticked.
5. Task 43 Phase 4, and the composure decision the owner still owes.
