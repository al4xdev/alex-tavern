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
descends. See `blind-read.md`.

> **⚠ Corrected 2026-08-02.** This paragraph used to continue: *"Verified: none of
> it is in `perception_events`. The prose renderer invented and re-invented it."*
> **That was false.** The **Director** proposed the ceiling collapse at T33, T34
> and T35, verbatim in `perception_events`; the renderer rendered what it was
> given. The check had been run against `state.json`, where the key does not
> exist at all. Standing rule that came out of it: **verify against
> `debug.jsonl`, not `state.json`.** Full correction in `blind-read.md`; the
> review that caught it is `docs/cases/21-independent-architecture-review-2026-08-02.md`.

## 6. Open, not fixed

> **This section was rewritten on 2026-08-02.** Its first two entries named the
> wrong layer and the wrong cause; both are corrected below. The phase that
> followed is planned in `.plan/ROADMAP.md`, and each item here now points at the
> task that owns it.

- **The DIRECTOR restages events** — not the renderer. Largest known remaining
  cause. See the correction in §5 and `.plan/tasks/69-...`. The prose guard
  numbers (0.1349 / 0.7770 against 0.85 / 0.8) are real but incidental: tightening
  a guard on the *rendering* of an event the Director decided to restage does not
  address it.
- **The Director authors speech.** Not listed here originally, and it is the
  largest measured defect in this archive: **467 of 1,649 persisted speech
  records (28%)** across the twelve P1 sessions came from Director
  `audible_speech` text rather than from a character agent, in **12 of 12**
  sessions. Owns the internal-id leak and the English flip below.
  `.plan/tasks/65-...`.
- **Fact churn.** Relaxing the `scene_update` schema to `additionalProperties:
  true` raised the Director's fact-writing rate from ~37 distinct keys per
  session to 51-80; two of three `base` runs finished pinned at the 40-key cap.
  Recorded here as "no harm observed" — a later review argued the harm is visible
  and misattributed, since a saturated cap evicts exactly the low-salience facts
  worth keeping. Instrument the evictions before building on this bag
  (`.plan/tasks/69-...`). *The original entry cited `main_doors: trancadas` as
  the example; that session is not in this archive and its restaging had a known,
  fixed cause (the R0 injection loop). Withdrawn.*
- **Internal ids in prose** (`C17`, `C20`) — one occurrence, `oldcode-r1` T39,
  and it arrived through the `audible_speech` channel. Closed by
  `.plan/tasks/65-...`.
- **Narration flipping to English** — **misfiled**. `null-r2` T2 has four Director
  `audible_speech` events in English; **zero** narration records in the corpus are
  English. Also `.plan/tasks/65-...`.
- **The redaction guard mutilates public speech.** 69 `[indistinct]` across 15 of
  16 transcripts, in dialogue and in narration, on ordinary words (`bengala`,
  `sinto`, `estão`). Not measured by anything here. `.plan/tasks/63-...`.
- Never run: the semantic delta judge (`MDR`, specified in
  `tools/acceptance/repetition_metrics.py::material_delta_rate`). **Its
  justification has since been withdrawn** — see §7.

## 7. What each number is, and how much to trust it

The tables above use short names. Nothing in this directory defined them, which
made the archive unreadable in exactly the way §1 says it must not be. All of it
is computed offline by `tools/acceptance/repetition_metrics.py` from `state.json`
+ `debug.jsonl`, and spends nothing.

**The unit almost everything is built on: a *stimulus*.** One `perception_event`
the Director proposed, taken from the **last successful** `director` record of
each turn (`proposed_stimuli`, `:127`) — transport retries and the
hint-materialization retry are not extra proposals. So these metrics measure the
Director's **decision**, not the prose. That distinction is the whole point of
the module and is what §5's correction turned on.

