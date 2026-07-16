"""Blind prose renderer hardening: spoken words never reach the prose prompt.

The renderer measurably re-voiced dialogue in narration despite an explicit
instruction not to. The fix is structural (selection of inputs): speech record
content and ``audible_speech`` event content are replaced by content-free
markers/staging lines before the prompt is built, so re-voicing is impossible
by construction. These tests pin that boundary at the unit level (no network).
"""

from __future__ import annotations

from typing import Any

from src.agents.prose import build_prose_messages
from src.models import Character, CharacterBody, CharacterMind, Scene, TurnRecord


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Alice"), "C2": _char("Bruno"), "C3": _char("Vitor")}
CONTROLLED_ID = "C1"

SCENE = Scene(
    location="Embaixada",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _record(
    speaker: str,
    content: str,
    content_type: str,
    audience: list[str] | None = None,
    turn_number: int = 1,
) -> TurnRecord:
    return TurnRecord(
        turn_number=turn_number,
        speaker=speaker,
        content=content,
        content_type=content_type,
        scene_snapshot=SCENE,
        audience=audience,
    )


def _prompt(history: list[TurnRecord], events: list[dict[str, Any]]) -> str:
    messages = build_prose_messages(SCENE, CHARACTERS, CONTROLLED_ID, history, events)
    return "\n".join(message["content"] for message in messages)


class TestSpeechContentNeverReachesProse:
    def test_public_speech_content_replaced_by_marker(self) -> None:
        history = [_record("C2", "O código do cofre é 7-4-1-9.", "speech")]
        prompt = _prompt(history, [])
        assert "7-4-1-9" not in prompt
        assert "código do cofre" not in prompt
        assert "Bruno fala" in prompt

    def test_whispered_speech_content_replaced_by_scoped_marker(self) -> None:
        history = [_record("C2", "A senha secreta é rosa-espelho.", "speech", audience=["C3"])]
        prompt = _prompt(history, [])
        assert "rosa-espelho" not in prompt
        assert "senha secreta" not in prompt
        assert "Bruno fala baixo (só Vitor percebem)" in prompt

    def test_player_speech_marker_uses_controlled_character_name(self) -> None:
        history = [_record("Player", "Eu confesso tudo agora.", "speech")]
        prompt = _prompt(history, [])
        assert "confesso" not in prompt
        assert "Alice fala" in prompt

    def test_previous_turn_speech_also_withheld(self) -> None:
        history = [
            _record("C2", "Frase antiga que não pode reaparecer.", "speech", turn_number=1),
            _record("Narrator", "A sala esfria.", "narration", turn_number=2),
        ]
        prompt = _prompt(history, [])
        assert "Frase antiga" not in prompt


class TestAudibleSpeechEventsAreStaged:
    def test_audible_speech_content_replaced_by_staging_line(self) -> None:
        events = [
            {
                "event_kind": "audible_speech",
                "subject_id": "C1",
                "content": "Alice revela que o cofre abre com 7419.",
                "witness_ids": ["C2", "C3"],
            }
        ]
        prompt = _prompt([], events)
        assert "7419" not in prompt
        assert "cofre" not in prompt
        assert "Alice diz algo audível para Bruno, Vitor" in prompt

    def test_audible_speech_without_witnesses_stages_os_presentes(self) -> None:
        events = [
            {
                "event_kind": "audible_speech",
                "subject_id": "C2",
                "content": "Bruno grita o segredo.",
                "witness_ids": [],
            }
        ]
        prompt = _prompt([], events)
        assert "segredo" not in prompt
        assert "Bruno diz algo audível para os presentes" in prompt

    def test_audible_speech_player_subject_resolves_to_controlled_name(self) -> None:
        events = [
            {
                "event_kind": "audible_speech",
                "subject_id": "Player",
                "content": "confissão em voz alta",
                "witness_ids": ["C2"],
            }
        ]
        prompt = _prompt([], events)
        assert "confissão" not in prompt
        assert "Alice diz algo audível para Bruno" in prompt

    def test_non_speech_events_keep_content(self) -> None:
        events = [
            {
                "event_kind": "observation",
                "subject_id": "C2",
                "content": "Bruno derruba a taça de vinho no tapete.",
                "witness_ids": ["C1"],
            },
            {
                "event_kind": "physical_outcome",
                "subject_id": "C3",
                "content": "A porta do compartimento tranca com um estalo.",
                "witness_ids": [],
            },
        ]
        prompt = _prompt([], events)
        assert "Bruno derruba a taça de vinho no tapete." in prompt
        assert "A porta do compartimento tranca com um estalo." in prompt


class TestNonSpeechRecordsKeepContent:
    def test_narration_records_keep_full_content(self) -> None:
        history = [_record("Narrator", "A chuva bate nas janelas do salão.", "narration")]
        prompt = _prompt(history, [])
        assert "A chuva bate nas janelas do salão." in prompt

    def test_public_action_records_keep_full_content(self) -> None:
        history = [_record("C3", "Vitor guarda o envelope no bolso interno.", "action")]
        prompt = _prompt(history, [])
        assert "Vitor guarda o envelope no bolso interno." in prompt

    def test_thoughts_never_enter_the_reader_transcript(self) -> None:
        history = [_record("C2", "Preciso esconder o mapa.", "thought")]
        prompt = _prompt(history, [])
        assert "esconder o mapa" not in prompt
