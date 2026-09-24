# Closed-transition contract screens

Date: 2026-09-19

These screens used the accepted Director request for session `fb62cc2f`, turn
5. At the end of turn 4, the wounded messenger had crossed the east threshold,
Marta had opened the equipment chest and students had begun taking equipment,
Maelis had declared selection by survival, the east passage was usable, and the
south arch seal was cracked. The source request nevertheless described the four
roteiro anchors as not yet in play.

The screens below, V1 through V5, were pre-registered separately. V1 is
rejected; V2 through V5 did not qualify to advance to a renderer screen.

## V1: free transition records linked from events

V1 compared the recorded request (A) with a request that added a closed-state
catalogue and required physical events to link to transition records (B). It
allowed the Director to write entry IDs, families and states as free strings.
Each B response could receive one correction after local validation.

The baseline reproduced the defect: three of four A responses were
schema-valid, and all four visible continuations reopened the already open
chest. One also repeated the messenger's arrival and the survival decree.

All four B first responses passed JSON Schema, but all four failed local state
validation. The failures were structural rather than punctuation mistakes: the
Director invented state vocabularies, created aliases for known entries, used
non-null source states for new entries, and omitted event links. None of the
four replacement responses converged after the single correction. The contract
therefore failed its requirement that an accepted B response contain only
valid transitions.

An independent reader saw chest reopening in five of the twelve blinded
outputs and possible chest reopening in three more. After unblinding, the
clear chest cases included all four A outputs and B3's first response. B first
and replacement responses also supplied new continuity defects: B0 moved the
equipment depot, B1 sent evacuation toward the threat and later moved the
platform, B2 called the south seal intact and later repeated the survival
decree, and B3 sent the messenger back toward the attacked patio. Because no B
response passed local validation, none was an accepted continuation and the
registered accepted-B content gate cannot pass. The blind mapping is recorded
with the archived reading; labels were revealed only after judgment.

## V2: transition-first, closed catalogue

V2 removed free physical event kinds and free transition states. A transition
had to select one of five catalogued entries and one state from a family enum.
Observations were instructed to remain passive, and no correction retry was
allowed. This was a different boundary from V1, registered before its calls.

Only one of four responses passed both JSON Schema and exact local transition
validation. The other three respectively returned two JSON objects, used a
forbidden physical event kind, and selected four next speakers where the schema
allows three. The fixed gate required at least three valid responses, so V2
stopped before any renderer experiment.

The three invalid responses were also read, but their fiction does not enter
V2's registered content gates because those gates apply to valid responses.
For diagnostic use only, the reader found that one replayed most of the prior
beat, one reopened the chest and reset the messenger, and one contained severe
position and direction contradictions.

The sole mechanically valid response had real tactical and sensory progression,
but it failed V2's source-reading continuity veto. It put the south arch at the
east side, gave characters impossible sight into the courtyard, disagreed about
Elowen's position, and assigned a door-opening transition to Marta while she
spoke from the depot without showing the action. The reader described the
surface continuation as compelling, but those generated positions and causes
feed the eventual prose and are material fiction, not harmless metadata.

There is only one valid sample and no renderer result, so V2 establishes
nothing about whether separating transitions from prose preserves narrative
quality.

## V2R: the production retry path

V2R kept the V2 request byte-for-byte at the prompt/schema boundary and sent
four independent calls through the production client's normal three-attempt
budget. This follow-up was registered before its calls and used an isolated
temporary data root.

All four calls exhausted all three attempts: zero of four returned a valid
object. Across the twelve attempts, the recurring failure was use of
`physical_outcome` or `scene_change`, with occasional malformed JSON, too many
events or too many next speakers. Production retry therefore does not make V2
mechanically usable.

Inspection of the archived request exposes an experimental defect: V2 narrowed
the JSON Schema event enum to passive observation, speech and identity claim,
but left the earlier system-field description explicitly listing
`physical_outcome` and `scene_change` as valid event kinds. The model followed
that contradictory instruction in most failed attempts. V2 and V2R therefore
measure an internally inconsistent contract; they cannot establish that a
fully aligned transition-first contract would fail. Retries do establish that
resampling the contradiction is not a remedy.

## V3: aligned atomic transitions

V3 removed the prompt/schema contradiction, forced `scene_update` to null and
encoded each allowed entry/source/target combination as one atomic operation
enum. All four calls passed schema and local validation on their first attempt.
This establishes that the aligned atomic representation is mechanically usable
on the source payload.

It fails the registered content gates. The blind reader passed only one of four
continuations:

- V3-0 relocked and reopened the chest, moved the messenger back to the east
  threshold and reset Holt's posture; it also assigned the east-door opening to
  a student without a coherent cause;
