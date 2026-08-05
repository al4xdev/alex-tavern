# Task 68 — Fix the cluster reporting, then scan

> **Status:** open. **Wave 0** — nothing else in the immersion roadmap should
> ship before this, because every other task's counterfactual is measured with
> this instrument.
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

- [ ] `cluster_span` reports a maximum; unit test with a hand-built cluster set
      where the largest-size cluster is not the widest;
- [ ] the whole archive re-scored, and `benchmarks/` amended where a documented
      number changes;
- [ ] a note in `benchmarks/README.md` §7 recording that `cluster_span` was
      misreported and which decision was taken on it;
- [ ] each of the **three** scanners has a test with a seeded positive and a
      seeded negative;
- [ ] the three run against the archived P1 and P2 batteries and their output is
      committed alongside, so wave 1 has a before number;
- [ ] `material_delta_rate` still unimplemented, with a comment pointing here.

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
