# Task 68 — Fix the cluster reporting, then scan

> **Status: DELIVERED 2026-08-05.** **Wave 0** — nothing else in the immersion
> roadmap should ship before this, because every other task's counterfactual is
> measured with this instrument. What it found is at the bottom, under
> "What the fixed instrument and the three scanners actually found"; two of the
> findings changed a wave-1 task before it started.
>
> Not migrated to `closed/` yet: the convention is to move a task only when it is
> closed **with confidence**, and this one is confirmed by the wave-1 fixes
> reading its numbers. Close it when 63, 65 and 67 have used it.
>
> This task exists because an earlier version of it was **wrong**. It was
> specified as "build a semantic judge, because the lexical family is exhausted".
> That premise was falsified by a blind audit. What is left is a reporting bug
> and a set of missing scanners, both cheap.

## The premise that was false

The claim, written into the roadmap's first draft and stated twice with
confidence:

> The three sentences in which the same ceiling collapses score 0.7927 / 0.6739 /
> 0.7039 against τ=0.8. No threshold works: at 0.8 the instrument cannot see the
> restaging, and at 0.65 it would flag every legitimate escalation.

Both halves are false.

**τ=0.8 is the wrong threshold to have cited.** `DEFAULT_TAU = 0.8`
(`tools/acceptance/repetition_metrics.py:33`) belongs to `RSR_prop`, which is
pairwise. The cluster metric — the one built to answer "how many times did ONE
situation come back" — runs at `CLUSTER_TAU = 0.6` (`:259`). All three ceiling
pairs are **above** it. The metric found the cluster.

Its own docstring said so when it was written:

> The threshold is looser than the pairwise one on purpose: a restaged scene
> drifts in wording, so "the doors seal again" lands at 0.6-0.8 against its own
> first staging and never trips a 0.8 pairwise test.

**The escalation counterexample was invented, not measured.** "The pillar cracks"
→ "the pillar collapses" was a phrase written to make the point. The real pillar
events in the same session (`8bd4d0f1` T28 vs T29) score **0.4873** — nowhere
near 0.6, let alone 0.65. Of the 16 clusters `base-P1-r2` produces at τ=0.6, the
audit found **zero** escalation false positives.

## The actual defect: the cluster is found and then thrown away

`analyze()` (`tools/acceptance/repetition_metrics.py:624-626`):

```python
cluster_max=clusters[0]["size"] if clusters else 0,
cluster_span=clusters[0]["span"] if clusters else 0,
clusters=clusters[:5],
```

`_cluster_stimuli` returns `sorted(clusters, key=lambda c: -c["size"])` (`:302`),
so:

- `cluster_max` is correct — it is the size of the largest cluster.
- **`cluster_span` is not a maximum.** It is the span of whichever largest-size
  cluster sorted first. `base-P1-r2` has eight clusters of size 3; the ceiling
  one is not necessarily first, and `[:5]` can drop it from the reported list
  entirely.

Re-derived by the audit, reported vs true maximum span:

| run | reported | true max |
|---|---|---|
| `base-P1-r2` | 5 | **15** |
| `oldcode-P1-r1` | 5 | **37** |
| `null-P1-r2` | 8 | **36** |
| `drive-P1-r2` | 3 | **24** |

**A gate has already been decided on this number.** Case 20 cancelled the durable
staged-event memory (the MEMORY factor) on `cluster_max >= 4` **and**
`cluster_span >= 10` in both cells. Re-derived, the span half is satisfied almost
everywhere; the conjunction still fails on `cluster_max` (base median 3), so the
cancellation survives — **but it survived on a scalar that was wrong**, and that
has to be written down rather than quietly re-confirmed.

## What to build

**1. The reporting fix** (~10 lines, `repetition_metrics.py:624-626`).
Report the maximum span across clusters, not `clusters[0]`'s. Stop truncating to
five, or report a count alongside. Add the count of clusters of size ≥3, which is
the number a human actually wants.

**2. The scanners that do not exist.** Same shape as the existing metrics —
offline, over an archived session, zero provider cost.

