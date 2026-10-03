"""Readers sharing a room do not automatically share private prose history."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from src.agents.prose import build_prose_messages, prose_history_for_viewers
from src.models import TurnRecord, deepcopy_scene, record_visible_to
from src.runner import Runner
from tests.factories import make_cast, make_game, make_scene

CAST = make_cast("Iara", "Bento", "Clara")
SECRET = "A cifra privada revela que a Dama do Norte é Glinda."
PUBLIC_EVENT = {
    "event_kind": "observation",
    "subject_id": "Narrator",
    "content": "Uma lâmpada pública pisca.",
    "witness_ids": ["C1", "C2", "C3"],
}


def private_history_game() -> Any:
    game = make_game(characters=CAST, scene=make_scene(characters=CAST), controlled="C1")
    game.history = [
        TurnRecord(
            1,
            "Narrator",
            SECRET,
            "narration",
            deepcopy_scene(game.scene),
            audience=["C1", "C2"],
            audience_origin="zone",
        )
    ]
    return game


def test_private_history_refines_a_shared_room() -> None:
    assert Runner._narration_clusters(private_history_game(), [PUBLIC_EVENT]) == [
        {"C1", "C2"},
        {"C3"},
    ]


def test_a_private_current_event_refines_a_shared_room() -> None:
    game = make_game(characters=CAST, scene=make_scene(characters=CAST), controlled="C1")
    private_event = {**PUBLIC_EVENT, "content": SECRET, "witness_ids": ["C1", "C2"]}
    assert Runner._narration_clusters(game, [PUBLIC_EVENT, private_event]) == [{"C1", "C2"}, {"C3"}]


@pytest.mark.asyncio
async def test_public_event_and_visible_bystander_survive_private_history_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = private_history_game()
    captured: list[tuple[set[str] | None, str]] = []

    async def renderer(
        state: Any,
        events: list[dict[str, Any]],
        step: int,
        viewers: set[str] | None = None,
        **kwargs: Any,
    ) -> str:
        messages = build_prose_messages(
            state.scene,
            state.characters,
            "C1",
            state.history,
            events,
            viewers=viewers,
            **kwargs,
        )
        user = messages[1]["content"]
        captured.append((viewers, user))
        return SECRET if SECRET in user else "Uma lâmpada pública pisca."

    async with httpx.AsyncClient() as client:
        runner = Runner(client, {})
        monkeypatch.setattr(runner, "_render_narration", renderer)
        await runner._render_and_prepare(
            game,
            {"perception_events": [PUBLIC_EVENT]},
            [],
            2,
            multi_beat=False,
        )
    assert len(captured) == 2
    for viewers, user in captured:
        assert "Uma lâmpada pública pisca." in user
        assert "Clara" in user.split("CAST (visible appearance only):", 1)[1].split("\n\n", 1)[0]
        if viewers == {"C3"}:
            assert SECRET not in user
        else:
            assert viewers == {"C1", "C2"} and SECRET in user
    private_record = next(r for r in game.history if r.turn_number == 2 and SECRET in r.content)
    assert record_visible_to(private_record, "C2")
    assert not record_visible_to(private_record, "C3")


def test_public_scene_retains_one_public_render() -> None:
    game = private_history_game()
    game.history[0].audience = None
    assert Runner._narration_clusters(game, [PUBLIC_EVENT]) == [None]


def test_later_public_disclosure_does_not_reveal_its_private_antecedent() -> None:
    game = private_history_game()
    private_source = game.history[0]
    public_reply = TurnRecord(
        2,
        "C2",
        "Sei onde Glinda se esconde.",
        "speech",
        deepcopy_scene(game.scene),
        audience=["C1", "C3"],
        audience_origin="zone",
    )
    game.history.append(public_reply)
    assert prose_history_for_viewers(game.history, {"C3"}) == [public_reply]
    assert prose_history_for_viewers(game.history, {"C2"}) == [private_source, public_reply]
    assert Runner._narration_clusters(game, [PUBLIC_EVENT]) == [{"C1", "C2"}, {"C3"}]
    prompt = build_prose_messages(
        game.scene,
        game.characters,
        "C1",
        game.history,
        [PUBLIC_EVENT],
        viewers={"C3"},
        staging_viewers=set(CAST),
    )[1]["content"]
    assert SECRET not in prompt
    assert "Bento [speech]" in prompt


def test_whisper_projection_keeps_visible_cast_without_its_words() -> None:
    game = private_history_game()
    whisper = TurnRecord(
        2,
        "C1",
        "O selo privado mostra a senha da cifra.",
        "speech",
        deepcopy_scene(game.scene),
        audience=["C2"],
        audience_origin="explicit",
    )
    game.history = [whisper]
    assert prose_history_for_viewers(game.history, {"C1"}) == [whisper]
    assert prose_history_for_viewers(game.history, {"C2"}) == [whisper]
    assert prose_history_for_viewers(game.history, {"C3"}) == []
    assert Runner._narration_clusters(game, [PUBLIC_EVENT]) == [{"C1", "C2"}, {"C3"}]
    prompt = build_prose_messages(
        game.scene,
        game.characters,
        "C1",
        game.history,
        [PUBLIC_EVENT],
        viewers={"C3"},
        staging_viewers=set(CAST),
    )[1]["content"]
    assert "Iara [speech]" not in prompt
    assert whisper.content not in prompt
    assert "Iara" in prompt.split("CAST (visible appearance only):", 1)[1].split("\n\n", 1)[0]
