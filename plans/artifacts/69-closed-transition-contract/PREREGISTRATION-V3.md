# Aligned atomic-transition Director screen

Date: 2026-09-19. Fixed before the V3 calls are dispatched.

V2 and V2R are rejected as an internally inconsistent treatment. Their system
field description names `physical_outcome` and `scene_change` as allowed event
kinds while their JSON Schema forbids both. V2R returned zero valid calls after
twelve production attempts, most often because the model selected one of those
textually allowed but schema-forbidden kinds. Resampling the conflict is not a
remedy.

## Variant

Use the same `fb62cc2f` turn-5 source request, provider and five-entry closed
catalogue. Change the V2 request in these explicit ways:

1. The prose description and schema both allow only `observation`,
   `audible_speech` and `identity_claim` in `perception_events`. The description
   says that these events cannot change catalogued durable state.
2. `scene_update` is described and schema-constrained as null for this screen,
   so it cannot restate a catalogued entity through an alias. Character
   `zone_moves` remain a separate existing contract; V3 does not claim to solve
   blocking or movement.
3. Replace V2's independently selected entry/family/source/target fields with
   one `operation` enum. Every enum member encodes one catalogued entry, its
   exact current state and a different target state. An object also carries a
   cause ID, witnesses and one sensory fragment. Duplicate operations on the
   same entry are rejected locally. This is materially different from V2:
   impossible combinations cannot satisfy the schema and reach local
   validation.
4. Calls use the production `call_agent` path and its existing maximum of three
   attempts. There is no corrective message and no extra retry after local
   validation.

All raw attempts use an isolated temporary data root and are archived. Four
independent calls are made, with at most four in flight.

## Decision rule

V3 advances to a separate renderer screen only if:

- at least three of four calls return a final schema-valid object within the
  existing attempt budget;
- at least three of four also pass duplicate-entry and atomic-operation local
  validation;
- no accepted output reopens the chest, repeats the messenger crossing or
  repeats the survival-selection decree in event content, blocking or transition
  detail;
- at least three accepted outputs progress the emergency through a new valid
  transition, a new sensory development or a changed decision grounded in the
  source scene;
- a blind source reader finds no material spatial, causal or continuity
  contradiction in more than one accepted output.

The blind read treats generated blocking and transition causes as fiction that
will feed the renderer, not as harmless metadata. Invalid outputs may be
inspected diagnostically but do not enter the content counts.

Failure of any item rejects V3. Passing does not authorize runtime code; it
only permits a preregistered renderer screen.

