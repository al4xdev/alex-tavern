# Task 69 — Physical state as a closed transition

**Second source session, kennel gate, 2026-09-24:** in `oldcode-P1-r2/a3e1ceda`,
persisted T33 Narrator prose explicitly closes the kennel gate, although the
T33 Director event says only `tranca` and its status is `trancado`. Final accepted
T34 Director retry and persisted prose close it again; T35 accepted event and
persisted prose close it a third time, with no intervening reopening. The T37
Director proposes another closure, but the recorded viewer's renderer input and
persisted prose omit it, so T37 is not counted as reader-facing repetition.
This is a second archived session, not a prevalence or causal estimate. The
[source finding](../../plans/artifacts/69-closed-transition-contract/T34-T35-KENNEL-GATE-REPEAT-FINDING.md)
separates the accepted proposal from persisted narration and the `trancado`
status from aperture closure.

**Action-only blue-gate candidate also stopped, 2026-09-24:** a second
pre-registered smoke test removed state comparison from the model input and
asked only whether each accepted proposal asserted a new completed gate
closure. All 16 curl calls were HTTP-200, schema-valid and supplied literal
event quotes. T37, T38 and T39 each matched their local label in 4/4 calls;
T36 yielded one `true` that quoted a warning that five seconds **remain**
before closing. The all-output semantic gate therefore failed. The quote
does not diagnose tense, keyword anchoring or other-event confusion, and the
three positive/negative turns do not establish semantic reliability. No
producer follows. See the [registered rule](../../plans/artifacts/69-closed-transition-contract/BLUE-GATE-ACTION-PREREGISTRATION.md)
and [result](../../plans/artifacts/69-closed-transition-contract/BLUE-GATE-ACTION-RESULT.md).

**Blue-gate extractor candidate stopped, 2026-09-24:** a pre-registered
four-turn screen on `7fd84e9a` T36–T39 included the T37 time-skip closure,
T38's repeated closure, and T39's same-state/no-new-closure control. All 16
fresh curl calls were HTTP-200 and schema-valid, but the semantic gate failed:
T38's `repeated_closure` was false in 3/4 calls; the fourth marked an aperture
`change` even though current and candidate were both `closed`. T36's discrete
`ajar -> closed` fixture also received only 1/4 expected `no_change` labels.
T37 and T39 controls matched 4/4 each. This is one session and one prompt shape,
not model reliability or a repair. No producer integration follows. See the
[registered rule](../../plans/artifacts/69-closed-transition-contract/BLUE-GATE-EXTRACTION-PREREGISTRATION.md)
and [result](../../plans/artifacts/69-closed-transition-contract/BLUE-GATE-EXTRACTION-RESULT.md).

**Blue-gate restaging source case, 2026-09-24:** in archived `7fd84e9a`,
T37's accepted time-skip summary closes the blue gate, `scene_update.gate_blue`
is `fechado`, and the persisted prose depicts the doors meeting. T38's accepted
Director event and persisted prose close that same gate again without an
intervening reopening; T38's update still says `fechado`. An isolated
content-only reader agreed this is a repeat of the completed closure, while
the characters' crossing requires separate assessment. This is one source
case, not a rate or producer validation. A storage-only refusal that leaves the
proposed event in prose would not repair the reader-visible repeat; the actual
repair path is untested. The next diagnostic can use the real T38 proposal with
a manually anchored `closed` aperture, checking both state and final prose.
See the [source finding](../../plans/artifacts/69-closed-transition-contract/T37-T38-BLUE-GATE-REPEAT-FINDING.md).

**Retry content read and T23 correction, 2026-09-24:** a purposive read of 12
archived repetition-retry turns across 12 sessions kept T32 as a source-checked
persisted same-turn physical conflict. Discarded-draft conflicts in other turns
were removed by retries; the read did not establish a general retry effect or
prevalence. Its initial T23 early-render verdict is **withdrawn**: the source
packet omitted `time_skip_summary`, which explicitly revealed the team and was
included in the actual renderer request as a confirmed event. T24 re-proposes
that already accepted reveal, a Director-beat repetition relevant to this task,
but not a demonstrated renderer invention. Future fidelity packets must include
every event the renderer actually received. No model guard or runtime change is
adopted from this read. See the
[read and correction](../../plans/artifacts/69-closed-transition-contract/REPETITION-RETRY-CONTENT-READ.md)
and [T23 withdrawal](../../plans/artifacts/69-closed-transition-contract/T23-EARLY-TEAM-REVEAL-FINDING.md).

**Renderer fidelity boundary, 2026-09-24:** a source check of archived
`5c994c42` T32 found an accepted Director state keeping a dust creature
active while the persisted narration says its remains disappear without trace.
The first prose response preserved the active threat; the contradictory
second followed a lexical-repetition correction. One isolated text reader
confirmed the physical conflict. Whether the correction caused it is
undiagnosed, and this one turn is no prevalence estimate. The case motivates
the next real-payload fidelity test before a producer is wired to narration.
See the [source finding](../../plans/artifacts/69-closed-transition-contract/T32-PROSE-STATE-FINDING.md).

**T32 retry replay, 2026-09-24:** the pre-registered comparison of the archived
lexical correction with a generic physical-fidelity reminder is **incomplete**:
eight curl calls returned HTTP 200, but one original-arm response contained an
extra JSON key, so only 7/8 met the required schema. No replacement call or
semantic A/B score followed. A separate blind prose read was descriptive;
readers disagreed on whether a candidate-arm passage erased the creature, and
the valid original-arm texts did not reproduce the archived explicit
disappearance. No correction or producer change is adopted. See the
[registered rule](../../plans/artifacts/69-closed-transition-contract/T32-RETRY-V2-PREREGISTRATION.md)
and [result](../../plans/artifacts/69-closed-transition-contract/T32-RETRY-V2-RESULT.md).

**Curated fidelity-reader screen, 2026-09-24:** a separate model compared three
accepted Director/prose pairs (T8 gates, T32 first prose, T32 persisted retry)
under a frozen contradiction rubric. Only **6/12** fresh curl responses matched
the required verdict/quote schema; the other six returned schema-shaped
objects rather than verdict instances. The all-valid prerequisite failed, so
no semantic gate was scored. Two valid responses supplied quotes that appear
to oppose their own verdicts, a descriptive concern only. This reader is not
adopted; it neither repairs the T32 conflict nor validates an end-to-end
producer. See the [registration](../../plans/artifacts/69-closed-transition-contract/PROSE-FIDELITY-LOCAL-PREREGISTRATION.md)
and [result](../../plans/artifacts/69-closed-transition-contract/PROSE-FIDELITY-LOCAL-RESULT.md).

**Second source screen, 2026-09-24:** one archived hall-gate sequence supplied
T7 (no opening), T8 (explicit `ajar -> open`) and T10 (impact while still open,
no `open -> closed` warrant). The pre-registered local rule passed: 12/12
HTTP-200, schema-valid responses, with 4/4 expected aperture labels on each
turn. These are repeated samples of **three proposals in one session** with
manual starting states; T8's positive update is explicit. T10's repeated guard
may be a separate continuity defect, and its `no_change` label alone does not
prove the extractor noticed the impact. This does not validate a model producer,
newly created gaps, narrative quality or reliability. The next diagnostic is
proposal-to-renderer fidelity on a real accepted Director proposal, followed
by the unresolved dynamic-entity and independent-escalation boundaries. See
the [V2 registration](../../plans/artifacts/69-closed-transition-contract/DOOR-EXTRACTION-V2-PREREGISTRATION.md)
and [result](../../plans/artifacts/69-closed-transition-contract/DOOR-EXTRACTION-V2-RESULT.md).

