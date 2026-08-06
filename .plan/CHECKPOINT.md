# Checkpoint — 2026-08-06, branch `fogo-baixo`

Hand-off for the next session. Written because the owner is moving machines; the
working tree syncs over SSH, so `.data/` (provider key included) travels with it.

## Where things stand

Branch **`fogo-baixo`** (off `master` at `ee89bf4`), 4 commits, tree clean,
**1016 tests green**, `ruff check` clean.

> `ruff format` is NOT clean on this repo and never has been — 36 files predate
> today's work. The gate is `ruff check`. Do not "fix" the formatting; it makes
> an unreadable diff and hides real changes.

| commit | what |
|---|---|
| `9c37340` | roadmap re-derived under the budget rule; backlog 74 + 75 written |
| `36524a8` | **74's inventory** — the survey that falsified its own headline |
| `6ce3924` | **65 item 4** — the two deterministic guards |
| `36acdf0` | **65 items 1-3** — the Director rules what is said, the character writes it |

## The one thing to do next

**Validate the Director prompt variant live, per `AGENTS.md` §6.** It is the only
outstanding obligation from task 65, and it is written up in
`.plan/tasks/65-director-must-not-author-speech.md` under
*"⚠ What is NOT validated"*.

Why it matters: the DIALOGUE OWNERSHIP rule **had to change** — the old text told
the Director *"never invent new dialogue… record only words already spoken in
HISTORY"*, which the new engine contradicts, so leaving it was not an option. But
§6 says the validated variant is the shipped variant, and this one has not faced
a live Director. It is shipped and unvalidated, which is a state this project
does not tolerate for long.

### Method (do not skip step 0)

0. **Pre-register the decision rule before running.** §6 is explicit about this,
   and this project has been burned by moving the goalposts afterwards. Suggested,
   but write down whatever you actually commit to:
   > *The new variant ships if, over 4 runs on the same real payload, its
   > `audible_speech` contents carry a quoted span at a materially lower rate than
   > the old variant, AND the count of `audible_speech` events per call does not
   > collapse toward zero. A Director that simply stops using the channel has not
   > fixed the defect — it has broken WT-09.*

   That second clause is the one that matters. It is easy to "win" this test by
   making the Director abandon the channel, which would silently delete facts
   witnesses need.

1. Take a REAL payload: an archived `director` record with ≥2 `audible_speech`
   events. `plans/artifacts/p1-archive/base-P1-r2/sessions/*/debug.jsonl` has
   several (T33-T35 are the ceiling-restaging turns).
2. Build the NEW variant by substituting the two changed paragraphs into the
   RECORDED system prompt, not by reconstructing the builder. Position is part of
   the variant (§6, measured 2026-07-18: the same rules validated at the END
   worked 3/3, buried in the MIDDLE failed 3/3), and substitution preserves it
   exactly. The two changed blocks are in `src/agents/narrator.py`:
   the `DIALOGUE OWNERSHIP:` bullet, and the `"content":` clause that now says
   *"for audible_speech the fact being made public, in reported form, never the
   spoken words"*.
3. `POST {api_base}/chat/completions`, `Authorization: Bearer <key>`, body
   `{"model","messages","response_format":{"type":"json_object"},"thinking":{"type":"disabled"}}`.
   Provider config lives in `.data/config.json` → `providers.deepseek`
   (`deepseek-v4-flash`, key already set). 4 runs per variant; the output is
   stochastic, so count the RATE, never a single case.
4. Only after the isolated call is clean does a battery make sense.

### And calibrate one threshold while you are there

`_INTENT_CARRIED_RATIO = 0.5` (`src/runner.py`) is the single number in task 65
that could **not** be sized against the archive, because it judges compliance
with a prompt that did not exist before today. Everything else in the task was
measured over 3,936 archived records; this one was not, and the code comment says
so. Calibrate it from `mandate_ignored` counts in `debug.jsonl` once real turns
exist.

**Falsifier, already written into the task:** if `mandate_ignored` fires on a
large share of case C, the mandate is a prompt promise that loses — which is
exactly what this task says about prompt promises — and case C falls back to
case A's dedicated call, at a cost the owner already accepted.

## What task 65 actually shipped, in one paragraph

The Director's `audible_speech` no longer persists its own text under a
character's byline. Three populations, measured before building: the subject is
**silent** this turn (209 of 639) → a call of their own, all of a beat's calls in
one `asyncio.gather`; the intent **restates their own line** (27) → dropped as an
echo; the subject **already speaks** this turn (403, the majority) → the intent
rides into the call they were making anyway as an obligation to voice, costing no
extra call and leaving one record where there were two. 257 of 434 turns need no
extra call at all. Six refusal reasons, all logged via `log_audible_speech_drop`
— that log is the calibration instrument for the threshold above.

Two invariants were nearly broken and are held by tests now: the runner must
never generate the human's dialogue, **and** refusing the controlled character
outright breaks WT-09, whose founding case *is* the player's character reading a
cipher aloud whose content exists only in the Director's event. That one degrades
to a Narrator report.

## The 74 finding, so it is not re-derived

`src/watcher.py` (task 33b, closed 2026-07-20) is **already** a
situation-reader → dispatcher → intervention chain, wired into the Runner and
disabled by `watcher_enabled=False`. Full inventory in
`.plan/backlog/74-orchestrator-agent-with-tools.md` §6. Three consequences:

1. **74's stillness argument is dead.** The ladder's `allow_silence` rung does
   not make a turn silent — it suppresses the watcher's own intervention, never
   `minItems: 1` or the 150-word floor. Stillness belongs to **task 72**.
2. **Three of five rungs are dead code** because the Runner never supplies their
   inputs — and those inputs are what **69** and **72** build. Wave 2 is what
   makes the dispatcher already on disk work as designed.
3. **There is no tool-calling anywhere in `src/`.** Every call is one
   grammar-constrained JSON-schema call through `call_agent`. So 74 cannot be an
   agent-SDK tool loop; it is a plan-returning schema call, which is *stricter*
   than its own §3 constraint asks.

Both 74 and 75 have free offline experiments that need **no new harness**:
`tools/acceptance/watcher_abc.py --audit <sid>` already runs an arm-neutral
per-turn audit over a finished history.

## Roadmap position

Wave 0 ✅ (task 68). Wave 1: **65 done bar the live validation**, then 63, 67,
70, 64. Wave 2: 69 (owns the durable-state interface for the phase), then 72 if
its gate opens. 71 is parked pending 67's re-measurement. 74/75 are backlog and
do **not** re-order anything.

## House rules that bit me today

- Prompts may not contain em/en dashes. Two tests enforce it
  (`test_integration.py`, `test_memory_retention.py`) and I tripped both.
- Verify against `debug.jsonl`, not `state.json`.
- The scanner in `tools/acceptance/immersion_scanners.py` keys matches by
  `id(record)`, not by list index. I got this wrong once and briefly believed the
  instrument was broken when my probe was.
