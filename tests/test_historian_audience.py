"""Task 35: the private Historian honors the perception boundary."""

from __future__ import annotations

from src.agents.summarizer import build_private_memory_messages
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    Scene,
    TurnRecord,
    deepcopy_scene,
)


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Alice"), "C2": _char("Watson"), "C3": _char("Dracula")}
SCENE = Scene(
    location="Salao",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _record(turn: int, speaker: str, content: str, kind: str = "speech", audience=None):
    return TurnRecord(
        turn_number=turn,
        speaker=speaker,
        content=content,
        content_type=kind,
        scene_snapshot=deepcopy_scene(SCENE),
        audience=audience,
    )


def _prompt_for(character_id: str, evicted: list[TurnRecord]) -> str:
    messages = build_private_memory_messages(
        character_id,
        CHARACTERS[character_id],
        "C1",
        "",
        evicted,
        CHARACTERS,
    )
    return messages[-1]["content"]


EVICTED = [
    _record(1, "Player", "O codigo do cofre e LUMEN-17.", audience=["C3"]),
    _record(1, "C3", "Entendido: LUMEN-17.", audience=["C3"]),
    _record(2, "C2", "O relatorio publico esta pronto."),
    _record(3, "Player", "Obrigado a todos pelo trabalho."),
]


class TestPrivateHistorianAudience:
    def test_outsider_note_prompt_never_sees_the_whisper(self) -> None:
        prompt = _prompt_for("C2", EVICTED)
        assert "LUMEN-17" not in prompt
        assert "relatorio publico" in prompt
        assert "Obrigado a todos" in prompt

    def test_confidant_keeps_the_whisper(self) -> None:
        prompt = _prompt_for("C3", EVICTED)
        assert prompt.count("LUMEN-17") == 2

    def test_whisperer_keeps_their_own_player_records(self) -> None:
        # "Player" records belong to the controlled character (C1) even when
        # the audience list does not repeat the speaker.
        prompt = _prompt_for("C1", EVICTED)
        assert "O codigo do cofre e LUMEN-17." in prompt

    def test_zone_scoped_record_respects_the_same_boundary(self) -> None:
        # Increment 2 computes effective audiences from zones; an empty
        # audience means nobody else perceived it.
        evicted = [
            _record(1, "C3", "Falo sozinho na sala isolada.", audience=[]),
            _record(2, "C2", "Conversa normal no salao."),
        ]
        assert "sala isolada" not in _prompt_for("C2", evicted)
        assert "sala isolada" in _prompt_for("C3", evicted)

    def test_foreign_thoughts_still_excluded(self) -> None:
        evicted = [_record(1, "C3", "Pensamento secreto.", kind="thought")]
        assert "Pensamento secreto" not in _prompt_for("C2", evicted)
        assert "Pensamento secreto" in _prompt_for("C3", evicted)

    def test_narration_never_enters_a_private_note_prompt(self) -> None:
        evicted = [
            _record(1, "Narrator", "O narrador reconta o sussurro: LUMEN-17.", kind="narration"),
            _record(2, "C2", "Fala publica normal."),
        ]
        prompt = _prompt_for("C2", evicted)
        assert "LUMEN-17" not in prompt
        assert "Fala publica normal" in prompt

    def test_world_directives_never_enter_a_private_note_prompt(self) -> None:
        messages = build_private_memory_messages(
            "C2",
            CHARACTERS["C2"],
            "C1",
            "",
            [_record(1, "C2", "Fala publica.")],
            CHARACTERS,
            narrator_directives="WT-11: the silver instrument LUMEN-17 opens the cities.",
        )
        joined = "\n".join(m["content"] for m in messages)
        assert "LUMEN-17" not in joined