**Pre-render extraction screen, 2026-09-24:** a separate model call on two
archived Director proposals from one session met its pre-registered **fixture
gate**: 8/8 schema-valid curl responses; T28 selected the pillar integrity
change in 4/4, and T29 avoided a new transition into its already held
`destroyed` state in 4/4. This is no reliability estimate or live producer.
The T29 rubble-gap choice was deliberately unscored because its post-event
aperture was not source-labelled; all four calls nevertheless selected
`ajar -> closed`. That is an observed tendency on one ambiguous payload, not
four established errors or proof of closure. No model-produced transition is
wired to the Runner. A separate existing-door aperture screen is now recorded
above; it does not resolve the rubble gap. See the [registered rule](../../plans/artifacts/69-closed-transition-contract/PROPOSAL-EXTRACTION-PREREGISTRATION.md)
and [result](../../plans/artifacts/69-closed-transition-contract/PROPOSAL-EXTRACTION-RESULT.md).

**Pillar-pair source-boundary correction, 2026-09-24:** the 8bd4d0f1 T29
`ajar -> closed` **aperture** label in the deterministic fixture is synthetic.
The later persisted narration says "vedando por completo o acesso", which
closes **access**, not necessarily the named opening's aperture. Neither
source boundary unambiguously labels that aperture. T29 `scene_blocking` leaves a narrow
basal gap **before** the decisions, then an event says blocks obstruct it and
an observation routes Liora's calls through it. The pre-decision gap can be
blocked later without contradiction; sound transmission alone cannot establish
physical passage. The proposal does not unambiguously assert a complete seal.
The accepted T29 `scene_update` repeats `pilar_rachado:
desabado`, while the prose again depicts blocks falling; whether a whole
pillar falls twice or remnants move is unresolved by that wording. The fixture
still proves duplicate rejection and an independently chosen legal transition
at the storage boundary. It does **not** prove a producer can extract that
legal transition from the Director output or correct prose before render.
See the corrected [pillar-pair result](../../plans/artifacts/69-closed-transition-contract/PILLAR-PAIR-RESULT.md).

**Durable growth boundary, 2026-09-21:** a code-path audit finds no cardinality
branch in physical registration, `asdict` serialization, current-schema
reconstruction or `save_game`/`load_game`: every map entry is copied and
validated. A regression now registers 41 entities, persists them through that
path and requires the exact 41 IDs after load, one above the descriptive fact
bag's separate `_MAX_PHYSICAL_FACTS = 40` cap. The checklist's old eviction
concern is therefore resolved for current physical-state persistence by a
no-eviction ownership contract and a regression at the known cap, rather than
telemetry around lossy eviction. This does not establish a practical maximum or
cover memory, large-manifest latency, runtime registration or future persistence
paths; prompt projection remains a separate bounded read concern.
`uv run pytest -q` passes 1,191 tests with 2 LLM tests deselected; see the
[growth-boundary result](../../plans/artifacts/69-closed-transition-contract/PERSISTENCE-GROWTH-RESULT.md).

**Active-only catalogue stopped; recorded escalation decomposed, 2026-09-21:**
the active-only prompt candidate failed its fixed boundary. All 20 calls were
technically valid, but the model selected the active C2-G label in 1/4 calls and
the blind reader found the target in 2/4 C2-G prose beats, below both 3/4
requirements; C1-G also had one blind-reader agency flag against zero in C1-A.
The separate full-versus-active contrast remained undiagnosed because C1-A
itself had future-test intrusion in 2/4. No schema or activation resolver for
this candidate follows. A source read then interpreted T29's later persisted
narration as sealing an independent rubble gap. The 2026-09-24 correction above
limits that reading to **access** in prose; the fixture's aperture closure is
synthetic, and the accepted proposal's final gap passability is unresolved.
A deterministic fixture rejects a repeated pillar state, preserves its T28
provenance and applies a separately chosen gap `ajar -> closed` transition; the
existing synthetic `intact -> damaged -> destroyed` path also passes. This
completes storage-fixture coverage, not source-grounded proposal extraction from
the recorded pair. It also records an open producer requirement: because the
batch API rolls back every member when one is invalid, a mixed batch of a
repeated state and an independently legal change would discard both; a future
producer must separate, correct or retry that batch before commit.
`uv run pytest -q` passed 1,190
tests with 2 LLM tests deselected; that validates deterministic behavior only.
See the [active-only result](../../plans/artifacts/69-closed-transition-contract/ACTIVE-OBJECTIVE-RESULT.md)
and [pillar-pair result](../../plans/artifacts/69-closed-transition-contract/PILLAR-PAIR-RESULT.md).

**Typed transition rejection, 2026-09-21:** refused transitions in the physical
engine now raise `PhysicalTransitionRejectionError`; registration and
whole-store validation remain separate failures. This satisfies the
component-level deterministic rejection item below. It does not mitigate the
live repetition by itself: no model target is selected and no pre-render path
omits or corrects an event whose state change was refused. The adopted next
diagnostic is a newly pre-registered active-only catalogue ablation, testing the
hypothesis that exposing a future objective contributed to the C1 outputs; it
is not an approved producer design. See the [Runner transition result](../../plans/artifacts/69-closed-transition-contract/RUNNER-TRANSITION-RESULT.md)
and [objective-catalogue rejection](../../plans/artifacts/69-closed-transition-contract/OBJECTIVE-CATALOG-RESULT.md).

**Objective-catalogue screen, 2026-09-21:** under its pre-registered decision
rule, the tested prompt shape stopped. All eight candidate responses were
schema-valid, but the required context label appeared in only 2/4 calls before
selection and 2/4 calls during the artifact test, below the required 3/4 in
each context. This is a result for two frozen payloads from one session, not a
model-reliability estimate, and no schema or runtime target path followed. Per
the existing closure criteria for duplicate rejection and legal escalation,
the next action is to exercise both across consecutive Runner submissions using
the bootstrapped fixture. See the [objective-catalogue result](../../plans/artifacts/69-closed-transition-contract/OBJECTIVE-CATALOG-RESULT.md).

**Deterministic bootstrap, 2026-09-21:** scenario manifests now materialize
typed physical fixtures as validated turn-zero durable state. The HTTP, direct
Runner and setup UI paths preserve the manifest; partial custom sessions cannot
inherit unrelated default fixtures; structural validation runs after the
session, turn and undo mutation hooks; and a hardcoded test hook proves a legal
turn-1 transition persists and undoes exactly. The full non-LLM suite passes
1,182 tests. This still supplies no model producer, prompt projection, dynamic
entity creation, roteiro target or narrative-quality result, so Task 69 remains
open. Raw model-authored physical triples are withdrawn because they would
expose internal IDs and leave target selection unvalidated. The next action is
a pre-registered real-payload screen of a scenario-owned, prompt-safe objective
catalogue before any roteiro schema change. See the [bootstrap result](../../plans/artifacts/69-closed-transition-contract/BOOTSTRAP-RESULT.md)
and [durable-state interface](../../plans/artifacts/69-closed-transition-contract/DURABLE-STATE-INTERFACE.md).