> **Scope cut, 2026-08-05.** This was five scanners. It is now **three** — the
> ones a wave-1 task reads before it can choose a fix. The phase rule *"every task
> ships a scanner or extends one"* was multiplying: five scanners, each with a
> seeded positive and negative and an archive run, is more work than the four
> wave-1 fixes combined, and two of them serve tasks that do not start until after
> the checkpoint re-derives their population anyway. Build a scanner when the task
> that reads it is being designed.

Ship in this task:

- `REDACTION_MARKER` occurrences, split by **channel**: prose, persisted speech
  record, and the perspective ledger. **Task 63 cannot choose between its four
  options without this** — it is the only scanner here that decides a design.
- Persisted speech records whose text came from a Director `audible_speech`
  event rather than from the character agent. Task 65's primary number, and the
  before/after for the phase's largest cut.
- Records whose audience is empty for an event the zone graph should have made
  audible. Task 67's closure evidence.

Deferred to the task that reads them:

- **Internal character ids (`C\d+`) in prose or a persisted record** → task 65.
  n=1 in the corpus and 65 closes the channel it arrived through; 65 already
  requires this as a *test*, which is the cheaper form and the one that prevents
  regression. No archive scan needed for a population of one.
- **Names in dialogue resolving to no cast id** → **task 66**, wave 3. 66's own
  falsifier says the phantom names may vanish once 65 and 69 land, so scanning
  the pre-wave-1 archive for them measures a population that is about to change.
  The check itself is still the cheapest item in 66; it moves, it does not die.

**3. `material_delta_rate` stays specified and NOT authorized.** Its
justification died with the premise above. Re-open it after task 69 exists and
there is a structural notion of "already staged" to judge against. Leave the spec
in place; do not implement it in this task.

## Counter-argument, recorded

*"A semantic judge is still obviously better than lexical similarity."* Possibly.
But the argument for it was that lexical similarity **cannot** see restaging, and
that argument is now known to be false — it saw it, and a reporting bug hid it.
Spending the phase's most expensive item on a premise that did not survive its
first audit is exactly the failure this project keeps repeating. Earn it with
evidence from the fixed instrument first.

## Closure evidence required

- [x] `cluster_span` reports a maximum; unit test with a hand-built cluster set
      where the largest-size cluster is not the widest
      (`tests/test_repetition_metrics_clusters.py`);
- [x] the whole archive re-scored, and `benchmarks/` amended where a documented
      number changes;
- [x] a note in `benchmarks/README.md` §7 recording that `cluster_span` was
      misreported and which decision was taken on it;
- [x] each of the **three** scanners has a test with a seeded positive and a
      seeded negative (`tests/test_immersion_scanners.py`);
- [x] the three run against the archived P1 and P2 batteries and their output is
      committed alongside, so wave 1 has a before number
      (`benchmarks/*/immersion-scan.json`, defined in `README.md` §8);
- [x] `material_delta_rate` still unimplemented, with a comment pointing here.

## What the fixed instrument and the three scanners actually found

**Delivered 2026-08-05.** `tools/acceptance/immersion_scanners.py`, run over both
archived batteries.

**The reporting bug was real, and the re-derivation reproduces the audit exactly**
— `base-P1-r2` 5 → **15**, `oldcode-P1-r1` 5 → **37**, `null-P1-r2` 8 → **36**,
`drive-P1-r2` 3 → **24**. `cluster_max` never moved, because the list was already
sorted by size; only the span was wrong. Both batteries' `metrics.json` now carry
corrected values plus `cluster_count` and `cluster_count_ge3`.

The scanners reproduce the roadmap's baseline numbers from a second, independent
implementation — 49 P1 redaction markers in prose and records, 12 of 12 sessions
with Director-authored speech at 21–41%, 33 empty-audience records in 5 of 12
sessions, 2 of 1,868 raw Director events proposing an empty witness list. Three
things they add that the baseline did not have:

1. **The redaction damage is larger than the transcript count suggests, and it
   is durable.** 87 markers in P1, not 49: the missing 38 are in the perspective
   **ledger** — `recent_memory` and `memory_summary`, i.e. what a character
   *remembers* someone saying. One mutilated public line propagates into every
   witness's durable memory, which is why the persisted-record count understates
   the reach. Task 63's channel split is now three ledger sub-channels, not one.
