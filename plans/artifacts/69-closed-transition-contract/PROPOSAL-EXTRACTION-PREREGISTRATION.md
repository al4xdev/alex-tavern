# Proposal-boundary physical extraction screen

Registered 2026-09-24 before any calls for this screen.

## Question and scope

Can a separate model read the accepted Director's **pre-render proposal** and
identify the clear T28 pillar change without proposing the same state again at
T29? The target is a transition *warranted by the proposal*, not the actual
later world state or the renderer's prose. T29's rubble-gap passability has no
settled source label and is descriptive only in this screen.
This is a fail-closed screen of one proposed extraction contract on two adjacent archived
turns from one session, not a model reliability estimate or an end-to-end
producer validation. No code or schema ships from a passing screen alone.

The frozen source is `plans/artifacts/p1-archive/base-P1-r2/sessions/8bd4d0f1/debug.jsonl`,
successful first-attempt Director responses at turns 28 and 29. The new
request projects only `scene_blocking.spatial_constraints`,
`perception_events[].content` and `scene_update` from each response. It never
includes character IDs, witness IDs, the persisted prose response or the
historical physical-fact bag. This projection is part of the tested contract.
The Director contract defines `scene_blocking` as a **pre-decision** spatial
draft. It supplies the situation before the later event list, not an after-state
that can contradict a subsequent event.

The source-inspired catalogue contains two public labels and fixed states:

- cracked hall pillar, integrity: T28 current `damaged`, T29 current
  `destroyed`; candidate new state `destroyed`;
- rubble gap to inner corridor, aperture: current `ajar` in both turns;
  candidate new state `closed`.

The per-turn starting states and catalogue are a manually chosen test fixture.
They are not historically persisted typed state, and no automatic entity registration is
under test. The model receives the current state and may return `change`,
`no_change` or `uncertain` per property. `change` names only the fixed candidate
new state, never a free model-authored value, and is valid only if the candidate
differs from that property's current state. This is a judgment about the named
integrity or aperture dimension, not about every possible physical change to
the object. `uncertain` means no transition is authorised; it is distinct from
asserting no change occurred.

## Fixed read and decision rule

Run four separate DeepSeek V4 Flash `curl` calls on each frozen turn, eight
total, using the same prompt, schema, model settings and source projection.
These are repeated samples, not statistically independent units; record
request IDs, temperature and any provider seed setting if available.
Save redacted requests, raw envelopes, parsed outputs, source hashes and the
script hash before scoring. Use local schema validation; a connection failure,
non-200 response or invalid JSON/schema is invalid, with no replacement call.

The source-boundary expected labels are fixed before execution:

| turn | pillar | gap | why |
|---|---|---|---|
| T28 | `change` | `no_change` or `uncertain` | Director stages the pillar collapse; no complete gap seal is asserted, while the collapse may still alter an opening within `ajar` |
| T29 | `no_change` or `uncertain` | **unscored** | Pillar integrity is already `destroyed`; moving remnants could change geometry without a new integrity value. The pre-decision draft has a narrow gap and the subsequent event says blocks obstruct it, without fixing post-event passability |

Technical gate: all eight calls must return valid contract objects. Content
gate: all four T28 outputs must choose `change` for the pillar and none may
choose `change` for the gap; all four T29 outputs must avoid `change` for the
pillar. Record every T29 gap label, but do not score it as correct or incorrect.
This deliberately strict operational gate is not a reliability estimate. Any
failure stops this candidate before a renderer or Runner implementation; a
failure may reflect source ambiguity or sampling rather than an extractor defect.
Passing permits a second, independently selected source case that includes an
unambiguous gap transition and a producer-to-renderer fidelity screen; it does
not authorise production code.

Judge the full physical proposal in order: spatial draft, event list and scene
update. Do not relabel the T29 gap from the later narration. The event saying
blocks "bloqueiam a fresta" and the observation carrying calls through a gap
must both be shown to the extractor; omitting either would change the variant.
An independent text-only reader assessed the T28/T29 wording before this
screen, but did not know the code contract's pre-decision timing. That later
contract check is why T29 gap now has no gold label. If later source review
changes a scored label, this screen is invalidated and must be registered
again; it is not rescored post hoc.

This screen has no A/B causal claim. Its eight outputs are repeated samples of
two payloads in **one session**, so counts are only a stop/advance decision for
this prompt shape. The storage validator would reject a repeated transition
even if the model proposed one, but cannot decide whether a textual assertion
was semantically warranted.
