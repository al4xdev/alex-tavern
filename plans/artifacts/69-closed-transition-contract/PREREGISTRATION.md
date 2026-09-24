# Closed-transition contract screen

Date: 2026-09-19. This rule is fixed before any new provider response is read.

## Source case

Use the accepted Director request for `fb62cc2f` turn 5. The preceding visible
turn has already put four things in play: the wounded east-door messenger, his
garrilha fragment, Marta's open equipment chest, and the east door as a usable
passage. A text-only reader independently classified the messenger and chest as
settled, the fragment and the exact `ajar` door wording as partial, and the turn-5
opening of the chest and messenger crossing as clear re-executions.

## Arms

- A: the recorded request, unchanged.
- B: the same request with the proposed closed-transition response contract.
  The current physical state lists four stable entries. Every
  `physical_outcome` or `scene_change` must reference at least one declared
  transition; observations may reference none. The stale `Not in play yet`
  line is removed because all four physical targets are already represented in
  the closed state. The rest of the roteiro, history, scene, characters and
  provider parameters are unchanged.

Four first responses are requested per arm. A mechanically conflicting B
response receives exactly one correction containing the canonical state; the
replacement response is also preserved. Calls are shuffled and run with at most
four in flight.

## Fixed reading rule

All returned first responses, and any corrected replacements, are read as
fiction. The target restagings are:

1. Marta unlocking or opening the already open equipment chest;
2. the already arrived messenger crossing the east threshold again;
3. Maelis newly declaring the already declared survival selection;
4. the east door becoming ajar/open as though it had been closed.

A genuine consequence is not a restaging: the creature reaching or damaging
the door, people taking equipment from the open chest, the messenger reaching a
new destination, or an authority changing the evacuation order for a new cause.

The contract is viable for implementation only if:

- at least three first responses per arm are schema-valid;
- A clearly restages at least one target in at least two of four valid first
  responses, otherwise this payload did not reproduce and the comparison stops;
- every valid B `physical_outcome` and `scene_change` is linked to a declared
  transition;
- after at most one correction, no accepted B response contains an invalid
  state transition;
- at most one accepted B continuation clearly restages any target in visible
  content, including restaging hidden inside an `observation` with no transition;
- B continues the emergency in at least three accepted outputs rather than
  buying compliance through silence or mere tableau description;
- an independent blind content reader finds no new material continuity failure
  in B that is worse than the target defect.

Failure of any item blocks implementation of this contract. Counts organize the
screen; source reading decides whether an event is repetition, progression or a
new continuity failure.