**Durable-state foundation, 2026-09-20:** schema 16 persists typed
physical-world entities as independent dimensions with explicit transition
graphs, caller-beat provenance, atomic batches and pre-beat undo snapshots. The
first single-enum draft was withdrawn after a content critic found that it
collapsed independent properties such as aperture, security and integrity.
At that checkpoint, focused transition, serialization and undo tests passed,
and the full non-LLM suite passed 1,167 tests with its two marked LLM tests
deselected. It established an enforceable storage interface, not evidence of
narrative improvement. See the [foundation result](../../plans/artifacts/69-closed-transition-contract/FOUNDATION-RESULT.md)
and [durable-state interface](../../plans/artifacts/69-closed-transition-contract/DURABLE-STATE-INTERFACE.md).

**Suffix-veto correction, 2026-09-14:** removed the rule that inferred
per-character transient state from new fact-key suffixes. A controlled replay
of d5a2ccf0 T8's recorded delta drops `doors_state: trancadas` with the archived
pre-change predicate and preserves it with the new predicate, with no other
fact difference. An isolated save/load check also preserves it. The historical
snapshot and next request lack the key, but that observation plus the replay
does not prove the full old execution path. A content reader reviewed 11
selected calls across three sessions and found both useful facts and duplication;
the separate similarity check remains unchanged and unvalidated by this read.
The full suite passes 1,141 tests. No narrative benefit or closure of 69 follows.
See [the report and critic qualifications](../../plans/artifacts/69-fact-intake-read/REPORT.md).

**Deterministic eviction correction, 2026-09-14:** an updated fact now moves
to the latest write position, and the cap is enforced after the complete delta.
Before the fix, rewriting the oldest fact then adding one could discard the
fresh update; adding before deleting could evict a fact unnecessarily. Both
regressions fail before and pass after the fix; the reverse-order control also
passes. The full suite passes 1,136 tests and a real isolated save/load check
preserves the order. This does not establish a narrative benefit or close 69.
The accompanying Director prompt screen has only two valid baseline responses
and stops below its registered minimum of three. Its source-reading deviation
and corrected V8 judgment remain explicit in the [report](../../plans/artifacts/69-state-delta-contract/REPORT.md).

**Replan-context diagnostic, 2026-09-14:** adding the full physical-facts
dictionary to fb62cc2f T7 did not validate a runtime change. All four outputs
per arm are schema-valid, but candidate V5 calls the explicitly closed arches
“still open”. The original arm also contains continuity defects. The report
preserves the late protocol clarification and critics' dispute over the word
“regression”; it does not establish that the candidate is worse than baseline.
A separate deterministic replay reproduces retention of the messenger's old
location beside his new arrival under a different key, without establishing
that this caused the replanner defect. See the [result and blind readings](../../plans/artifacts/69-replan-physical-context/REPORT.md).

**Fresh current-engine case, 2026-09-14:** fb62cc2f T7 contains the explicit
physical fact `porta_leste = aberta de par em par` and a roteiro beat assuming
Holt was sealing that door with a bar. The accepted Director then supplies
the bar bending and door breaking. A text-only reader noticed the unexplained
change before the source comparison. This supplied the replan-context
diagnostic above; the observation does not establish that
adding state will fix it. See the [live result and source trace](../../plans/artifacts/77-p3-input-dispatch/LIVE-RESULT.md).

**Movement-contract diagnostic, 2026-09-14:** the 8bd4d0f1 T21 replay did not
reproduce Liora's historical unsupported move: all four original responses
and both returned candidate responses keep her in the inner corridor. Two
candidate calls exhausted connection retries without an HTTP response. The
registered baseline-reproduction and completion requirements both fail; no
prompt correction is validated. See the [individual fields and literary read](../../plans/artifacts/69-movement-event-contract/REPORT.md).

**Prose-history diagnostic, 2026-09-14:** removing the transcript from the
d5a2ccf0 T32 prose request did not meet the registered screen: the original
arm has four schema-valid responses, the ablated arm only two, below the
minimum of three. Report critics also disputed whether Link's wall contact
constitutes a new arrival or a posture adjustment; those cases remain
ambiguous. A further collapse praised as progression by the literary reader
was absent from the renderer's confirmed events. No history removal or quality
gain follows. See the [report with source corrections and disputed readings](../../plans/artifacts/69-projectile-boundary/REPORT.md).

**Plan-precedence result, reviewed 2026-09-14:** the second candidate also
failed its fixed screen: on the roof payload the source-checked valid outputs
contain three original restagings, two with the candidate, and none with the
complete planning block removed. The candidate required at most one. The
no-plan continuations still include “ninguém desceu” after Maelis descended
and an unexplained return to descent; the diagnostic contrast is not a quality
verdict or a reason to delete the feature. Both candidates remain unvalidated.
The registered stop ends wording trials on these two frozen payloads. See the
[report, individual classifications and limits](../../plans/artifacts/69-plan-precedence/REPORT.md).

**Heading candidate, 2026-09-05:** the resumed model comparison meets its
completion/schema requirement but fails its predeclared qualitative veto. In
the roof continuation B3, Maelis redirects evacuation from the patio to stands
that the same output calls corroded and unstable, without explaining the change.
This is a source-checked contextual concern, not a demonstrated causal heading
effect. The candidate remains isolated; main runtime code is unchanged. The
[report and source check](../../plans/artifacts/69-anchor-heading-replay/REPORT.md)
retain the original HTTP 402 execution and the separately completed comparison.
The lexical mismatch still reproduces an unsupported “Not in play yet” claim
about a confirmed gate closure; the proposed heading correction is unvalidated.

**Evacuation replay, 2026-09-05:** the text-selected bb72dc94 T10 replay failed
its preregistered follow-up criterion. The original arm produced one schema-valid
formation reset, one schema-valid continuation, one invalid continuation
projection and one connection failure. Deleting two pending-planning lines
produced three ambiguous continuations and one connection failure. The text
reader retained coherent action alongside unexplained reversals of order and
position: a continuation can preserve formed groups while reversing the
authorization to leave. No deletion or narrative-quality gain is validated.
See the [report and literary read](../../plans/artifacts/69-evacuation-input-replay/REPORT.md).

**Content evidence, 2026-09-05:** a separate text-only sequence read found a
concrete reset in bb72dc94: T9 supplies forming and departing groups through
`time_skip_summary`, materialized into the prose request; T10 sets
`group_formation` to “hesitante, quartetos ainda não formados”. T7→T8 also repeats
the messenger's fainting, with additional holder/posture discontinuity in prose.
The [read and boundary trace](../../plans/artifacts/79-content-read/REPORT.md)
provide investigation cases, not a capacity diagnosis or a corpus rate. This
cross-reference keeps continuity evidence in the existing investigation.

> **Update, 2026-09-05: capacity remains undiagnosed.** The promised
> session-cohort comparison has been run. Its lexical flags are not a semantic
> restaging rate, and the fixed contextual read of the earliest flagged pair
> in each of 16 measurable below-threshold sessions found no unequivocal
> re-staging of a completed physical event. That leaves the registered
> threshold-necessity question unresolved; it does not establish absence of
> narrative repetition. See [the cohort report](../../plans/artifacts/69-session-cohorts/REPORT.md).
> The historical “capacity excluded”, “at most a minority” and “retrieval
> already works” conclusions below are withdrawn as causal conclusions:
> visible text does not establish its use, and the new cohort read supplies
> no causal comparison. The historical visibility observations remain.
> The [ceiling replay](../../plans/artifacts/69-roof-input-replay/REPORT.md)
> also did not pass its fixed follow-up gate: both selected unchanged payloads
> produced one clear RESET in four calls, with ambiguity retained. No prompt
> deletion is validated. The state/planning conflict remains a hypothesis.

