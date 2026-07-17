"""Unit tests for tools/render_transcript.py rendering rules."""

from __future__ import annotations

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
)
from tools.render_transcript import render_session


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


def _game(history: list[TurnRecord]) -> GameState:
    return GameState(
        session_id="s1",
        characters={"C1": _char("Alice"), "C2": _char("Bruno")},
        player=Player(controlled_character_id="C1"),
        scene=Scene(
            location="Sala",
            time_of_day="Dia",
            present_characters=["C1", "C2"],
            physical_facts={},
        ),
        history=history,
    )


def _speech(audience: list[str] | None) -> TurnRecord:
    return TurnRecord(
        turn_number=1,
        speaker="C2",
        content="Escuta isto.",
        content_type="speech",
        scene_snapshot=Scene(
            location="Sala", time_of_day="Dia", present_characters=["C1", "C2"], physical_facts={}
        ),
        audience=audience,
    )


class TestAudienceMarkers:
    def test_public_speech_has_no_whisper_marker(self) -> None:
        rendered = render_session(_game([_speech(None)]))
        assert "**Bruno:** Escuta isto." in rendered
        assert "sussurrado" not in rendered

    def test_nonempty_audience_lists_the_hearers(self) -> None:
        rendered = render_session(_game([_speech(["C1"])]))
        assert "**Bruno (sussurrado — só Alice percebe):** Escuta isto." in rendered

    def test_empty_audience_renders_nobody_perceives_marker(self) -> None:
        rendered = render_session(_game([_speech([])]))
        assert "**Bruno (ninguém além dele percebe):** Escuta isto." in rendered
        assert "só  percebem" not in rendered


def test_zone_scoped_speech_renders_without_whisper_wording() -> None:
    from src.models import (
        Character,
        CharacterBody,
        CharacterMind,
        GameState,
        Player,
        Scene,
        TurnRecord,
    )
    from tools.render_transcript import render_session

    scene = Scene(
        location="x", time_of_day="y", present_characters=["C1", "C2", "Player"],
        physical_facts={},
    )
    chars = {
        "C1": Character(
            mind=CharacterMind(name="Alice", personality="p", knowledge=[], current_mood="m"),
            body=CharacterBody(name="Alice", physical_description="d", outfit="o"),
        ),
        "C2": Character(
            mind=CharacterMind(name="Bruno", personality="p", knowledge=[], current_mood="m"),
            body=CharacterBody(name="Bruno", physical_description="d", outfit="o"),
        ),
    }
    game = GameState(
        session_id="t", characters=chars, player=Player(controlled_character_id="C1"),
        scene=scene,
    )
    game.history.append(
        TurnRecord(
            turn_number=1, speaker="C1", content="Falei no salao.",
            content_type="speech", scene_snapshot=scene,
            audience=["C2"], audience_origin="zone",
        )
    )
    rendered = render_session(game)
    assert "(só Bruno percebe)" in rendered
    assert "sussurrado" not in rendered
