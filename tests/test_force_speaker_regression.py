"""Task 28: force_speaker must be honored on every turn path, including skips."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    Scene,
    deepcopy_scene,
)
from src.store.sessions import delete_session

APP_JS = Path(__file__).resolve().parents[1] / "src" / "static" / "app.js"


async def _fake_prose() -> str:
    return "Narracao de teste."


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta"), "C3": _char("Bento")}
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


class TestFrontendBoundary:
    def test_skip_payload_reads_force_from_the_select_control(self) -> None:
        """The skip path must use the same source of truth as ordinary sends.

        Regression: a dead `state.forceSpeaker` read silently dropped the force
        on every skip turn ("forced Narrator, a character still answered").
        """
        source = APP_JS.read_text(encoding="utf-8")
        skip_block = source[source.index("skip: true") - 400 : source.index("skip: true") + 400]
        assert "forceSpeakerSelect ? forceSpeakerSelect.value : ''" in skip_block
        # The dead-state read must never come back as the payload source.
        assert "force_speaker: state.forceSpeaker" not in source


class TestBackendForceHonored:
    def _runner(self, monkeypatch, queue_from_director):  # noqa: ANN001, ANN202
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, config, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        calls: list[str] = []

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            # Simulate a model that IGNORES the constraint: the runner must
            # still enforce the manual force downstream.
            return {
                "next_speakers": list(queue_from_director),
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            calls.append(character_id)
            return {"speech": "Presente.", "thought": None, "action_intent": None}

        return Runner, fake_narrator, fake_character, calls

    @pytest.mark.asyncio
    async def test_skip_with_forced_narrator_produces_no_character_call(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        Runner, fake_narrator, fake_character, calls = self._runner(monkeypatch, ["C2", "C3"])
        async with httpx.AsyncClient() as client:
            runner = Runner(client, {"auto_event_enabled": False})
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            monkeypatch.setattr(
                runner, "_render_narration", lambda g, e, t: _fake_prose()
            )
            try:
                result = await runner.player_turn(sid, skip=True, force_speaker="Narrator")
            finally:
                await delete_session(sid)
        assert calls == []
        assert result["next_speakers"] == ["Narrator"]
        assert result["character_responses"] == []

    @pytest.mark.asyncio
    async def test_skip_with_forced_npc_calls_exactly_that_npc(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        Runner, fake_narrator, fake_character, calls = self._runner(monkeypatch, ["C3"])
        async with httpx.AsyncClient() as client:
            runner = Runner(client, {"auto_event_enabled": False})
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            monkeypatch.setattr(
                runner, "_render_narration", lambda g, e, t: _fake_prose()
            )
            try:
                result = await runner.player_turn(sid, skip=True, force_speaker="C2")
            finally:
                await delete_session(sid)
        assert calls == ["C2"]
        assert result["next_speakers"] == ["C2"]

    @pytest.mark.asyncio
    async def test_forced_controlled_character_never_generates_speech(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        Runner, fake_narrator, fake_character, calls = self._runner(monkeypatch, ["C2"])
        async with httpx.AsyncClient() as client:
            runner = Runner(client, {"auto_event_enabled": False})
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            monkeypatch.setattr(
                runner, "_render_narration", lambda g, e, t: _fake_prose()
            )
            try:
                result = await runner.player_turn(
                    sid, speech="Minha vez.", force_speaker="C1"
                )
            finally:
                await delete_session(sid)
        assert calls == []
        assert result["character_responses"] == []
