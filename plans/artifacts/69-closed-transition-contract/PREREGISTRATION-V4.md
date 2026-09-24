# Zero-prose Director decision screen

Date: 2026-09-19. Fixed before the V4 calls are dispatched.

V3 made atomic transitions mechanically reliable (four of four valid on their
first attempt) but failed its content gate: three of four accepted outputs
restaged settled actions through free observation, blocking or sensory-detail
text. Another prohibition would repeat a falsified strategy. V4 removes the
Director's ability to author prose at this boundary.

## Contract

Use the same `fb62cc2f` turn-5 user payload, with its false pending-anchor line
removed and the five-entry closed state retained. Replace the experimental
system message and response schema together. The response contains only:

- `next_speakers`: zero to three present character IDs;
- `physical_transitions`: zero to five objects containing one allowed atomic
  operation, one cause ID and witness IDs;
- `cue_events`: one to three objects containing one cue ID and witness IDs;
- `blocking_frame_id`: one closed frame ID;
- `return_control`: a boolean.

There are no model-authored strings outside enums, and no observation content,
sensory detail, scene update, blocking prose, mood prose, zone name or time
summary.

Allowed operations are deliberately forward edges from the current catalogue:

- messenger `present -> incapacitated | dead | gone`;
- fragment `available -> used | destroyed | unavailable`;
- chest `open -> empty | broken | closed`;
- east door `ajar -> open | blocked | sealed | broken | closed`;
- south seal `cracked -> collapsed | cleared`.

Allowed non-agentive cue IDs and their deterministic meanings are:

- `east_courtyard_roar_nearer`: the external roar moves nearer;
- `east_courtyard_roar_fades`: the external roar fades;
- `east_courtyard_blood_scent_intensifies`: blood scent from the courtyard grows;
- `south_arch_cold_intensifies`: cold from the cracked south seal grows;
- `south_arch_green_light_fades`: green light at the south seal fades;
- `equipment_rattles_from_roar`: equipment rattles from the external roar;
- `floor_vibration_intensifies`: vibration through the hall floor grows.

Allowed frame IDs are `east_threshold_threat`, `south_arch_failure`,
`equipment_triage`, `command_platform_response` and `split_east_and_south`.
They choose focus only and assert no character position or action.

The prompt states that a cue is a new change, not a restatement; only an atomic
operation changes durable state; and speaker selection routes future speech
rather than authoring it. `zone_moves` and detailed character blocking are
outside this screen and receive no replacement free string.

Four independent production-path calls use the existing maximum of three
attempts, an isolated temporary data root and at most four calls in flight.
Every attempt is archived. Local validation rejects duplicate operations on one
entry, duplicate cues and any value outside the registered sets.

## Decision rule

V4 advances to a separate deterministic-projection plus prose-renderer screen
only if:

- at least three of four calls return a schema-valid, locally valid object;
- a serialized-object audit finds zero non-enum model-authored strings;
- no accepted plan repeats or reverses a settled target transition;
- at least three accepted plans materially advance the emergency through a new
  operation, or through at least two compatible cues plus a speaker/control
  decision;
- a blind source reader finds no material spatial, causal or continuity defect
  in any accepted plan.

If fewer than three plans progress, the closed catalogue bought silence and V4
fails. If the Director plan passes, the renderer can still fail by inventing or
repeating action; that is the next screen's veto, not evidence credited here.

