"""Task 29.2 increment 2: zone graph, event clamping, and viewer rendering."""

from __future__ import annotations

import pytest

from src.agents.character import _leaked_secret_tokens
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    PersonView,
    Scene,
    TurnRecord,
)
from src.perception import (
    MAX_EVENTS_PER_TURN,
    can_perceive,
    describe_zones_for_narrator,
    eligible_witnesses,
    render_events_for_viewer,
    validate_perception_events,
)


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Alice"), "C2": _char("Bruno"), "C3": _char("Vitor")}

# salao hears varanda; varanda hears salao; compartimento is acoustically isolated.
ZONED_SCENE = Scene(
    location="Embaixada",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
    zones={"salao": ["varanda"], "varanda": ["salao"], "compartimento": []},
    positions={"C1": "salao", "C2": "varanda", "C3": "compartimento"},
)
FLAT_SCENE = Scene(
    location="Sala",
    time_of_day="Dia",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


class TestZonePerception:
    def test_without_zones_everyone_perceives(self) -> None:
        assert can_perceive(FLAT_SCENE, "C3", "C1") is True
        assert eligible_witnesses(FLAT_SCENE, CHARACTERS, "C1") == {"C2", "C3"}

    def test_same_zone_and_audible_edge_perceive(self) -> None:
        assert can_perceive(ZONED_SCENE, "C2", "C1") is True  # varanda hears salao
        assert can_perceive(ZONED_SCENE, "C1", "C2") is True  # salao hears varanda

    def test_isolated_zone_cannot_perceive_or_be_perceived(self) -> None:
        assert can_perceive(ZONED_SCENE, "C3", "C1") is False
        assert can_perceive(ZONED_SCENE, "C1", "C3") is False
        assert eligible_witnesses(ZONED_SCENE, CHARACTERS, "C1") == {"C2"}

    def test_unplaced_character_perceives_everything(self) -> None:
        scene = Scene(
            location="x",
            time_of_day="y",
            present_characters=["C1", "C2", "C3", "Player"],
            physical_facts={},
            zones={"salao": [], "compartimento": []},
            positions={"C1": "salao"},
        )
        assert can_perceive(scene, "C2", "C1") is True


class TestValidateEvents:
    def test_witnesses_are_clamped_to_the_zone_eligible_set(self) -> None:
        events = validate_perception_events(
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C1",
                    "content": "Alice fala alto no salao.",
                    "witness_ids": ["C2", "C3", "C1", "GHOST"],
                }
            ],
            ZONED_SCENE,
            CHARACTERS,
        )
        assert events[0]["witness_ids"] == ["C2"]

    def test_model_may_narrow_but_never_widen(self) -> None:
        events = validate_perception_events(
            [
                {
                    "event_kind": "observation",
                    "subject_id": "C1",
                    "content": "Um gesto discreto.",
                    "witness_ids": [],
                }
            ],
            FLAT_SCENE,
            CHARACTERS,
        )
        assert events[0]["witness_ids"] == []

    def test_malformed_events_are_dropped(self) -> None:
        events = validate_perception_events(
            [
                {"event_kind": "telepathy", "subject_id": "C1", "content": "x", "witness_ids": []},
                {"event_kind": "observation", "subject_id": "GHOST", "content": "x", "witness_ids": []},
                {"event_kind": "observation", "subject_id": "C1", "content": "  ", "witness_ids": []},
                "not-a-dict",
                {"event_kind": "observation", "subject_id": "C1", "content": "ok", "witness_ids": ["C2"]},
            ],
            FLAT_SCENE,
            CHARACTERS,
        )
        assert len(events) == 1 and events[0]["content"] == "ok"

    def test_narrator_environmental_event_reaches_all_present(self) -> None:
        events = validate_perception_events(
            [
                {
                    "event_kind": "scene_change",
                    "subject_id": "Narrator",
                    "content": "A luz pisca.",
                    "witness_ids": ["C1", "C2", "C3"],
                }
            ],
            FLAT_SCENE,
            CHARACTERS,
        )
        assert events[0]["witness_ids"] == ["C1", "C2", "C3"]

    def test_event_count_is_capped(self) -> None:
        raw = [
            {"event_kind": "observation", "subject_id": "C1", "content": f"e{i}", "witness_ids": []}
            for i in range(10)
        ]
        assert len(validate_perception_events(raw, FLAT_SCENE, CHARACTERS)) == MAX_EVENTS_PER_TURN

    def test_non_list_returns_empty(self) -> None:
        assert validate_perception_events(None, FLAT_SCENE, CHARACTERS) == []


class TestRenderForViewer:
    def test_only_witnessed_events_render_and_names_are_projected(self) -> None:
        perspective = CharacterPerspective(
            initialized_turn=1,
            processed_through_turn=1,
            people={"C1": PersonView(known_name=None, reference="a diplomata", source_turn=1)},
        )
        events = [
            {
                "event_kind": "audible_speech",
                "subject_id": "C1",
                "content": "Alice cumprimenta a sala.",
                "witness_ids": ["C2"],
            },
            {
                "event_kind": "observation",
                "subject_id": "C1",
                "content": "Alice ajeita o casaco.",
                "witness_ids": ["C3"],
            },
        ]
        rendered = render_events_for_viewer(events, "C2", CHARACTERS, perspective)
        assert rendered == "a diplomata cumprimenta a sala."
        assert "ajeita o casaco" not in rendered

    def test_subject_always_perceives_their_own_event(self) -> None:
        events = [
            {
                "event_kind": "physical_outcome",
                "subject_id": "C2",
                "content": "Bruno derruba o copo.",
                "witness_ids": [],
            }
        ]
        assert "derruba o copo" in render_events_for_viewer(events, "C2", CHARACTERS, None)


