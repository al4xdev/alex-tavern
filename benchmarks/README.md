# benchmarks/

Archived acceptance batteries, and the reasoning attached to them. Written so
someone with **no context from the session that produced them** can pick this up.

Deep narrative, with every counterfactual:
`docs/cases/20-repetition-baseline-2026-08-01.md`.

---

## 1. What was being investigated

The complaint: **the Narrator re-tells the same scene for several turns in a
row** — the floor trembles and stone chips fall, again, and again, while the
story stands still.

A previous attempt (`602e562`, reverted in `2eabc81`) tuned prompts, was declared
fixed on a sample of one, and the session cited as proof fails in its own log.
Everything here exists to not repeat that: build the ruler before the cut, cut
only causes that can be shown deterministically, and never compare two things
that differ by more than the change under test.

## 2. The engine, in one paragraph

A **Director** (`src/agents/narrator.py`) decides what physically happens each
turn and who reacts, emitting typed `perception_events`. A blind **prose
renderer** (`src/agents/prose.py`) turns those events into narration — it never
sees the Director's reasoning. A **roteiro** (`src/roteiro.py`) is an optional
private story plan: a premise, an act skeleton with a tick clock, and one rolling
"beat" contract; deterministic code decides *when* to replan, an LLM only writes
*what* the new beat says. A bare "skip" from the player triggers an **autonomous
burst**: up to 6 turns committed from one submission.

## 3. The two batteries

Both ran on `deepseek-v4-flash`, language pinned to Brazilian Portuguese, cast of
21, with `auto_event` / `character_roteiro_alignment` / `automatic_compaction`
held off, cell order randomized inside each replicate block.

### `2026-08-02-6ed5639e049f-p1-burst` — 12 runs, 4 cells × 3

Input profile: mostly bare skips, so most turns come from autonomous bursts.

| cell | what it is |
|---|---|
| `base` | the engine as it stands after this investigation's fixes |
| `oldcode` | **the control.** The pre-fix engine (commit `2eabc81`) run on the CURRENT model, from a git worktree. Explained in §5 — without it nothing is attributable |
| `null` | roteiro disabled entirely. The cheapest refutation of the premise |
| `drive` | `base` plus the autonomous event scheduler back on. Existed to decide whether a guard was needed; it was not |

Medians:

| cell | repeated injected event | RSR_prop | ECHO | BOCC | cluster | NSR | SIL | GUARD |
|---|---|---|---|---|---|---|---|---|
| `oldcode` | **4x** | 9.9% | 4 | 6 | 4x/5t | 3.92 | 0% | 30.8% |
| `base` | **1x** | 1.7% | 0 | 3 | 3x/5t | 3.77 | 0% | 15.4% |
| `drive` | 1x | 5.2% | 0 | 3 | 3x/5t | 3.79 | 0% | 13.2% |
| `null` | 0 | 9.4% | 0 | 0 | 4x/8t | 2.87 | 0% | 32.5% |

Per run the repeated-event count is `oldcode` [4,4,4] vs `base` [1,1,1] — zero
overlap, zero within-cell variance.

Also here: **`blind-read.md`**, and it is the most useful file in this directory.

### `2026-08-02-6ed5639e049f-p2-spoken` — 4 runs, 2 cells × 2

Input profile: the player speaks every turn, 40 distinct lines, so `max_beats=1`
throughout and **no autonomous burst at all**. This path has no stimulus dedup
whatsoever; P1 alone was measuring the path that already had a filter.

| cell | repeated injected event | RSR_prop | ECHO | BOCC | cluster | NSR | GUARD |
|---|---|---|---|---|---|---|---|
| `oldcode` | 5x | 3.2% | 4 | 3 | 4x/20t | 4.19 | 15.0% |
| `base` | **1x** | 1.6% | **0** | 2 | 3x/4t | 3.99 | 15.0% |

Unbalanced (2 v 2) because the battery was stopped early; the four runs are
complete 40-turn sessions.

## 4. What was concluded

**The defect had a code cause, not a prompt cause.** On the LAST act, the clock
guarded the act-index advance but still reset the tick and re-emitted the act's
`world_event`, forever. In one 38-turn session that produced 17 act deadlines and
the *same text* injected twelve times into a prompt block the Director's contract
declares MANDATORY ("no coherence concern overrides it"), while the same prompt
also said "never restage what already happened". The mandate won 7 times out of
12. Fixed: a story that runs out of acts gets new ones.

**Three smaller defects on the same theme**, each with a counterfactual against
the old engine: a beat clock counted in player actions could never fire inside a
burst (beats held 5-7 turns; now capped at 3); the speech echo guard compared raw
strings over a record window, so an attribution wrapper hid nine verbatim
duplicates (now 0); a control signal was held to the event contract it can never
satisfy, burning ~13% of a session's tokens on a retry that could not succeed.

