# Checkpoint — 2026-08-06, branch `fogo-baixo`

Hand-off for the next session. Written because the owner is moving machines; the
working tree syncs over SSH, so `.data/` (provider key included) travels with it.

## Where things stand

Branch **`fogo-baixo`** (off `master` at `ee89bf4`), 11 commits, tree clean,
**1048 tests green**, `ruff check` clean.

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
| `1089484` | **70** — the named exclusion is deleted, and guarded |
| `168000e` | 65's drop log stops merging two different falsifiers |
| `e34adb7` | **the fresh cell** — 63 falsified, 70/64 re-measured, two instruments fixed |
| `def9e8c` | emptiness is the extreme of the audience bug, not the bug |
| `39d0464` | **67's graph fixes** — a partial link list stops deleting what it omits |
| `9e39a86` | the metric register: which metrics survived a read, and which did not |
| `bb70047` | **67's re-run cell passes**, and the clamp metric stops blaming the speaker |
| `e0d052d` | the split rate becomes an instrument instead of a lost script |
| `adbd370` | 67's mirror failure withdrawn; the graph was the guilty party (task 76) |
| `8be8c06` | a clamp loss is only a graph bug if nobody meant the silence |
| *(HEAD)* | **71's re-measurement** — the task stands, and every singleton was an artifact |

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

### ~~And the threshold is calibrated: 0.5 → 0.34~~ — SUPERSEDED same day

A two-arm replay of 20 synthetic replies put an empty band at `(0.29, 0.39)` and
shipped 0.34. **The fresh cell falsified it hours later.** The threshold is now
**0.15**, the "band" does not exist on real data, and the reasoning is under
"Two instruments were wrong" below. Left here rather than deleted because the
shape of the error is the useful part: a clean band over 20 replies from one
scene was not evidence of a band.

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
what it catches. **Its last closure item is now closed too** — see the fresh
cell below, which also fixed a false positive in that very guard.

## ✅ A fresh cell was run 2026-08-06 — and it moved three tasks

Session `34390b86`, 40-turn P2 `base`, same scenario/model/controls as the
archive, post-65 and post-70. `plans/artifacts/repetition-battery/base-P2-r1/`.

| | archive | fresh cell |
|---|---|---|
| **65** `director_authored` speech records | 181/618 (**29.3%**) | **0/119 (0%)** |
| **63** marker on persisted speech | 15 | **0** |
| **63** marker in the live ledger | 6 | **0** |
| **63** marker in narration | 4 | 3 |
| **70/64** `return_control=True` | 5/482 (1.0%) | 2/40 (**5.0%**) |
| **70/64** controlled character routed | 11/482 (2.3%) | 1/40 (2.5%) |

1. **65's headline defect is at zero on a live session.** First closure item met.
2. **63's falsifier fired** — zero in persisted speech AND zero in the ledger, so
   by its own written rule it is *"a prose-rendering cosmetic issue and drops out
   of wave 1"*. Not cancelled; re-scope it (option 2 alone is probably enough now,
   option 1's architecture was sized against damage that no longer exists).
3. **70's last item is closed** and 64's gate is open, with 64's numbers now
   marked stale.

### ⚠ Two instruments were wrong, and the cell is what found them

**`named_exclusions` had a false positive that the archive could not show.**
`\bmenos\b` matched *"despenca a menos de dois metros de Link"* — a distance, not
an exclusion — firing 15 times in the fresh session and **zero** times across all
631 archived prompts. Fixed to require a universal (`todos menos`). The archive
"before" number of 371/631 is unaffected: all 371 were real blocks.

**`_INTENT_CARRIED_RATIO`'s band was a synthetic artifact, and is now 0.15.**
The 20-reply replay said `(0.29, 0.39)` was empty. The live cell flagged 9 of 42
case-C events at 0.34, and **a read of all 9 finds every one compliant** — the
cause is Portuguese morphology (`formarem` against `formem`), which exact token
matching cannot pair. Pooled real+synthetic compliant replies span 0.15-0.79
against a control of 0.00-0.29: **the clouds overlap and no threshold separates
them.** 0.15 is damage control, not calibration, because the expensive error is
a Narrator report printed beside a compliant line.

**The lesson worth carrying:** the case-C falsifier *fired and was wrong*. It
reads a high `mandate_ignored` rate as the mandate losing, which would have sent
case C back to a dedicated call — but 42 of 42 case-C events were compliant. The
mandate won and the ruler lost. Falsifiers over a measured quantity need a clause
that checks the measurement, and 65's now has one.

## ✅ Task 67's graph fixes are in — 2026-08-06, re-run cell owed