| name in the tables | field | what it is | the catch |
|---|---|---|---|
| **repeated injected event** | `max_hint_repeats` | Largest number of turns handed the *same* `UPCOMING EVENT` text. Read from the **prompt**, not the response (`injected_hints`, `:314`); the block is contract-mandatory, so a repeat is an order repeated, not a model preference. Control signals excluded | The metric that carried the whole investigation. `oldcode` [4,4,4] vs `base` [1,1,1] |
| **RSR_prop** | `rsr_prop` | Fraction of stimuli whose similarity to *anything already in play* exceeds τ. Priors = every earlier stimulus **plus** all prior speech/action (`spoken_before`, `:164`) | τ = `DEFAULT_TAU` **0.8**, pairwise. Cells overlap at n=3 |
| **ECHO** | `echo_persist` | Speech records that verbatim-duplicate an earlier line **by the same voice** (`_echo_persist`, `:449`) | τ = `ECHO_TAU` **0.95**, deliberately far above the rest. The `Player` sentinel is skipped, so a scripted input profile no longer scores its own repeats — but a Director reformulation of the human's words still counts, because that record carries the character's id |
| **BOCC** | `beat_occupancy_max` | Longest run of consecutive turns under one roteiro beat | Keyed by beat **content** (intent + sorted anchors), never `beat_id` — that string is model-written, unstable across replans, and collides across acts (`_beat_timeline`, `:491`) |
| **cluster** | `cluster_max` / `cluster_span` | How many times ONE situation came back: leader clustering, every member similar to the cluster's **first** member (`_cluster_stimuli`, `:262`). Reported `size × span` | τ = `CLUSTER_TAU` **0.6** — a *different, looser* threshold than `RSR_prop`'s 0.8, on purpose: a restaged scene drifts in wording. Leader, not single-linkage, because chaining fused 22 unrelated stimuli on `null-P1-r2`. Only clusters spanning >1 turn count. **`cluster_span` is misreported throughout this archive — see the warning below** |
| **NSR** | `nsr` | Novel stimuli per turn — stimuli whose similarity to every prior is `<= τ` | **Not a gate. Inverted on this corpus — see below** |
| **SIL** | `sil` | Fraction of turns with no narration record | **0.0 in 16/16 runs. Structurally cannot fire — see below** |
| **GUARD** | `guard` | Fraction of prose turns that hit the prose repetition-guard retry | Measures the *renderer's* guard firing, one layer below where §6 says the defect lives |
| **REVERT** | `revert_total` | Fact values returning to a value the key already held — doors cannot seal twice (`_reverts`, `:382`) | 0 almost everywhere; floor effect, no power |

Secondary fields in `metrics.json`, reported but never decisive: `fact_keys` /
`fact_bytes` (scene fact-bag size — watch the 40-key cap), `injected_turn_fraction`,
`act_deadlines`, `act_rewrites`, `exit_reasons`, `replans_per_action`,
`llm_calls_per_action`, `distinct_hints`.

### How much to trust them

Only three metrics ever decided anything, and they are the ones measuring a
*specific deterministic defect* rather than "how repetitive is this":

| metric | within-cell spread | verdict |
|---|---|---|
| repeated injected event | none (4,4,4 vs 1,1,1) | trust it |
| `BOCC` (turns under one beat) | none in `base`/`drive` | trust it |
| `ECHO_PERSIST` | none | trust it |
| `RSR_prop`, `GUARD` | **cells overlap at n=3** | indicative only |
| `NSR` | **anti-correlated with read quality** | never a gate — see below |
| `REVERT`, `SIL` | 0 almost everywhere / 0 everywhere | floor effect, no power |

Roughly twenty-five numbers were built; three carried the result. The rest are
attempts to quantify a subjective judgement and behaved accordingly — one
produced a false cluster of 22 unrelated stimuli, one caught 4 of 7 restagings,
one scored 20 duplicates that were the *input profile* repeating itself.
**Reading the transcripts found more, faster, than any of them.**

> **⚠ `cluster_span` was misreported everywhere in this archive (found
> 2026-08-02, **fixed and the archive re-scored 2026-08-05**).**
> `analyze()` took `cluster_span=clusters[0]["span"]`, and `clusters` is sorted
> by size — so the reported span belonged to the largest cluster, not to the
> widest one, and `clusters[:5]` could drop a real cluster from the listing.
> Re-derived maxima: `base-P1-r2` 15 (reported 5), `oldcode-P1-r1` 37 (5),
> `null-P1-r2` 36 (8), `drive-P1-r2` 24 (3).
>
> **`metrics.json` in both batteries now carries the corrected values**, so any
> table in this directory quoting a pre-2026-08-05 `cluster_span` is stale. Both
> scalars are maxima over every cluster now, and two fields join them:
> `cluster_count` and `cluster_count_ge3` — how many distinct situations came
> back at all, and how many came back three turns or more, which is the number a
> human actually wanted from this metric.
>
> Case 20 cancelled the durable staged-event memory on a gate keyed partly on
> this scalar (`cluster_span >= 10`). Re-derived, the span half is satisfied
> almost everywhere; the conjunction still fails on `cluster_max`, so **the
> cancellation stands — but it stood on a wrong number.**
>
> **`cluster_count_ge3` is the one number here that does not score `base-P1-r2`
> clean.** That session — the reader's worst of twelve, `RSR_prop` 1.7%,
> `cluster_max` 3 — ties for the archive's highest count of situations recurring
> three turns or more (8, with `oldcode-P1-r1`), and the column tracks the blind
> ranking at ρ = +0.60 where `RSR_prop` manages −0.09. **Do not gate on it.**
> n = 12, one battery, and `BOCC` scores +0.74 on the same ranking without
> claiming to measure reading quality. Re-check at the phase checkpoint;
> `.plan/tasks/68-...` records why it is deliberately not being promoted.
>
> The same finding retires a claim made after this battery, that the lexical
> instrument was exhausted and "no threshold works". False: `CLUSTER_TAU = 0.6`
> (the 0.8 is `DEFAULT_TAU`, pairwise only), the three ceiling sentences are all
> above it, and the metric **did** find the cluster — the reporting hid it. The
> real pillar escalation pair scores 0.4873, so the feared escalation
> false-positive did not materialise either: zero of `base-P1-r2`'s 16 clusters
> at τ=0.6 are escalations. Fix in `.plan/tasks/68-...`.

