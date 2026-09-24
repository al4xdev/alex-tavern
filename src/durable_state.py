"""Closed, durable state dimensions for physical world entities."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, cast

PhysicalKind = Literal["actor", "passage", "container", "object", "structure"]
PhysicalDimension = Literal[
    "vitality",
    "aperture",
    "security",
    "integrity",
    "traversability",
    "resource",
]

PHYSICAL_STATE_VOCABULARIES: dict[PhysicalDimension, frozenset[str]] = {
    "vitality": frozenset({"active", "incapacitated", "dead"}),
    "aperture": frozenset({"closed", "ajar", "open"}),
    "security": frozenset({"unlocked", "locked", "sealed"}),
    "integrity": frozenset({"intact", "damaged", "destroyed"}),
    "traversability": frozenset({"clear", "obstructed"}),
    "resource": frozenset({"ready", "spent"}),
}

ALLOWED_PHYSICAL_TRANSITIONS: dict[PhysicalDimension, frozenset[tuple[str, str]]] = {
    "vitality": frozenset(
        {
            ("active", "incapacitated"),
            ("active", "dead"),
            ("incapacitated", "active"),
            ("incapacitated", "dead"),
        }
    ),
    "aperture": frozenset(
        {
            ("closed", "ajar"),
            ("closed", "open"),
            ("ajar", "closed"),
            ("ajar", "open"),
            ("open", "ajar"),
            ("open", "closed"),
        }
    ),
    "security": frozenset(
        {
            ("unlocked", "locked"),
            ("unlocked", "sealed"),
            ("locked", "unlocked"),
            ("locked", "sealed"),
            ("sealed", "unlocked"),
            ("sealed", "locked"),
        }
    ),
    "integrity": frozenset(
        {
            ("intact", "damaged"),
            ("intact", "destroyed"),
            ("damaged", "destroyed"),
        }
    ),
    "traversability": frozenset(
        {
            ("clear", "obstructed"),
            ("obstructed", "clear"),
        }
    ),
    "resource": frozenset({("ready", "spent")}),
}

ALLOWED_DIMENSIONS_BY_KIND: dict[PhysicalKind, frozenset[PhysicalDimension]] = {
    "actor": frozenset({"vitality"}),
    "passage": frozenset({"aperture", "security", "integrity", "traversability"}),
    "container": frozenset({"aperture", "security", "integrity"}),
    "object": frozenset({"integrity", "resource"}),
    "structure": frozenset({"integrity"}),
}

REQUIRED_DIMENSIONS_BY_KIND: dict[PhysicalKind, frozenset[PhysicalDimension]] = {
    "actor": frozenset({"vitality"}),
    "passage": frozenset(),
    "container": frozenset({"aperture"}),
    "object": frozenset({"integrity"}),
    "structure": frozenset({"integrity"}),
}

SCENE_BOUND_KINDS: frozenset[PhysicalKind] = frozenset(
    {"passage", "container", "object", "structure"}
)


class PhysicalTransitionRejectionError(ValueError):
    """A proposed transition refused by the durable physical-state contract."""


@dataclass
class PhysicalValue:
    """One independent state dimension and its latest accepted provenance."""

    state: str
    updated_turn_number: int
    updated_update_id: str
    updated_transition_id: str | None


@dataclass
class PhysicalEntity:
    """One stable subject with independent, enforceable physical dimensions."""

    entity_id: str
    key: str
    kind: PhysicalKind
    # Scene membership for scene-owned entities. Actors are located by Scene;
    # Task 66 will own the handoff when portable entities become possessed.
    scene_key: str | None
    registered_turn_number: int
    registered_update_id: str
    dimensions: dict[PhysicalDimension, PhysicalValue]


@dataclass(frozen=True)
class PhysicalTransition:
    """A proposed state change for one dimension of a registered entity."""

    transition_id: str
    entity_id: str
    key: str
    dimension: PhysicalDimension
    from_state: str
    to_state: str
    turn_number: int
    update_id: str


@dataclass
class DurableState:
    """Persisted current physical entities, with bounded per-dimension provenance."""

    physical_entities: dict[str, PhysicalEntity] = field(default_factory=dict)


_MANIFEST_REQUIRED_FIELDS = frozenset({"entity_id", "key", "kind", "dimensions"})
_MANIFEST_OPTIONAL_FIELDS = frozenset({"scene_key"})


def bootstrap_physical_entities(
    manifest: Sequence[object],
    *,
    character_ids: set[str],
) -> DurableState:
    """Build turn-zero physical state from a provenance-free scenario manifest."""
    if isinstance(manifest, (str, bytes)) or not isinstance(manifest, Sequence):
        raise ValueError("Physical entity manifest must be a list.")
    parsed: list[PhysicalEntity] = []
    for index, raw in enumerate(manifest):
        if not isinstance(raw, Mapping):
            raise ValueError(f"Physical entity manifest item {index} must be an object.")
        fields = set(raw)
        if not all(isinstance(field, str) for field in fields):
            raise ValueError("Physical entity manifest field names must be strings.")
        missing = _MANIFEST_REQUIRED_FIELDS - fields
        if missing:
            raise ValueError(
                f"Physical entity manifest item {index} is missing fields: {sorted(missing)!r}."
            )
        unknown = fields - _MANIFEST_REQUIRED_FIELDS - _MANIFEST_OPTIONAL_FIELDS
        if unknown:
            raise ValueError(
                f"Physical entity manifest item {index} has unknown fields: {sorted(unknown)!r}."
            )

        entity_id = raw["entity_id"]
        key = raw["key"]
        kind = raw["kind"]
        scene_key = raw.get("scene_key")
        raw_dimensions = raw["dimensions"]
        if not isinstance(entity_id, str) or not isinstance(key, str):
            raise ValueError("Physical entity manifest IDs and keys must be strings.")
        if not isinstance(kind, str) or kind not in ALLOWED_DIMENSIONS_BY_KIND:
            raise ValueError(f"Unknown physical entity kind: {kind!r}.")
        if scene_key is not None and not isinstance(scene_key, str):
            raise ValueError("Physical entity manifest scene key must be a string or null.")
        if not isinstance(raw_dimensions, Mapping):
            raise ValueError("Physical entity manifest dimensions must be an object.")

        update_id = f"scenario-bootstrap:{entity_id}"
        dimensions: dict[PhysicalDimension, PhysicalValue] = {}
        for raw_dimension, state in raw_dimensions.items():
            if raw_dimension not in PHYSICAL_STATE_VOCABULARIES:
                raise ValueError(f"Unknown physical state dimension: {raw_dimension!r}.")
            if not isinstance(state, str):
                raise ValueError("Physical entity manifest dimension states must be strings.")
            dimension = cast(PhysicalDimension, raw_dimension)
            dimensions[dimension] = PhysicalValue(
                state=state,
                updated_turn_number=0,
                updated_update_id=update_id,
                updated_transition_id=None,
            )

        parsed.append(
            PhysicalEntity(
                entity_id=entity_id,
                key=key,
                kind=cast(PhysicalKind, kind),
                scene_key=scene_key,
                registered_turn_number=0,
                registered_update_id=update_id,
                dimensions=dimensions,
            )
        )

    durable_state = DurableState()
    for entity in sorted(parsed, key=lambda item: item.entity_id):
        register_physical_entity(durable_state, entity)
    validate_actor_entity_ids(durable_state, character_ids)
    return durable_state


def _validate_state(dimension: PhysicalDimension, state: str) -> None:
    if dimension not in PHYSICAL_STATE_VOCABULARIES:
        raise ValueError(f"Unknown physical state dimension: {dimension!r}.")
    if state not in PHYSICAL_STATE_VOCABULARIES[dimension]:
        raise ValueError(f"Invalid {dimension} state: {state!r}.")


def register_physical_entity(durable_state: DurableState, entity: PhysicalEntity) -> None:
    """Materialize one validated entity exactly once, using a defensive copy."""
    if not isinstance(entity.entity_id, str) or not isinstance(entity.key, str):
        raise ValueError("Physical entity IDs and keys must be strings.")
    if not entity.entity_id.strip():
        raise ValueError("Physical entity ID cannot be empty.")
    if not entity.key.strip():
        raise ValueError("Physical entity key cannot be empty.")
    if not isinstance(entity.kind, str) or entity.kind not in ALLOWED_DIMENSIONS_BY_KIND:
        raise ValueError(f"Unknown physical entity kind: {entity.kind!r}.")
    if entity.scene_key is not None and not isinstance(entity.scene_key, str):
        raise ValueError("Physical entity scene key must be a string or null.")
    if entity.kind in SCENE_BOUND_KINDS and not (entity.scene_key or "").strip():
        raise ValueError(f"Physical {entity.kind} requires a scene key.")
    if entity.kind == "actor" and entity.scene_key is not None:
        raise ValueError("Actor location belongs to the position domain.")
    if not isinstance(entity.registered_turn_number, int) or entity.registered_turn_number < 0:
        raise ValueError("Physical entity registration turn must be a non-negative integer.")
    if not isinstance(entity.registered_update_id, str) or not entity.registered_update_id.strip():
        raise ValueError("Physical entity registration update ID cannot be empty.")

    if not isinstance(entity.dimensions, dict):
        raise ValueError("Physical entity dimensions must use the canonical dimension map.")
    dimensions = set(entity.dimensions)
    if not dimensions:
        raise ValueError("Physical entity must declare at least one dimension.")
    missing = REQUIRED_DIMENSIONS_BY_KIND[entity.kind] - dimensions
    if missing:
        raise ValueError(
            f"Physical {entity.kind} is missing required dimensions: {sorted(missing)!r}."
        )
    unsupported = dimensions - ALLOWED_DIMENSIONS_BY_KIND[entity.kind]
    if unsupported:
        raise ValueError(
            f"Physical {entity.kind} has unsupported dimensions: {sorted(unsupported)!r}."
        )

    for dimension, value in entity.dimensions.items():
        if not isinstance(value, PhysicalValue):
            raise ValueError("Physical dimensions must use the canonical value type.")
        if not isinstance(value.state, str):
            raise ValueError("Physical dimension state must be a string.")
        _validate_state(dimension, value.state)
        if not isinstance(value.updated_turn_number, int):
            raise ValueError("Physical value update turn must be an integer.")
        if value.updated_turn_number < entity.registered_turn_number:
            raise ValueError("Physical value update turn precedes entity registration.")
        if not isinstance(value.updated_update_id, str) or not value.updated_update_id.strip():
            raise ValueError("Physical value update ID cannot be empty.")
        if value.updated_transition_id is None:
            if (
                value.updated_turn_number != entity.registered_turn_number
                or value.updated_update_id != entity.registered_update_id
            ):
                raise ValueError("Untransitioned physical value provenance is inconsistent.")
        else:
            if not isinstance(value.updated_transition_id, str):
                raise ValueError("Physical value transition ID must be a string or null.")
            if value.updated_turn_number == entity.registered_turn_number:
                raise ValueError("Physical transition must follow entity registration turn.")
            if not value.updated_transition_id.strip():
                raise ValueError("Physical value transition ID cannot be empty.")

    if entity.entity_id in durable_state.physical_entities:
        raise ValueError(f"Physical entity already exists: {entity.entity_id!r}.")
    if any(existing.key == entity.key for existing in durable_state.physical_entities.values()):
        raise ValueError(f"Physical entity key already exists: {entity.key!r}.")
    durable_state.physical_entities[entity.entity_id] = copy.deepcopy(entity)


def validate_actor_entity_ids(durable_state: DurableState, character_ids: set[str]) -> None:
    """Require actor entities to cover the canonical cast uniformly or not at all."""
    actor_ids = {
        entity.entity_id
        for entity in durable_state.physical_entities.values()
        if entity.kind == "actor"
    }
    invalid = sorted(actor_ids - character_ids)
    if invalid:
        raise ValueError(f"Physical actor entities lack canonical characters: {invalid!r}.")
    missing = sorted(character_ids - actor_ids) if actor_ids else []
    if missing:
        raise ValueError(
            f"Physical actor entities must cover every character uniformly; missing: {missing!r}."
        )


def validate_durable_state(durable_state: DurableState, character_ids: set[str]) -> None:
    """Revalidate a complete store after an extension point returns its draft."""
    if not isinstance(durable_state, DurableState):
        raise ValueError("Durable state must use the canonical domain type.")
    if not isinstance(durable_state.physical_entities, dict):
        raise ValueError("Durable physical entities must use the canonical entity map.")
    validated = DurableState()
    for stored_id, entity in durable_state.physical_entities.items():
        if not isinstance(entity, PhysicalEntity):
            raise ValueError("Durable physical entities must use the canonical domain type.")
        if stored_id != entity.entity_id:
            raise ValueError("Physical entity map key does not match its entity ID.")
        register_physical_entity(validated, entity)
    validate_actor_entity_ids(validated, character_ids)


def _validate_transition_shape(transition: PhysicalTransition) -> None:
    if not isinstance(transition, PhysicalTransition):
        raise PhysicalTransitionRejectionError(
            "Physical transition must use the canonical domain type."
        )
    for label, value in (
        ("ID", transition.transition_id),
        ("entity ID", transition.entity_id),
        ("key", transition.key),
        ("update ID", transition.update_id),
        ("source state", transition.from_state),
        ("target state", transition.to_state),
    ):
        if not isinstance(value, str):
            raise PhysicalTransitionRejectionError(f"Physical transition {label} must be a string.")
    if (
        not isinstance(transition.dimension, str)
        or transition.dimension not in PHYSICAL_STATE_VOCABULARIES
    ):
        raise PhysicalTransitionRejectionError(
            f"Unknown physical state dimension: {transition.dimension!r}."
        )
    if type(transition.turn_number) is not int or transition.turn_number < 0:
        raise PhysicalTransitionRejectionError(
            "Physical transition turn must be a non-negative integer."
        )


def _validate_expected_turn_number(expected_turn_number: int) -> None:
    if type(expected_turn_number) is not int or expected_turn_number < 0:
        raise PhysicalTransitionRejectionError(
            "Expected physical transition turn must be a non-negative integer."
        )


def _apply_physical_transition(
    durable_state: DurableState,
    transition: PhysicalTransition,
) -> None:
    _validate_transition_shape(transition)
    entity = durable_state.physical_entities.get(transition.entity_id)
    if entity is None:
        raise PhysicalTransitionRejectionError(
            f"Physical entity does not exist: {transition.entity_id!r}."
        )
    if entity.key != transition.key:
        raise PhysicalTransitionRejectionError("Physical transition key does not match its entity.")
    value = entity.dimensions.get(transition.dimension)
    if value is None:
        raise PhysicalTransitionRejectionError(
            "Physical transition dimension is not registered for its entity."
        )
    if transition.turn_number <= value.updated_turn_number:
        raise PhysicalTransitionRejectionError("Physical transition provenance is stale.")
    if not transition.update_id.strip():
        raise PhysicalTransitionRejectionError("Physical transition update ID cannot be empty.")
    if not transition.transition_id.strip():
        raise PhysicalTransitionRejectionError("Physical transition ID cannot be empty.")
    if transition.update_id == value.updated_update_id:
        raise PhysicalTransitionRejectionError(
            "Physical transition update ID was already applied to this dimension."
        )
    if transition.transition_id == value.updated_transition_id:
        raise PhysicalTransitionRejectionError(
            "Physical transition ID was already applied to this dimension."
        )
    if value.state != transition.from_state:
        raise PhysicalTransitionRejectionError("Physical transition source state is not current.")
    if transition.from_state == transition.to_state:
        raise PhysicalTransitionRejectionError(
            "Physical transition cannot repeat the current state."
        )
    try:
        _validate_state(transition.dimension, transition.from_state)
        _validate_state(transition.dimension, transition.to_state)
    except ValueError as error:
        raise PhysicalTransitionRejectionError(str(error)) from error
    if (transition.from_state, transition.to_state) not in ALLOWED_PHYSICAL_TRANSITIONS[
        transition.dimension
    ]:
        raise PhysicalTransitionRejectionError(
            f"Illegal {transition.dimension} transition: "
            f"{transition.from_state!r} -> {transition.to_state!r}."
        )

    value.state = transition.to_state
    value.updated_turn_number = transition.turn_number
    value.updated_update_id = transition.update_id
    value.updated_transition_id = transition.transition_id


def apply_physical_transition(
    durable_state: DurableState,
    transition: PhysicalTransition,
    *,
    expected_turn_number: int,
) -> None:
    """Apply one transition only in the Runner beat that supplied its provenance."""
    _validate_expected_turn_number(expected_turn_number)
    _validate_transition_shape(transition)
    if transition.turn_number != expected_turn_number:
        raise PhysicalTransitionRejectionError(
            "Physical transition turn does not match the current beat."
        )
    candidate = copy.deepcopy(durable_state)
    _apply_physical_transition(candidate, transition)
    durable_state.physical_entities = candidate.physical_entities


def apply_physical_state_batch(
    durable_state: DurableState,
    registrations: Sequence[PhysicalEntity],
    transitions: Sequence[PhysicalTransition],
    *,
    expected_turn_number: int,
) -> None:
    """Apply one entity/transition batch without partial mutation."""
    _validate_expected_turn_number(expected_turn_number)
    candidate = copy.deepcopy(durable_state)
    for entity in registrations:
        register_physical_entity(candidate, entity)
    for transition in transitions:
        _validate_transition_shape(transition)
        if transition.turn_number != expected_turn_number:
            raise PhysicalTransitionRejectionError(
                "Physical transition turn does not match the current beat."
            )
        _apply_physical_transition(candidate, transition)
    durable_state.physical_entities = candidate.physical_entities
