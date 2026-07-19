"""Task 41: omniscient Director, thought guard, dynamic zones, canon-before-prose."""

from __future__ import annotations

import httpx
import pytest

from src.confidentiality import hidden_thought_tokens
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    Scene,
    TurnRecord,
    deepcopy_scene,
)
from src.store.sessions import delete_session


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Link"), "C2": _char("Marta"), "C3": _char("Bento")}
SCENE = Scene(
    location="Salao dos Quatro Arcos",
    time_of_day="Manha",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _rec(turn: int, speaker: str, content: str, ctype: str = "speech") -> TurnRecord:
    return TurnRecord(turn, speaker, content, ctype, deepcopy_scene(SCENE))


class TestHiddenThoughtTokens:
    def test_specific_thought_content_is_guarded(self) -> None:
        history = [_rec(1, "Player", "O codigo GIRASSOL-222 esta no cofre da torre.", "thought")]
        secret = hidden_thought_tokens(history, CHARACTERS, SCENE)
        assert "girassol" in secret or "girassol-222" in set(secret)

    def test_spoken_content_stops_being_secret(self) -> None:
        history = [
            _rec(1, "Player", "O codigo GIRASSOL-222 esta comigo.", "thought"),
            _rec(2, "Player", "O codigo e GIRASSOL-222, escutem."),  # said aloud
        ]
        secret = hidden_thought_tokens(history, CHARACTERS, SCENE)
        assert not any("girassol" in token for token in secret)

    def test_ordinary_feeling_thought_contributes_nothing(self) -> None:
        history = [
            _rec(1, "Player", "nossa estou atrasado, o evento ja deve ter comecado", "thought")
        ]
        assert hidden_thought_tokens(history, CHARACTERS, SCENE) == set()

    def test_no_thoughts_no_secrets(self) -> None:
        assert hidden_thought_tokens([_rec(1, "C2", "Bom dia.")], CHARACTERS, SCENE) == set()


class TestNarrateThoughtGuardAndZones:
    async def _narrate(self, monkeypatch, fake_response, history):  # noqa: ANN001, ANN202
        import src.agents.narrator as narrator_mod

        async def fake_chat(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            return fake_response

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_chat)
        return await narrator_mod.narrate(
            client=None,
            scene=SCENE,
            characters=CHARACTERS,
            player_controlled_id="C1",
            history=history,
            config={},
        )

    @pytest.mark.asyncio
    async def test_thought_only_token_redacted_from_events(self, monkeypatch) -> None:  # noqa: ANN001
        history = [_rec(1, "Player", "Escondi o mapa na CRIPTA-77 ontem.", "thought")]
        result = await self._narrate(
            monkeypatch,
            {
                "next_speakers": ["C2"],
                "perception_events": [
                    {
                        "event_kind": "observation",
                        "subject_id": "Narrator",
                        "content": "Marta comenta algo sobre a CRIPTA-77 do mapa.",
                        "witness_ids": ["C2", "C3"],
                    }
                ],
            },
            history,
        )
        content = result["perception_events"][0]["content"]
        assert "CRIPTA-77" not in content
        assert "[indistinct]" in content

    @pytest.mark.asyncio
    async def test_new_zone_names_accepted_and_sanitized(self, monkeypatch) -> None:  # noqa: ANN001
        result = await self._narrate(
            monkeypatch,
            {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "zone_moves": {
                    "C1": "  ruas da cidade  ",  # new zone, needs strip
                    "C2": "",  # blank -> dropped
                    "GHOST": "praca",  # unknown character -> dropped
                    "C3": "z" * 61,  # too long -> dropped
                },
            },
            [],
        )
        assert result["zone_moves"] == {"C1": "ruas da cidade"}


class TestRunnerZoneMaterialization:
    async def _turn(self, monkeypatch, narrator_response):  # noqa: ANN001, ANN202
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return narrator_response

        prose_scenes: list[dict] = []

        async def fake_prose(game, events, turn_number):  # noqa: ANN001, ANN202
            prose_scenes.append({"location": game.scene.location, "zones": dict(game.scene.zones)})
            return "Prosa."

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
            monkeypatch.setattr(runner, "_render_narration", fake_prose)
            try:
                await runner.player_turn(sid, action="Correr pela cidade")
                game = await runner.get_state(sid)
            finally:
                await delete_session(sid)
        return game, prose_scenes

    @pytest.mark.asyncio
    async def test_first_split_creates_stage_and_isolated_zone(self, monkeypatch) -> None:  # noqa: ANN001
        game, _ = await self._turn(
            monkeypatch,
            {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "zone_moves": {"C1": "ruas da cidade"},
                "return_control": False,
            },
        )
        assert game is not None
        # New zone materialized isolated; everyone else got the stage zone, so
        # the mover is genuinely imperceptible to them (unplaced would see all).
        assert game.scene.zones["ruas da cidade"] == []
        stage = "Salao dos Quatro Arcos"
        assert game.scene.zones[stage] == []
        assert game.scene.positions["C1"] == "ruas da cidade"
        assert game.scene.positions["C2"] == stage
        assert game.scene.positions["C3"] == stage

    @pytest.mark.asyncio
    async def test_prose_renders_with_reconciled_canon(self, monkeypatch) -> None:  # noqa: ANN001
        _, prose_scenes = await self._turn(
            monkeypatch,
            {
                "next_speakers": ["Narrator"],
                "perception_events": [
                    {
                        "event_kind": "observation",
                        "subject_id": "C1",
                        "content": "Link corre pelas ruas da cidade.",
                        "witness_ids": [],
                    }
                ],
                "scene_update": {"location": "Ruas da cidade"},
                "mood_updates": None,
                "zone_moves": {},
                "return_control": False,
            },
        )
        # The prose renderer saw the UPDATED location (Task 41 ordering fix),
        # not the stale one it used to invent reconciliations against.
        assert prose_scenes and prose_scenes[0]["location"] == "Ruas da cidade"


class TestPartialMoveLocationClamp:
    @pytest.mark.asyncio
    async def test_partial_split_keeps_stage_location(self, monkeypatch) -> None:  # noqa: ANN001
        # The model's common wart: zone split + a global location change that
        # would drag the whole cast to the mover's place in canon. Partial
        # movement keeps the stage location; zones express the split.
        game, _ = await TestRunnerZoneMaterialization()._turn(
            monkeypatch,
            {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": {"location": "Ruas da Cidade Alta", "time_of_day": "manha"},
                "mood_updates": None,
                "zone_moves": {"C1": "Ruas da Cidade Alta"},
                "return_control": False,
            },
        )
        assert game is not None
        assert game.scene.location == "Salao dos Quatro Arcos"  # stage unchanged
        assert game.scene.time_of_day == "manha"  # non-location updates still apply
        assert game.scene.positions["C1"] == "Ruas da Cidade Alta"
        assert game.scene.zones["Ruas da Cidade Alta"] == []
        assert game.scene.positions["C2"] == "Salao dos Quatro Arcos"
