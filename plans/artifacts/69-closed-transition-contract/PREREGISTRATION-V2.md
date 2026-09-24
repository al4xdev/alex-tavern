# Transition-first Director contract screen

Date: 2026-09-19. Fixed before the v2 calls are dispatched.

The v1 contract is rejected. All four candidate first responses violated the
local state vocabulary, and none of four correction responses converged. The
blind read also found continued chest reopening and new spatial contradictions.
V2 changes the contract boundary rather than tuning the rejected wording.

## Variant

Use the same accepted `fb62cc2f` turn-5 Director request. The request receives a
closed catalogue of five existing physical entries: the messenger, his fragment,
Marta's open chest, the ajar east door, and the cracked south arch seal.

The Director may express physical change only through `physical_transitions`.
Every transition selects one catalogued entry, its exact current family/state,
a different allowed target state, the responsible subject and witnesses, plus a
short sensory fragment. There is no free physical event sentence, no new entity,
no null `from_state`, and no retry.

`perception_events` retains only passive observation, audible speech and identity
claim. An observation may describe sensed current conditions; it may not contain
an actor changing physical state. The stale pending-anchor line is absent.

## Decision rule

Four responses are requested. V2 proceeds to a renderer screen only if:

- at least three responses pass both JSON Schema and exact local transition
  validation;
- no valid response smuggles a physical change into an observation;
- no sensory fragment restages a settled transition;
- no valid response reopens the chest or makes the messenger cross the east
  threshold again;
- at least three valid responses materially progress the emergency through a
  real new transition, a new sensory development or a changed decision grounded
  in the scene;
- source reading finds no new material continuity contradiction.

If this passes, a separate preregistered screen will give the structured
transitions to the production prose renderer. No runtime code follows from the
Director-only screen by itself.

