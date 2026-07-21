"""Task 43, Phase 3: the feedback loop wired into the runner (behind a flag).

Proves the end-to-end control flow with the appraisal call mocked: with the loop
enabled, a per-turn relationship delta is integrated into the disposition substrate
and, sustained over turns, flips the dyadic band; with the loop disabled (default),
the appraiser is never called and the substrate stays at its seeded set-point.
"""

from __future__ import annotations

import httpx
import pytest

from src.disposition import AXIS_TRUST, RelationshipDelta, project_band
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    Scene,
    deepcopy_scene,
)
from src.store.sessions import delete_session


async def _fake_prose() -> str:
    return "Narracao de teste."


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(
            name=name,
            personality="p",
            knowledge=[],
            current_mood="m",
        ),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta")}
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "Player"],
    physical_facts={},
)


async def _fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
    return {
        "narration": "Segue.",
        "next_speakers": ["Narrator"],
        "perception_events": [],
        "scene_update": None,
        "mood_updates": None,
    }


@pytest.mark.asyncio
async def test_enabled_feedback_moves_dyad_and_flips_band(monkeypatch) -> None:  # noqa: ANN001
    import src.runner as runner_mod
    from src.runner import Runner

    async def fake_appraise(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        # every turn, C1's trust toward C2 takes a strong hit (a sustained betrayal)
        return [RelationshipDelta("C1", "C2", AXIS_TRUST, "down", "strong", "traiu de novo")]

    monkeypatch.setattr(runner_mod, "appraise_relationships", fake_appraise)

    async with httpx.AsyncClient() as client:
        runner = Runner(client, {"disposition_feedback_enabled": True, "auto_event_enabled": False})
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", _fake_narrator)
        monkeypatch.setattr(
            runner, "_render_narration", lambda game, events, turn_number: _fake_prose()
        )
        try:
            for _ in range(4):
                await runner.player_turn(sid, speech="Sigo observando.")
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    assert game is not None
    trust = game.dispositions.per_dyad["C1"]["C2"][AXIS_TRUST]
    assert trust.value < 0.5  # sustained betrayal dragged trust below neutral
    assert project_band(AXIS_TRUST, trust.value) in {"desconfiado", "cauteloso"}


@pytest.mark.asyncio
async def test_disabled_feedback_never_appraises_and_stays_seeded(monkeypatch) -> None:  # noqa: ANN001
    import src.runner as runner_mod
    from src.runner import Runner

    calls = {"appraise": 0}

    async def fake_appraise(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        calls["appraise"] += 1
        return [RelationshipDelta("C1", "C2", AXIS_TRUST, "down", "strong", "x")]

    monkeypatch.setattr(runner_mod, "appraise_relationships", fake_appraise)

    async with httpx.AsyncClient() as client:
        runner = Runner(client, {"auto_event_enabled": False})  # feedback flag absent -> OFF
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", _fake_narrator)
        monkeypatch.setattr(
            runner, "_render_narration", lambda game, events, turn_number: _fake_prose()
        )
        try:
            for _ in range(3):
                await runner.player_turn(sid, speech="Sigo observando.")
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    assert calls == {"appraise": 0}
    assert game is not None
    assert game.dispositions.per_dyad == {}  # no dyad materialized; substrate static


@pytest.mark.asyncio
async def test_undo_restores_pre_turn_dispositions(monkeypatch) -> None:  # noqa: ANN001
    """A feedback mutation belongs to its turn and must disappear with that turn."""
    import src.runner as runner_mod
    from src.runner import Runner

    async def fake_appraise(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        return [RelationshipDelta("C1", "C2", AXIS_TRUST, "down", "strong", "traiu")]

    monkeypatch.setattr(runner_mod, "appraise_relationships", fake_appraise)

    async with httpx.AsyncClient() as client:
        runner = Runner(client, {"disposition_feedback_enabled": True, "auto_event_enabled": False})
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", _fake_narrator)
        monkeypatch.setattr(
            runner, "_render_narration", lambda game, events, turn_number: _fake_prose()
        )
        try:
            await runner.player_turn(sid, speech="Observo a traicao.")
            changed = await runner.get_state(sid)
            assert changed is not None
            assert changed.dispositions.per_dyad["C1"]["C2"][AXIS_TRUST].value < 0.5

            result = await runner.undo_turn(sid)
            restored = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    assert result["undone"] is True
    assert restored is not None
    assert restored.history == []
    assert restored.dispositions.per_dyad == {}
