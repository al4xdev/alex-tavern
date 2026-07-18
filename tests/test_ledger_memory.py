"""Task 39 increment 1: durable ledger memory (deterministic, continuous)."""

from __future__ import annotations

from src.agents.character import _build_user_prompt, _ledger_memory_text
from src.agents.perspective import MAX_RECENT_MEMORY, capture_memory
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    PersonView,
    Scene,
    TurnRecord,
    deepcopy_scene,
    dict_to_perspective,
    perspective_to_dict,
)

SCENE = Scene(
    location="Salao", time_of_day="Noite", present_characters=["C1", "C2", "C3"], physical_facts={}
)


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta"), "C3": _char("Bento")}


def _rec(turn: int, speaker: str, content: str, ctype: str = "speech") -> TurnRecord:
    return TurnRecord(turn, speaker, content, ctype, deepcopy_scene(SCENE))


def _perspective(**over) -> CharacterPerspective:  # noqa: ANN003
    fields = dict(initialized_turn=0, processed_through_turn=0, people={})
    fields.update(over)
    return CharacterPerspective(**fields)


class TestCaptureMemory:
    def test_folds_visible_speech_projected(self) -> None:
        # Viewer C3 has not learned C2's name -> the digest uses the reference.
        p = _perspective(people={"C2": PersonView(known_name=None, reference="a estalajadeira", source_turn=0)})
        history = [_rec(1, "C2", "Marta serve o vinho para Rui.")]
        capture_memory(p, history, "C3", CHARACTERS, controlled_id="C1")
        assert len(p.recent_memory) == 1
        assert "a estalajadeira" in p.recent_memory[0]
        assert "Marta" not in p.recent_memory[0]
        assert p.memory_through_turn == 1

    def test_captures_own_and_others_actions(self) -> None:
        p = _perspective()
        history = [
            _rec(1, "C3", "Fico de olho na porta.", "speech"),
            _rec(2, "C2", "caminhar ate a janela", "action"),
        ]
        capture_memory(p, history, "C3", CHARACTERS, controlled_id="C1")
        assert len(p.recent_memory) == 2
        assert "disse" in p.recent_memory[0] and "fez" in p.recent_memory[1]

    def test_cursor_prevents_double_capture(self) -> None:
        p = _perspective()
        history = [_rec(1, "C2", "Boa noite a todos.")]
        capture_memory(p, history, "C3", CHARACTERS, controlled_id="C1")
        capture_memory(p, history, "C3", CHARACTERS, controlled_id="C1")  # no new records
        assert len(p.recent_memory) == 1

    def test_whispered_record_not_captured_by_outsider(self) -> None:
        p = _perspective()
        whisper = _rec(1, "C2", "senha secreta", "speech")
        whisper.audience = ["C1", "C2"]  # C3 is outside
        capture_memory(p, [whisper], "C3", CHARACTERS, controlled_id="C1")
        assert p.recent_memory == []

    def test_bounded_to_max(self) -> None:
        p = _perspective()
        history = [_rec(t, "C2", f"Fala numero {t} bem longa aqui.") for t in range(1, 40)]
        capture_memory(p, history, "C3", CHARACTERS, controlled_id="C1")
        assert len(p.recent_memory) == MAX_RECENT_MEMORY
        assert "numero 39" in p.recent_memory[-1]  # newest kept


class TestPromptWiring:
    def test_ledger_memory_preferred_over_notes(self) -> None:
        p = _perspective(recent_memory=["T1 Marta disse: oi"])
        prompt = _build_user_prompt(
            "ctx", "hist", "calmo", notes="nota antiga", ledger_memory=_ledger_memory_text(p)
        )
        assert "T1 Marta disse: oi" in prompt
        assert "nota antiga" not in prompt

    def test_falls_back_to_notes_when_memory_empty(self) -> None:
        p = _perspective()
        prompt = _build_user_prompt(
            "ctx", "hist", "calmo", notes="lembro de algo", ledger_memory=_ledger_memory_text(p)
        )
        assert "lembro de algo" in prompt

    def test_summary_leads_recent_follows(self) -> None:
        p = _perspective(memory_summary="Resumo do que vivi.", recent_memory=["T5 Bento fez: saiu"])
        text = _ledger_memory_text(p)
        assert text.index("Resumo") < text.index("T5 Bento")


class TestPersistence:
    def test_roundtrip_preserves_memory(self) -> None:
        p = _perspective(
            recent_memory=["T1 x disse: y"], memory_summary="resumo", memory_through_turn=3
        )
        restored = dict_to_perspective(perspective_to_dict(p))
        assert restored.recent_memory == ["T1 x disse: y"]
        assert restored.memory_summary == "resumo"
        assert restored.memory_through_turn == 3

    def test_legacy_perspective_without_memory_loads_empty(self) -> None:
        data = {"initialized_turn": 0, "processed_through_turn": 2, "people": {}}
        restored = dict_to_perspective(data)
        assert restored.recent_memory == []
        assert restored.memory_summary == ""
        assert restored.memory_through_turn == 0
