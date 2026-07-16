"""Task 29.2 increment 1: perspective ledger, projection, and runner wiring."""

from __future__ import annotations

import httpx
import pytest

from src.agents.perspective import (
    FALLBACK_REFERENCE,
    _validated_people,
    needs_identity_update,
    project_text_for_viewer,
    viewer_speaker_label,
)
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    PersonView,
    Scene,
    TurnRecord,
    deepcopy_scene,
)

CHARACTERS = {
    "C1": Character(
        mind=CharacterMind(name="Alex", personality="Direto.", knowledge=[], current_mood="neutro"),
        body=CharacterBody(name="Alex", physical_description="Alto.", outfit="Camisa."),
    ),
    "C2": Character(
        mind=CharacterMind(name="Sofia", personality="Viva.", knowledge=[], current_mood="alegre"),
        body=CharacterBody(name="Sofia", physical_description="Sorridente.", outfit="Vestido."),
    ),
    "C3": Character(
        mind=CharacterMind(
            name="Fernanda", personality="Tímida.", knowledge=[], current_mood="quieta"
        ),
        body=CharacterBody(name="Fernanda", physical_description="Ruiva.", outfit="Blusa."),
    ),
}

SCENE = Scene(
    location="Sala", time_of_day="Noite", present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _perspective(**people: PersonView) -> CharacterPerspective:
    return CharacterPerspective(initialized_turn=1, processed_through_turn=0, people=dict(people))


def _record(turn: int, speaker: str, content: str, kind: str = "speech", audience=None):
    return TurnRecord(
        turn_number=turn,
        speaker=speaker,
        content=content,
        content_type=kind,
        scene_snapshot=deepcopy_scene(SCENE),
        audience=audience,
    )


class TestViewerSpeakerLabel:
    def test_unknown_person_renders_as_reference(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name=None, reference="o homem na entrada", source_turn=1)
        )
        assert (
            viewer_speaker_label("C1", CHARACTERS, "C1", perspective) == "o homem na entrada"
        )

    def test_player_marker_resolves_through_controlled_view(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name=None, reference="o desconhecido", source_turn=1)
        )
        assert viewer_speaker_label("Player", CHARACTERS, "C1", perspective) == "o desconhecido"

    def test_known_name_wins_even_when_false(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name="Ricardo", reference="o homem", source_turn=2)
        )
        assert viewer_speaker_label("C1", CHARACTERS, "C1", perspective) == "Ricardo"

    def test_without_ledger_falls_back_to_canonical(self) -> None:
        assert viewer_speaker_label("C1", CHARACTERS, "C1", None) == "Alex"
        assert viewer_speaker_label("Narrator", CHARACTERS, "C1", None) == "Narrator"

    def test_subject_missing_from_ledger_falls_back_to_canonical(self) -> None:
        assert viewer_speaker_label("C3", CHARACTERS, "C1", _perspective()) == "Fernanda"


class TestProjection:
    def test_unknown_canonical_name_and_id_are_replaced(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name=None, reference="o homem de camisa aberta", source_turn=1)
        )
        text = "Você ouviu Alex falar algo. C1 parece esperar uma resposta."
        projected = project_text_for_viewer(text, CHARACTERS, perspective)
        assert "Alex" not in projected and "C1" not in projected
        assert projected.count("o homem de camisa aberta") == 2

    def test_known_person_keeps_their_name_and_id_is_still_replaced(self) -> None:
        perspective = _perspective(
            C3=PersonView(known_name="Fernanda", reference="a ruiva", source_turn=1)
        )
        projected = project_text_for_viewer("C3 sorri. Fernanda acena.", CHARACTERS, perspective)
        assert projected == "Fernanda sorri. Fernanda acena."

    def test_no_ledger_is_a_no_op(self) -> None:
        assert project_text_for_viewer("Alex fala.", CHARACTERS, None) == "Alex fala."


class TestValidatedPeople:
    def test_clamps_unknown_subjects_and_fills_reference(self) -> None:
        result = {
            "people": [
                {"subject_id": "C1", "known_name": "  ", "reference": "  "},
                {"subject_id": "HACK", "known_name": "x", "reference": "y"},
            ]
        }
        people = _validated_people(result, {"C1"}, turn_number=3)
        assert set(people) == {"C1"}
        assert people["C1"].known_name is None
        assert people["C1"].reference == FALLBACK_REFERENCE
        assert people["C1"].source_turn == 3

    def test_unchanged_view_keeps_original_provenance(self) -> None:
        previous = {"C1": PersonView(known_name=None, reference="o homem", source_turn=1)}
        result = {"people": [{"subject_id": "C1", "known_name": None, "reference": "o homem"}]}
        people = _validated_people(result, {"C1"}, turn_number=9, previous=previous)
        assert people["C1"].source_turn == 1