2. **31 of the 33 empty-audience records are the zone graph cutting people off;
   2 are the Director narrowing its own witness list to nothing.** The scanner
   refuses to ask the graph whether the audience should have been empty — that
   question is circular when the graph is the suspect — and classifies by whether
   anyone else was *present*. It also recovers the clamped witness counts: **18**
   in `base-P1-r2`, **19** in `null-P1-r1`. See task 67, which this confirms and
   sharpens.
3. **The two "narrowed to none" cases are a defect nobody had named**
   (`oldcode-P1-r1` T18/T19): the Director listed the **speaker as the only
   witness of their own shout**, and then three people the graph put out of
   earshot. Two occurrences, so it is a footnote, not a task — but it is not the
   graph bug and a fix for the graph will not remove it.

**Also measured here, for task 71** (it needed a number and the machinery was
warm): scenes split into more than one mutually-perceiving cluster on **168 of
610 narrated turns (28%)**, bimodally — 8 of 16 sessions never split, 5 split on
42–78% of turns. That is an **upper bound measured on the broken graph**; the
number is recorded in task 71 with that caveat attached.

### One observation worth checking at the checkpoint — NOT a gate

`benchmarks/README.md` §5's headline complaint is that every metric scored
`base-P1-r2` clean while a blind reader ranked it **worst of twelve**. Of the
corrected cluster family, `cluster_count_ge3` is the one that does not:

| run | `cluster_max` | `cluster_count_ge3` | blind rank |
|---|---|---|---|
| `base-P1-r2` | 3 | **8** | **12 of 12** |
| `oldcode-P1-r1` | 4 | **8** | 11 of 12 |
| `base-P1-r1` | 2 | 0 | 3 of 12 |

`base-P1-r2` is **tied for the highest count of situations that came back three
turns or more**, with the session the reader ranked second-worst — while
`cluster_max` (3) puts it below the Case 20 gate and `RSR_prop` (1.7%) calls it
the cleanest run in the battery. Against the reader's full ranking it scores
ρ = +0.60 in the correct direction, where `RSR_prop` is −0.09 and `cluster_max`
is +0.05.

**This is an observation, not a new gate**, and it is written down here so it is
not quietly promoted into one. n = 12, one battery, and `beat_occupancy_max`
scores higher (+0.74) on the same ranking without anyone claiming it measures
reading quality. The phase's rule stands: deterministic per-defect counters gate
their own task, and narrative quality is judged by the blind read. **Re-check
this column at the checkpoint** — if it survives a second battery, it is worth an
argument; if it does not, it was n=12.

The gate the correction was supposed to settle **survives**: Case 20 cancelled
the durable staged-event memory on `cluster_max >= 4` AND `cluster_span >= 10` in
both cells. With the corrected spans the span half is now satisfied nearly
everywhere (10 of 16 runs changed, up to 5 → 37), but `base` runs at
`cluster_max` 2 / 3 / 3, so the conjunction still fails and the cancellation
stands — now on numbers that are right.

## Also record here: `NSR` and `SIL` are not gates

While re-deriving `cluster_span` this task's audit found the phase's acceptance
gate is inverted — `NSR` correlates with the blind reader's ranking at
**ρ = +0.923 in the wrong direction**, and `SIL` is `0.0` in 16/16 runs. Full
derivation in `.plan/ROADMAP.md` §"The acceptance gate this roadmap shipped with
was inverted".

- [x] `benchmarks/README.md` §7 records that `NSR` measures event volume, is
      anti-correlated with read quality on this corpus, and is not a gate;
- [x] `SIL` listed with `REVERT` as a floor-effect metric with no power.

**Done 2026-08-05, ahead of the rest of this task**, because §7 is where metric
trust lives and anyone reading it in the meantime would still have gated on
`NSR`. The same pass gave §7 a **glossary** — every short name used in the
archive's tables (`RSR_prop`, `BOCC`, `GUARD`, `cluster_*`, `max_hint_repeats`)
now has a definition, a `file:line`, and its catch. It had none, which is what
let the `DEFAULT_TAU` / `CLUSTER_TAU` confusion above happen in the first place.

**The measurement that would falsify this task:** if the re-derived
`cluster_span` matches the reported one across the archive, the reporting bug is
imaginary and only the scanners remain.
