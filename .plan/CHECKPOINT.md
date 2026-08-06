# Checkpoint — 2026-08-06, branch `fogo-baixo`

Hand-off for the next session. Written because the owner is moving machines; the
working tree syncs over SSH, so `.data/` (provider key included) travels with it.

## Where things stand

Branch **`fogo-baixo`** (off `master` at `ee89bf4`), 7 commits, tree clean,
**1034 tests green**, `ruff check` clean.

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
| `2caa203` | **65's live validation** — the prompt variant faces a real Director |
| `93a8840` | **65's threshold** — 0.5 was above its own empty band, now 0.34 |
| *(HEAD)* | **70** — the named exclusion is deleted, and guarded |

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

### ✅ And the threshold is calibrated: 0.5 → 0.34

Two arms of 10 real replies on the same payloads — **with** the shipped mandate
and **without** it. The archive had no positives for this prompt, so they were
built rather than found.

| | range |
|---|---|
| mandated | **0.39 – 0.79** |
| unmandated control | **0.00 – 0.29** |

**An empty band from 0.29 to 0.39.** The falsifier does not fire (every mandated
reply voiced the fact, so case C stays), and **0.5 was above the band**, inside
the mandated cluster, which is why it cost 1 in 10 compliant replies a spurious
record. Shipped at the band's midpoint, **0.34**, where the sample classifies
perfectly both ways.

The expensive error here is the false negative: `runner.py:1721` then prints a
Narrator report *beside* the character's own compliant line — this task's own
duplication, wearing the degradation path's byline.

n=10 per arm, one scenario, one model. The language guard in this task was sized
over 3,936 records; this is twenty. **0.34 is a first calibration, not a settled
constant** — re-derive it against real `mandate_ignored` records.

Measured and *not* shipped: excluding the subject's own name from the denominator
(10/10 intents name it, 0/10 replies do) widens the band 0.10 → 0.13. If ever
adopted, re-derive the threshold with it; the midpoint moves to ≈0.375.

## ✅ Task 70 delivered 2026-08-06 — the named exclusion is gone

The Director prompt appended *"Let someone other than C1 carry this beat"* on
**371 of 631 archived turns (58.8%)** — 100% of every P2 cell. `exclude_speaker`
is always the controlled character, so `AGENTS.md` §3's *"exclusão nomeada"* was
being emitted every turn, and both existing `prompt_contract` checks were
structurally blind to it.

**The block is deleted, not reworded.** `_build_user_prompt` no longer accepts
`exclude_speaker` at all, so the exclusion is no longer expressible in the
prompt. It is enforced where it always actually was — `narrate`'s normalization
at `narrator.py:750`.

Two things worth carrying forward:

1. **The task's suggested fix was already dead.** It proposed constraining the
   candidate set; `narrator.py:298-303` records that as rejected with a
   measurement (a narrowed enum → 3 straight schema failures). Read the code's
   own comments before implementing a task's Direction section.
2. **The clause was buying nothing.** Pre-registered 3-arm test, 2 archived P2
   payloads × 4 runs: the Director routed the controlled character **0/8 with
   the line and 0/8 without it**, with no beat collapsing to Narrator-only in
   any arm. Evidence in `plans/artifacts/70-routing-constraint/`.

`named_exclusions()` now guards the shape, is swept per call by
`tools/playtest_harness.py`, and a test asserts the two older checks cannot see
what it catches. **Still open:** `return_control`/PC-routing re-measured on a
fresh cell, which task 64 is waiting on.

## ⚠ `plans/` vanished mid-session, and was restored

`plans/artifacts/p1-archive/` (16 archived sessions) was emptied at **11:47 on
2026-08-06**, between the Director runs and the control arm — the SSH sync of the
machine move. Restored the same afternoon from `alex@192.168.0.100` with
`rsync -av --ignore-existing`, which brought back `p2-archive` and
`repetition-battery` too and left the new evidence directory untouched.

**`plans/` is gitignored: git cannot protect it.** Every number from those runs
is therefore written out in the reference doc rather than left as a pointer.
Raw outputs and the three harness scripts are in
`plans/artifacts/65-live-validation/` — which has the same exposure, so treat the
reference doc as the record of last resort.

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

Wave 0 ✅ (task 68). Wave 1 is **65 ✅, 70 ✅, then 63, then 67** — that is the
ROADMAP table's order, which is the authority; the line here used to say
"63, 67, 70, 64" and was wrong.

**63 is next, and it must be re-measured before it is designed.** The ROADMAP
gates it on 65, which removed 42 of its 43 cases, and the roadmap's re-review
already killed its option-shopping: *"option 1, per-viewer projection, is the
correct one and the drop path is dead."* Its "before" number is stale — it was
taken with the producer 65 just replaced still in play.

Wave 2: 69 (owns the durable-state interface for the phase), then 72 if its gate
opens. 71 is parked pending 67's re-measurement. 64 is waiting on 70's
`return_control` re-measurement, which needs a fresh cell. 74/75 are backlog and
do **not** re-order anything.

## House rules that bit me today

- Prompts may not contain em/en dashes. Two tests enforce it
  (`test_integration.py`, `test_memory_retention.py`) and I tripped both.
- Verify against `debug.jsonl`, not `state.json`.
- The scanner in `tools/acceptance/immersion_scanners.py` keys matches by
  `id(record)`, not by list index. I got this wrong once and briefly believed the
  instrument was broken when my probe was.