**Two cancellations, by rules written before the data.** A durable staged-event
memory was cancelled — residual recurrence fell below the authorization gate. A
producer-agnostic injection guard was cancelled — the `drive` cell showed the
event scheduler does not repeat its own seeds, so the schema bump it needed was
never spent.

**A trade-off that is a product decision, not a metric.** `null` (no roteiro) is
the *least* repetitive configuration and the dullest — the blind reader called
those three "the only ones where nothing ever bursts in". The roteiro adds events
and adds repetition.

## 5. Two traps that cost real time here

**The provider changed the model without changing its name.** DeepSeek updated
`deepseek-v4-flash` **in place on 2026-07-31**. The reference sessions from 07-28
and everything run after carry the same model id in every log line and are
different weights. A before/after against those sessions therefore measured the
fixes *and* a model upgrade together — and the model turned out to explain most
of the headline number. The `oldcode` cell exists solely to separate them. **A
model id is not evidence of comparability.**

**The metrics missed the worst session in the battery.** `base-r2` scored clean
on everything and a blind reader ranked it worst of twelve: a ceiling ruptures
four times, a character announces she is descending nine times and never
descends. Verified: none of it is in `perception_events`. The **prose renderer**
invented and re-invented it, and the instrument was blind to that by design — its
own docstring says it measures the decision, not the prose. See `blind-read.md`.

## 6. Open, not fixed

- **The prose renderer restages events.** Unfixed, and the largest known
  remaining cause. `prose._repeats_prior_narration` compares whole text (>0.85)
  and sentences (>0.8); on the measured pair those score 0.1349 and 0.7770. It
  misses by 0.023, and it misses structurally: one event re-described across a
  long freshly-worded paragraph is not a similar sentence.
- **Fact churn.** Relaxing the `scene_update` schema to `additionalProperties:
  true` raised the Director's fact-writing rate from ~37 distinct keys per
  session to 51-80; two of three `base` runs finished pinned at the 40-key cap.
  No harm observed, but a saturated cap means constant eviction, and evicting
  `main_doors: trancadas` is precisely what re-enables re-staging.
- **Internal ids in prose** (`C17`, `C20`) — one occurrence, `oldcode-r1` T39.
- **Narration flipping to English** under a pinned language — one occurrence,
  `null-r2`.
- Never run: the semantic delta judge (`MDR`, specified in
  `tools/acceptance/repetition_metrics.py::material_delta_rate`) and any
  reader-facing pairwise judgement. **Every repetition metric here is lexical.**

## 7. How much to trust the numbers

Only three metrics ever decided anything, and they are the ones measuring a
*specific deterministic defect* rather than "how repetitive is this":

| metric | within-cell spread | verdict |
|---|---|---|
| repeated injected event | none (4,4,4 vs 1,1,1) | trust it |
| `BOCC` (turns under one beat) | none in `base`/`drive` | trust it |
| `ECHO_PERSIST` | none | trust it |
| `RSR_prop`, `GUARD`, `NSR` | **cells overlap at n=3** | indicative only |
| `REVERT` | 0 almost everywhere | floor effect, no power |

Roughly twenty-five numbers were built; three carried the result. The rest are
attempts to quantify a subjective judgement and behaved accordingly — one
produced a false cluster of 22 unrelated stimuli, one caught 4 of 7 restagings,
one scored 20 duplicates that were the *input profile* repeating itself.
**Reading the transcripts found more, faster, than any of them.**

---

## Format

```
<date>-<engine-fingerprint>-<label>/
  manifest.json    engine, models, per-run config
  metrics.json     every metric for every run
  transcripts/     one readable transcript per run
  blind-read.md    (p1 only) what a clean-context reader saw
```

`engine.fingerprint` is a hash of `src/**/*.py`, not a commit — batteries are run
from dirty trees and a commit would claim precision the run did not have. The
commit and a `dirty` flag are recorded alongside.

**Two batteries are comparable only if they share an engine fingerprint or ran in
the same provider-weights window.** When in doubt, re-run the control cell rather
than assume.

Raw sessions are not archived (one is ~14MB, a battery ~500MB); they live in
`plans/artifacts/` (gitignored) until the disk reclaims them.

## Adding one

```bash
uv run python -m tools.acceptance.repetition_battery --cell base --cell oldcode --replicates 3
uv run python -m tools.acceptance.archive_benchmark <artifact-dir> --label <what-it-answered>
```

The `oldcode` cell needs a worktree at the pre-fix commit with today's tooling
copied in — see `PREFIX_REPO` in `tools/acceptance/repetition_battery.py`.

**Start with `transcripts/`, not `metrics.json`.**