class TestNeedsIdentityUpdate:
    def test_no_strangers_short_circuits(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name="Alex", reference="o homem", source_turn=1)
        )
        history = [_record(2, "C1", "Oi de novo.")]
        assert needs_identity_update(history, "C2", perspective) is False

    def test_new_visible_speech_with_strangers_triggers(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name=None, reference="o homem", source_turn=1)
        )
        history = [_record(2, "Player", "Oi! Eu sou o Alex.")]
        assert needs_identity_update(history, "C2", perspective) is True

    def test_whisper_outside_audience_is_not_visible(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name=None, reference="o homem", source_turn=1)
        )
        history = [_record(2, "Player", "Sou o Alex.", audience=["C3"])]
        assert needs_identity_update(history, "C2", perspective) is False

    def test_already_processed_records_do_not_retrigger(self) -> None:
        perspective = _perspective(
            C1=PersonView(known_name=None, reference="o homem", source_turn=1)
        )
        perspective.processed_through_turn = 2
        history = [_record(2, "Player", "Sou o Alex.")]
        assert needs_identity_update(history, "C2", perspective) is False


class TestRunnerWiring:
    @pytest.mark.asyncio
    async def test_first_character_call_initializes_projects_and_snapshots(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        init_calls: list[str] = []

        async def fake_init(client, viewer_id, characters, controlled_id, config, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            init_calls.append(viewer_id)
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
                people={
                    "C1": PersonView(
                        known_name=None, reference="o recém-chegado", source_turn=1
                    ),
                    "C3": PersonView(known_name="Fernanda", reference="a ruiva", source_turn=1),
                },
            )

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "narration": "A sala vibra.",
                "next_speakers": ["C2"],
                "perception_events": [
                    {
                        "event_kind": "observation",
                        "subject_id": "C1",
                        "content": "Você vê Alex parado perto de C1 na entrada.",
                        "witness_ids": ["C2", "C3"],
                    }
                ],
                "scene_update": None,
                "mood_updates": None,
            }

        captured: dict[str, object] = {}

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["context"] = context
            captured["perspective"] = game.character_perspectives.get(character_id)
            return {"speech": "Oi!", "thought": None}

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            sid = runner.start_session(
                {
                    "characters": CHARACTERS,
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            result = await runner.player_turn(sid, speech="Oi, gente!")
            game = await runner.get_state(sid)

        assert init_calls == ["C2"]
        # Unknown canonical name AND raw ID were projected out of the context.
        assert "Alex" not in str(captured["context"])
        assert "C1" not in str(captured["context"])
        assert str(captured["context"]).count("o recém-chegado") == 2
        assert result["character_responses"][0]["speech"] == "Oi!"
        assert game is not None
        assert "C2" in game.character_perspectives
        assert game.history[-1].perspective_snapshot["C2"]["people"]["C1"]["known_name"] is None

    @pytest.mark.asyncio
    async def test_undo_restores_previous_perspectives(self, monkeypatch) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, config, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
                people={
                    "C1": PersonView(known_name=None, reference="o homem", source_turn=1),
                },
            )

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "narration": "Segue a noite.",
                "next_speakers": ["C2"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {"speech": "Certo.", "thought": None}

        async def fake_update(client, viewer_id, perspective, history, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202, ARG001
            perspective.processed_through_turn = max(
                [perspective.processed_through_turn, *(r.turn_number for r in history)]
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)
        monkeypatch.setattr(runner_mod, "update_identity", fake_update)

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            sid = runner.start_session(
                {
                    "characters": CHARACTERS,
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)

            await runner.player_turn(sid, speech="Primeiro turno.")
            game = await runner.get_state(sid)
            assert game is not None and "C2" in game.character_perspectives

            # Simulate a name learned on turn 2, then undo turn 2 entirely.
            await runner.player_turn(sid, speech="Eu sou o Alex!")
            game = await runner.get_state(sid)
            assert game is not None
            game.character_perspectives["C2"].people["C1"] = PersonView(
                known_name="Alex", reference="o homem", source_turn=2
            )

            await runner.undo_turn(sid)
            game = await runner.get_state(sid)

        assert game is not None
        restored = game.character_perspectives["C2"].people["C1"]
        assert restored.known_name is None
        assert restored.reference == "o homem"
