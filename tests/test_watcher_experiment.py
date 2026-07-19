"""Deterministic pieces of the experimental 33b watcher (tools-only, no API)."""

from __future__ import annotations

from tools.watcher_experiment import (
    DELTA_KINDS,
    StallLadder,
    build_delta_audit_schema,
    build_intervention_schema,
)


def test_delta_audit_schema_is_closed_over_known_kinds() -> None:
    schema = build_delta_audit_schema()["schema"]
    assert schema["properties"]["deltas"]["items"]["enum"] == DELTA_KINDS
    assert "none" in DELTA_KINDS
    assert schema["additionalProperties"] is False


def test_intervention_schema_requires_the_full_causal_contract() -> None:
    schema = build_intervention_schema()["schema"]
    intervention = schema["properties"]["intervention"]
    assert set(intervention["required"]) == {
        "source_thread",
        "target_state",
        "event_now",
        "expected_delta",
        "closes_or_advances",
        "refractory_turns",
    }
    assert "open_threads" in schema["required"]


def test_ladder_fires_on_threshold_and_respects_refractory() -> None:
    ladder = StallLadder(threshold=2, refractory_turns=3)
    sequence = [
        (1, ["none"], False),
        (2, [], True),  # two quiet turns -> fire, cooldown starts
        (3, ["none"], False),  # cooling down
        (4, ["threat_advanced"], False),  # material progress resets quiet
        (5, [], False),  # cooldown expires this turn
        (6, ["none"], True),  # quiet again for two turns -> fire
        (7, [], False),
        (8, [], False),  # still cooling
    ]
    for turn, deltas, expected in sequence:
        assert ladder.observe(turn, deltas) is expected, turn
    assert ladder.fired == [2, 6]


def test_ladder_never_fires_while_scene_progresses() -> None:
    ladder = StallLadder(threshold=2, refractory_turns=3)
    for turn in range(1, 12):
        assert ladder.observe(turn, ["decision_taken"]) is False
    assert ladder.fired == []
