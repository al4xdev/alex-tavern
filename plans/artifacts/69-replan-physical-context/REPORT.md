# Physical facts did not validate this replanner insertion

2026-09-14. **OBSERVED, one selected session (fb62cc2f T7):** adding the
complete canonical physical-facts dictionary to the recorded replan request
does not qualify for follow-up under the disclosed clarified rule below.
Candidate B0/V5 plans escape
through “arcos ainda abertos antes que Holt consiga lacrá-los”, although the
inserted state says the four arches are closed. Candidate B1/V7 also offers
the arch passages as available exits without opening them. No runtime change
is validated. The same insertion will not be tuned on this frozen payload.

## Execution and reading

The source is the accepted replan at line 86 of
`../77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl`. A preserves its
messages and request settings. B adds only `CURRENT PHYSICAL FACTS` as JSON
after LOCATION/TIME, from `state.json` history[55].scene_snapshot. That record
is the T7 physical-action input. The open-door and closed-arches facts also
appear in the accepted T7 Director request at line 88. The manifest records
source hashes; a direct comparison confirmed that removing this insertion
makes A and B equal. This tests a payload, not a production builder.

**Execution count, not quality:** four responses per arm; all eight HTTP 200,
schema-valid, one attempt each. The validator accepts the recorded JSON schema;
it does not establish narrative correctness.
Calls use real curl, shuffled order, concurrency four, and the original model
and token limit. Requests, responses and durations remain in `runs/`.

The [original rule](PREREGISTRATION.md) was written before calls and its hash
is recorded in run.json. A subsequent protocol critique identified ambiguity
in eligibility and bias from source checking after revealing arms. The dated
addendum, made after calls but before reading alternatives, explicitly blocks
material ambiguity and moves source adjudication before unblinding. This
is a disclosed restriction of the rule, not an original preregistered detail.
The original candidate clause was: “B is eligible for a production-builder
follow-up only if none of its valid responses contains a source-checked
unsupported antecedent or a material continuity/agency regression.” Report
critics disputed whether “regression” means an absolute continuity defect or
a demonstrated worsening relative to A, which also offers closed arches as
exits in V3. That ambiguity is real: this report does not claim B is worse
than A or that the original wording unambiguously forces rejection. Under
the disclosed clarification, unresolved material continuity blocks follow-up;
V5's open arches supply a direct conflict, not just an absence of proof.

The isolated literary reader saw preceding visible fiction, canonical facts
and opaque alternatives. A separate source reader also saw accepted prior
responses and the replan input, distinguishing plans and attempts from
execution. The [blind adjudication](BLIND-ADJUDICATION.md) was saved before
consulting the key. Full readings are in [FICTION-VERDICT.md](FICTION-VERDICT.md)
and [SOURCE-VERDICT.md](SOURCE-VERDICT.md).

| Output | Arm/repeat | Source-checked reading |
|---|---|---|
| V1 | A3 | Treats a planned leadership dispute as underway; prescribes Holt/Maelis decisions. Door mechanics ambiguous. |
| V2 | A0 | Same unsupported leadership-discussion antecedent; equipment determining teams remains ambiguous. New invasion itself is plausible. |
| V3 | A1 | Wooden door becomes iron; offers immediate departure through closed arches without opening them. |
| V4 | B3 | Supplies Link near the central table after an unresolved attempt from the depot; movement continuity remains unclear. |
| V5 | B0 | Calls closed arches still open and Holt's planned sealing underway; crystal falls from the table but its anchor remains on the table. |
| V6 | A2 | Main invasion is compatible; blood becoming a present problem is ambiguous given the already bleeding messenger. Readers differ on required injury as event versus forced outcome. |
| V7 | B1 | Southern corridor existed, but current availability/safety and usable arch passages are not established; containment option conflicts with required invasion/retreat. |
| V8 | B2 | Raised-shield antecedent exceeds explicit confirmation of Bram's position; crystal in Holt's glove conflicts with table location while echoing ambiguous input wording. |

The original arm reproduces an unsupported prior-plan antecedent in V1/V2,
but the precise historical iron-bar/wax-seal antecedent does not recur in
these eight outputs. This distinction prevents claiming a measured reduction
of that exact symptom. Candidate V5 supplies another unsupported sealing
antecedent, now about the arches, with an explicit state contradiction.
Individual alternatives are repeated generations of one selected context;
there is no per-session population estimate or overall quality score.

## Corrections and next boundary

The supplied state already contains a stale messenger location: T2 director,
line 20, writes `plataforma_de_comando` with the messenger retained at the east
door. T4, line 42, adds `feridos_no_portao_leste` saying he reached the command
platform; T6, line 74, adds `mensageiro_ferido` with arrival there. All survive
in the T7 physical-facts input, alongside the T6 blocking that places him partway
there. These entries are supplied together under CURRENT PHYSICAL FACTS,
without timestamps separating old from current locations. Thus providing
canonical state is not equivalent to providing internally consistent state.
This observation does not establish that the stale messenger
fact caused any candidate defect or that an additional memory mechanism is needed.

The deterministic [delta replay](trace_state_delta.py) invokes the current
`Runner._update_scene` on an isolated copy of the T3 snapshot with the accepted
T4 delta. It reproduces the entire T4 physical-facts snapshot exactly: the delta
adds `feridos_no_portao_leste` and never updates/removes `plataforma_de_comando`,
so both statements remain. Its first assertion failed when the trace mistakenly
used the T4 post-update snapshot as input; correcting the source to T3 made the
boundary check pass. This identifies retention under the existing delta contract,
not a persistence race or a demonstrated cause of replan behavior.

The delta replay is a separate bounded trace within task 69, not evidence that
messenger-state retention caused the arch defect or deserves priority over
other hypotheses. The broader cause remains undiagnosed. This experiment does
not validate deleting the planner or adding facts globally.
