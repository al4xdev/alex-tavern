# Disposition after measurement: two axes survive, the public prior does not

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 16 |
| **Date** | 2026-07-21 |
| **Program** | Task 43, character disposition substrate |
| **Status** | Measured closure, including a negative Phase 4 |

## Abstract

Task 43 began with three candidate disposition axes and a proposed unification:
public persona as a shared prior, observer-relative relationships as posteriors.
Measurement narrowed that design. Warmth was blind-readable in 8/10, 9/10 and
9/10 trials; Trust reached 10/10 on a balanced stimulus; Composure failed in all
three batteries (5/10, 5/10, 7/10) and was removed rather than persisted as
decoration. A relationship appraisal classified directional changes reliably
enough to ship behind an opt-in flag, including betrayal at 4/4 and zero false
positives on neutral turns.

The proposed public-prior bridge did not survive its own gate. Through the exact
production Character path, low versus high public Trust separated only 5/8. An
explicit semantics variant, pre-registered before execution, fell to 4/8. The
feature was removed. The related boundary did confirm that the Director adjudged
an overclaimed power-8 attack against real capability in 3/3 runs, while a new
code gate now prevents omniscient appraisal from revising relationships without
witnessed evidence.

The shipped result is therefore smaller than the proposal: lazy, witnessed,
observer-relative Trust/Warmth with code-owned scalars and model-visible bands.
Public-vs-real persona remains a distinct unsolved product problem.

## 1. The invariant that did the cutting

The scalar belongs to code; only a qualitative band reaches a model. An axis
earns persistence only if a blind reader can identify its behavioral pole. This
kept numeric integration deterministic and made removal possible when a candidate
failed. It also separated two questions that had looked identical on paper:

- a relationship formed through events can become a useful dyadic state;
- a static first impression does not automatically become useful merely because
  it is represented by the same scalar.

## 2. Phase 2: which bands reached behavior

The gate used production Character builders, five renders per pole and a blind
forced-choice judge. An axis passed at 8/10 with a non-degenerate judge.

| Axis | v1 | v2 | v3 | Verdict |
|---|---:|---:|---:|---|
| Warmth | 8/10 | 9/10 | 9/10 | Retain |
| Trust | 7/10 | 5/10 | 10/10 | Retain after balanced stimulus |
| Composure | 5/10 | 5/10 | 7/10 | Cut |

The early Trust failures were stimulus failures: the first scene gave the axis
little room and the second forced caution regardless of band. A balanced request
to hold a package until morning separated 10/10. Composure did not recover under
three designs. A competent character still sounded composed in one utterance, or
the scene itself saturated both poles. Keeping it would have violated the task's
anti-complexity razor, so schema 13 removes it.

## 3. Phase 3: events move observer-relative state

The appraisal model sees the latest committed turn and emits qualitative shifts:
observer, target, Trust or Warmth, direction and slight/strong intensity. Code
maps that verdict to a bounded scalar nudge and applies gravity toward baseline.
The pre-registered real-provider battery required at least 3/4 per scenario and
four of five scenarios overall.

- Direction and ordered pair were reliable.
- The corrected betrayal case improved from 2/4 to 4/4.
- Neutral silent turns produced zero false positives in both rounds.
- Four of five scenarios passed; rescue sometimes classified Warmth rather than
  Trust, an honest soft boundary because both axes moved in the same direction.

The loop remains OFF by default because it adds one model appraisal to every
committed turn. Its arithmetic, gravity, serialization, undo snapshot and disabled
path are deterministic tests; the classifier is the explicitly variable part.

## 4. Phase 4: the public-prior proposal failed

The proposal encoded an authored public Trust/Warmth first impression as a scalar
prior. Before any dyad existed, a Character would read the target's public band;
the first witnessed relationship event would materialize a posterior whose
baseline was that prior.

The production boundary was pre-registered at four low-Trust and four high-Trust
renders under the same balanced package-custody stimulus. A blind judge needed at
least 7/8 and had to choose both poles.

| Variant | Only change | Result | Verdict |
|---|---|---:|---|
| v1 | Public band through the existing production note | 5/8 | Fail |
| v2 | Define Trust as reliance/verification and Warmth as receptiveness/hostility | 4/8 | Fail |

Both judges were non-degenerate. Low-Trust characters often accepted custody with
contractual safeguards; the blind judge reasonably treated acceptance as high
Trust. V2 made no reliable improvement. Thresholds and stimulus were not changed
after either result. The public-prior field, UI and prompt path were removed.

This does not disprove public versus real persona as a product concept. It rejects
one representation: a shared static Trust/Warmth band is too weak to carry bluff,
disguise, reputation and claimed capability. Those require their own authored and
witness-revisable semantic contract, not reuse by analogy.

## 5. Boundaries retained from the failed phase

Two adjacent claims passed independently:

1. **Real capability remains Director-side.** In three production Narrator calls,
   Link's public framing was maximally favorable but his real sheet fixed him at
   power 8 against Garran at 145. All 3/3 outcomes rejected victory-by-boast and
   none invented Link's will, courage, speech, thought or feeling.
2. **A posterior requires perceived evidence.** The appraisal model is
   Director-side and can see the whole turn, so code now clamps each proposed
   `observer→target` shift. The same target speech updates the observer when heard
   and is discarded when whispered away. This is deterministic and test-locked.

## 6. Cost and latency

The retained feature adds no call for reading bands, but the opt-in feedback loop
adds one sequential appraisal call per committed turn. The Phase 4 v1 gate made 22
sequential generation/judge calls in roughly 76 seconds; v2 made 16 in roughly
284 seconds. These are boundary wall times, not provider latency percentiles, but
their spread is the relevant product warning: an enabled classifier adds visibly
variable turn latency. The feature stays OFF by default.

## 7. Final contract

- Persist only Trust and Warmth, lazily per ordered observer→target pair.
- Numeric values remain in code; prompts receive qualitative bands only.
- Appraisal is opt-in and revisions require evidence perceived by the observer.
- Gravity relaxes values toward their neutral baseline.
- Composure is absent, not parked behind a dormant branch.
- Boldness remains Task 44's transient dramatic impulse, not a persisted axis.
- Public-versus-real persona remains open as a separate semantic design problem;
  the rejected public-prior implementation is not retained as fallback.

That smaller contract is the task's actual result. The negative is part of the
delivery: it prevented an elegant diagram from becoming permanent inert state.
