"""The factories are a contract, so they get tested like one.

`director_beat` exists so the Director's response shape lives in ONE place. A
test that hand-writes the dict is a test that can silently drift from the
schema, which is how `zone_moves` and `return_control` ended up absent from
most doubles for months.
"""

from __future__ import annotations

import pytest

from src.agents.narrator import build_narrator_json_schema
from tests.factories import (
    DIRECTOR_CONTRACT_DEFAULTS,
    FakeDirector,
    director_beat,
    make_cast,
    make_game,
    make_record,
)


def test_director_beat_covers_every_field_the_real_schema_requires() -> None:
    """The factory must not drift from what the Director actually returns."""
    required = set(build_narrator_json_schema(["C1", "C2"])["schema"]["required"])
    missing = required - set(DIRECTOR_CONTRACT_DEFAULTS)
    assert missing == set(), f"director_beat is missing required fields: {sorted(missing)}"


def test_director_beat_returns_the_whole_contract() -> None:
    beat = director_beat(next_speakers=["C2"])
    assert set(beat) == set(DIRECTOR_CONTRACT_DEFAULTS)
    assert beat["next_speakers"] == ["C2"]
    assert beat["perception_events"] == []
    assert beat["return_control"] is False


def test_director_beat_rejects_a_field_the_contract_does_not_have() -> None:
    """A typo used to become a silently ignored key in a hand-written dict."""
    with pytest.raises(AssertionError, match="not part of the Director contract"):
        director_beat(next_speaker=["C2"])


def test_director_beat_does_not_share_mutable_defaults() -> None:
    first = director_beat()
    first["perception_events"].append({"event_kind": "observation"})
    assert director_beat()["perception_events"] == []


@pytest.mark.asyncio
async def test_fake_director_answers_in_order_then_holds_the_last_beat() -> None:
    director = FakeDirector(
        director_beat(next_speakers=["C2"]),
        director_beat(next_speakers=["C3"], return_control=True),
    )
    assert (await director(turn_number=1))["next_speakers"] == ["C2"]
    assert (await director(turn_number=2))["next_speakers"] == ["C3"]
    assert (await director(turn_number=3))["next_speakers"] == ["C3"]
    assert director.call_count == 3
    assert [call["turn_number"] for call in director.calls] == [1, 2, 3]


def test_make_record_defaults_the_snapshot_nobody_asserts_on() -> None:
    game = make_game(characters=make_cast("Rui", "Marta"))
    record = make_record(3, "C2", "Uma fala.", scene=game.scene)
    assert record.turn_number == 3
    assert record.content_type == "speech"
    assert record.scene_snapshot.location == game.scene.location
    assert record.scene_snapshot is not game.scene, "the snapshot must be a copy"