> **⚠ `NSR` is inverted on this corpus, and `SIL` cannot fire (found 2026-08-05).**
> The module docstring calls them the two guards *"against a degenerate engine
> that fixes repetition by going quiet"*, and the phase that followed this battery
> made *"`NSR` must not fall"* its acceptance gate. **Applied to this archive that
> gate endorses the worst session in it and rejects the three best.**
>
> `NSR` is `len(novel) / turn_count` (`:609`) over *lexically* novel stimuli
> (`:555`). It measures **event volume**, not narrative substance. Against the
> blind reader's ranking of these same twelve sessions:
>
> | | |
> |---|---|
> | Spearman ρ, blind rank (1 = best read) vs `NSR` | **+0.923** |
> | `base-P1-r2` — the reader's **worst of twelve** | **highest `NSR` in its cell** (4.54 vs 3.41 / 3.78) |
> | within-`base` spread | **1.12** |
> | `base` − `oldcode` median delta | **−0.15** |
>
> Higher `NSR` tracks *worse* reading, almost monotonically — this corpus's
> failure mode is over-production, which is the direction `NSR` rewards. And the
> within-cell spread is **7× the effect it would be asked to detect**; at n=3 it
> cannot see anything.
>
> `SIL` is `0.0` in **16 of 16 runs**, both batteries. It cannot degrade, because
> `perception_events` `minItems: 1` (`narrator.py:333`) and the 150-word floor
> (`prose.py:59`) make a silent turn structurally impossible. A future task
> (`.plan/tasks/72-...`) exists to legalise the silence those two forbid — after
> which a **nonzero `SIL` is the feature**, not the regression.
>
> The rule they encode is still right; the instruments are not. Both are now
> **reported, never a gate** — a large move in either is a prompt to go read.
> Full derivation and the replacement gate in `.plan/ROADMAP.md`.

## 8. `immersion-scan.json` — three counters that DO gate

Added 2026-08-05 by `tools/acceptance/immersion_scanners.py`, and present in both
batteries. Everything in §7 tries to quantify "how repetitive is this", overlaps
between cells at n=3, and ends up indicative. These three do the opposite: each
counts a **specific invariant being violated**, so each one is parameter-free,
needs no replicates, and gates its own task at **zero**. They are the deterministic
half of the replacement gate; the blind read is the other half.

| counter | what it counts | this archive (P1 / P2) |
|---|---|---|
| `redaction` | `REDACTION_MARKER` by channel — narration, persisted speech/action, and the three ledger channels (`recent_memory`, `memory_summary`, `people`) | **87 / 28** occurrences; **42 / 15** persisted records; **33 / 6** ledger entries |
| `director_speech` | persisted speech records whose text came from a Director `audible_speech` event, matched back to the event in `debug.jsonl` | **458 of 1,601 (28.6%) / 181 of 618 (29.3%)**, in **12 of 12** and **4 of 4** sessions; **303 / 132** of them for a character the engine routed that same turn |
| `empty_audience` | speech/action persisted with an audience of nobody, classified WITHOUT trusting the zone graph | **33 / 2** records, all with other characters present; **31 / 2** cut off by the graph, **2 / 0** narrowed to none by the Director's own list |

Three things about how they are computed matter more than the numbers:

- **Nothing here reads a stored flag.** A Director-authored line is persisted with
  `audience_origin='zone'` exactly like an ordinary one, so `state.json` cannot
  tell them apart. The scanner matches record text back to the Director event
  that produced it, at a similarity threshold high enough to survive redaction
  replacing tokens inside the line.
- **The audience scanner refuses to ask the zone graph whether the audience
  should have been empty**, because the graph is the suspect: when a sub-zone is
  minted with no inbound edge the graph agrees nobody can hear, and a
  graph-trusting scanner would certify the bug as correct. It asks instead
  whether anyone else was *present*, and reports the graph's opinion separately.
  That split is what shows 31 of the 33 are the graph cutting people off and 2
  are the Director narrowing its own witness list to nothing.
- **`director_events_raw_empty_witnesses` is the control**: 2 of 1,868 raw
  Director events in P1 proposed an empty witness list, against 33 persisted
  records that have one. Whatever emptied them, it was not the model.

Seeded positives and negatives for all three live in
`tests/test_immersion_scanners.py`, and the scanner's raw-dict copy of the zone
rule is cross-checked there against the shipped `src.perception.can_perceive`, so
it cannot drift into agreeing with a broken graph.

---

## Format

```
<date>-<engine-fingerprint>-<label>/
  manifest.json       engine, models, per-run config
  metrics.json        every metric for every run (§7)
  immersion-scan.json the three invariant counters (§8)
  transcripts/        one readable transcript per run
  blind-read.md       (p1 only) what a clean-context reader saw
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