class TestNarratorZoneBriefing:
    def test_flat_scene_produces_no_lines(self) -> None:
        assert describe_zones_for_narrator(FLAT_SCENE, CHARACTERS) == []

    def test_zoned_scene_lists_occupants_and_audibility(self) -> None:
        lines = "\n".join(describe_zones_for_narrator(ZONED_SCENE, CHARACTERS))
        assert "salao: hears varanda | occupants: Alice" in lines
        assert "compartimento: hears nothing outside itself | occupants: Vitor" in lines


class TestWhisperOutputGuardZoneExposure:
    """Regression: the character output guard must compute public exposure from
    the zone-eligible witnesses of the speaker, not everyone present.

    Setup mirrors ZONED_SCENE: the speaker (C2, varanda) and the secret's
    confidant (C1, salao) mutually perceive each other, while C3 sits in the
    acoustically isolated compartimento. A secret whispered C1 -> C2 and then
    said aloud by C2 can physically reach only C1, who already knows it.
    """

    WHISPER = "O ponto de encontro é a ponte GIRASSOL, pilar 4127."
    REPLY = "Confirmo: ponte GIRASSOL, pilar 4127, ao anoitecer."

    @staticmethod
    def _history(scene: Scene) -> list[TurnRecord]:
        return [
            TurnRecord(
                turn_number=1,
                speaker="C1",
                content=TestWhisperOutputGuardZoneExposure.WHISPER,
                content_type="speech",
                scene_snapshot=scene,
                audience=["C2"],
            )
        ]

    def test_zoned_public_reply_heard_only_by_the_confidant_is_not_flagged(self) -> None:
        leaked = _leaked_secret_tokens(
            self.REPLY,
            self._history(ZONED_SCENE),
            CHARACTERS,
            controlled_id="C1",
            character_id="C2",
            reply_audience=None,
            scene=ZONED_SCENE,
        )
        assert leaked == set()

    def test_flat_scene_public_reply_still_flags_the_secret(self) -> None:
        leaked = _leaked_secret_tokens(
            self.REPLY,
            self._history(FLAT_SCENE),
            CHARACTERS,
            controlled_id="C1",
            character_id="C2",
            reply_audience=None,
            scene=FLAT_SCENE,
        )
        assert {"girassol", "4127"} <= leaked

    def test_zoned_whispered_reply_keeps_existing_audience_semantics(self) -> None:
        leaked = _leaked_secret_tokens(
            self.REPLY,
            self._history(ZONED_SCENE),
            CHARACTERS,
            controlled_id="C1",
            character_id="C2",
            reply_audience=["C3"],
            scene=ZONED_SCENE,
        )
        assert {"girassol", "4127"} <= leaked


class TestZoneScopedRecords:
    @pytest.mark.asyncio
    async def test_public_speech_record_gets_zone_computed_audience(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.models import CharacterPerspective
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, config, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "narration": "O salao vibra.",
                "next_speakers": ["C2"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {"speech": "Ouvi voce.", "thought": None}

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        import httpx

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            scene = Scene(
                location="Embaixada",
                time_of_day="Noite",
                present_characters=["C1", "C2", "C3", "Player"],
                physical_facts={},
                zones={"salao": [], "compartimento": []},
                positions={"C1": "salao", "C2": "salao", "C3": "compartimento"},
            )
            sid = runner.start_session(
                {"characters": dict(CHARACTERS), "scene": scene, "controlled_character_id": "C1"}
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            await runner.player_turn(sid, speech="Declaro aberta a sessao!")
            game = await runner.get_state(sid)

        assert game is not None
        speech_records = [r for r in game.history if r.content_type == "speech"]
        # Player speech in the salao: C2 (same zone) perceives, C3 (isolated) does not.
        assert speech_records[0].speaker == "Player"
        assert speech_records[0].audience == ["C2"]
        # C2's reply is likewise zone-scoped away from C3.
        assert speech_records[1].speaker == "C2"
        assert speech_records[1].audience == ["C1"]
        from src.models import record_visible_to

        assert record_visible_to(speech_records[0], "C3") is False


class TestEmptyPerceptionVoid:
    @pytest.mark.asyncio
    async def test_speaker_with_no_witnessed_events_gets_the_void_statement(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, config, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "narration": "O salao segue.",
                "next_speakers": ["C3"],
                "perception_events": [
                    {
                        "event_kind": "audible_speech",
                        "subject_id": "C1",
                        "content": "Alice fala no salao.",
                        "witness_ids": ["C2"],
                    }
                ],
                "scene_update": None,
                "mood_updates": None,
            }

        captured: dict[str, str] = {}

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            captured["context"] = context
            return {"speech": None, "thought": "Sigo com meu arquivo."}

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        import httpx

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            scene = Scene(
                location="Embaixada",
                time_of_day="Tarde",
                present_characters=["C1", "C2", "C3", "Player"],
                physical_facts={},
                zones={"salao": [], "compartimento": []},
                positions={"C1": "salao", "C2": "salao", "C3": "compartimento"},
            )
            sid = runner.start_session(
                {"characters": dict(CHARACTERS), "scene": scene, "controlled_character_id": "C1"}
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            await runner.player_turn(sid, speech="Bom dia a todos do salao!")

        assert "Nothing new reaches your senses" in captured["context"]
        assert "Alice fala" not in captured["context"]
