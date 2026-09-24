# Objective-catalog screen result

Date completed: 2026-09-21

## Recorded decision

Under the pre-registered decision rule, this tested prompt shape does **not**
advance to Roteiro schema design. In both frozen contexts it returned the
required context label in 2/4 calls, below the pre-registered minimum of 3/4.
No Roteiro field, private target resolver or transition producer follows from
this screen.

This is a decision about this prompt shape on two payloads from one session. It
is not an estimate of model reliability or evidence that every prompt-safe
catalogue must fail.

## Evidence collected

The screen replayed two frozen production payloads from session
`20d4cdb3`: the turn-1 compile before team selection (C1) and the turn-9
replan at the beginning of the courtyard artifact test (C2). Four baseline and
four catalogue calls were made for each context, for 16 calls total. The
[preregistration](OBJECTIVE-CATALOG-PREREGISTRATION.md) fixes the payloads,
catalogue, arms and decision rules. Raw envelopes, extracted responses,
payloads and the deterministic blind key are in `objective-catalog-screen/`.

All 16 responses parsed and satisfied their respective schemas. The eight
candidate responses also returned one of the two allowed labels, so condition
1 passed.

| context | pre-registered requirement | observed candidate choices | condition 2 |
|---|---|---|---|
| C1, before selection | at least 3/4 `none` | 2 `none`, 2 `test_artifact_damaged` | fail |
| C2, artifact test | at least 3/4 `test_artifact_damaged` | 2 `test_artifact_damaged`, 2 `none` | fail |

Condition 2 failed in both tested payloads. That result alone stops this
candidate under the recorded decision rule.

## Blind content reading

An isolated Gemini reader received the 16 shuffled beats without arm, context,
selected label or private mapping. It classified the physical objective from
the prose and listed concrete agency, context and physical-sequencing defects.
Its response was saved before unblinding as
[`blind-reader.md`](objective-catalog-screen/blind-reader.md).

Condition 3 required the reader's prose classification to agree with at least
three of four candidate selections in each context. It passed: C1 agreed in
4/4 and C2 in 3/4. This establishes label-to-prose agreement for seven of the
eight candidate outputs read here. It does not establish that the selected
label was appropriate to the source context.

The read supplies the following small-sample observations:

- In C1, candidate beats X05 (`response-c1-b-1.json`), X06
  (`response-c1-b-4.json`) and X10 (`response-c1-b-2.json`) introduced active
  mana-test artifacts before team selection. The C1 baseline's one
  context-contradicting beat, X13 (`response-c1-a-3.json`), prematurely ran a
  different scoring test. Whether the catalogue caused this contrast remains
  unverified.
- In C2, candidate X15 (`response-c2-b-4.json`) selected `none`, while the
  reader classified its prose as `test_artifact_damaged` because an artifact
  broke. This is the one candidate disagreement counted under condition 3.

Condition 4 required the candidate to have no more concrete agency,
context-contradiction or physical-sequencing defects than baseline within
either context, and no private-token leak. The registration asked the reader
to list defects but did not say whether several claims inside one bullet should
count separately. Treating each returned bullet as one finding gives the
following audit index:

| context | arm | agency bullets | contradiction bullets | sequence bullets |
|---|---:|---:|---:|---:|
| C1 | baseline | 7 | 1 | 0 |
| C1 | catalogue | 5 | 3 | 1 |
| C2 | baseline | 7 | 4 | 4 |
| C2 | catalogue | 5 | 1 | 4 |

The same C1 contrast appears without splitting bullets: context contradictions
occur in 3/4 candidate beats and 1/4 baseline beats, while a sequence defect
occurs in 1/4 candidate beats and 0/4 baseline beats. Thus both readings violate
the literal "no more defects" rule in C1. Two report critics disagreed about
status: one treated agreement across both units as a measured condition-4
failure; the other held that the unregistered aggregation rule prevents an
independent pass/fail claim. This report retains the stricter status and records
the result as observed, because condition 2 already stops the candidate and
condition 4 cannot change that decision. The [first critique](objective-catalog-screen/result-report-critic.md)
and [revised-report critique](objective-catalog-screen/result-report-critic-v2.md)
preserve the disagreement.

The pre-registered literal-token subcheck found zero exact occurrences of
`turma-test-artifact`, `integrity` or `damaged` in the eight candidate prose
outputs. Semantic secrecy was not evaluated.

## Scope and next action

The experiment never reached private target resolution or deterministic state
consumption, so it provides no evidence for or against those later stages. The
observed failure is limited to the candidate's two pre-registered context
selection gates.

Any subsequent prompt variant requires a new preregistration and screen. The
reason three C1 candidate beats contained future artifact-test material remains
undiagnosed. Task 69 can continue its deterministic transition work, while this
screen adds no model-authored physical target path.
