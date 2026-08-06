# Checkpoint — 2026-08-06, branch `fogo-baixo`

Hand-off for the next session. Written because the owner is moving machines; the
working tree syncs over SSH, so `.data/` (provider key included) travels with it.

## Where things stand

Branch **`fogo-baixo`** (off `master` at `ee89bf4`), 5 commits, tree clean,
**1017 tests green**, `ruff check` clean.

> The venv did not survive the machine move. `uv sync` rebuilds it; the Bash
> tooling runs bash, not the login fish, so call `.venv/bin/python` directly.

> `ruff format` is NOT clean on this repo and never has been — 36 files predate
> today's work. The gate is `ruff check`. Do not "fix" the formatting; it makes
> an unreadable diff and hides real changes.

| commit | what |
|---|---|
| `9c37340` | roadmap re-derived under the budget rule; backlog 74 + 75 written |
| `36524a8` | **74's inventory** — the survey that falsified its own headline |
| `6ce3924` | **65 item 4** — the two deterministic guards |
| `36acdf0` | **65 items 1-3** — the Director rules what is said, the character writes it |
| *(HEAD)* | **65's live validation** — the prompt variant faces a real Director |

## ✅ Done 2026-08-06 — the Director prompt variant is validated

Evidence: `.plan/reference/65-director-prompt-live-validation.md`. Decision rule
pre-registered before any call; both changed blocks substituted into the RECORDED
system prompt so position is preserved; 2 real payloads × 2 variants × 4 runs.

**Quoted `audible_speech`: 5/8 (62%) under OLD, 0/11 (0%) under NEW, p = 0.0048.**
The channel was used *more*, not less (1.38 vs 1.00 per call), so the clause that
mattered — a Director that "wins" by abandoning the channel and breaking WT-09 —
is satisfied too.

Two dropped words in the shipped prompt were found while reading it for the
replay and fixed **before** it ran, so the validated text is the shipped text.

### The threshold: one arm measured, the control still owed

`_INTENT_CARRIED_RATIO = 0.5` now has real positives — 10 character replies under
the shipped mandate. **The falsifier does not fire:** every one voiced the fact,
so case C stays. But:

- **0.5 is not in an empty band.** Ratios run `0.39 … 0.79` continuously. Unlike
  the language guard (0.012 vs 1.000), this is a cost/benefit cut through a dense
  cluster. Do not quote it with the language guard's confidence.
- **The one miss is a false positive**, and false positives are the expensive
  direction: `runner.py:1721` then emits a Narrator report *beside* the
  character's own compliant line, which is this task's own defect returning.
- **Measured cause:** 10/10 intents name their subject, 0/10 replies do — reported
  form always names the speaker, so the name sits unmatched in every denominator.
  Excluding it lifts every ratio (mean +0.073). **Measured, not shipped**: it
  moves the operating point and the false-negative cost is invisible while all
  ten observations are compliant.

**Next, and it is blocked:** the negative control — the same payloads fired
*without* the mandate, to see what overlap topicality alone produces. It needs the
corpus below.

## ⚠ The evidence corpus vanished mid-session

`plans/artifacts/p1-archive/` (16 archived sessions) was emptied at **11:47 on
2026-08-06**, between the validation runs and the write-up. `plans/` is
gitignored, so git cannot restore it, and it is not in the trash on this machine.
Nothing in this session deleted it; the likely cause is the SSH sync of the
machine move described above.

**It needs to come back from the other machine.** Blocked on it: the negative
control arm, the task-68 scanner re-run, and any re-derivation of the 3,936-record
measurements this task rests on. The numbers already extracted are written into
the reference doc rather than left as pointers, for exactly this reason.

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