> **Status:** open. **Wave 2, second as of 2026-08-13** (behind 79, which has the
> only established mechanism in the phase). Symptom re-measured post-wave-1 and
> still real: 97 of 987 Director events re-proposed within three turns. Its
> channel is identified and provably saturated - `_MAX_PHYSICAL_FACTS = 40` with
> eviction, and `09aabf25` sits at exactly 40 of 40. Whether saturation CAUSES
> the re-proposal is untested and should be tested before anything is designed.
>
> ⚠ **2026-08-13, after a critic review: BOTH halves of the line above are weaker
> than written.**
>
> **The symptom number is demoted, MEASURED → OBSERVED.** The 9.8% comes from an
> `sim >= 0.6` recurrence detector that was unregistered and had never been read.
> Reading five flagged pairs: two genuine restatements, one clear false positive
> (*"o clarão verde continua pulsando"* against *"o clarão verde cessa de
> repente"* — opposite events, shared vocabulary), two progressions. See
> `.plan/reference/metric-validity.md`. **The defect is still real** — the
> verbatim triples in this file were read, not scored — but the rate is not.
>
> **The capacity mechanism is UNTESTED, not excluded.** See the
> measured-and-rejected section below.
>
> ⚠⚠ **2026-08-13, later the same day: CAPACITY IS NOW EXCLUDED, on a
> pre-registered read.** Of 18 genuine re-proposals sampled systematically from
> 703 flagged pairs, **17 happened while the original event was still in front of
> the Director** — in the facts bag, in the transcript, or both. In one of them
> the bag literally read `"parede_rompida": "true"` and the Director broke the
> wall again. **The `_MAX_PHYSICAL_FACTS` cap is real and eviction is not the
> cause; the eviction bullet below drops to hygiene.**
>
> ⚠ **Scoped after three critics: this is narrower than "nothing is forgotten".**
> Presence in a prompt is not use, so a retrieval failure is still open; the CI on
> 17/18 is [73%, 99%], so capacity could still explain a minority; and the
> session-level test (18 never-capping sessions against 15 capping ones) has never
> been run although both groups are already identified. **"Capacity is not
> necessary and explains at most a minority" is what the evidence carries.**
>
> **The thesis of this task is unharmed and better aimed:** settled state has to
> become **binding on the output**, not easier to retrieve. Retrieval already
> works and is already ignored. **This inference is withdrawn, 2026-09-05:
> visible text does not establish retrieval or use.**
>
> ⚠ **And roughly half of this task's headline symptom belongs elsewhere.**
> 43.4% of the flagged pairs are the Director re-summarising **speech**, not
> restaging a physical event. 69's own half is about 8% of Director events.
>
> Originally: **Wave 2, first.** This is the residual restaging — what is
> left after the previous phase closed every *code loop* that fed the Director
> the same input twelve times.
>
> The first draft of this task cited evidence that does not survive audit. Both
> the bad evidence and the good evidence are below; do not let the bad one back
> in.

## Problem

The Director re-proposes physical events it has already resolved.

`8bd4d0f1` (`base-P1-r2`), verbatim from `perception_events`:

| turn | event |
|---|---|
| T33 | `physical_outcome` — "O teto da câmara oculta desaba com um estrondo, abrindo um buraco de onde a névoa verde jorra…" |
| T34 | `observation` — "O teto da câmara oculta desaba com um rugido, abrindo um buraco por onde um jato espesso de névoa verde dispara…" |
| T35 | `physical_outcome` — "O teto da câmara oculta desaba com estrondo, e um jato espesso de névoa verde dispara pelo buraco…" |

Liora dies at T36, T37 **and** T38. The pillar collapses at T28 and T29. The
hidden duct is "revealed" six times. In `null-P1-r1` — roteiro **off** — the
green gate closes "com um baque surdo" at T18, T19 and T20 and Link's
disqualification is announced on all three. **No cell escapes this**, which rules
out the roteiro as the root cause.

Contradiction is worse than repetition. Once Liora has died twice, the reader
stops assigning weight to anything, including the next death.

## Evidence that the advisory channel does not prevent it

**This is the citation to use.** In the Director's own prompt at T34 of
`base-P1-r2`, the `Physical facts` block already contained:

```
"câmara_oculta": "teto desabou, buraco aberto", "entrada_câmara": "soterrada"
```

and the Director then emitted *"O teto da câmara oculta desaba com um rugido…
enquanto a entrada fica soterrada por blocos."* Same at T35. This is the
**post-R0 engine**. **Correction, 2026-09-05:** T34 does have an
`UPCOMING EVENT` block, a clock signal requesting time compression. It does not
command the roof collapse. The earlier literal no-block claim is withdrawn.
The state channel said the ceiling had already fallen, in the same message, and
the Director staged it again.

### The evidence the first draft used, and why it is withdrawn

The draft cited: *"`main_doors: trancadas` was in `physical_facts` from T11 of
`base-r1` and the Director re-sealed the doors seven times."* Two problems:

1. **The session is not on disk.** `main_doors` appears in **zero** files under
   `plans/artifacts/`. It came from an unarchived round-1 run.
2. **That effect already had a known cause, and it was fixed.** Case 20
   established that the terminal-act loop injected byte-identical text as a
   MANDATORY `UPCOMING EVENT` twelve times, and its own words are *"the
   doors-sealing cluster is a subset of the injection turns… the mandatory
   instruction won, correctly."* Using it to prove the state channel fails is
   re-attributing an effect to a cause that was not responsible.

## The input contradiction nothing currently addresses

At T33, T34 and T35 the ROTEIRO block of the same prompt carried, together:

> `Current beat: O teto da câmara oculta desaba de repente, abrindo uma nova
> fonte de névoa…`
>
> `Not in play yet — introduce as concrete perception events: pedras do teto
> desabado, entrada soterrada da câmara, gritos de alunos próximos`

The prompt asserts *"this is the current beat"* and *"this is not in play yet"*
about the same event, in the same message, while `physical_facts` says it has
already happened. **Correction, 2026-09-05:** the juxtaposition is observed; interpreting it as
a semantic conflict and causal loop remains a hypothesis after the ceiling
replay above. The historical mechanism claim follows for context.

The anchor matcher cannot close the beat because
"pedras do teto desabado" does not lexically match "O teto da câmara oculta
desaba", so coverage never completes and the turn clock forces a replan that
regenerates the same standoff.

**Closed transitions constrain the output. Nothing here reconciles the input.**
A task that only guards the output will be fighting a prompt that is still asking
for the event.

## Why not semantic similarity

`docs/cases/21` recommends durable memory plus **semantic comparison** applied to
the Director. Right target, wrong instrument, for two reasons:

1. **Similarity cannot separate escalation from repetition**, and escalation is
   the engine of a story. "The pillar cracks" → "the pillar collapses" is
   progress.
2. The advisory version of the state channel has now been measured failing
   (T34 above). Making it *louder* is the same class of fix as the reverted
   `602e562`.

A closed transition distinguishes them by construction: a ceiling that is
`desabado` cannot transition to `desabado`; it can transition to
`escombros removidos`. A door that is `trancada` cannot become `trancada`; it can
become `arrombada`.

**One measured caveat against my own argument:** the audit found that at
`CLUSTER_TAU = 0.6` the existing lexical clustering *did* catch the ceiling
restaging, and produced **zero** escalation false positives across `base-P1-r2`'s
16 clusters. So lexical detection is more capable than this task assumed. That
strengthens the *scanner* (task 68) but not the *runtime guard* — an offline
metric may accept a false positive rate that a guard blocking the Director's
output may not.

## Also in scope

- **`burst.event_texts` dies every submission** (`runner.py:1163-1169`). It only
  exists `if multi_beat`, so cross-submission re-proposal has no barrier at all.
  A durable equivalent is part of this task.
- **`scene.physical_facts` saturation — historical HYGIENE demotion, 2026-08-13.**
  **Causal exclusion withdrawn 2026-09-05; see the cohort report above.** The
  visibility read above excludes it as the mechanism: 17 of 18 re-proposals
  happen with the original still in the prompt. Over all 33 sessions, **15 reach
  the 40-key cap and 18 never do**, at a median 69% through the session. Measure
  eviction if it is cheap; do not design the storage model around it, and do not
  cite the cap as a cause. The paragraph below is kept as the sizing, not as an
  argument. Re-derived from `metrics.json`
  2026-08-05: **4 of 12 P1 runs finished pinned at the 40-key cap** — `base-r2`,
  `base-r3`, `drive-r1`, `drive-r2`. (The archive also shows the cap is the
  *current* engine's: `oldcode-P2-r1` and `-r2` finish at 70 and 59 keys.) Closed
  transitions will live in that same bag, so measure what gets evicted **before**
  building on it. **Separate the two arguments for the cap when you decide the
  storage (added 2026-08-05).** It bounds prompt growth, which was partly about
  cost — dead under `AGENTS.md` §2 — and partly about **model attention**, which
  is very much alive: a bigger prompt is a worse prompt long before it is an
  expensive one. This task owns the storage decision, so it has to say which of
  the two it is optimising. *"Tokens are cheap now"* is not a licence to hand the
  Director an unbounded fact bag. Case 20 called fact churn "no harm observed"; a blind reviewer
  argued the harm is visible and misattributed. The low-salience entries that get
  evicted are exactly the ones worth keeping.

- **A consumer already exists for the transition state, and it is starved
  (found 2026-08-06).** `watcher.LadderContext.promised_transition_ready` gates
  the ladder's gentlest rung, `execute_promised_transition` — and the Runner
  never sets it (`runner.py:2244-2248`), so it is permanently `False` and the
  ladder skips to its most disruptive rung. `watcher.py:2236-2240` says the
  task-40 clock "already owns" that rung, but the ladder cannot see it. When this
  task lands, deriving that flag is close to free and turns a dead rung on. The
  storage interface below should be shaped with that reader in mind, not only
  with tasks 72 and 66.

- **This task owns the durable-state storage decision for the phase.** Added
  2026-08-05. Tasks **72** (commitments) and **66** (possession) both want durable
  state, and 66 says outright that possession *"should reuse [69's machinery]
  rather than build a parallel one"*. 69 builds first, so 69 decides — the shape,
  where it lives, and what happens at the cap — and writes it down here as an
  interface the other two consume. Three tasks each inventing their own store,
  on top of a bag that is already evicting, is the most expensive mistake
  available in this phase.

## Closure evidence required

- [x] a re-proposed transition into a state already held is rejected or corrected
      deterministically, with a test per transition family;
- [x] an independently chosen legal transition is **not** blocked at the
      storage boundary — the source-inspired pillar duplicate plus synthetic
      gap closure and a seeded crack→collapse both pass; accepted-T29 gap
      extraction remains unproved;
- [ ] the input contradiction is closed: a beat whose anchors are already
      satisfied cannot be re-issued as "not in play yet";
- [ ] cross-submission coverage: the same event proposed in two consecutive
      submissions is caught;
- [x] eviction disposition explicit before state is trusted to persist: the
      authoritative store has no eviction and preserves 41 exact IDs across
      save/load, beyond the separate 40-key descriptive-fact cap;
- [x] the storage model written down here as an interface, **before** 72 or 66
      designs against it;
- [ ] measured on a live cell: the ceiling-family cluster does not recur, judged
      with the fixed `cluster_max`/`cluster_span` from task 68 and a blind read
      (`NSR` is reported, not a gate — `.plan/ROADMAP.md`);
- [ ] `docs/cases/21`'s semantic-comparison recommendation answered in writing —
      either adopted after this ships, or refused with the counterfactual.

**The measurement that would falsify this task:** if closed transitions land and
the restaging cluster count does not fall, the state model is not the mechanism
and the production mandate (task 72) is carrying all of it.

## Related: historical shared-state hypothesis, not a diagnosis

Task 69 contains resolved events re-proposed. Task 77's cited passages include
repeated orders, but the 2026-09-24 content read also found movement, resistance
and uncertain group identity; it did not establish that nobody crossed or that
missing commitment state caused those passages. Task 72 proposes such durable
state. These remain separate questions rather than one established mechanism.

## Measured and rejected — the saturation test, 2026-08-13

Recorded so nobody re-derives it.

**Hypothesis (pre-registered):** `physical_facts` is capped at 40 keys and
evicts, so if the engine forgets a resolved event the Director re-proposes it.
Test: within a session, re-proposal rate AFTER the store first hits 40 should
exceed the rate BEFORE. Paired, session as the unit.

**Result:** 15 sessions, median change **+4.5 points**, up in 10 of 15,
sign test **p = 0.302**.

**Control** (identical design, splitting at each session's MIDPOINT instead):
31 sessions, median **+8.3 points**, up in 25 of 31, **p = 0.001**.

**Why this does NOT show capacity is irrelevant**, which is how I first wrote it:

- The two arms are different populations. The 15 are selected for having ≥10
  events either side of saturation, i.e. long, event-dense sessions.
- Saturation falls at a **median 68% through a session** (range 44-94%), so the
  saturation split IS a position split, just a later one. On a monotonic rise, a
  later split leaves more of the rise inside the "before" arm and yields a
  *smaller* gap. **+4.5 against +8.3 is exactly what position alone predicts.**
- At the observed effect size a sign test on n=15 needs about 12/15 to reach
  p<0.05. **This design could not have confirmed its own hypothesis.**

**Correct status: capacity is UNTESTED.** The decisive design was not run:
compare saturated against non-saturated sessions **at the same turn index**.
Until that exists, do not build a storage fix on the capacity story and do not
cite this as ruling it out.

**What did survive**, and it reframes the search: re-proposal is **higher in the
second half of a session**, median +8.3 points, 25 of 31 sessions, p = 0.001,
session as the unit. Checked against the obvious artifact — a 3-turn lookback
cannot fire on turn 1, so the first half is structurally depressed — by dropping
the first three turns of every session: **+7.9 points, still 25 of 31, p =
0.001.** Not an edge effect.

⚠ Still **OBSERVED, not MEASURED**: it rests on the same unread detector, and
baseline similarity between unrelated events (≥10 turns apart, so they cannot be
repeats) drifts **+0.013** upward across the halves in 14 of 19 sessions. Too
small to manufacture +8 points, the right size to inflate it.

**So the mechanism to look for is position-shaped, not capacity-shaped** —
context growth, accumulated history, prompt length — and that is the one genuinely
new thing this test produced.

## The capacity test, take two — pre-registered 2026-08-13, BEFORE any result

Written before the measurement runs, and the design is deliberately **not** a
rate comparison, because the archive cannot power one.

**Why not the design the section above names.** *"Compare saturated against
non-saturated sessions at the same turn index"* is the right idea and the corpus
will not carry it. Counted first, over the **33 distinct** sessions (the archive
holds 49 `state.json` files because the same sessions sit in two trees; anything
counted over paths double-counts):

| | |
|---|---|
| sessions that reach the 40-key cap | **15** |
| sessions that never do | 18, of which **16** are long enough to use |
| where saturation falls | median **69%** through the session, range 0.45-0.95 |
| peak facts, never-saturated sessions | 9 to 36 — a genuinely different population, not a near-miss |

A sign test on 15 pairs needs about 12 of 15 to clear p<0.05 at this effect size.
**That is the same wall the first test hit**, and running it again to get another
inconclusive number would be re-deriving a known failure.

### The test that does not need a p-value

The capacity story makes a **mechanical** claim, not a statistical one:

> the engine forgets a resolved event, so the Director re-proposes it.

**Every Director prompt in this archive is recorded in `debug.jsonl`.** So the
claim can be checked directly instead of inferred: at the moment the Director
re-proposed an event, **was the original event still in front of it?**

- **Still visible** — in `physical_facts`, in the transcript, anywhere in the
  message — then nothing was forgotten and capacity cannot be the mechanism.
- **No longer visible** — evicted or scrolled out — then the capacity story is
  live and a bigger or smarter store is aimed at the right thing.

The task file already contains **one** case of the first kind: at T34 of
`base-P1-r2` the prompt carried `"câmara_oculta": "teto desabou, buraco aberto"`
and the Director staged the ceiling falling anyway. This test asks whether that
case is the rule or the exception.

### Decision rule

**Population.** Director `perception_events` flagged by the recurrence detector
(`sim >= 0.6` against an event from the previous 3 turns) across the 33 distinct
sessions.

**Sample.** 20 flagged pairs drawn **systematically** (every k-th of the ordered
list), so the sample is not chosen by me. Every one is read.

**Each pair is classified twice**, and the first classification comes first:

1. **Is it a genuine re-proposal?** The detector is REPORT-DO-NOT-GATE and has a
   read false-positive rate of about 1 in 5 (`metric-validity.md`). Opposite
   events sharing vocabulary, and escalations, are **not** re-proposals and are
   excluded from the denominator.
2. **Was the original still visible in the re-proposing prompt?** Yes / no, by
   reading the recorded request.

**The rule, both directions stated before the data exists:**

| result over genuine re-proposals | conclusion |
|---|---|
| **≥ 70% still visible** | **capacity is NOT the mechanism.** The Director re-proposes events it can still see. A bigger or better-remembered store cannot fix it, and 69's argument must rest entirely on **constraining the output**, not on memory. The eviction bullet in "Also in scope" gets demoted to hygiene |
| **≥ 70% no longer visible** | **capacity is live.** Forgetting precedes re-proposal, the storage decision is aimed correctly, and eviction is the first thing to instrument |
| anything between | **inconclusive, and reported as inconclusive.** No third story invented afterwards to explain the split |

**What would falsify the test itself:** if fewer than 10 of the 20 sampled pairs
survive classification 1, the detector is too noisy to carry this and the sample
is enlarged rather than the finding being reported on n<10.

⚠ **This tests the capacity sub-story only.** Whatever it returns, the verbatim
triples at the top of this file are still there — the ceiling still falls three
times. This decides *why*, not *whether*.

### ✅ RAN 2026-08-13 — the rule fires, and CAPACITY IS NOT THE MECHANISM

**17 of 18 genuine re-proposals happened while the original was still in front
of the Director.** The registered threshold was 70%; this is **94%**.

| | |
|---|---|
| sampled, systematically (every 35th of 703 flagged pairs) | 20 |
| excluded — detector false positives, read | **2** |
| genuine re-proposals | **18** |
| original **still visible** in the re-proposing prompt | **17** |
| original **not visible** | **1** |

The rule was registered in both directions before any of this existed, and it
lands on the side that **removes** a justification from this task rather than
adding one.

**The strongest cases are the ones where the engine said it out loud.**

- `834f91e5` T28→T29. The facts bag the Director was handed contained
  `"parede_rompida": "true"` and `"criatura_emergiu": "true"`. It staged the
  claws breaking the wall again.
- `8bd4d0f1` T37→T38 — **Liora dying twice**, the case this task opens with. At
  T37 the narration describes the mist reaching her and her collapsing, and
  Maelis says *"Link, o portal não vai salvar Liora agora; ela se foi."* At T38
  the Director kills her again.
- `a3e1ceda` T21→T22. `"equipes_de_resposta": "partindo pela porta leste"` was in
  the bag — the teams were **already leaving** — and Maelis re-issues the order.
- `d5a2ccf0` T31→T32. `"projectile_hit": "true"`. The projectile hits again.

**The original was present in the prompt in every one of them.** The state channel
held the fact, the transcript held the event, and the Director re-proposed anyway.

⚠ **Scoped 2026-08-13 after three isolated critics, and the scoping matters:**

- ~~*"nothing is being forgotten"*~~ — **presence in a prompt is not use.** This
  method inspects the input; it never observes whether the model attended to it.
  Every one of the 17 is equally consistent with a retrieval failure this design
  is structurally incapable of seeing.
- ~~*"a larger or smarter store cannot fix it"*~~ — the evidence rules out
  **eviction**. It does not rule out a store that pins, re-ranks or summarises
  settled facts, which addresses salience rather than capacity.
- **17 of 18 is not a rate.** Exact 95% CI **[73%, 99%]**, so at its lower bound
  capacity could still account for up to 27%. The claim that survives is
  *"capacity is not necessary and explains at most a minority"*, not *"plays no
  role"*. And the 18 have **no session denominator** — under rule 1 they could be
  a handful of sessions.
- **The in-scope n is smaller than 18.** 43.4% of the flagged population is
  speech, out of this task's scope, and the 17/18 was never split by event kind.

**The session-level test that would settle it was never run, and both groups are
already identified:** compare re-proposal rate between the **18 sessions that
never reach the 40-key cap** and the **15 that do**. If the defect occurs at the
same rate where the mechanism is structurally impossible, that is evidence of
absence rather than absence of evidence.

### The one exception is not capacity either — it is an event that was LOST

`b11b38dc` T18→T19. The Director emitted *"a diretora Maelis anuncia que a
entrada na masmorra é imediata e que cada equipe deve atravessar o limiar em um
minuto ou será desclassificada"* — and it **reached nothing.** No speech record
at T18, no C17 line at all, and the T18 narration covers the mist and Garran at
the door without a word of the announcement. At T19 the Director proposed it
again.

So the sample's only *"not visible"* case is not a memory failure. **The event
was never enacted, so it was never there to remember.** That is task 78's shape
(routed into silence) and task 77's (the order nobody executes), arriving from a
third direction. Counted against this task's hypothesis anyway, because rounding
against yourself is the only honest direction.

### What this does to task 69

> **Correction, 2026-09-05:** the causal conclusions in this historical section
> are withdrawn. Neither prompt visibility nor the new cohort comparison
> establishes that memory/attention is irrelevant, or validates binding-output
> storage as the remedy. See the update and cohort report at the top.

**The thesis survives and the sub-story dies.** *"Closed transitions constrain
the output"* is exactly what a defect where the Director can see the fact and
re-proposes anyway needs. What dies is the idea that this is about **memory**:

1. **`scene.physical_facts` saturation drops from a suspect to hygiene.** The cap
   is real (15 of 33 sessions reach 40 keys) and it is not what is producing
   this. Instrument eviction if it is cheap; do not design storage around it.
2. **Do not "make the channel louder".** Already argued in this file against a
   semantic advisory; now measured. The channel is not quiet, it is **ignored**.
3. **The storage decision this task owns gets simpler.** It has to make settled
   state *binding on the output*, not *retrievable*. Retrieval already works.

### Recurrence, re-derived over the full archive with its spread

The 9.8% at the top of this file came from a smaller corpus. Re-run over all
**33 distinct** sessions (the archive holds 49 `state.json` files; counting over
paths double-counts):

| | pooled | per session |
|---|---|---|
| flagged pairs (`sim >= 0.6`, lookback 3) | **703 of 5,064 = 13.9%** | median **12.5%**, sd **5.2pts**, range 4.6-24.9%, n=31 |
| ⚠ **corrected to this task's own scope** | **~7.9%** (13.9% x 0.566, speech removed), **~7.1%** if the detector's 10% false-positive rate is also applied | **no per-session spread exists for the corrected figure** — the median/sd/range above belong to the uncorrected 13.9% and must not travel with it |

**This is one of the few numbers in this project whose per-session spread does
not destroy it** — sd 5.2 points, against 17.9 for the split rate and 31.5 for
intra-room moves. Worth saying plainly, because the standing lesson here is the
opposite one.

⚠ **But half of it is not this task's defect.** By the kind of the re-proposed
event:

| kind | share |
|---|---|
| `audible_speech` | **43.4%** |
| `observation` | 28.6% |
| `physical_outcome` | 24.3% |
| `scene_change` | 3.3% |

**43.5% of the flagged pairs are the Director re-summarising speech**, not
restaging a physical event. This task is about physical events, so its own
symptom is roughly **half** the headline: the physical and observational half,
about 8% of Director events. The speech half is the same engine failure wearing
77's clothes, and neither task should quote 13.9% as its own.

### The detector gets a measured false-positive rate, at last

**2 of 20 read as false positives (10%)**, against the 1-in-5 previously guessed
from five cases. Both misses share a shape — *same phrasing, different content*:

- `d0cc98e5` T28→T29: a fissure swallows **Mirella, Liora and Lucan**; one turn
  later a *new* fissure swallows **Cael, Ysara, Oriana and Téo**. Different hole,
  different people.
- `5d60575d` T20→T22: **Nix** shouts to back away from the fissure edge; **Bruna**
  shouts to fall back to the east and west arches because the fire will surround
  them. Different speaker, different instruction.

Still **REPORT, DO NOT GATE** — a 10% error rate is fine for a description and
not fine for a guard. Logged in `.plan/reference/metric-validity.md`.

**Status of this section: MEASURED for the visibility count** (n=18 genuine, read
individually, rule pre-registered, both directions stated). **The 13.9% stays
OBSERVED** — it is the same lexical instrument, now with a read error rate but
still no control.

⚠ **Not yet through an isolated critic.** The protocol asks for one on a claim
that gates a design decision, and this one does.

## The closed-transition replay — pre-registered 2026-08-13, BEFORE any call

The read above says the Director re-proposes what it can still see. That makes
this task's own thesis testable **before a line of code**, under `AGENTS.md` §6:
*does an output constraint stop it?*

If a contract clause is enough, this task is cheap and prompt-shaped, like task
70. If it is not, the fix has to be **mechanical** — the engine rejecting the
transition — which is expensive, and worth knowing before it is built rather
than after.

**Payloads**, chosen on recorded output before any new call, all four from the
read above, all four cases where the original was demonstrably in the prompt:

| payload | what was visible, and re-staged anyway |
|---|---|
| `834f91e5` T29 | bag holds `"parede_rompida": "true"`, `"criatura_emergiu": "true"` |
| `8bd4d0f1` T38 | Liora died at T37 and Maelis says *"ela se foi"* in the transcript |
| `a3e1ceda` T22 | bag holds `"equipes_de_resposta": "partindo pela porta leste"` |
| `d5a2ccf0` T32 | bag holds `"projectile_hit": "true"` |

4 runs per arm per payload, **32 calls**.

**Arms.** A is the recorded system prompt verbatim. B inserts one bullet into the
existing `RULES:` block, adjacent to the rule about resolving consequences,
because position in the prompt is part of the variant and the validated variant
must BE the shipped one:

> **SETTLED FACTS DO NOT HAPPEN TWICE.** Every entry in `Physical facts` is
> already true, and every HISTORY line has already been perceived. Do not emit a
> `perception_event` that states one of them again, however differently worded.
> An event MAY change a settled fact to a new state, and MAY describe its
> consequences — it may never re-stage the moment it became true.

That is this task's thesis written as a contract clause: restatement forbidden,
**transition and consequence explicitly permitted**.

**Primary measure.** Per run: does any emitted event match the known re-staged
original at `sim >= 0.6`? That is `recurrence`. The detector's 10% error rate
applies to both arms equally, and every run is read regardless.

**The rule, all four outcomes written before the data exists:**

| result | conclusion |
|---|---|
| **B's recurrence ≤ half of A's, and B's mean event count ≥ 70% of A's** | a contract clause is enough. This task is prompt-shaped and cheap, like task 70 |
| **B's recurrence falls, event count collapses below 70%** | **the rule bought silence.** Worse than the defect, not adopted, and recorded as measured-and-rejected |
| **B's recurrence does not fall** | a clause is not enough; the fix is **mechanical** — the engine rejecting the transition — and this task is expensive. Better to know now |
| **A's own recurrence is below 40% of runs** | these re-stagings are **variance**, not a contract property. Neither arm can be credited or blamed, the design question is untouched, and this is 77's finding arriving in 69. Report and stop |

⚠ **The last row is the one I expect to have to write**, because it is what
happened to task 77's identically-shaped replay: the recorded payload had emitted
`zone_moves: null`, and the unchanged contract moved people on 3 of 8 replays. It
is registered here so it cannot be presented afterwards as an insight.

### ✅ RAN 2026-08-13 — VARIANCE row, as registered. And the average was hiding the finding.

**A: 5 of 16 runs recurred (31%). B: 6 of 16 (38%).** A is below the 40% line, so
by the rule registered above this is the **variance** outcome:

⚠ **The unit is wrong and the gate was mis-specified.** 16 runs over 4 payloads is
**n=4**, not 16 — runs inside a payload share a prompt and a scene, which is rule
1 exactly. The paired per-payload differences are **+1, +2, -1, -1**, and a signed
test at n=4 cannot reach p<0.05 two-sided **by construction**: the design could not
have returned a positive result. The 40% floor was also set in run units, and a
Wilson interval on 5/16 is [14%, 56%], straddling it — two more recurrences and
the identical null would have been called informative.

**The verdict stands** (the gate fired *and* the direction was adverse) but it
stands on procedure, not on power. **If this is ever re-run, block on payload and
report per-payload.** the contract clause
is neither credited nor blamed, and **the closed-transition thesis is untested by
this experiment.** B was directionally *worse*, well inside noise.

**The clause changed nothing and cost nothing.** Mean events per run 4.75 (A) vs
4.94 (B), so it did not buy silence either. A rule forbidding restatement, placed
in the same block as the rules the Director obeys, is simply not read as binding.

**But the pooled 31% is an average over two different behaviours**, and the
per-payload spread is the whole result:

| payload | A | B |
|---|---|---|
| `834f91e5` T29 | **0/4** | 1/4 |
| `8bd4d0f1` T38 | **0/4** | 2/4 |
| `a3e1ceda` T22 | 1/4 | 0/4 |
| **`d5a2ccf0` T32** | **4/4** | **3/4** |

Three payloads are coin flips at best. **One re-stages every time, in both arms,
in near-verbatim words** — A r2, A r3, B r2 and B r4 all produce *"Um projétil
mágico sibila pelo ar e se estilhaça contra a parede atrás de Link, arrancando
lascas de pedra"*, and A r1's variant differs by two words.

That is not variance. That payload is doing something the other three are not.

### What is different about `d5a2ccf0` T32 — and the next test, registered first

It is the only one of the four whose prompt carries an **UPCOMING EVENT block**,
and the block is not a world event at all:

> `UPCOMING EVENT (incorporate this into your narration):`
> `CLOCK SIGNAL: the scene has produced no material change for 2 turns; only`
> `waiting remains. Compress time now (time_skip_ticks) unless someone is`
> `visibly mid-action.`

And the Director's contract, in `RULES:`, says of that block:

> *"UPCOMING EVENT IS MANDATORY. When an UPCOMING EVENT block is present, the
> FIRST entry of perception_events IS that event, written as a witness would
> perceive it... It happens: it is not a suggestion, it does not wait for a
> better moment, and **no coherence concern overrides it**."*

**A CLOCK SIGNAL cannot be written as a witness would perceive it.** Nobody in
the room can see "compress time". So the Director is handed a mandatory
instruction to put a non-event in slot 0, and what it puts there instead is the
most recent physical thing it has:

- the re-staged projectile is **event 0** in 6 of the 8 runs;
- `time_skip_ticks` is **0 in all 8** — the compression the signal demanded was
  refused every single time.

That second number replicates a task-72 figure from a different session and a
different engine state: the roadmap already records **0 of 6** CLOCK SIGNAL
invitations accepted in `base-P1-r2`. It is now 0 of 6 plus 0 of 8.

**THEORY, explicitly.** Nothing above shows the block *causes* the re-staging;
one payload with the block re-stages and three without it mostly do not, which is
n=1 on the thing that varies.

#### Registered before running, in both directions

1. **Corpus control first, no inference cost.** Across the 33 sessions, compare
   `P(UPCOMING EVENT block present | turn re-proposes a flagged event)` against
   `P(same | every other Director turn)`. **Session as the unit.** If the two
   rates are within a few points, this theory is dead and the deterministic
   payload is a coincidence, recorded as measured-and-rejected.
2. **Only if the corpus rate is elevated:** arm **C** on `d5a2ccf0` T32 — the
   recorded prompt with the UPCOMING EVENT block **removed**, nothing else
   changed, 8 runs. **If recurrence collapses from 4/4 to at or below 1/8, the
   block is the cause.** If it stays high, the payload re-stages for some other
   reason and the theory is wrong.

⚠ **If this holds it is not task 69's defect at all.** A mandatory-injection
clause that forces a non-event into slot 0 belongs to whichever task owns the
clock (**40**) and the drive layer (**33**), and 69 would have found it rather
than owned it. Recording that now, before the numbers arrive, so the result
cannot be annexed to this task afterwards.

#### ❌ FALSIFIED by its own control, same day. The theory is dead and inverted.

Step 1 ran, cost nothing, and killed it:

| | UPCOMING EVENT block present |
|---|---|
| Director turns that re-propose a flagged event | **108 of 456 = 23.7%** |
| **every other Director turn (the control)** | **202 of 747 = 27.0%** |

Per session, session as the unit, n=31: median **22.2%** against **26.9%**,
paired difference **-5.3 points, DOWN in 20 of 31 sessions.**

**Re-proposal turns carry the block LESS often than ordinary turns.** The theory
predicted the opposite. **Arm C was not run**, exactly as the rule said — *"only
if the corpus rate is elevated"* — and the inference it would have cost was not
spent.

This is the seventh causal story falsified in this phase, and the second one
where the kill condition was written down before the number existed. Recorded as
**measured-and-rejected**: do not re-derive it.

**What survives, and what does not:**

- ❌ *"the mandatory-injection clause forces a non-event into slot 0, so the
  Director fills it with the last physical thing"* — **dead**. Whatever slot 0
  does, it is not what produces re-proposal across the corpus.
- ✅ **`time_skip_ticks` was 0 in all 8 runs** on a payload whose prompt
  explicitly demanded compression. That number is unaffected by the falsification
  above — it is a direct observation of refusal, and it replicates the roadmap's
  **0 of 6** CLOCK SIGNAL invitations accepted in `base-P1-r2`. **0 of 6 plus 0
  of 8, two sessions, two engine states.** It belongs to task 72 and to whoever
  owns the clock, and it is the only thing this replay produced that another task
  can use.
- ❓ **`d5a2ccf0` T32 re-stages the projectile in 7 of 8 runs across both arms,
  and nobody knows why.** It is not the UPCOMING EVENT block. Left **undiagnosed
  and named**, rather than given a second story: this file has now spent two
  hypotheses on it and the honest position is n=1.

### What the whole replay leaves this task with

**The closed-transition thesis is still untested.** The clause did not fail; it
was never engaged, because 3 of 4 payloads do not reliably reproduce the defect
under replay at all. **A test of a fix needs a payload that reliably shows the
defect, and this experiment's real product is knowing that we do not have one.**

Anyone building closed transitions should first find payloads where re-staging is
reproducible — `d5a2ccf0` T32 is the only known one — or accept that the fix will
have to be validated on a live cell rather than a replay, which is slower and
what task 68's instruments exist for.

## Inherited from task 76's falsifier — a missing spatial field

Measured 2026-08-13 over 33 sessions: **136 of 403 `zone_moves` (34%) send a
character to a position inside the room they are already in** — `Salão dos
Quatro Arcos` to `Salão dos Quatro Arcos, junto ao duto de ventilação`.

The cause is that `Scene` has nowhere else to put it. It holds `zones` (the
audibility graph) and `positions` (character -> zone), and `scene_blocking` is
scratch that `narrate()` pops. **A position within a room can only be expressed
by minting a zone, and a zone is the unit of audibility**, so blocking detail
becomes an acoustic wall.

Task 76 stops short here deliberately: the fix is neither its graph rule nor a
contract clause, because the contract has nowhere to redirect the Director to.

**Split out as task 79 by the owner, on size rather than ownership.** It is a
schema change with its own migration, contract work and closure evidence, and
inside this file it would read as one bullet and lose them. **69 keeps the
durable-state storage decision generally; 79 answers the blocking question**, and
whatever 79 chooses has to fit the model 69 picks.
