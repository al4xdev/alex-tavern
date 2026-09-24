"""Closed durable physical-state contract (Task 69 foundation)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import httpx
import pytest

from src.durable_state import (
    DurableState,
    PhysicalDimension,
    PhysicalEntity,
    PhysicalKind,
    PhysicalTransition,
    PhysicalTransitionRejectionError,
    PhysicalValue,
    apply_physical_state_batch,
    apply_physical_transition,
    bootstrap_physical_entities,
    register_physical_entity,
)
from src.models import dict_to_game_state, game_state_to_dict
from src.plugins.runtime import PluginRuntime
from src.runner import Runner, _stamp_undo_anchor, _undo_anchor
from src.store.sessions import delete_session, list_sessions, load_game, save_game
from tests.factories import director_beat, make_game


def _value(
    state: str,
    *,
    turn: int = 3,
    update_id: str = "register-roof",
    transition_id: str | None = None,
) -> PhysicalValue:
    return PhysicalValue(
        state=state,
        updated_turn_number=turn,
        updated_update_id=update_id,
        updated_transition_id=transition_id,
    )


def _entity(
    kind: PhysicalKind = "structure",
    dimensions: dict[PhysicalDimension, PhysicalValue] | None = None,
    *,
    entity_id: str = "entity-roof",
    key: str = "observatory-roof",
    scene_key: str | None = "observatory",
) -> PhysicalEntity:
    if dimensions is None:
        dimensions = {"integrity": _value("intact")}
    if kind == "actor":
        scene_key = None
    return PhysicalEntity(
        entity_id=entity_id,
        key=key,
        kind=kind,
        scene_key=scene_key,
        registered_turn_number=3,
        registered_update_id="register-roof",
        dimensions=dimensions,
    )


def _entity_for_dimension(dimension: PhysicalDimension, state: str) -> PhysicalEntity:
    if dimension == "vitality":
        return _entity("actor", {dimension: _value(state)})
    if dimension in {"aperture", "security", "traversability"}:
        dimensions: dict[PhysicalDimension, PhysicalValue] = {"aperture": _value("closed")}
        dimensions[dimension] = _value(state)
        return _entity("passage", dimensions)
    if dimension == "resource":
        return _entity("object", {"integrity": _value("intact"), dimension: _value(state)})
    return _entity("structure", {dimension: _value(state)})


def _transition(
    transition_id: str,
    dimension: PhysicalDimension,
    from_state: str,
    to_state: str,
    *,
    turn_number: int = 4,
) -> PhysicalTransition:
    return PhysicalTransition(
        transition_id=transition_id,
        entity_id="entity-roof",
        key="observatory-roof",
        dimension=dimension,
        from_state=from_state,
        to_state=to_state,
        turn_number=turn_number,
        update_id=f"update-{turn_number}",
    )


def _apply(durable: DurableState, transition: PhysicalTransition) -> None:
    apply_physical_transition(
        durable,
        transition,
        expected_turn_number=transition.turn_number,
    )


def test_scenario_bootstrap_normalizes_order_and_assigns_turn_zero_provenance() -> None:
    durable = bootstrap_physical_entities(
        [
            {
                "entity_id": "z-door",
                "key": "tavern.door",
                "kind": "passage",
                "scene_key": "tavern",
                "dimensions": {"aperture": "closed"},
            },
            {
                "entity_id": "a-roof",
                "key": "tavern.roof",
                "kind": "structure",
                "scene_key": "tavern",
                "dimensions": {"integrity": "intact"},
            },
        ],
        character_ids={"C1"},
    )

    assert list(durable.physical_entities) == ["a-roof", "z-door"]
    door = durable.physical_entities["z-door"]
    aperture = door.dimensions["aperture"]
    assert door.registered_turn_number == 0
    assert door.registered_update_id == "scenario-bootstrap:z-door"
    assert aperture.updated_turn_number == 0
    assert aperture.updated_update_id == door.registered_update_id
    assert aperture.updated_transition_id is None


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ([{"entity_id": "incomplete"}], "missing fields"),
        (
            [
                {
                    "entity_id": "roof",
                    "key": "roof",
                    "kind": "structure",
                    "scene_key": "hall",
                    "dimensions": {"integrity": "intact"},
                    "provenance": "authored",
                }
            ],
            "unknown fields",
        ),
        (
            [
                {
                    "entity_id": "C999",
                    "key": "unknown-actor",
                    "kind": "actor",
                    "dimensions": {"vitality": "active"},
                }
            ],
            "lack canonical characters",
        ),
        (
            [
                {
                    "entity_id": "C1",
                    "key": "actor-one",
                    "kind": "actor",
                    "dimensions": {"vitality": "active"},
                }
            ],
            "cover every character uniformly",
        ),
    ],
)
def test_scenario_bootstrap_rejects_malformed_or_dangling_entries(
    manifest: list[object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        bootstrap_physical_entities(manifest, character_ids={"C1", "C2"})


@pytest.mark.parametrize(
    ("dimension", "state"),
    [
        ("vitality", "active"),
        ("aperture", "closed"),
        ("security", "unlocked"),
        ("integrity", "intact"),
        ("traversability", "clear"),
        ("resource", "ready"),
    ],
)
def test_each_dimension_rejects_a_reproposal_of_its_current_state(
    dimension: PhysicalDimension, state: str
) -> None:
    durable = DurableState()
    register_physical_entity(durable, _entity_for_dimension(dimension, state))

    with pytest.raises(PhysicalTransitionRejectionError, match="cannot repeat"):
        _apply(
            durable,
            _transition("repeat", dimension, state, state),
        )


def test_integrity_damage_can_escalate_to_destruction() -> None:
    durable = DurableState()
    register_physical_entity(durable, _entity())
    _apply(
        durable,
        _transition("damage", "integrity", "intact", "damaged"),
    )
    _apply(
        durable,
        _transition("destroy", "integrity", "damaged", "destroyed", turn_number=5),
    )

    value = durable.physical_entities["entity-roof"].dimensions["integrity"]
    assert value.state == "destroyed"
    assert value.updated_transition_id == "destroy"


def test_source_inspired_pillar_duplicate_and_independent_gap_transition() -> None:
    durable = DurableState()
    source_update = "source:8bd4d0f1:t27"
    register_physical_entity(
        durable,
        PhysicalEntity(
            entity_id="hall-pillar",
            key="hall.pillar",
            kind="structure",
            scene_key="great-hall",
            registered_turn_number=27,
            registered_update_id=source_update,
            dimensions={
                "integrity": PhysicalValue(
                    state="damaged",
                    updated_turn_number=27,
                    updated_update_id=source_update,
                    updated_transition_id=None,
                )
            },
        ),
    )
    register_physical_entity(
        durable,
        PhysicalEntity(
            entity_id="rubble-gap",
            key="hall.rubble-gap",
            kind="passage",
            scene_key="great-hall",
            registered_turn_number=27,
            registered_update_id=source_update,
            dimensions={
                "aperture": PhysicalValue(
                    state="ajar",
                    updated_turn_number=27,
                    updated_update_id=source_update,
                    updated_transition_id=None,
                )
            },
        ),
    )

    apply_physical_transition(
        durable,
        PhysicalTransition(
            transition_id="8bd4d0f1:t28:pillar-collapse",
            entity_id="hall-pillar",
            key="hall.pillar",
            dimension="integrity",
            from_state="damaged",
            to_state="destroyed",
            turn_number=28,
            update_id="source:8bd4d0f1:t28",
        ),
        expected_turn_number=28,
    )

    with pytest.raises(PhysicalTransitionRejectionError, match="cannot repeat"):
        apply_physical_transition(
            durable,
            PhysicalTransition(
                transition_id="8bd4d0f1:t29:repeated-pillar-collapse",
                entity_id="hall-pillar",
                key="hall.pillar",
                dimension="integrity",
                from_state="destroyed",
                to_state="destroyed",
                turn_number=29,
                update_id="source:8bd4d0f1:t29",
            ),
            expected_turn_number=29,
        )

    apply_physical_transition(
        durable,
        PhysicalTransition(
            transition_id="fixture:t29:gap-sealed",
            entity_id="rubble-gap",
            key="hall.rubble-gap",
            dimension="aperture",
            from_state="ajar",
            to_state="closed",
            turn_number=29,
            update_id="source:8bd4d0f1:t29",
        ),
        expected_turn_number=29,
    )

    pillar = durable.physical_entities["hall-pillar"].dimensions["integrity"]
    assert pillar.state == "destroyed"
    assert pillar.updated_turn_number == 28
    assert pillar.updated_transition_id == "8bd4d0f1:t28:pillar-collapse"
    gap = durable.physical_entities["rubble-gap"].dimensions["aperture"]
    assert gap.state == "closed"
    assert gap.updated_turn_number == 29
    assert gap.updated_transition_id == "fixture:t29:gap-sealed"


def test_independent_dimensions_can_change_atomically_in_one_beat() -> None:
    durable = DurableState()
    door = _entity(
        "passage",
        {
            "aperture": _value("closed"),
            "security": _value("locked"),
            "integrity": _value("intact"),
        },
    )
    register_physical_entity(durable, door)

    apply_physical_state_batch(
        durable,
        [],
        [
            _transition("unlock", "security", "locked", "unlocked"),
            _transition("open", "aperture", "closed", "open"),
        ],
        expected_turn_number=4,
    )

    states = {
        dimension: value.state
        for dimension, value in durable.physical_entities["entity-roof"].dimensions.items()
    }
    assert states == {"aperture": "open", "security": "unlocked", "integrity": "intact"}


def test_doorless_passage_can_track_only_traversability() -> None:
    durable = DurableState()
    arch = _entity("passage", {"traversability": _value("clear")})

    register_physical_entity(durable, arch)
    _apply(
        durable,
        _transition("rubble", "traversability", "clear", "obstructed"),
    )

    stored = durable.physical_entities["entity-roof"]
    assert set(stored.dimensions) == {"traversability"}
    assert stored.dimensions["traversability"].state == "obstructed"


def test_one_dimension_cannot_change_twice_in_the_same_beat() -> None:
    durable = DurableState()
    register_physical_entity(durable, _entity())

    with pytest.raises(PhysicalTransitionRejectionError, match="provenance is stale"):
        apply_physical_state_batch(
            durable,
            [],
            [
                _transition("damage", "integrity", "intact", "damaged"),
                _transition("destroy", "integrity", "damaged", "destroyed"),
            ],
            expected_turn_number=4,
        )

    assert durable.physical_entities["entity-roof"].dimensions["integrity"].state == "intact"


def test_old_transition_cannot_be_replayed_after_a_legal_reversal() -> None:
    durable = DurableState()
    register_physical_entity(
        durable,
        _entity("passage", {"aperture": _value("closed")}),
    )
    opened = _transition("open", "aperture", "closed", "open")

    _apply(durable, opened)
    _apply(
        durable,
        _transition("close", "aperture", "open", "closed", turn_number=5),
    )

    with pytest.raises(PhysicalTransitionRejectionError, match="provenance is stale"):
        _apply(durable, opened)


def test_transition_turn_must_match_the_callers_current_beat() -> None:
    durable = DurableState()
    register_physical_entity(durable, _entity())
    transition = _transition("damage", "integrity", "intact", "damaged")

    with pytest.raises(PhysicalTransitionRejectionError, match="does not match the current beat"):
        apply_physical_transition(durable, transition, expected_turn_number=999)

    assert durable.physical_entities["entity-roof"].dimensions["integrity"].state == "intact"


@pytest.mark.parametrize(
    ("transition", "expected_turn_number", "message"),
    [
        (
            replace(_transition("damage", "integrity", "intact", "damaged"), turn_number="4"),
            4,
            "turn must be",
        ),
        (
            replace(_transition("damage", "integrity", "intact", "damaged"), turn_number=True),
            True,
            "turn must be",
        ),
        (
            replace(_transition("damage", "integrity", "intact", "damaged"), transition_id=None),
            4,
            "ID must be",
        ),
        (
            replace(_transition("damage", "integrity", "intact", "damaged"), update_id=None),
            4,
            "update ID must be",
        ),
        (
            replace(_transition("damage", "integrity", "intact", "damaged"), to_state=None),
            4,
            "target state must be",
        ),
    ],
)
def test_malformed_transition_fields_use_the_rejection_boundary(
    transition: PhysicalTransition,
    expected_turn_number: int,
    message: str,
) -> None:
    durable = DurableState()
    register_physical_entity(durable, _entity())

    with pytest.raises(PhysicalTransitionRejectionError, match=message):
        apply_physical_transition(
            durable,
            transition,
            expected_turn_number=expected_turn_number,
        )

    assert durable.physical_entities["entity-roof"].dimensions["integrity"].state == "intact"


def test_registration_is_unique_and_keeps_a_defensive_copy() -> None:
    durable = DurableState()
    entity = _entity()
    register_physical_entity(durable, entity)
    with pytest.raises(ValueError, match="already exists"):
        register_physical_entity(durable, entity)
    with pytest.raises(ValueError, match="key already exists"):
        register_physical_entity(durable, replace(entity, entity_id="another-roof"))

    entity.dimensions["integrity"].state = "invented"
    stored = durable.physical_entities["entity-roof"]
    assert stored.dimensions["integrity"].state == "intact"


@pytest.mark.parametrize(
    ("entity", "message"),
    [
        (replace(_entity(), entity_id="  "), "entity ID cannot be empty"),
        (replace(_entity(), key=""), "entity key cannot be empty"),
        (replace(_entity(), scene_key=None), "requires a scene key"),
        (
            _entity("object", {"integrity": _value("intact")}, scene_key=None),
            "requires a scene key",
        ),
        (
            replace(_entity("actor", {"vitality": _value("active")}), scene_key="hall"),
            "position domain",
        ),
        (_entity("structure", {"aperture": _value("closed")}), "missing required"),
        (
            _entity(
                "structure",
                {"integrity": _value("intact"), "security": _value("unlocked")},
            ),
            "unsupported dimensions",
        ),
    ],
)
def test_registration_rejects_invalid_identity_scope_and_shape(
    entity: PhysicalEntity, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        register_physical_entity(DurableState(), entity)


def test_transition_rejects_entity_key_dimension_source_and_edge_mismatches() -> None:
    durable = DurableState()
    register_physical_entity(durable, _entity())
    candidate = _transition("damage", "integrity", "intact", "damaged")

    for invalid, message in (
        (replace(candidate, entity_id="missing"), "does not exist"),
        (replace(candidate, key="other-roof"), "key does not match"),
        (replace(candidate, dimension="resource"), "dimension is not registered"),
        (replace(candidate, from_state="damaged"), "source state is not current"),
        (replace(candidate, to_state="ready"), "Invalid integrity state"),
    ):
        with pytest.raises(PhysicalTransitionRejectionError, match=message):
            _apply(durable, invalid)


def test_terminal_integrity_cannot_be_repaired_by_the_transition_graph() -> None:
    durable = DurableState()
    register_physical_entity(
        durable,
        _entity(
            dimensions={
                "integrity": _value(
                    "destroyed",
                    turn=4,
                    update_id="destroy-update",
                    transition_id="destroy",
                )
            }
        ),
    )

    with pytest.raises(PhysicalTransitionRejectionError, match="Illegal integrity transition"):
        _apply(
            durable,
            _transition("repair", "integrity", "destroyed", "intact", turn_number=5),
        )


def test_batch_discards_earlier_members_when_a_later_one_fails() -> None:
    durable = DurableState()
    register_physical_entity(
        durable,
        _entity(
            "passage",
            {"aperture": _value("closed"), "integrity": _value("intact")},
        ),
    )
    before = deepcopy(durable)
    registered_in_draft = _entity(
        "object",
        {"integrity": _value("intact")},
        entity_id="entity-crate",
        key="observatory-crate",
    )

    with pytest.raises(PhysicalTransitionRejectionError, match="source state is not current"):
        apply_physical_state_batch(
            durable,
            [registered_in_draft],
            [
                _transition("damage", "integrity", "intact", "damaged"),
                _transition("stale", "aperture", "open", "ajar"),
            ],
            expected_turn_number=4,
        )

    assert durable == before


def test_round_trip_requires_current_durable_shape_and_valid_provenance() -> None:
    game = make_game()
    register_physical_entity(game.durable_state, _entity())
    runner = Runner.__new__(Runner)
    runner._append_history(game, "Narrator", "O teto estala.", "narration", 3)
    data = game_state_to_dict(game)

    restored = dict_to_game_state(data)
    assert set(data["durable_state"]) == {"physical_entities"}
    entity = restored.durable_state.physical_entities["entity-roof"]
    assert entity.scene_key == "observatory"
    assert entity.dimensions["integrity"].state == "intact"
    snapshot = restored.history[0].durable_state_snapshot
    assert snapshot.physical_entities["entity-roof"].dimensions["integrity"].state == "intact"

    without_state = deepcopy(data)
    del without_state["durable_state"]
    with pytest.raises(KeyError, match="durable_state"):
        dict_to_game_state(without_state)

    without_snapshot = deepcopy(data)
    del without_snapshot["history"][0]["durable_state_snapshot"]
    with pytest.raises(KeyError, match="durable_state_snapshot"):
        dict_to_game_state(without_snapshot)

    mismatched_key = deepcopy(data)
    mismatched_key["durable_state"]["physical_entities"]["entity-roof"]["entity_id"] = "other"
    with pytest.raises(ValueError, match="does not match"):
        dict_to_game_state(mismatched_key)

    inconsistent = deepcopy(data)
    value = inconsistent["durable_state"]["physical_entities"]["entity-roof"]["dimensions"][
        "integrity"
    ]
    value["updated_turn_number"] = 2
    with pytest.raises(ValueError, match="precedes entity registration"):
        dict_to_game_state(inconsistent)

    unknown_actor = deepcopy(data)
    actor = _entity(
        "actor",
        {"vitality": _value("active")},
        entity_id="C999",
        key="unknown-actor",
    )
    unknown_actor["durable_state"]["physical_entities"][actor.entity_id] = {
        "entity_id": actor.entity_id,
        "key": actor.key,
        "kind": actor.kind,
        "scene_key": actor.scene_key,
        "registered_turn_number": actor.registered_turn_number,
        "registered_update_id": actor.registered_update_id,
        "dimensions": {
            "vitality": {
                "state": "active",
                "updated_turn_number": 3,
                "updated_update_id": "register-roof",
                "updated_transition_id": None,
            }
        },
    }
    with pytest.raises(ValueError, match="lack canonical characters"):
        dict_to_game_state(unknown_actor)


@pytest.mark.asyncio
async def test_authoritative_store_persists_beyond_the_descriptive_fact_cap() -> None:
    game = make_game()
    try:
        for index in range(41):
            entity_id = f"fixture-{index:02d}"
            register_physical_entity(
                game.durable_state,
                _entity(
                    entity_id=entity_id,
                    key=f"hall.fixture-{index:02d}",
                ),
            )

        save_game(game)
        restored = load_game(game.session_id)
    finally:
        await delete_session(game.session_id)

    assert restored is not None
    assert len(restored.durable_state.physical_entities) == 41
    assert set(restored.durable_state.physical_entities) == {
        f"fixture-{index:02d}" for index in range(41)
    }


def test_pre_beat_anchor_overrides_a_post_transition_record_snapshot() -> None:
    game = make_game()
    register_physical_entity(game.durable_state, _entity())
    anchor = _undo_anchor(game)

    _apply(
        game.durable_state,
        _transition("damage", "integrity", "intact", "damaged"),
    )
    runner = Runner.__new__(Runner)
    runner._append_history(game, "Narrator", "O teto estala.", "narration", 4)
    stored = game.history[-1].durable_state_snapshot.physical_entities["entity-roof"]
    assert stored.dimensions["integrity"].state == "damaged"

    _stamp_undo_anchor(game, 4, anchor)

    snapshot = game.history[-1].durable_state_snapshot.physical_entities["entity-roof"]
    assert snapshot.dimensions["integrity"].state == "intact"


@pytest.mark.asyncio
async def test_undo_restores_the_pre_turn_durable_state() -> None:
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {})
        seed = make_game()
        session_id = await runner.start_session(
            {
                "characters": seed.characters,
                "scene": seed.scene,
                "controlled_character_id": "C1",
            }
        )
        try:
            game = await runner.get_state(session_id)
            assert game is not None
            entity = _entity()
            entity.registered_turn_number = 0
            entity.dimensions["integrity"].updated_turn_number = 0
            register_physical_entity(game.durable_state, entity)
            runner._append_history(game, "Narrator", "O teto estala.", "narration", 1)
            _apply(
                game.durable_state,
                _transition("damage", "integrity", "intact", "damaged", turn_number=1),
            )
            save_game(game)

            result = await runner.undo_turn(session_id)
            restored = await runner.get_state(session_id)
        finally:
            await delete_session(session_id)

    assert result["undone"] is True
    assert restored is not None
    value = restored.durable_state.physical_entities["entity-roof"].dimensions["integrity"]
    assert value.state == "intact"
    assert value.updated_transition_id is None


@pytest.mark.asyncio
async def test_invalid_bootstrap_aborts_before_a_session_is_saved() -> None:
    before = {item["session_id"] for item in list_sessions()}
    seed = make_game()
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {})
        with pytest.raises(ValueError, match="Invalid integrity state"):
            await runner.start_session(
                {
                    "characters": seed.characters,
                    "scene": seed.scene,
                    "controlled_character_id": "C1",
                    "physical_entities": [
                        {
                            "entity_id": "roof",
                            "key": "hall.roof",
                            "kind": "structure",
                            "scene_key": "hall",
                            "dimensions": {"integrity": "pristine"},
                        }
                    ],
                }
            )

    assert {item["session_id"] for item in list_sessions()} == before


@pytest.mark.asyncio
async def test_partial_custom_session_does_not_inherit_the_default_manifest() -> None:
    seed = make_game()
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {})
        session_ids: list[str] = []
        try:
            for config in (
                {"scene": seed.scene},
                {"characters": seed.characters},
            ):
                session_id = await runner.start_session(config)
                session_ids.append(session_id)
                game = await runner.get_state(session_id)
                assert game is not None
                assert game.durable_state.physical_entities == {}
        finally:
            for session_id in session_ids:
                await delete_session(session_id)


@pytest.mark.asyncio
async def test_session_precommit_cannot_persist_invalid_durable_state() -> None:
    runtime = PluginRuntime()

    def corrupt_durable_state(game, context):  # noqa: ANN001, ANN202, ARG001
        entity = game.durable_state.physical_entities["thorn-lyra-main-hall-door"]
        entity.dimensions["aperture"].state = "invented"
        return game

    runtime.hooks.register(
        "test.invalid-durable-state",
        "session.before_commit",
        "filter",
        corrupt_durable_state,
    )
    before = {item["session_id"] for item in list_sessions()}
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)
        with pytest.raises(ValueError, match="Invalid aperture state"):
            await runner.start_session()

    assert {item["session_id"] for item in list_sessions()} == before


@pytest.mark.asyncio
@pytest.mark.parametrize("hook_name", ["narrator.result", "turn.before_commit"])
async def test_turn_precommit_cannot_persist_invalid_durable_state(hook_name: str) -> None:
    runtime = PluginRuntime()

    def corrupt_durable_state(game, context):  # noqa: ANN001, ANN202, ARG001
        entity = game.durable_state.physical_entities["thorn-lyra-main-hall-door"]
        entity.dimensions["aperture"].state = "invented"
        return game

    runtime.hooks.register(
        "test.invalid-turn-durable-state",
        hook_name,
        "filter",
        corrupt_durable_state,
    )
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return director_beat(next_speakers=["Narrator"])

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A porta permanece imóvel."

        runner._call_narrator = fake_narrator
        runner._render_narration = fake_prose
        session_id = await runner.start_session()
        try:
            with pytest.raises(ValueError, match="Invalid aperture state"):
                await runner.player_turn(session_id, thought="Observo a porta.")
            persisted = await runner.get_state(session_id)
        finally:
            await delete_session(session_id)

    assert persisted is not None
    assert persisted.history == []
    value = persisted.durable_state.physical_entities["thorn-lyra-main-hall-door"].dimensions[
        "aperture"
    ]
    assert value.state == "closed"


@pytest.mark.asyncio
async def test_undo_precommit_cannot_persist_invalid_durable_state() -> None:
    runtime = PluginRuntime()

    def corrupt_durable_state(game, context):  # noqa: ANN001, ANN202, ARG001
        entity = game.durable_state.physical_entities["thorn-lyra-main-hall-door"]
        entity.dimensions["aperture"].state = "invented"
        return game

    runtime.hooks.register(
        "test.invalid-undo-durable-state",
        "undo.before_commit",
        "filter",
        corrupt_durable_state,
    )
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return director_beat(next_speakers=["Narrator"])

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A porta permanece imóvel."

        runner._call_narrator = fake_narrator
        runner._render_narration = fake_prose
        session_id = await runner.start_session()
        try:
            await runner.player_turn(session_id, thought="Observo a porta.")
            before = await runner.get_state(session_id)
            with pytest.raises(ValueError, match="Invalid aperture state"):
                await runner.undo_turn(session_id)
            persisted = await runner.get_state(session_id)
        finally:
            await delete_session(session_id)

    assert before is not None
    assert persisted is not None
    assert persisted.history == before.history
    value = persisted.durable_state.physical_entities["thorn-lyra-main-hall-door"].dimensions[
        "aperture"
    ]
    assert value.state == "closed"


@pytest.mark.asyncio
async def test_bootstrapped_fixture_transitions_in_a_real_beat_and_undoes() -> None:
    runtime = PluginRuntime()

    def hardcoded_transition(game, context):  # noqa: ANN001, ANN202
        apply_physical_transition(
            game.durable_state,
            PhysicalTransition(
                transition_id="test-open-door",
                entity_id="thorn-lyra-main-hall-door",
                key="thorn-lyra.main-hall.door",
                dimension="aperture",
                from_state="closed",
                to_state="open",
                turn_number=context["turn_number"],
                update_id="test-beat-1",
            ),
            expected_turn_number=context["turn_number"],
        )
        return game

    runtime.hooks.register(
        "test.durable-state",
        "narrator.result",
        "filter",
        hardcoded_transition,
    )
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return director_beat(next_speakers=["Narrator"])

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A porta se abre."

        runner._call_narrator = fake_narrator
        runner._render_narration = fake_prose
        session_id = await runner.start_session()
        try:
            bootstrapped = await runner.get_state(session_id)
            assert bootstrapped is not None
            initial = bootstrapped.durable_state.physical_entities["thorn-lyra-main-hall-door"]
            assert initial.dimensions["aperture"].state == "closed"
            assert initial.registered_turn_number == 0

            result = await runner.player_turn(session_id, thought="Observo a porta.")
            transitioned = await runner.get_state(session_id)
            assert result["turn_number"] == 1
            assert transitioned is not None
            value = transitioned.durable_state.physical_entities[
                "thorn-lyra-main-hall-door"
            ].dimensions["aperture"]
            assert value.state == "open"
            assert value.updated_turn_number == 1

            await runner.undo_turn(session_id)
            restored = await runner.get_state(session_id)
        finally:
            await delete_session(session_id)

    assert restored is not None
    value = restored.durable_state.physical_entities["thorn-lyra-main-hall-door"].dimensions[
        "aperture"
    ]
    assert value.state == "closed"
    assert value.updated_transition_id is None


@pytest.mark.asyncio
async def test_repeated_state_transition_is_rejected_across_runner_submissions() -> None:
    runtime = PluginRuntime()
    rejected: list[tuple[int, str]] = []

    def target_open_door(game, context):  # noqa: ANN001, ANN202
        turn_number = context["turn_number"]
        value = game.durable_state.physical_entities["thorn-lyra-main-hall-door"].dimensions[
            "aperture"
        ]
        try:
            apply_physical_transition(
                game.durable_state,
                PhysicalTransition(
                    transition_id=f"test-open-door-{turn_number}",
                    entity_id="thorn-lyra-main-hall-door",
                    key="thorn-lyra.main-hall.door",
                    dimension="aperture",
                    from_state=value.state,
                    to_state="open",
                    turn_number=turn_number,
                    update_id=f"test-beat-{turn_number}",
                ),
                expected_turn_number=turn_number,
            )
        except PhysicalTransitionRejectionError as error:
            rejected.append((turn_number, str(error)))
        return game

    runtime.hooks.register(
        "test.durable-state-target",
        "narrator.result",
        "filter",
        target_open_door,
    )
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return director_beat(next_speakers=["Narrator"])

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A porta permanece como está."

        runner._call_narrator = fake_narrator
        runner._render_narration = fake_prose
        session_id = await runner.start_session()
        try:
            first_result = await runner.player_turn(session_id, thought="Observo a porta.")
            after_first = await runner.get_state(session_id)
            second_result = await runner.player_turn(session_id, thought="Continuo observando.")
            after_second = await runner.get_state(session_id)
        finally:
            await delete_session(session_id)

    assert first_result["turn_number"] == 1
    assert second_result["turn_number"] == 2
    assert rejected == [(2, "Physical transition cannot repeat the current state.")]
    assert after_first is not None
    assert after_second is not None
    first_value = after_first.durable_state.physical_entities[
        "thorn-lyra-main-hall-door"
    ].dimensions["aperture"]
    second_value = after_second.durable_state.physical_entities[
        "thorn-lyra-main-hall-door"
    ].dimensions["aperture"]
    assert second_value == first_value
    assert second_value.state == "open"
    assert second_value.updated_turn_number == 1
    assert second_value.updated_transition_id == "test-open-door-1"


@pytest.mark.asyncio
async def test_legal_integrity_escalation_crosses_runner_submissions() -> None:
    runtime = PluginRuntime()

    def escalate_roof(game, context):  # noqa: ANN001, ANN202
        turn_number = context["turn_number"]
        from_state, to_state, transition_id = {
            1: ("intact", "damaged", "test-damage-roof"),
            2: ("damaged", "destroyed", "test-destroy-roof"),
        }[turn_number]
        apply_physical_transition(
            game.durable_state,
            PhysicalTransition(
                transition_id=transition_id,
                entity_id="test-hall-roof",
                key="test.hall.roof",
                dimension="integrity",
                from_state=from_state,
                to_state=to_state,
                turn_number=turn_number,
                update_id=f"test-beat-{turn_number}",
            ),
            expected_turn_number=turn_number,
        )
        return game

    runtime.hooks.register(
        "test.durable-state-escalation",
        "narrator.result",
        "filter",
        escalate_roof,
    )
    seed = make_game()
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return director_beat(next_speakers=["Narrator"])

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A estrutura cede mais um pouco."

        runner._call_narrator = fake_narrator
        runner._render_narration = fake_prose
        session_id = await runner.start_session(
            {
                "characters": seed.characters,
                "scene": seed.scene,
                "controlled_character_id": "C1",
                "physical_entities": [
                    {
                        "entity_id": "test-hall-roof",
                        "key": "test.hall.roof",
                        "kind": "structure",
                        "scene_key": "test.hall",
                        "dimensions": {"integrity": "intact"},
                    }
                ],
            }
        )
        try:
            first_result = await runner.player_turn(session_id, thought="Ouço um estalo.")
            second_result = await runner.player_turn(session_id, thought="O teto continua cedendo.")
            persisted = await runner.get_state(session_id)
        finally:
            await delete_session(session_id)

    assert first_result["turn_number"] == 1
    assert second_result["turn_number"] == 2
    assert persisted is not None
    value = persisted.durable_state.physical_entities["test-hall-roof"].dimensions["integrity"]
    assert value.state == "destroyed"
    assert value.updated_turn_number == 2
    assert value.updated_update_id == "test-beat-2"
    assert value.updated_transition_id == "test-destroy-roof"
    assert {record.turn_number for record in persisted.history} == {1, 2}