`zone_link_updates` **merges** now; an empty list is still a total seal, which is
the only severance idiom the corpus uses (36 of 106 archived updates).

Bug 1 in 67's diagnosis was **already fixed** by task 54 — `_open_new_zones` has
given new sub-zones a reciprocal edge for a while. The live bug was bug 2 alone,
and the compound was worse than either: that reciprocal edge could be wiped by
`zone_link_updates` **in the same turn**.

The ambiguity is real and written into the code: of 36 non-empty updates to a
zone that already had edges, **20 only add and 16 remove at least one**, and
reading them, some narrowings are intentional and some are collateral. Counts
cannot separate them. Resolved on this file's own precedent — **err toward
hearing**, since over-hearing costs realism and under-hearing costs the defect.
Cost stated: removing one edge in a single update is no longer expressible.

Two silences now log: `log_zone_link_dropped` and `log_witness_clamp`. Verified
by replaying `base-P1-r2` T19-T23's real updates through the new code (hall keeps
all three edges; archived run had one), pinned as a test with the data **inlined**
because `plans/` is gitignored.

## 📐 Metric validity — read this before trusting any number

**`.plan/reference/metric-validity.md`** is new and is the most reusable thing
from today. Three instruments failed a read of the actual text on 2026-08-06,
two of them written the same day:

- **`_INTENT_CARRIED_RATIO`'s empty band** was an artifact of 20 synthetic
  replies from one scene; it vanished at n=42 on real data.
- **`named_exclusions`** shipped with a false positive that fired 15× on fresh
  output and **0×** on the 631-prompt archive it was validated against.
- **`empty_audience`** counted the extreme and missed the near-miss population
  that is 8× larger and the same defect.

Plus three graph metrics measured and **rejected** — they look plausible and rank
sessions wrong. The standing rule: *never accept a metric on the strength of its
numbers; read the records it flagged and the records it cleared.*

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

Wave 0 ✅ (task 68). Wave 1 was **65, 70, 63, 67**.
**65 ✅, 70 ✅, 63 falsified out, 67's re-run cell passed 2026-08-12 — wave 1 is
closed** apart from one item carried forward (below).

67's verification cell (`d0cc98e5`, 37/40 turns) came back with
**`clamp_lost_half` 6 → 0** and **`with_others_present` 2 → 0**, and after
correcting the counter (the subject is not their own witness) there were no
audience losses of any size at all. The pre-fix baseline `34390b86` was re-scored
with the same corrected counter and still shows its six, worst 20 → 1. Details
in `.plan/tasks/67-zone-graph-integrity.md`, section "The re-run cell".

**Carried out of wave 1:** 67's last closure item — *a character who can no
longer perceive must not be listed as a witness*. It is the mirror of the bug
just fixed (dead/departed staying in the audience rather than the living being
clamped out) and has never been measured. It needs its own scanner pass before
anyone claims it is absent.

**Task 71 is unblocked — the re-measurement ran 2026-08-12 and the task
stands.** Three post-67 `base-P1` replicates against the three archived pre-67
ones, landing on exactly 108 narrated turns each side:

| | split | mean clusters | singletons/turn |
|---|---|---|---|
| pre-67 | 58/108 (53.7%) | 2.352 | **0.740** |
| post-67 | 30/108 (27.8%) | 1.278 | **0.000** |

Fisher p=1.7e-4. The rate halved but stayed above the 20% line the decision rule
was registered against, so 71 stands. **Every singleton cluster was an
artifact** — none in the four post-67 sessions scored that day — so the cost
multiplier is 1.28x under either policy. A fifth session (`21f7c4e1`) later
found singletons on all ten of its split turns, each one task 76's sealed
sibling, so the population is rare and graph-shaped rather than empty. Task 76's sibling confound was checked against this sample
rather than assumed: merging siblings changes the post-67 split count not at all
(30 → 30).

The splits that remain were read, not just counted: a corridor buried by a
collapse, a dungeon door sealed shut, each stated in the sentence that creates
it — and in both, the people on the far side are handed narration describing the
room they cannot see. 71's leak is alive in the post-67 graph.

Wave 2: 69 (owns the durable-state interface for the phase), then 72 if its gate
opens. 64 is waiting on 70's
`return_control` re-measurement, which needs a fresh cell. 74/75 are backlog and
do **not** re-order anything.

## House rules that bit me today

- Prompts may not contain em/en dashes. Two tests enforce it
  (`test_integration.py`, `test_memory_retention.py`) and I tripped both.
- Verify against `debug.jsonl`, not `state.json`.
- The scanner in `tools/acceptance/immersion_scanners.py` keys matches by
  `id(record)`, not by list index. I got this wrong once and briefly believed the
  instrument was broken when my probe was.