- V3-1 reopened the chest and repeated Asword and Holt's turn-4 lines;
- V3-2 reopened the chest, placed the messenger at the platform and threshold
  simultaneously, and made Marta open the east door by operating the depot
  bolt;
- V3-3 preserved the settled facts and advanced the emergency by intensifying
  the external threat and making Holt shorten the evacuation window.

The model smuggled the rejected physical actions through free observation text
and generated blocking even though the atomic transition list itself remained
valid. In one case the free transition sensory detail also supplied an
incoherent cause. V3 therefore proves the mechanical representation and rejects
the surrounding free-text Director contract. It does not advance to a renderer
screen.

## V4: zero-prose Director decisions

V4 removed every model-authored prose value. The Director selected only atomic
operations, cue IDs, witnesses, speaker IDs, a focus-frame ID and a boolean.
All four outputs passed schema and local validation on their first attempt, and
the serialized objects contain no open string surface.

The closed shape prevents literal restaging, but only one of four plans passed
the preregistered blind continuity veto. The reader accepted V4-2: the wounded
messenger becomes incapacitated from his injuries, Marta finishes emptying the
already open chest, the external roar moves nearer, equipment rattles and cold
from the south seal intensifies.

The other three expose semantic relations that an operation token alone does
not carry:

- V4-0 collapses the south seal while Holt is touching it without accounting
  for him, opens the east door and empties the chest in the same overloaded
  beat, and assigns implausible witnesses;
- V4-1 makes Marta both barricade the evacuation door and empty the chest, and
  names Elowen as the cause of her wounded patient's incapacitation;
- V4-3 marks the garrilha fragment merely as `used` by Elowen without any
  established use, and omits her from witnesses to the roar at the doorway.

V4 fails because the fixed gate required every accepted plan to avoid a
material spatial, causal or continuity defect. It establishes a narrower fact:
removing prose closes the smuggling path and preserves mechanical reliability,
but entry/state/cause/witness IDs are insufficient to make every sampled plan
coherent.

## V5: same-model continuity selection

V5 kept the four archived V4 plans unchanged and asked an isolated production
model call to recover the prior blind reader's sole passing plan. The opaque
mapping and target were fixed before calls: S was V4-2; P, Q and R were the
three vetoed plans.

All four judge responses were mechanically valid on their first attempt. None
selected S. Two chose P, one chose Q and one chose R, so every selected plan had
already failed the blind source read. The judges also vetoed S four times with
inconsistent reasons such as causal mismatch, missing progress or route
contradiction.

This fails every substantive V5 gate. A second call to the same production
model, even under an isolated critic role, is not a reliable semantic selector
for this case. It must not be used to turn V4's one-in-four content success into
an accepted runtime plan.

## Decision

Do not implement V1 or advance V2/V3/V4/V5 to a renderer screen. V1 shows that free
model-authored state vocabulary cannot be the authoritative transition
boundary, even with a correction. V2 failed its mechanical and continuity gates,
and V2R showed that ordinary retry cannot repair its prompt/schema conflict. V3
made the boundary mechanically reliable but left enough free prose for the same
restaging to bypass it in three of four outputs.

V4 also shows why adding more state enums is not enough: causal role,
simultaneous actor workload and witness plausibility remain semantic judgments.
V5 shows that resampling those judgments through the same production model does
not recover the independent content read. The supported next work is therefore
the deterministic half that does not depend on this failed generation contract:
define the durable-state storage interface, exact transition-family graphs,
same-state rejection and undo snapshots, then use the adjacent ownership tasks
for the missing causal inputs (commitments, possession and position). A new
Director contract should be screened only after those inputs can make cause,
witness and route checks mechanical. No renderer screen is justified by these
runs.

## Artifacts

- `PREREGISTRATION.md`: V1 rule fixed before calls.
- `runs/`: V1 requests, provider envelopes and validations.
- `PREREGISTRATION-V2.md`: V2 rule fixed before calls.
- `runs-v2/`: V2 requests, provider envelopes and validations.
- `PREREGISTRATION-V2R.md`: unchanged-V2 production retry rule.
- `runs-v2r/`: all twelve production attempts and final failures.
- `production_retry_screen.py`: isolated production-client executor.
- `PREREGISTRATION-V3.md`: aligned atomic-transition rule.
- `runs-v3/`: four accepted V3 outputs and production debug logs.
- `v3_screen.py`: aligned atomic request and local validation.
- `PREREGISTRATION-V4.md`: zero-prose Director rule.
- `runs-v4/`: four accepted zero-prose plans and production debug logs.
- `v4_screen.py`: closed-plan request and local validation.
- `PREREGISTRATION-V5.md`: isolated selector agreement rule.
- `runs-v5/`: four selector verdicts and production debug logs.
- `v5_selector.py`: opaque-plan continuity selector.
- `replay_contract.py`: request construction, execution and local checks.
