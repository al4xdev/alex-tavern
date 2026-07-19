"""Task 39 increment 1: durable ledger memory (deterministic, continuous)."""

from __future__ import annotations

import pytest

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
    fields = {"initialized_turn": 0, "processed_through_turn": 0, "people": {}}
    fields.update(over)
    return CharacterPerspective(**fields)


class TestCaptureMemory:
    def test_folds_visible_speech_projected(self) -> None:
        # Viewer C3 has not learned C2's name -> the digest uses the reference.
        p = _perspective(
            people={"C2": PersonView(known_name=None, reference="a estalajadeira", source_turn=0)}
        )
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
    def test_ledger_memory_renders_in_prompt(self) -> None:
        p = _perspective(recent_memory=["T1 Marta disse: oi"])
        prompt = _build_user_prompt("ctx", "hist", "calmo", ledger_memory=_ledger_memory_text(p))
        assert "T1 Marta disse: oi" in prompt

    def test_empty_ledger_renders_none_yet(self) -> None:
        p = _perspective()
        prompt = _build_user_prompt("ctx", "hist", "calmo", ledger_memory=_ledger_memory_text(p))
        assert "(none yet)" in prompt

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


class TestUndoPreservesMemory:
    """Undo restores the ledger memory exactly (per-record perspective snapshots)."""

    async def _session(self, monkeypatch):  # noqa: ANN001, ANN202
        import httpx

        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "next_speakers": ["C2"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "return_control": False,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "speech": f"Resposta no turno {turn_number}.",
                "thought": None,
                "action_intent": None,
            }

        async def fake_prose() -> str:
            return "Narracao."

        client = httpx.AsyncClient()
        runner = Runner(client, {"auto_event_enabled": False})
        session_scene = Scene(
            location="Salao",
            time_of_day="Noite",
            present_characters=["C1", "C2", "C3", "Player"],
            physical_facts={},
        )
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": session_scene,
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(runner, "_call_character", fake_character)
        monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: fake_prose())
        return runner, sid, client

    async def test_undo_rolls_ledger_memory_back(self, monkeypatch) -> None:  # noqa: ANN001
        from src.store.sessions import delete_session

        runner, sid, client = await self._session(monkeypatch)
        try:
            await runner.player_turn(sid, speech="Primeira fala.")
            game1 = await runner.get_state(sid)
            memory_after_1 = list(game1.character_perspectives["C2"].recent_memory)
            cursor_after_1 = game1.character_perspectives["C2"].memory_through_turn
            assert memory_after_1  # turn 1 speech was captured

            await runner.player_turn(sid, speech="Segunda fala.")
            game2 = await runner.get_state(sid)
            assert len(game2.character_perspectives["C2"].recent_memory) > len(memory_after_1)

            await runner.undo_turn(sid)
            game3 = await runner.get_state(sid)
            perspective = game3.character_perspectives["C2"]
            # Memory AND cursor roll back exactly: the regenerated turn 2 will
            # be captured fresh instead of being skipped as already-seen.
            assert perspective.recent_memory == memory_after_1
            assert perspective.memory_through_turn == cursor_after_1
        finally:
            await delete_session(sid)
            await client.aclose()


class TestMemoryRevision:
    def test_trigger_threshold(self) -> None:
        from src.agents.perspective import MEMORY_REVISION_TRIGGER, needs_memory_revision

        assert not needs_memory_revision(
            _perspective(recent_memory=["x"] * (MEMORY_REVISION_TRIGGER - 1))
        )
        assert needs_memory_revision(_perspective(recent_memory=["x"] * MEMORY_REVISION_TRIGGER))

    def test_builder_carries_rules_and_lines(self) -> None:
        from src.agents.perspective import build_memory_revision_messages

        msgs = build_memory_revision_messages(
            "Marta", "resumo atual", ["T1 A disse: oi", "T2 B fez: saiu"]
        )
        system, user = msgs[0]["content"], msgs[1]["content"]
        assert "FIRST PERSON" in system
        assert "never merge" in system
        # Task 23 reconciliation: confided codes survive condensation verbatim
        # (the history-side code-anchor pinning is the other half and stays).
        assert "secrets/codes/numbers verbatim" in system
        assert "resumo atual" in user and "T2 B fez: saiu" in user

    @pytest.mark.asyncio
    async def test_revision_condenses_and_keeps_tail(self, monkeypatch) -> None:  # noqa: ANN001
        import src.agents.perspective as pmod
        from src.agents.perspective import MEMORY_KEEP_RAW_TAIL, revise_memory

        async def fake_chat(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {"memory_summary": "Lembro do essencial."}

        monkeypatch.setattr(pmod, "chat_completion_json", fake_chat)
        p = _perspective(recent_memory=[f"linha {i}" for i in range(22)])
        await revise_memory(None, "C2", p, CHARACTERS, {})
        assert p.memory_summary == "Lembro do essencial."
        assert p.recent_memory == [f"linha {i}" for i in range(22 - MEMORY_KEEP_RAW_TAIL, 22)]

    @pytest.mark.asyncio
    async def test_provider_failure_never_mutates_or_raises(self, monkeypatch) -> None:  # noqa: ANN001
        import src.agents.perspective as pmod
        from src.agents.perspective import revise_memory

        async def boom(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            raise ValueError("provider flake")

        monkeypatch.setattr(pmod, "chat_completion_json", boom)
        p = _perspective(recent_memory=[f"linha {i}" for i in range(22)], memory_summary="antigo")
        await revise_memory(None, "C2", p, CHARACTERS, {})  # must not raise
        assert p.memory_summary == "antigo"
        assert len(p.recent_memory) == 22
