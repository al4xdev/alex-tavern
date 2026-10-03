# Runner anchor-coverage screen, 2026-10-03

## 1. Observed input boundary
Two real Runner.player_turn submissions, in isolated /tmp storage, persisted
revision 1 and revision 2. Deterministic planner/Director/render doubles forced
a storm beat with anchors "viga" and "portal verde". The green portal was
already closed and intact in canonical scene facts/history before submission 1;
the beam and portal were both mentioned in persisted events before submission 2.
Replan cleared the new beat's anchors_seen, and each actual Director request
rendered "Not in play yet — introduce as concrete perception events: viga,
portal verde". This reproduces coverage status being presented as world
existence/introduction status. Fault injection establishes this boundary
condition, not its frequency among unconstrained planner outputs.

## 2. Measured raw-call completion, not a population reliability estimate
PREREGISTRATION.md and script/source/request hashes in ignored manifest.json
precede the sixteen fresh direct curls. One synthetic session supplied two
submissions; these are repeated draws from those fixed inputs, not sixteen
independent play sessions. DeepSeek V4 Flash, high thinking, 8192 output tokens,
four calls per submission/arm, no retries or replacements.

| Captured submission | Control schema-valid / attempted | Coverage-label schema-valid / attempted |
| --- | --- | --- |
| 1 | 4/4 | 3/4 |
| 2 | 4/4 | 4/4 |

All sixteen replies were HTTP200, with distinct response IDs and nonempty
provider-returned reasoning. submission1-coverage-3 omitted required
scene_blocking.destination_reachable_this_beat; local validation rejected it.
Its raw JSON and failed result remain preserved. No attribution of that
omission to the label change is established.

## 3. Observed semantic reading
Reader 57b1c0d71925 received fifteen schema-valid outputs with shuffled labels,
without arm labels or a supplied verdict. Its source packets used the common
control source for both arms: the source-conflict finding therefore cannot
measure whether the candidate prompt removed that conflict. Candidate versus
control request construction is separately explicit in the frozen manifest.

Across these fifteen outputs, the reader found no fresh green-portal closure,
forced voluntary action by waiting Iara, or private thought/speech disclosure.
Reading confirmed continuing closure and new roof cracks, displaced wood or
water entry. Complete controls also avoided fresh closure: no reduction of
portal restaging is established here.

The reader flagged repeated wind/beam framing in R03 (submission2-coverage-2)
and R12 (submission2-control-3), but both also add physical consequences.
Its R05 objection that vibration/humming contradicts "closed and intact" is
not supported by that source: closure and integrity do not require inertness.
Do not count it as an established physical contradiction. These judgments
remain observations limited to this synthetic fixture, with placeholder
personas and no real planner, Character call or prose generation.

## 4. Decision and instrument limits
The pre-registered all-raw-valid gate failed; this screen does not authorize
delivery of the coverage-label candidate. Runtime source remains unchanged.
The failed reply is neither replaced nor retroactively counted as accepted.

Method critic c54a39cfb591 distinguished failure of the registered raw-call
contract from falsification of the semantic label hypothesis. This distinction
is warranted: production validates/retries up to three attempts, while this
screen deliberately ran single raw calls. One omission establishes a rejected
draw, not a causal effect of wording. Its statement that raw rejection aborted
semantic analysis is inaccurate: the fifteen valid replies were read.

Any subsequent acceptance screen must register its different boundary before
fresh calls and retain rejected attempts; it must not relabel this failed
screen as passing. Separating input truthfulness, production schema acceptance
and narrative consequences is a proposed next method, not measured improvement.
Task69 remains open: durable transition production, cross-submission transition
rejection and broader live fiction acceptance were not established.

Report critic 133c680ebee4 retained the boundary, raw-call gate outcome,
limited semantic reading and open-task claims. It marked the common-source
reader disclosure NEUTRAL; retain it as an audit limitation so that this reader
cannot later be quoted as an arm-specific input-correction test. No such
metric is claimed. Counterarguments remain bounded fault injection, small
samples and a control with no fresh closure in the responses read.

