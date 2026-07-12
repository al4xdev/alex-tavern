"""Testes de integração — modelos, sessões e fluxo do Runner.

Requer servidor llama.cpp em http://localhost:8888 para testes de LLM.
Testes que não dependem do LLM são marcados como ``unit``.
"""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    deepcopy_scene,
    dict_to_game_state,
    game_state_to_dict,
)
from src.runner import Runner
from src.store.sessions import (
    SESSIONS_DIR,
    _get_lock,
    fork_session,
    generate_session_id,
    list_sessions,
    load_game,
    save_game,
)
from src.store.sessions import (
    delete_session as delete_session_async,
)

DEFAULT_CHARACTERS: dict[str, Character] = {
    "C1": Character(
        mind=CharacterMind(
            name="Thorn",
            personality=(
                "Stoic and loyal veteran warrior. Speaks little, acts with resolve.\n\n"
                "Thorn is a 40-year-old veteran warrior who served in the Iron Guard "
                "for two decades. Stoic, loyal to a fault, and deeply suspicious of magic. "
                "Speaks in short, direct sentences. Instinctively protects the weak. "
                "Carries guilt for failing to save his younger brother in an ambush years ago."
            ),
            knowledge=[
                "The Iron Guard was disbanded 3 years ago",
                "Old Mork's tavern is a common meeting place for mercenaries",
                "Lyra is a mage he met 2 weeks ago",
            ],
            current_mood="cautious",
        ),
        body=CharacterBody(
            name="Thorn",
            physical_description="Tall, muscular, scar on his chin, short grizzled hair",
            outfit="Reinforced leather armor, longsword at his waist",
        ),
    ),
    "C2": Character(
        mind=CharacterMind(
            name="Lyra",
            personality=(
                "Curious and impulsive elf mage. Talks too much when nervous.\n\n"
                "Lyra is a 120-year-old elf mage (very young for an elf). Curious to the point "
                "of getting into trouble. Impulsive — acts first, thinks later. When "
                "nervous, she talks endlessly. Has a sarcastic sense of humor. Treats magic "
                "as science, not mysticism. Left the mages' tower because she grew bored "
                "with theory."
            ),
            knowledge=[
                "The forest to the north is corrupted by black magic",
                "The medallion they found emits a weak arcane aura",
                "Thorn is a warrior she met 2 weeks ago",
            ],
            current_mood="curious",
        ),
        body=CharacterBody(
            name="Lyra",
            physical_description="Slender, pointed ears, violet eyes, long silver hair",
            outfit="Dark blue robe with embroidered runes, oak staff",
        ),
    ),
}

DEFAULT_SCENE = Scene(
    location="Old Mork's Tavern — main hall, dim lighting",
    time_of_day="night",
    present_characters=["C1", "C2", "Player"],
    physical_facts={
        "lighting": "dim candles",
        "crowd": "half a dozen drunk patrons",
        "weather_outside": "heavy rain",
        "door": "closed",
    },
)

# ── Helpers ───────────────────────────────────────────────────────────────


def _make_test_game(session_id: str | None = None) -> GameState:
    return GameState(
        session_id=session_id or generate_session_id(),
        characters=DEFAULT_CHARACTERS.copy(),
        player=Player(controlled_character_id="C1"),
        scene=copy.deepcopy(DEFAULT_SCENE),
    )


def delete_session(session_id: str) -> None:
    """Discard isolated test artifacts without exercising the async public operation."""
    for path in (
        SESSIONS_DIR / f"{session_id}.json",
        SESSIONS_DIR / f"{session_id}.debug.jsonl",
        *SESSIONS_DIR.glob(f"{session_id}.kb_*.json"),
    ):
        if path.exists():
            path.unlink()


# ═══════════════════════════════════════════════════════════════════════════
# Testes Unitários — Models
# ═══════════════════════════════════════════════════════════════════════════


class TestModels:
    """Testes das dataclasses em src/models.py."""

    def test_deepcopy_scene_independence(self) -> None:
        """deepcopy_scene retorna cópia independente."""
        s1 = Scene(
            location="taverna",
            time_of_day="noite",
            present_characters=["C1"],
            physical_facts={"door": "fechada", "weather": "chuva"},
        )
        s2 = deepcopy_scene(s1)
        s1.physical_facts["door"] = "aberta"
        assert s2.physical_facts["door"] == "fechada", "deepcopy falhou"

    def test_game_state_round_trip(self) -> None:
        """game_state_to_dict + dict_to_game_state deve ser idempotente."""
        original = _make_test_game()
        original.story_summary = "Thorn e Lyra se conheceram na taverna."
        original.character_notes = {"C1": "Desconfia de magia.", "C2": "Curiosa demais."}
        data = game_state_to_dict(original)
        restored = dict_to_game_state(data)
        assert restored.session_id == original.session_id
        assert len(restored.characters) == len(original.characters)
        assert restored.player.controlled_character_id == original.player.controlled_character_id
        assert restored.scene.location == original.scene.location
        assert restored.scene.physical_facts == original.scene.physical_facts
        assert restored.story_summary == original.story_summary
        assert restored.character_notes == original.character_notes

    def test_game_state_round_trip_with_history(self) -> None:
        """Round-trip preserva histórico e snapshots."""
        original = _make_test_game()
        original.history.append(
            TurnRecord(
                turn_number=1,
                speaker="Narrator",
                content="A taverna está silenciosa.",
                content_type="narration",
                scene_snapshot=deepcopy_scene(original.scene),
            )
        )
        data = game_state_to_dict(original)
        restored = dict_to_game_state(data)
        assert len(restored.history) == 1
        assert restored.history[0].content == "A taverna está silenciosa."
        snap = restored.history[0].scene_snapshot
        expected = "Old Mork's Tavern — main hall, dim lighting"
        assert snap.location == expected

    def test_legacy_history_migration_handles_empty_and_is_idempotent(self) -> None:
        from src.models import migrate_legacy_history

        assert migrate_legacy_history([]) == []
        scene = deepcopy_scene(DEFAULT_SCENE)
        legacy = [
            TurnRecord(1, "C2", "**Isso parece estranho.**\nEu concordo.", "speech", scene)
        ]
        migrated = migrate_legacy_history(legacy)
        assert [(record.content_type, record.content) for record in migrated] == [
            ("thought", "Isso parece estranho."),
            ("speech", "Eu concordo."),
        ]
        assert migrate_legacy_history(migrated) == migrated

    def test_legacy_history_migration_leaves_partial_markup_unchanged(self) -> None:
        from src.models import migrate_legacy_history

        scene = deepcopy_scene(DEFAULT_SCENE)
        partial = [TurnRecord(1, "C2", "**pensamento incompleto", "speech", scene)]
        assert migrate_legacy_history(partial) == partial


# ═══════════════════════════════════════════════════════════════════════════
# Testes Unitários — Sessions (Persistência)
# ═══════════════════════════════════════════════════════════════════════════


class TestSessions:
    """Testes da camada de persistência em src/store/sessions.py."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        # Garante que o diretório existe e está limpo
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def teardown_method(self) -> None:
        delete_session(self.sid)

    def test_save_and_load(self) -> None:
        """save_game seguido de load_game retorna estado equivalente."""
        original = _make_test_game(self.sid)
        save_game(original)
        loaded = load_game(self.sid)
        assert loaded is not None
        assert loaded.session_id == original.session_id
        assert loaded.player.controlled_character_id == original.player.controlled_character_id

    def test_save_idempotent(self) -> None:
        """Salvar duas vezes não corrompe o estado."""
        original = _make_test_game(self.sid)
        original.player.controlled_character_id = "Versão 1"
        save_game(original)
        original.player.controlled_character_id = "Versão 2"
        save_game(original)
        loaded = load_game(self.sid)
        assert loaded is not None
        assert loaded.player.controlled_character_id == "Versão 2"

    def test_load_nonexistent(self) -> None:
        """load_game de sessão inexistente retorna None."""
        loaded = load_game("nonexistent")
        assert loaded is None

    def test_history_persistence(self) -> None:
        """Histórico com múltiplos turnos sobrevive a save/load."""
        original = _make_test_game(self.sid)
        for i in range(3):
            original.history.append(
                TurnRecord(
                    turn_number=i + 1,
                    speaker="Narrator",
                    content=f"Narração {i + 1}",
                    content_type="narration",
                    scene_snapshot=deepcopy_scene(original.scene),
                )
            )
        save_game(original)
        loaded = load_game(self.sid)
        assert loaded is not None
        assert len(loaded.history) == 3
        assert loaded.history[-1].content == "Narração 3"

    # ── List / Fork / Delete ─────────────────────────────────────────

    def test_list_sessions_empty(self) -> None:
        """list_sessions retorna [] quando não há sessões."""
        result = list_sessions()
        assert result == []

    def test_list_sessions_with_data(self) -> None:
        """list_sessions retorna resumo de sessões criadas."""
        # Cria 2 sessões
        g1 = _make_test_game()
        save_game(g1)
        g2 = _make_test_game()
        g2.scene.location = "Floresta Negra"
        save_game(g2)

        result = list_sessions()
        # Pelo menos 2 sessões
        assert len(result) >= 2
        ids = {r["session_id"] for r in result}
        assert g1.session_id in ids
        assert g2.session_id in ids
        # Verifica campos do resumo
        for r in result:
            assert "session_id" in r
            assert "characters" in r
            assert "turn_count" in r
            assert "created_at" in r

    @pytest.mark.asyncio
    async def test_fork_session(self) -> None:
        """fork_session copia sessão com novo ID."""
        original = _make_test_game(self.sid)
        history_item = TurnRecord(
            turn_number=1,
            speaker="Narrator",
            content="Teste",
            content_type="narration",
            scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
        )
        original.history.append(history_item)
        save_game(original)

        new_id = await fork_session(self.sid)
        assert new_id is not None
        assert new_id != self.sid

        loaded = load_game(new_id)
        assert loaded is not None
        assert loaded.session_id == new_id
        assert len(loaded.history) == 1
        assert loaded.history[0].content == "Teste"
        # Limpa
        delete_session(new_id)

    @pytest.mark.asyncio
    async def test_fork_nonexistent(self) -> None:
        """fork_session em sessão inexistente retorna None."""
        assert await fork_session("ffffffff") is None

    @pytest.mark.asyncio
    async def test_fork_idempotent(self) -> None:
        """fork_session pode ser chamada 2x — cria 2 cópias distintas."""
        original = _make_test_game(self.sid)
        save_game(original)
        n1 = await fork_session(self.sid)
        n2 = await fork_session(self.sid)
        assert n1 is not None
        assert n2 is not None
        assert n1 != n2
        delete_session(n1)
        delete_session(n2)

    @pytest.mark.asyncio
    async def test_delete_session(self) -> None:
        """delete_session remove o arquivo."""
        g = _make_test_game(self.sid)
        save_game(g)
        path = SESSIONS_DIR / f"{self.sid}.json"
        assert path.exists()
        assert await delete_session_async(self.sid) is True
        assert not path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        """delete_session em ID inexistente não levanta erro."""
        assert await delete_session_async("ffffffff") is False

    @pytest.mark.asyncio
    async def test_fork_waits_for_active_session_transaction(self) -> None:
        """Fork cannot snapshot the middle of an in-flight turn transaction."""
        save_game(_make_test_game(self.sid))
        lock = _get_lock(self.sid)
        await lock.acquire()
        task = asyncio.create_task(fork_session(self.sid))
        await asyncio.sleep(0)
        assert not task.done()
        lock.release()
        new_id = await task
        assert new_id is not None
        delete_session(new_id)

    @pytest.mark.asyncio
    async def test_delete_waits_and_removes_all_session_artifacts(self) -> None:
        """Delete serializes with turns and removes state, log, and compaction backups."""
        save_game(_make_test_game(self.sid))
        (SESSIONS_DIR / f"{self.sid}.debug.jsonl").write_text("{}\n", encoding="utf-8")
        (SESSIONS_DIR / f"{self.sid}.kb_0.json").write_text("{}", encoding="utf-8")
        lock = _get_lock(self.sid)
        await lock.acquire()
        task = asyncio.create_task(delete_session_async(self.sid))
        await asyncio.sleep(0)
        assert not task.done()
        lock.release()
        assert await task is True
        assert not list(SESSIONS_DIR.glob(f"{self.sid}*"))


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Runner (sem LLM real, testa lógica pura)
# ═══════════════════════════════════════════════════════════════════════════


class TestRunnerLogic:
    """Testes do Runner que NÃO dependem de LLM."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        # Runner com client mock (não usado nesses testes)
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, {})

    def teardown_method(self) -> None:
        delete_session(self.sid)

    @pytest.mark.asyncio
    async def test_start_session_persists_default_state(self) -> None:
        """start_session retorna um ID e persiste o estado padrão recuperável."""
        sid = self.runner.start_session()
        assert isinstance(sid, str)
        assert len(sid) == 8
        path = SESSIONS_DIR / f"{sid}.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["session_id"] == sid
        state = await self.runner.get_state(sid)
        assert state is not None
        assert state.session_id == sid
        assert state.characters["C1"].mind.name == "Thorn"
        assert state.characters["C2"].mind.name == "Lyra"

    @pytest.mark.asyncio
    async def test_get_state_nonexistent(self) -> None:
        """get_state de sessão inexistente retorna None."""
        assert await self.runner.get_state("naoexiste") is None

    @pytest.mark.asyncio
    async def test_get_history_empty(self) -> None:
        """get_history de sessão nova retorna lista vazia."""
        sid = self.runner.start_session()
        history = await self.runner.get_history(sid)
        assert history == []

    @pytest.mark.asyncio
    async def test_get_history_limit(self) -> None:
        """get_history respeita parâmetro limit."""
        sid = self.runner.start_session()
        game = load_game(sid)
        assert game is not None
        for i in range(10):
            game.history.append(
                TurnRecord(
                    turn_number=i + 1,
                    speaker="Narrator",
                    content=f"Turno {i + 1}",
                    content_type="narration",
                    scene_snapshot=deepcopy_scene(game.scene),
                )
            )
        save_game(game)
        history = await self.runner.get_history(sid, limit=3)
        assert len(history) == 3
        assert history[-1].content == "Turno 10"

    def test_default_characters_complete(self) -> None:
        """Personagens padrão têm todos os campos preenchidos."""
        for cid, ch in DEFAULT_CHARACTERS.items():
            assert ch.mind.name, f"{cid} sem nome"
            assert ch.mind.personality, f"{cid} sem personality"
            assert ch.mind.knowledge, f"{cid} sem knowledge"
            assert ch.mind.current_mood, f"{cid} sem mood"
            assert ch.body.physical_description, f"{cid} sem descrição física"
            assert ch.body.outfit, f"{cid} sem outfit"

    def test_default_scene_complete(self) -> None:
        """Cena padrão tem todos os campos."""
        assert DEFAULT_SCENE.location
        assert DEFAULT_SCENE.time_of_day
        assert "C1" in DEFAULT_SCENE.present_characters
        assert "C2" in DEFAULT_SCENE.present_characters
        assert "Player" in DEFAULT_SCENE.present_characters
        assert len(DEFAULT_SCENE.physical_facts) >= 3

    # ── Undo ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_undo_restores_mood_and_full_step(self) -> None:
        """Undo restaura o humor E remove todos os registros do passo (mesmo turn_number)."""
        sid = self.runner.start_session()
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            original_mood_c1 = game.characters["C1"].mind.current_mood
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            # Simula um passo completo: jogada do humano + narração + fala do
            # personagem, todos com o mesmo turn_number (ver _append_history).
            runner._append_history(game, "Player", "oi", "speech", 1)
            runner._append_history(game, "Player", "acena", "action", 1)
            runner._append_history(game, "Narrator", "Algo acontece.", "narration", 1)
            runner._append_history(game, "C2", "Resposta.", "speech", 1)
            # Só DEPOIS dos appends o Narrador aplicaria mood_updates/scene_update.
            game.characters["C1"].mind.current_mood = "furious"
            game.scene.physical_facts["door"] = "open"
            save_game(game)

        result = await self.runner.undo_turn(sid)
        assert result["undone"] is True

        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 0, "todos os 4 registros do passo devem sumir"
            assert game.characters["C1"].mind.current_mood == original_mood_c1
            assert game.scene.physical_facts["door"] == "closed"

    @pytest.mark.asyncio
    async def test_undo_restores_location_and_previous_scene_facts(self) -> None:
        sid = self.runner.start_session()
        game = load_game(sid)
        assert game is not None
        original_scene = copy.deepcopy(game.scene)
        self.runner._append_history(game, "Narrator", "The road opens.", "narration", 1)
        self.runner._update_scene(
            game,
            {"location": "The Old Watchtower", "door": "ajar"},
        )
        save_game(game)

        persisted = load_game(sid)
        assert persisted is not None
        assert persisted.scene.location == "The Old Watchtower"
        assert persisted.scene.physical_facts == {"door": "ajar"}

        result = await self.runner.undo_turn(sid)

        assert result["undone"] is True
        restored = load_game(sid)
        assert restored is not None
        assert restored.scene == original_scene

    @pytest.mark.asyncio
    async def test_undo_nothing(self) -> None:
        """Undo em sessão sem histórico retorna undone=False."""
        sid = self.runner.start_session()
        result = await self.runner.undo_turn(sid)
        assert result["undone"] is False

    @pytest.mark.asyncio
    async def test_undo_nonexistent_session(self) -> None:
        """Undo em sessão inexistente retorna error."""
        result = await self.runner.undo_turn("ffffffff")
        assert result["undone"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_undo_idempotent(self) -> None:
        """Undo duas vezes — segunda retorna undone=False."""
        sid = self.runner.start_session()
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Teste.", "narration", 1)
            save_game(game)

        r1 = await self.runner.undo_turn(sid)
        assert r1["undone"] is True
        r2 = await self.runner.undo_turn(sid)
        assert r2["undone"] is False

    @pytest.mark.asyncio
    async def test_undo_multiple_turns(self) -> None:
        """Três turnos, desfaz um por um — cada undo remove um turno."""
        sid = self.runner.start_session()
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 1.", "narration", 1)
            game.scene.physical_facts["door"] = "ajar"
            save_game(game)

        # Turno 2
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 2.", "narration", 2)
            runner._append_history(game, "C1", "Resposta 2.", "speech", 2)
            game.scene.physical_facts["door"] = "open"
            save_game(game)

        # Turno 3
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 3.", "narration", 3)
            game.scene.physical_facts["door"] = "wide open"
            save_game(game)

        # Undo turno 3
        r = await self.runner.undo_turn(sid)
        assert r["undone"] is True
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 3  # Narrador 1 + Narrador 2 + C1
            assert game.scene.physical_facts["door"] == "open"

        # Undo turno 2
        r = await self.runner.undo_turn(sid)
        assert r["undone"] is True
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 1  # Narrador 1
            assert game.scene.physical_facts["door"] == "ajar"

        # Undo turno 1
        r = await self.runner.undo_turn(sid)
        assert r["undone"] is True
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 0
            assert game.scene.physical_facts["door"] == "closed"  # original

    @pytest.mark.asyncio
    async def test_call_narrator_passes_story_summary(self, monkeypatch) -> None:  # noqa: ANN001
        """_call_narrator repassa game.story_summary pro Narrador."""
        from src import runner as runner_mod

        captured: dict = {}

        async def fake_narrate(**kwargs):  # noqa: ANN003, ANN202
            captured.update(kwargs)
            return {"narration": "ok", "next_speaker": "Narrator", "context_for_character": ""}

        monkeypatch.setattr(runner_mod, "narrate", fake_narrate)

        game = _make_test_game()
        game.story_summary = "Resumo de teste."
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        await runner._call_narrator(game, 1)
        assert captured["story_summary"] == "Resumo de teste."

    @pytest.mark.asyncio
    async def test_force_speaker_is_known_before_character_context_is_built(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        sid = self.runner.start_session()
        captured: dict[str, object] = {}

        async def fake_narrator(game, turn_number, forced_speaker=None):  # noqa: ANN001, ANN202
            captured["forced_speaker"] = forced_speaker
            return {
                "narration": "The room stills.",
                "next_speaker": "C1",
                "context_for_character": f"Context filtered for {forced_speaker}",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number):  # noqa: ANN001, ANN202
            captured["character_id"] = character_id
            captured["context"] = context
            return {"speech": "I answer.", "thought": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_call_character", fake_character)

        result = await self.runner.player_turn(
            sid,
            speech="Answer me.",
            force_speaker="C2",
        )

        assert result["next_speaker"] == "C2"
        assert captured == {
            "forced_speaker": "C2",
            "character_id": "C2",
            "context": "Context filtered for C2",
        }

        debug_path = SESSIONS_DIR / f"{sid}.debug.jsonl"
        marker = json.loads(debug_path.read_text(encoding="utf-8").splitlines()[0])
        assert marker["agent"] == "turn_input"
        assert marker["input"] == {
            "speech": "Answer me.",
            "thought": "",
            "action": "",
            "force_speaker": "C2",
        }
        assert marker["effective_force_speaker"] == "C2"
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_call_character_passes_own_notes_only(self, monkeypatch) -> None:  # noqa: ANN001
        """_call_character repassa só a nota do PRÓPRIO personagem, nunca a de outro."""
        from src import runner as runner_mod

        captured: dict = {}

        async def fake_act(**kwargs):  # noqa: ANN003, ANN202
            captured.update(kwargs)
            return {"speech": "fala", "thought": None}

        monkeypatch.setattr(runner_mod, "character_act", fake_act)

        game = _make_test_game()
        game.character_notes = {"C1": "nota do Thorn", "C2": "nota da Lyra"}
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        await runner._call_character(game, "C1", "ctx", 1)
        assert captured["notes"] == "nota do Thorn"

    @pytest.mark.asyncio
    async def test_private_thought_only_turn_persists_without_calling_narrator(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        sid = self.runner.start_session()

        async def forbidden_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            raise AssertionError("Narrator must not receive a thought-only turn")

        monkeypatch.setattr(self.runner, "_call_narrator", forbidden_narrator)
        result = await self.runner.player_turn(
            sid,
            thought="Não devo demonstrar preocupação.",
            force_speaker="C2",
        )
        game = await self.runner.get_state(sid)
        assert game is not None
        assert result["narration"] is None
        assert result["next_speaker"] == game.player.controlled_character_id
        assert [(record.content_type, record.content) for record in game.history] == [
            ("thought", "Não devo demonstrar preocupação.")
        ]
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_suggestions_wait_for_active_session_transaction(self, monkeypatch) -> None:  # noqa: ANN001
        """Suggestion snapshots cannot race an in-flight turn mutation."""
        from src import runner as runner_mod

        save_game(_make_test_game(self.sid))

        async def fake_suggest(**kwargs):  # noqa: ANN003, ANN202
            return [{"speech": "Wait.", "action": "Listen."}]

        monkeypatch.setattr(runner_mod, "narrator_suggest", fake_suggest)
        lock = _get_lock(self.sid)
        await lock.acquire()
        task = asyncio.create_task(self.runner.suggest_actions(self.sid))
        await asyncio.sleep(0)
        assert not task.done()
        lock.release()
        result = await task
        assert result["suggestions"][0]["speech"] == "Wait."


# ═══════════════════════════════════════════════════════════════════════════
# Testes — compact_session (compactação de sessão)
# ═══════════════════════════════════════════════════════════════════════════


class TestCompactSession:
    """Testes de compact_session — Resumidor mockado, sem LLM real."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, {"compaction_keep_recent_turns": 8})

    def teardown_method(self) -> None:
        delete_session(self.sid)
        # Limpa eventuais backups kb_N.json criados pelo teste
        for f in SESSIONS_DIR.glob(f"{self.sid}.kb_*.json"):
            f.unlink()

    def _seed_history(self, num_turns: int) -> None:
        """Monta uma sessão com `num_turns` passos (Narrator + Player), salva no disco."""
        game = _make_test_game(self.sid)
        for i in range(1, num_turns + 1):
            game.history.append(
                TurnRecord(
                    turn_number=i,
                    speaker="Player",
                    content=f"Ação do turno {i}.",
                    content_type="action",
                    scene_snapshot=copy.deepcopy(game.scene),
                    mood_snapshot={"C1": "cauteloso", "C2": "curiosa"},
                )
            )
            game.history.append(
                TurnRecord(
                    turn_number=i,
                    speaker="Narrator",
                    content=f"Narração do turno {i}.",
                    content_type="narration",
                    scene_snapshot=copy.deepcopy(game.scene),
                    mood_snapshot={"C1": "cauteloso", "C2": "curiosa"},
                )
            )
        save_game(game)

    def _mock_summarize(self, monkeypatch) -> None:  # noqa: ANN001
        from src import runner as runner_mod

        async def fake_summarize(**kwargs):  # noqa: ANN003, ANN202
            return "Resumo dos turnos antigos.", {"C1": "Nota atualizada sobre Thorn."}

        monkeypatch.setattr(runner_mod, "summarize", fake_summarize)

    @pytest.mark.asyncio
    async def test_compact_below_window_does_nothing(self, monkeypatch) -> None:  # noqa: ANN001
        """Histórico menor ou igual à janela → compacted=False, nada muda no disco."""
        self._mock_summarize(monkeypatch)
        self._seed_history(5)  # 5 <= compaction_keep_recent_turns (8)

        result = await self.runner.compact_session(self.sid)
        assert result["compacted"] is False

        assert list(SESSIONS_DIR.glob(f"{self.sid}.kb_*.json")) == []
        game = load_game(self.sid)
        assert game is not None
        assert len(game.history) == 10  # 5 passos * 2 registros, intocado

    @pytest.mark.asyncio
    async def test_compact_above_window_rewrites_session_with_backup(
        self,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """Histórico maior que a janela → compacta, faz backup idêntico ao pré-estado."""
        self._mock_summarize(monkeypatch)
        self._seed_history(12)  # 12 passos, janela = 8 -> compacta os 4 mais antigos

        pre_compaction_bytes = (SESSIONS_DIR / f"{self.sid}.json").read_bytes()

        result = await self.runner.compact_session(self.sid)
        assert result["compacted"] is True
        assert result["evicted_turns"] == 8  # 4 passos evictados * 2 registros
        assert result["kept_turns"] == 16  # 8 passos mantidos * 2 registros

        # Backup kb_0 existe e é byte-a-byte igual ao estado pré-compactação
        backup_path = Path(result["backup_path"])
        assert backup_path.exists()
        assert backup_path.read_bytes() == pre_compaction_bytes

        # Sessão real foi reescrita: histórico menor, resumo/notas preenchidos
        game = load_game(self.sid)
        assert game is not None
        assert len(game.history) == 16
        assert game.history[0].turn_number == 5  # os 4 primeiros passos saíram
        assert game.story_summary == "Resumo dos turnos antigos."
        assert game.character_notes["C1"] == "Nota atualizada sobre Thorn."

    @pytest.mark.asyncio
    async def test_undo_still_works_after_compaction(self, monkeypatch) -> None:  # noqa: ANN001
        """undo_turn continua funcionando dentro da janela que sobrou pós-compactação."""
        self._mock_summarize(monkeypatch)
        self._seed_history(10)

        await self.runner.compact_session(self.sid)
        game = load_game(self.sid)
        assert game is not None
        turns_after_compaction = len(game.history)

        r = await self.runner.undo_turn(self.sid)
        assert r["undone"] is True
        game = load_game(self.sid)
        assert game is not None
        assert len(game.history) == turns_after_compaction - 2  # um passo (2 registros) a menos

    @pytest.mark.asyncio
    async def test_turn_after_compaction_uses_summary_and_character_note(self, monkeypatch) -> None:  # noqa: ANN001
        from src import runner as runner_mod

        async def fake_summarize(**kwargs):  # noqa: ANN003, ANN202
            return "Durable world summary.", {"C2": "Lyra remembers the sealed gate."}

        captured: dict[str, str] = {}

        async def fake_narrator(game, turn_number, forced_speaker=None):  # noqa: ANN001, ANN202
            captured["summary"] = game.story_summary
            return {
                "narration": "The gate hums.",
                "next_speaker": "C2",
                "context_for_character": "The sealed gate is visible.",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number):  # noqa: ANN001, ANN202
            captured["note"] = game.character_notes.get(character_id, "")
            captured["context"] = context
            return {"speech": "I remember this gate.", "thought": None}

        monkeypatch.setattr(runner_mod, "summarize", fake_summarize)
        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_call_character", fake_character)
        self._seed_history(12)

        compacted = await self.runner.compact_session(self.sid)
        result = await self.runner.player_turn(
            self.sid,
            action="Thorn points to the gate.",
            force_speaker="C2",
        )

        assert compacted["compacted"] is True
        assert result["character_response"] == {
            "speech": "I remember this gate.",
            "thought": None,
        }
        assert captured == {
            "summary": "Durable world summary.",
            "note": "Lyra remembers the sealed gate.",
            "context": "The sealed gate is visible.",
        }

    @pytest.mark.asyncio
    async def test_compact_missing_session(self) -> None:
        """Compactar sessão inexistente devolve erro, sem levantar exceção."""
        result = await self.runner.compact_session("naoexiste")
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# Testes — restore_last_compaction (desfazer compactação, com trava de segurança)
# ═══════════════════════════════════════════════════════════════════════════


class TestRestoreCompaction:
    """A trava de segurança é o que importa aqui: nunca perder jogadas novas."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, {"compaction_keep_recent_turns": 8})

    def teardown_method(self) -> None:
        delete_session(self.sid)
        for f in SESSIONS_DIR.glob(f"{self.sid}.kb_*.json"):
            f.unlink()

    def _seed_history(self, num_turns: int) -> None:
        game = _make_test_game(self.sid)
        save_game(game)
        self._append_turns(num_turns)

    def _append_turns(self, count: int) -> None:
        """Acrescenta mais `count` passos (1 registro cada) à sessão já salva."""
        game = load_game(self.sid)
        assert game is not None
        start = (game.history[-1].turn_number + 1) if game.history else 1
        for i in range(start, start + count):
            game.history.append(
                TurnRecord(
                    turn_number=i,
                    speaker="Player",
                    content=f"Ação do turno {i}.",
                    content_type="action",
                    scene_snapshot=copy.deepcopy(game.scene),
                    mood_snapshot={"C1": "cauteloso", "C2": "curiosa"},
                )
            )
        save_game(game)

    def _mock_summarize(self, monkeypatch) -> None:  # noqa: ANN001
        from src import runner as runner_mod

        async def fake_summarize(**kwargs):  # noqa: ANN003, ANN202
            return "Resumo.", {}

        monkeypatch.setattr(runner_mod, "summarize", fake_summarize)

    @pytest.mark.asyncio
    async def test_restore_after_compaction_with_no_new_turns(self, monkeypatch) -> None:  # noqa: ANN001
        """Nada mudou desde a compactação -> restaura, backup some, histórico volta."""
        self._mock_summarize(monkeypatch)
        self._seed_history(12)
        pre_compaction_bytes = (SESSIONS_DIR / f"{self.sid}.json").read_bytes()

        compact_result = await self.runner.compact_session(self.sid)
        assert compact_result["compacted"] is True

        result = await self.runner.restore_last_compaction(self.sid)
        assert result["restored"] is True
        assert result["history_length"] == 12

        assert (SESSIONS_DIR / f"{self.sid}.json").read_bytes() == pre_compaction_bytes
        assert list(SESSIONS_DIR.glob(f"{self.sid}.kb_*.json")) == []  # backup consumido

    @pytest.mark.asyncio
    async def test_restore_refuses_when_new_turns_played_after_compaction(
        self,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """Jogou mais depois de compactar -> restaurar é recusado, nada muda."""
        self._mock_summarize(monkeypatch)
        self._seed_history(12)
        await self.runner.compact_session(self.sid)

        # Joga mais um passo em cima da sessão já compactada
        game = load_game(self.sid)
        assert game is not None
        game.history.append(
            TurnRecord(
                turn_number=game.history[-1].turn_number + 1,
                speaker="Player",
                content="Ação nova pós-compactação.",
                content_type="action",
                scene_snapshot=copy.deepcopy(game.scene),
                mood_snapshot={"C1": "cauteloso", "C2": "curiosa"},
            )
        )
        save_game(game)
        pre_restore_bytes = (SESSIONS_DIR / f"{self.sid}.json").read_bytes()

        result = await self.runner.restore_last_compaction(self.sid)
        assert result["restored"] is False
        assert "more recent" in result["reason"]

        # Nada foi alterado: sessão idêntica, backup continua existindo
        assert (SESSIONS_DIR / f"{self.sid}.json").read_bytes() == pre_restore_bytes
        assert len(list(SESSIONS_DIR.glob(f"{self.sid}.kb_*.json"))) == 1

    @pytest.mark.asyncio
    async def test_restore_no_backup_available(self) -> None:
        """Sem nenhuma compactação feita -> recusa por falta de backup."""
        self._seed_history(3)
        result = await self.runner.restore_last_compaction(self.sid)
        assert result["restored"] is False
        assert "No compaction backup" in result["reason"]

    @pytest.mark.asyncio
    async def test_restore_missing_session(self) -> None:
        """Sessão inexistente devolve erro, no mesmo formato de compact/undo."""
        result = await self.runner.restore_last_compaction("naoexiste")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_restore_only_undoes_the_most_recent_compaction(
        self,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """Restaurar é um "ctrl-Z" de uma camada só — não empilha através de
        múltiplas compactações.

        Depois de restaurar a 2ª compactação (kb_1), os turnos que ela trazia
        de volta (21-32) voltam a existir ao vivo. Tentar restaurar a 1ª
        compactação (kb_0, que só conhece até o turno 20) nesse momento
        apagaria esses turnos — a trava de segurança RECUSA corretamente,
        em vez de permitir. kb_0 continua intacto, disponível pra restaurar
        manualmente depois, se o dono aceitar perder 21-32 de propósito.
        """
        self._mock_summarize(monkeypatch)
        self._seed_history(20)

        first_compact = await self.runner.compact_session(self.sid)
        assert first_compact["compacted"] is True  # evicta 1-12, mantém 13-20 (8 turnos)

        # Sem mais turnos, 8 <= janela(8) -> uma segunda compactação não faria
        # nada. Joga mais 12 pra passar da janela de novo antes de compactar.
        self._append_turns(12)
        second_compact = await self.runner.compact_session(self.sid)
        assert second_compact["compacted"] is True  # evicta 13-24, mantém 25-32
        assert len(list(SESSIONS_DIR.glob(f"{self.sid}.kb_*.json"))) == 2

        # Restaura a compactação mais recente (kb_1) -> turnos 13-32 voltam
        r1 = await self.runner.restore_last_compaction(self.sid)
        assert r1["restored"] is True
        assert len(list(SESSIONS_DIR.glob(f"{self.sid}.kb_*.json"))) == 1

        # Tentar ir além (kb_0, só conhece até o turno 20) é recusado: isso
        # apagaria os turnos 21-32 que r1 acabou de trazer de volta.
        r2 = await self.runner.restore_last_compaction(self.sid)
        assert r2["restored"] is False
        assert "more recent" in r2["reason"]
        assert len(list(SESSIONS_DIR.glob(f"{self.sid}.kb_*.json"))) == 1  # kb_0 intacto


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Config customizada + Debug (LLM mockado)
# ═══════════════════════════════════════════════════════════════════════════


def _custom_char(name: str, mood: str = "neutro") -> Character:
    from src.models import CharacterBody, CharacterMind

    return Character(
        mind=CharacterMind(
            name=name,
            personality=f"{name} personalidade completa",
            knowledge=[f"{name} sabe de algo"],
            current_mood=mood,
        ),
        body=CharacterBody(
            name=name,
            physical_description=f"{name} aparência",
            outfit=f"{name} roupa",
        ),
    )


class TestCustomSessionAndDebug:
    """start_session custom, prompts dinâmicos, debug e preview (sem LLM real)."""

    def setup_method(self) -> None:
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, {})
        self.created: list[str] = []

    def teardown_method(self) -> None:
        for sid in self.created:
            delete_session(sid)

    def _start_custom(self) -> str:
        chars = {
            "C1": _custom_char("Aria"),
            "C2": _custom_char("Bron"),
            "C3": _custom_char("Caius"),
        }
        scene = Scene(
            location="Cripta antiga",
            time_of_day="madrugada",
            present_characters=[],  # deve ser recomputado
            physical_facts={"ar": "úmido"},
        )
        sid = self.runner.start_session(
            {
                "characters": chars,
                "scene": scene,
                "controlled_character_id": "C2",
                "narrator_directives": "Mundo de horror gótico. Tom sombrio.",
            }
        )
        self.created.append(sid)
        return sid

    def test_start_session_custom_round_trip(self) -> None:
        """Personagens custom + narrator_directives fazem round-trip via load_game."""
        sid = self._start_custom()
        game = load_game(sid)
        assert game is not None
        assert set(game.characters) == {"C1", "C2", "C3"}
        assert game.characters["C1"].mind.name == "Aria"
        assert game.player.controlled_character_id == "C2"
        assert game.narrator_directives == "Mundo de horror gótico. Tom sombrio."

    def test_start_session_recomputes_present_characters(self) -> None:
        """present_characters é recomputado no servidor, ignorando o cliente."""
        sid = self._start_custom()
        game = load_game(sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "C3", "Player"]

    def test_start_session_no_characters_raises(self) -> None:
        """start_session sem personagens levanta ValueError."""
        with pytest.raises(ValueError, match="at least one character"):
            self.runner.start_session({"characters": {}})

    def test_start_session_invalid_controlled_fallback(self) -> None:
        """controlled_character_id inexistente cai no primeiro personagem."""
        sid = self.runner.start_session(
            {
                "characters": {"C1": _custom_char("Solo")},
                "controlled_character_id": "C9",
            }
        )
        self.created.append(sid)
        game = load_game(sid)
        assert game is not None
        assert game.player.controlled_character_id == "C1"

    def test_build_system_prompt_dynamic_ids_and_directives(self) -> None:
        """_build_system_prompt enumera IDs dinâmicos e anexa diretivas."""
        from src.agents.narrator import _build_system_prompt

        prompt = _build_system_prompt(["C1", "C2", "C3"], "Regras do mundo aqui.")
        assert "C1, C2, C3, Narrator" in prompt
        assert "Player" not in prompt
        assert "Regras do mundo aqui." in prompt

    def test_build_system_prompt_no_directives(self) -> None:
        """Sem diretivas, não anexa o bloco de WORLD DIRECTIVES."""
        from src.agents.narrator import _build_system_prompt

        prompt = _build_system_prompt(["C1"], "")
        assert "WORLD DIRECTIVES" not in prompt

    @pytest.mark.asyncio
    async def test_valid_speakers_accepts_custom_id(self, monkeypatch) -> None:  # noqa: ANN001
        """valid_speakers aceita IDs custom (C3) e não faz fallback."""
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "narration": "Algo acontece.",
                "next_speaker": "C3",
                "context_for_character": "ctx",
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        chars = {"C3": _custom_char("Caius")}
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(location="x", time_of_day="y", present_characters=[], physical_facts={}),
            characters=chars,
            player_controlled_id="C3",
            history=[],
            config={},
        )
        assert result["next_speaker"] == "C3"

    @pytest.mark.asyncio
    async def test_valid_speakers_fallback_invalid(self, monkeypatch) -> None:  # noqa: ANN001
        """next_speaker inválido cai para Narrator (o Narrador não conhece "Player")."""
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "narration": "Algo acontece.",
                "next_speaker": "Fantasma",
                "context_for_character": "",
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(location="x", time_of_day="y", present_characters=[], physical_facts={}),
            characters={"C1": _custom_char("Solo")},
            player_controlled_id="C1",
            history=[],
            config={},
        )
        assert result["next_speaker"] == "Narrator"

    @pytest.mark.asyncio
    async def test_forced_speaker_constrains_schema_and_context_target(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import narrator as narrator_mod

        captured: dict[str, object] = {}

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            captured["messages"] = messages
            captured["json_schema"] = kwargs["json_schema"]
            return {
                "narration": "Something happens.",
                "next_speaker": "C1",
                "context_for_character": "Only C2 can perceive this.",
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(location="x", time_of_day="y", present_characters=[], physical_facts={}),
            characters={"C1": _custom_char("One"), "C2": _custom_char("Two")},
            player_controlled_id="C1",
            history=[],
            config={},
            forced_speaker="C2",
        )

        schema = captured["json_schema"]
        assert isinstance(schema, dict)
        next_speaker = schema["schema"]["properties"]["next_speaker"]
        assert next_speaker["enum"] == ["C2"]
        messages = captured["messages"]
        assert isinstance(messages, list)
        assert "next_speaker is fixed as C2" in messages[1]["content"]
        assert "what C2 perceives" in messages[1]["content"]
        assert result["next_speaker"] == "C2"

    @pytest.mark.asyncio
    async def test_forced_narrator_always_clears_character_context(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "narration": "Something happens.",
                "next_speaker": "C1",
                "context_for_character": "Stale character context.",
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(location="x", time_of_day="y", present_characters=[], physical_facts={}),
            characters={"C1": _custom_char("One")},
            player_controlled_id="C1",
            history=[],
            config={},
            forced_speaker="Narrator",
        )

        assert result["next_speaker"] == "Narrator"
        assert result["context_for_character"] == ""

    @pytest.mark.asyncio
    async def test_debug_log_records_llm_calls(self, monkeypatch) -> None:  # noqa: ANN001
        """Cada chamada REAL ao LLM grava uma linha no log bruto .debug.jsonl da sessão.

        Mocka no nível de ``client.post`` (não em chat_completion_json/chat_completion)
        pra exercitar de verdade a interceptação em src/llm/client.py.
        """
        import json as json_module

        from src.store.sessions import SESSIONS_DIR

        async def mock_post(url, json, **kwargs):  # noqa: ANN001, A002, ARG001
            schema_name = json.get("response_format", {}).get("json_schema", {}).get("name")
            if schema_name == "narrator_turn":
                content = json_module.dumps(
                    {
                        "narration": "A cripta range.",
                        "next_speaker": "C1",
                        "context_for_character": "Você ouve um rangido.",
                        "scene_update": None,
                        "mood_updates": None,
                    }
                )
            else:
                content = json_module.dumps({"speech": "Estou pronto.", "thought": None})
            req = httpx.Request("POST", url)
            return httpx.Response(
                200, json={"choices": [{"message": {"content": content}}]}, request=req
            )

        monkeypatch.setattr(self.client, "post", mock_post)

        # next_speaker="C1" precisa ser diferente do controlado, senão o
        # runner pausa (agência do jogador) em vez de chamar o Personagem.
        sid = self.runner.start_session(
            {
                "characters": {"C1": _custom_char("Solo"), "C2": _custom_char("Outro")},
                "controlled_character_id": "C2",
            }
        )
        self.created.append(sid)
        result = await self.runner.player_turn(sid, speech="oi")
        assert result["character_response"] == {"speech": "Estou pronto.", "thought": None}

        debug_path = SESSIONS_DIR / f"{sid}.debug.jsonl"
        assert debug_path.exists()
        entries = [
            json_module.loads(line) for line in debug_path.read_text(encoding="utf-8").splitlines()
        ]
        assert len(entries) == 3  # payload do turno, Narrador e Personagem
        assert entries[0]["session_id"] == sid
        assert entries[0]["turn_number"] == 1
        assert entries[0]["agent"] == "turn_input"
        assert entries[0]["input"]["speech"] == "oi"
        assert entries[1]["agent"] == "narrator"
        assert entries[1]["response"] is not None
        assert entries[2]["agent"] == "character:Solo"
        assert json_module.loads(entries[2]["response"]) == {
            "speech": "Estou pronto.",
            "thought": None,
        }

    @pytest.mark.asyncio
    async def test_preview_narrator_prompt(self) -> None:
        """preview_narrator_prompt monta messages corretos sem tocar no LLM."""
        sid = self._start_custom()
        messages = await self.runner.preview_narrator_prompt(sid, speech="olá", action="acena")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        # IDs dinâmicos + diretivas no system prompt
        assert "C1, C2, C3, Narrator" in messages[0]["content"]
        assert "Player" not in messages[0]["content"]
        assert "horror gótico" in messages[0]["content"]
        # jogada do humano aparece no HISTORY, renderizada com o nome do
        # personagem controlado (C2 = Bron) — nunca como "Player".
        assert "olá" in messages[1]["content"]
        assert "acena" in messages[1]["content"]
        assert "Bron" in messages[1]["content"]
        assert "Player" not in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_preview_narrator_prompt_missing_session(self) -> None:
        """preview de sessão inexistente retorna lista vazia."""
        assert await self.runner.preview_narrator_prompt("naoexiste") == []


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Agente Resumidor (summarizer.py)
# ═══════════════════════════════════════════════════════════════════════════


class TestSummarizerAgent:
    """Testes do agente Resumidor — foco em imersão (nunca vazar 'Player')."""

    def test_build_summarizer_messages_never_leaks_player(self) -> None:
        """A jogada do humano (speaker='Player') aparece traduzida com o nome
        do personagem controlado — a string 'Player' nunca aparece no prompt."""
        from src.agents.summarizer import build_summarizer_messages

        evicted = [
            TurnRecord(
                turn_number=1,
                speaker="Player",
                content="Encaro Lyra e pergunto sobre o forasteiro.",
                content_type="speech",
                scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
            ),
            TurnRecord(
                turn_number=1,
                speaker="Narrator",
                content="Thorn se inclina, a luz das velas tremendo na sua cicatriz.",
                content_type="narration",
                scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
            ),
            TurnRecord(
                turn_number=1,
                speaker="C2",
                content="Lyra sorri, curiosa.",
                content_type="speech",
                scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
            ),
        ]

        messages = build_summarizer_messages(
            characters=DEFAULT_CHARACTERS,
            controlled_id="C1",
            story_summary="",
            character_notes={},
            evicted_turns=evicted,
            narrator_directives="Fantasia sombria.",
        )

        assert messages[0]["role"] == "system"
        assert "player" not in messages[0]["content"].lower()
        assert "user" not in messages[0]["content"].lower()
        assert "Fantasia sombria." in messages[0]["content"]

        assert "Thorn" in messages[1]["content"]
        assert "Encaro Lyra" in messages[1]["content"]
        assert "TYPE=speech" in messages[1]["content"]
        assert "TYPE=narration" in messages[1]["content"]
        assert "SPEAKER=Thorn" in messages[1]["content"]
        assert "Player" not in messages[1]["content"]

    def test_build_summarizer_messages_keeps_private_notes_out(self) -> None:
        """O resumo público nunca recebe notas privadas existentes."""
        from src.agents.summarizer import build_summarizer_messages

        messages = build_summarizer_messages(
            characters=DEFAULT_CHARACTERS,
            controlled_id="C1",
            story_summary="Thorn e Lyra se conheceram na taverna.",
            character_notes={"C1": "Desconfia de magia."},
            evicted_turns=[],
        )
        user_content = messages[1]["content"]
        assert "Thorn e Lyra se conheceram na taverna." in user_content
        assert "Desconfia de magia." not in user_content

    @pytest.mark.asyncio
    async def test_summarize_returns_only_changed_notes(self, monkeypatch) -> None:  # noqa: ANN001
        """summarize() devolve o resumo + só as notas que o LLM decidiu mudar
        (merge com as notas antigas é responsabilidade de quem chama)."""
        from src.agents import summarizer as summarizer_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            if kwargs["agent"] == "summarizer:world":
                return {"story_summary": "Resumo atualizado."}
            return {"character_note": "Ficou tenso ao ouvir sobre a Guarda de Ferro."}

        monkeypatch.setattr(summarizer_mod, "chat_completion_json", fake_json)

        client = httpx.AsyncClient(base_url="http://localhost:8888")
        summary, changed_notes = await summarizer_mod.summarize(
            client=client,
            characters=DEFAULT_CHARACTERS,
            controlled_id="C1",
            story_summary="Resumo antigo.",
            character_notes={"C1": "nota antiga", "C2": "nota antiga da Lyra"},
            evicted_turns=[
                TurnRecord(
                    turn_number=1,
                    speaker="Player",
                    content="Penso na Guarda de Ferro.",
                    content_type="thought",
                    scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
                )
            ],
            config={},
        )
        assert summary == "Resumo atualizado."
        assert changed_notes == {"C1": "Ficou tenso ao ouvir sobre a Guarda de Ferro."}
        assert "C2" not in changed_notes  # não mencionada -> não retorna, runner mantém a antiga
        await client.aclose()

    @pytest.mark.asyncio
    async def test_summarize_isolates_private_character_calls(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import summarizer as summarizer_mod

        prompts: dict[str, str] = {}

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            prompts[kwargs["agent"]] = messages[1]["content"]
            if kwargs["agent"] == "summarizer:world":
                return {"story_summary": "Summary."}
            return {"character_note": f"Private {kwargs['agent']} note."}

        monkeypatch.setattr(summarizer_mod, "chat_completion_json", fake_json)
        client = httpx.AsyncClient(base_url="http://localhost:8888")
        _, changed_notes = await summarizer_mod.summarize(
            client=client,
            characters=DEFAULT_CHARACTERS,
            controlled_id="C1",
            story_summary="",
            character_notes={},
            evicted_turns=[
                TurnRecord(
                    turn_number=1,
                    speaker="Player",
                    content="Segredo do Thorn.",
                    content_type="thought",
                    scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
                ),
                TurnRecord(
                    turn_number=1,
                    speaker="C2",
                    content="Segredo da Lyra.",
                    content_type="thought",
                    scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
                ),
            ],
            config={},
        )
        assert set(changed_notes) == {"C1", "C2"}
        assert "Segredo do Thorn." not in prompts["summarizer:Lyra"]
        assert "Segredo da Lyra." not in prompts["summarizer:Thorn"]
        assert "Segredo do Thorn." not in prompts["summarizer:world"]
        assert "Segredo da Lyra." not in prompts["summarizer:world"]
        await client.aclose()

    def test_summarizer_schema_is_public_only(self) -> None:
        from src.agents.summarizer import build_summarizer_json_schema

        schema = build_summarizer_json_schema(["hero", "guide"])["schema"]
        assert set(schema["properties"]) == {"story_summary"}
        assert schema["additionalProperties"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Casos de borda e validações críticas."""

    def test_update_scene(self) -> None:
        """_update_scene atualiza physical_facts."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._update_scene(game, {"door": "open", "lighting": "off"})
        assert game.scene.physical_facts["door"] == "open"
        assert game.scene.physical_facts["lighting"] == "off"
        # Campo não afetado permanece
        assert game.scene.physical_facts["weather_outside"] == "heavy rain"

    def test_update_scene_routes_reserved_fields_and_clears_old_location_facts(self) -> None:
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]

        runner._update_scene(
            game,
            {
                "location": "  The Old Watchtower  ",
                "time_of_day": "dawn",
                "door": "ajar",
            },
        )

        assert game.scene.location == "The Old Watchtower"
        assert game.scene.time_of_day == "dawn"
        assert game.scene.physical_facts == {"door": "ajar"}
        assert "location" not in game.scene.physical_facts
        assert "time_of_day" not in game.scene.physical_facts

    def test_update_scene_does_not_clear_facts_without_real_location_change(self) -> None:
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]

        runner._update_scene(
            game,
            {
                "location": game.scene.location,
                "time_of_day": None,
                "door": None,
            },
        )

        assert game.scene.time_of_day == DEFAULT_SCENE.time_of_day
        assert "door" not in game.scene.physical_facts
        assert game.scene.physical_facts["weather_outside"] == "heavy rain"

    def test_update_scene_none(self) -> None:
        """_update_scene com None não altera nada."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._update_scene(game, None)
        assert game.scene.physical_facts["door"] == "closed"

    def test_format_history_for_character_sees_public_speech_and_own_thought(self) -> None:
        from src.agents.character import _format_history_for_character

        scene = deepcopy_scene(DEFAULT_SCENE)
        history = [
            TurnRecord(
                turn_number=1,
                speaker="Player",
                content="oi",
                content_type="speech",
                scene_snapshot=scene,
            ),
            TurnRecord(
                turn_number=1,
                speaker="Player",
                content="Thorn acena",
                content_type="action",
                scene_snapshot=scene,
            ),
            TurnRecord(
                turn_number=1,
                speaker="Narrator",
                content="A porta range.",
                content_type="narration",
                scene_snapshot=scene,
            ),
            TurnRecord(
                turn_number=1,
                speaker="C2",
                content="Oi Thorn.",
                content_type="speech",
                scene_snapshot=scene,
            ),
            TurnRecord(
                turn_number=1,
                speaker="C2",
                content="Meu próprio segredo.",
                content_type="thought",
                scene_snapshot=scene,
            ),
            TurnRecord(
                turn_number=1,
                speaker="C1",
                content="Segredo alheio.",
                content_type="thought",
                scene_snapshot=scene,
            ),
        ]
        text = _format_history_for_character(history, DEFAULT_CHARACTERS, "C1", "C2")
        assert "Thorn acena" not in text
        assert "porta range" not in text
        assert "Thorn: oi" in text  # "Player" traduzido pro nome do controlado
        assert "Player" not in text
        assert "Oi Thorn." in text
        assert "Meu próprio segredo." in text
        assert "Segredo alheio." not in text

    def test_narrator_prompt_includes_story_summary(self) -> None:
        """story_summary não vazio vira uma seção STORY SO FAR no prompt do Narrador."""
        from src.agents.narrator import _build_user_prompt

        prompt = _build_user_prompt(
            scene=DEFAULT_SCENE,
            characters=DEFAULT_CHARACTERS,
            player_controlled_id="C1",
            history=[],
            story_summary="Thorn e Lyra se conheceram numa taverna sombria.",
        )
        assert "STORY SO FAR:" in prompt
        assert "Thorn e Lyra se conheceram numa taverna sombria." in prompt

    def test_narrator_prompt_omits_story_summary_when_empty(self) -> None:
        """Sem story_summary, a seção STORY SO FAR nem aparece."""
        from src.agents.narrator import _build_user_prompt

        prompt = _build_user_prompt(
            scene=DEFAULT_SCENE,
            characters=DEFAULT_CHARACTERS,
            player_controlled_id="C1",
            history=[],
        )
        assert "STORY SO FAR" not in prompt

    def test_narrator_prompt_orders_stable_prefix_before_changing_state(self) -> None:
        from src.agents.narrator import _build_user_prompt

        scene = deepcopy_scene(DEFAULT_SCENE)
        history = [TurnRecord(1, "C2", "Olá.", "speech", scene)]
        prompt = _build_user_prompt(
            scene,
            DEFAULT_CHARACTERS,
            "C1",
            history,
            story_summary="Resumo antigo.",
            forced_speaker="C2",
        )

        assert prompt.index("CHARACTERS PRESENT:") < prompt.index("STORY SO FAR:")
        assert prompt.index("STORY SO FAR:") < prompt.index("HISTORY:")
        assert prompt.index("HISTORY:") < prompt.index("CURRENT SCENE:")
        assert prompt.index("CURRENT SCENE:") < prompt.index("CURRENT MOODS:")
        assert prompt.index("CURRENT MOODS:") < prompt.index("ROUTING CONSTRAINT:")

    def test_narrator_prompt_never_receives_private_thoughts(self) -> None:
        from src.agents.narrator import _build_user_prompt

        scene = deepcopy_scene(DEFAULT_SCENE)
        history = [
            TurnRecord(1, "Player", "Segredo do Thorn.", "thought", scene),
            TurnRecord(1, "Player", "Pode me ouvir?", "speech", scene),
        ]
        prompt = _build_user_prompt(
            DEFAULT_SCENE,
            DEFAULT_CHARACTERS,
            "C1",
            history,
            context_max=4096,
        )
        assert "Segredo do Thorn." not in prompt
        assert "Pode me ouvir?" in prompt

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ({"speech": "Olá.", "thought": None}, {"speech": "Olá.", "thought": None}),
            (
                {"speech": None, "thought": "Isso parece errado."},
                {"speech": None, "thought": "Isso parece errado."},
            ),
            (
                {"speech": "Olá.", "thought": "Preciso ter cuidado."},
                {"speech": "Olá.", "thought": "Preciso ter cuidado."},
            ),
        ],
    )
    def test_character_output_accepts_speech_thought_or_both(
        self, raw: dict, expected: dict
    ) -> None:
        from src.agents.character import _normalize_output

        assert _normalize_output(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            {"speech": None, "thought": None},
            {"speech": " ", "thought": ""},
            {"speech": None, "thought": "Arrumo um tufo de cabelo atrás da orelha."},
        ],
    )
    def test_character_output_rejects_empty_or_physical_action(self, raw: dict) -> None:
        from src.agents.character import _normalize_output

        with pytest.raises(ValueError):
            _normalize_output(raw)

    @pytest.mark.asyncio
    async def test_character_retries_once_after_physical_action(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import character as character_mod

        responses = iter(
            [
                {"speech": "Oi.", "thought": "Inclino a cabeça."},
                {"speech": "Oi.", "thought": "Ele parece cansado para mim."},
            ]
        )

        async def fake_json(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            return next(responses)

        monkeypatch.setattr(character_mod, "chat_completion_json", fake_json)
        async with httpx.AsyncClient() as client:
            output = await character_mod.act(
                client=client,
                character=DEFAULT_CHARACTERS["C2"],
                context="Thorn parece cansado.",
                history=[],
                characters=DEFAULT_CHARACTERS,
                controlled_id="C1",
                character_id="C2",
                config={},
            )
        assert output == {"speech": "Oi.", "thought": "Ele parece cansado para mim."}

    def test_character_prompt_includes_own_notes(self) -> None:
        """A nota do próprio personagem vira uma linha 'What you remember' no prompt."""
        from src.agents.character import _build_user_prompt

        thorn = DEFAULT_CHARACTERS["C1"]
        prompt = _build_user_prompt(
            "Contexto.",
            "(none)",
            thorn.mind.current_mood,
            "Ficou tenso ao ouvir sobre a Guarda de Ferro.",
        )
        assert "What you remember: Ficou tenso ao ouvir sobre a Guarda de Ferro." in prompt

    def test_character_prompt_never_leaks_another_characters_notes(self) -> None:
        """act() só recebe a nota do PRÓPRIO personagem — nunca a de outro.

        A assinatura de `act`/`_build_user_prompt` só aceita uma string
        (a nota de um personagem só), então não há como o runner passar o
        dict inteiro por engano — mas o teste documenta a garantia: a nota
        de C2 nunca aparece no prompt de C1 quando só a nota de C1 é passada.
        """
        from src.agents.character import _build_user_prompt

        thorn = DEFAULT_CHARACTERS["C1"]
        prompt = _build_user_prompt(
            "Contexto.", "(none)", thorn.mind.current_mood, "Nota exclusiva do Thorn."
        )
        assert "Nota exclusiva do Thorn." in prompt
        assert "nota da Lyra" not in prompt  # nunca foi passada, nem podia vazar

    def test_character_prompt_marks_empty_notes_explicitly(self) -> None:
        """Sem nota, o estado privado explicita que ainda não há memória compactada."""
        from src.agents.character import _build_user_prompt

        thorn = DEFAULT_CHARACTERS["C1"]
        prompt = _build_user_prompt("Contexto.", "(none)", thorn.mind.current_mood, "")
        assert "What you remember: (none yet)" in prompt

    def test_character_prompt_keeps_rules_stable_and_state_after_history(self) -> None:
        from src.agents.character import _build_system_prompt, _build_user_prompt

        calm = copy.deepcopy(DEFAULT_CHARACTERS["C1"])
        tense = copy.deepcopy(calm)
        tense.mind.current_mood = "tense"

        assert _build_system_prompt(calm) == _build_system_prompt(tense)
        assert "Current mood:" not in _build_system_prompt(calm)
        user_prompt = _build_user_prompt(
            "A porta range.", "Turn 1: Olá.", "tense", "Lembra da chave."
        )
        assert user_prompt.index("RECENT EVENTS:") < user_prompt.index("CURRENT PRIVATE STATE:")
        assert user_prompt.index("CURRENT PRIVATE STATE:") < user_prompt.index("SCENE CONTEXT")

    def test_agent_prompts_encode_quality_and_provenance_rules(self) -> None:
        from src.agents.character import _build_system_prompt as build_character_prompt
        from src.agents.narrator import _build_system_prompt as build_narrator_prompt
        from src.agents.summarizer import _build_system_prompt as build_summarizer_prompt

        narrator_prompt = build_narrator_prompt(["C1"])
        character_prompt = build_character_prompt(_custom_char("Plain"))
        summarizer_prompt = build_summarizer_prompt()

        assert "Resolve the immediate consequence" in narrator_prompt
        assert "unspoken thoughts" in narrator_prompt
        assert "Mood is persistent state" in narrator_prompt
        assert "Dialogue is an attributed claim" in narrator_prompt
        assert "never invent a location, backstory" in character_prompt
        assert "Never repeat a complete sentence" in character_prompt
        assert "TYPE=speech is an attributed claim" in summarizer_prompt
        assert "TYPE=action is an attempt" in summarizer_prompt
        for prompt in (narrator_prompt, character_prompt, summarizer_prompt):
            assert "—" not in prompt
            assert "–" not in prompt

    def test_append_history_deepcopy(self) -> None:
        """_append_history usa deepcopy — modificar cena posterior não afeta snapshot."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._append_history(game, "Narrator", "Teste", "narration", 1)
        assert len(game.history) == 1
        snapshot_door = game.history[0].scene_snapshot.physical_facts["door"]
        assert snapshot_door == "closed"
        # Modifica cena atual
        game.scene.physical_facts["door"] = "open"
        # Snapshot não foi afetado
        assert game.history[0].scene_snapshot.physical_facts["door"] == "closed"


class TestDynamicConfigAndPresets:
    """Testes para o novo sistema de configuração dinâmica e presets no servidor."""

    def setup_method(self) -> None:
        from src.store.presets import PRESETS_DIR

        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        self.temp_preset_name = "temp_test_preset"

    def teardown_method(self) -> None:
        from src.store.presets import delete_preset

        delete_preset(self.temp_preset_name)

    def test_config_load_creates_canonical_provider_defaults(self, tmp_path: Path) -> None:
        from src.config import load_config

        path = tmp_path / "config.json"
        cfg = load_config(path)

        assert cfg["active_provider"] == "llama_cpp"
        assert cfg["providers"]["llama_cpp"]["api_base"] == "http://localhost:8888/v1"
        assert cfg["providers"]["deepseek"]["model"] == "deepseek-v4-flash"
        assert cfg["providers"]["deepseek"]["thinking_enabled"] is False
        assert path.exists()

    def test_session_request_accepts_only_canonical_nested_characters(self) -> None:
        """The API has one preset/session character shape and no flat legacy branch."""
        from pydantic import ValidationError

        from src.main import StartSessionRequest

        canonical = {
            "mind": {
                "name": "Aria",
                "personality": "Direct and observant.",
                "knowledge": [],
                "current_mood": "calm",
            },
            "body": {
                "name": "Aria",
                "physical_description": "Tall",
                "outfit": "Travel coat",
            },
        }
        request = StartSessionRequest(characters={"C1": canonical})
        assert request.characters is not None
        assert request.characters["C1"].mind.name == "Aria"
        with pytest.raises(ValidationError):
            StartSessionRequest(characters={"C1": {"name": "legacy-flat"}})

    def test_presets_store_crud(self) -> None:
        """Verifica as operações de CRUD diretamente no presets store."""
        from src.store.presets import delete_preset, list_presets, load_preset, save_preset

        preset_data = {"test_key": "test_value"}
        save_preset(self.temp_preset_name, preset_data)

        presets = list_presets()
        assert self.temp_preset_name in presets

        loaded = load_preset(self.temp_preset_name)
        assert loaded == preset_data

        success = delete_preset(self.temp_preset_name)
        assert success is True
        assert self.temp_preset_name not in list_presets()

    @pytest.mark.asyncio
    async def test_concurrent_preset_writes_remain_complete(self) -> None:
        """Per-name locking keeps concurrent atomic writes as complete JSON documents."""
        from src.store.presets import load_user_preset, save_preset

        first = {"controlled_character_id": "C1", "characters": {"C1": {"version": 1}}}
        second = {"controlled_character_id": "C2", "characters": {"C2": {"version": 2}}}
        await asyncio.gather(
            asyncio.to_thread(save_preset, self.temp_preset_name, first),
            asyncio.to_thread(save_preset, self.temp_preset_name, second),
        )
        assert load_user_preset(self.temp_preset_name) in (first, second)

    def test_presets_defaults_fallback(self) -> None:
        """Built-ins são assets imutáveis e usam o mesmo formato canônico."""
        from src.store.presets import load_default, load_preset

        loaded = load_default("thorn-lyra")
        assert loaded is not None
        assert loaded == load_preset("thorn-lyra")
        assert loaded["controlled_character_id"] == "C1"
        assert set(loaded["characters"]["C1"]) == {"mind", "body"}


class TestLanguageConfiguration:
    """Testes para validação da injeção dinâmica de idioma no system prompt."""

    @pytest.mark.asyncio
    async def test_language_injection_with_existing_system_prompt(self, monkeypatch) -> None:
        """Verifica se a instrução de idioma é anexada ao system prompt existente."""
        import httpx

        from src.llm.client import chat_completion

        captured_payload = None

        async def mock_post(url, json, **kwargs):
            nonlocal captured_payload
            captured_payload = json
            req = httpx.Request("POST", url)
            mock_res = httpx.Response(
                200, json={"choices": [{"message": {"content": "Olá"}}]}, request=req
            )
            return mock_res

        client = httpx.AsyncClient()
        monkeypatch.setattr(client, "post", mock_post)

        messages = [
            {"role": "system", "content": "Você é o narrador."},
            {"role": "user", "content": "Olá"},
        ]

        await chat_completion(
            client=client,
            messages=messages,
            language="French",
        )

        assert captured_payload is not None
        msgs = captured_payload["messages"]
        assert msgs[0]["role"] == "system"
        assert "Você é o narrador.\n- Always respond and write in French." in msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_language_injection_without_system_prompt(self, monkeypatch) -> None:
        """Verifica se a instrução de idioma cria um novo system prompt se ausente."""
        import httpx

        from src.llm.client import chat_completion

        captured_payload = None

        async def mock_post(url, json, **kwargs):
            nonlocal captured_payload
            captured_payload = json
            req = httpx.Request("POST", url)
            mock_res = httpx.Response(
                200, json={"choices": [{"message": {"content": "Olá"}}]}, request=req
            )
            return mock_res

        client = httpx.AsyncClient()
        monkeypatch.setattr(client, "post", mock_post)

        messages = [
            {"role": "user", "content": "Olá"},
        ]

        await chat_completion(
            client=client,
            messages=messages,
            language="French",
        )

        assert captured_payload is not None
        msgs = captured_payload["messages"]
        assert msgs[0]["role"] == "system"
        assert "- Always respond and write in French." in msgs[0]["content"]
        assert "em dash" in msgs[0]["content"]
        assert msgs[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_dash_avoidance_injected_without_language(self, monkeypatch) -> None:
        """A instrução de evitar travessão/en dash é injetada mesmo sem `language`."""
        import httpx

        from src.llm.client import chat_completion

        captured_payload = None

        async def mock_post(url, json, **kwargs):
            nonlocal captured_payload
            captured_payload = json
            req = httpx.Request("POST", url)
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "Olá"}}]}, request=req
            )

        client = httpx.AsyncClient()
        monkeypatch.setattr(client, "post", mock_post)

        await chat_completion(
            client=client,
            messages=[{"role": "system", "content": "Você é o narrador."}],
        )

        assert captured_payload is not None
        content = captured_payload["messages"][0]["content"]
        assert "em dash" in content
        assert "Always respond and write in" not in content
        assert "—" not in content
        assert "–" not in content

    @pytest.mark.asyncio
    async def test_character_text_is_normalized_after_raw_response_is_logged(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import json as json_module

        from src.agents.character import act

        sid = generate_session_id()
        client = httpx.AsyncClient(base_url="http://localhost:8888")

        async def mock_post(url, json, **kwargs):  # noqa: ANN001, ANN202, A002, ARG001
            request = httpx.Request("POST", url)
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json_module.dumps(
                                    {
                                        "speech": "Wait — listen between doors 1–3.",
                                        "thought": None,
                                    }
                                )
                            }
                        }
                    ]
                },
                request=request,
            )

        monkeypatch.setattr(client, "post", mock_post)
        try:
            output = await act(
                client=client,
                character=_custom_char("Plain"),
                context="A sound.",
                history=[],
                characters={"C1": _custom_char("Plain")},
                controlled_id="C1",
                character_id="C1",
                config={},
                session_id=sid,
                turn_number=1,
            )

            assert output == {"speech": "Wait, listen between doors 1-3.", "thought": None}
            path = SESSIONS_DIR / f"{sid}.debug.jsonl"
            raw_entry = json.loads(path.read_text(encoding="utf-8"))
            assert json.loads(raw_entry["response"]) == {
                "speech": "Wait — listen between doors 1–3.",
                "thought": None,
            }
        finally:
            await client.aclose()
            delete_session(sid)

    def test_generated_text_normalization_is_idempotent(self) -> None:
        from src.llm.client import normalize_generated_text

        normalized = normalize_generated_text("One — two, range 1–3.")
        assert normalized == "One, two, range 1-3."
        assert normalize_generated_text(normalized) == normalized


class TestLLMObservability:
    """Regression coverage for structured debug-call diagnostics."""

    @pytest.mark.asyncio
    async def test_empty_timeout_error_keeps_type_repr_and_metrics(self, monkeypatch) -> None:
        from src.llm.client import chat_completion

        sid = generate_session_id()
        client = httpx.AsyncClient(base_url="http://localhost:8888")

        async def timeout_post(url, json, **kwargs):  # noqa: ANN001, ANN202, ARG001
            request = httpx.Request("POST", url)
            raise httpx.ReadTimeout("", request=request)

        monkeypatch.setattr(client, "post", timeout_post)
        try:
            with pytest.raises(httpx.ReadTimeout):
                await chat_completion(
                    client,
                    [{"role": "user", "content": "A measured prompt."}],
                    session_id=sid,
                    turn_number=14,
                    agent="narrator",
                )

            path = SESSIONS_DIR / f"{sid}.debug.jsonl"
            entry = json.loads(path.read_text(encoding="utf-8"))
            assert entry["error"]
            assert entry["error_type"] == "ReadTimeout"
            assert "ReadTimeout" in entry["error_repr"]
            assert entry["duration_ms"] >= 0
            assert entry["attempt_number"] == 1
            assert entry["prompt_chars"] > len("A measured prompt.")
            assert entry["prompt_estimated_tokens"] == entry["prompt_chars"] // 4
        finally:
            await client.aclose()
            delete_session(sid)

    @pytest.mark.asyncio
    async def test_structured_retry_logs_http_json_and_success_attempts(self, monkeypatch) -> None:  # noqa: ANN001
        from src.llm.client import chat_completion_json

        sid = generate_session_id()
        client = httpx.AsyncClient(base_url="http://localhost:8888")
        call_count = 0

        async def skip_retry_delay(delay: float) -> None:
            assert delay > 0

        async def sequenced_post(url, json, **kwargs):  # noqa: ANN001, ANN202, A002, ARG001
            nonlocal call_count
            call_count += 1
            request = httpx.Request("POST", url)
            if call_count == 1:
                return httpx.Response(503, text="busy", request=request)
            content = "not-json" if call_count == 2 else '{"result":"ok"}'
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": content}}],
                    "usage": {
                        "prompt_tokens": 20,
                        "prompt_tokens_details": {"cached_tokens": 12},
                    },
                },
                request=request,
            )

        monkeypatch.setattr(client, "post", sequenced_post)
        monkeypatch.setattr("src.llm.client.asyncio.sleep", skip_retry_delay)
        try:
            result = await chat_completion_json(
                client,
                [{"role": "user", "content": "Return JSON."}],
                retries=2,
                session_id=sid,
                turn_number=3,
                agent="narrator",
            )

            assert result == {"result": "ok"}
            path = SESSIONS_DIR / f"{sid}.debug.jsonl"
            entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            assert [entry["attempt_number"] for entry in entries] == [1, 2, 3]
            assert entries[0]["error_type"] == "HTTPStatusError"
            assert entries[0]["response"] is None
            assert entries[1]["error_type"] == "JSONDecodeError"
            assert entries[1]["response"] == "not-json"
            assert entries[2]["error"] is None
            assert entries[2]["response"] == '{"result":"ok"}'
            assert entries[2]["usage"]["prompt_tokens"] == 20
            assert entries[2]["prompt_cache"] == {"hit_tokens": 12, "miss_tokens": 8}
        finally:
            await client.aclose()
            delete_session(sid)

    @pytest.mark.asyncio
    async def test_concurrent_debug_markers_remain_complete_json_lines(self) -> None:
        from src.llm.debug_log import log_turn_input

        sid = generate_session_id()
        try:
            await asyncio.gather(
                *(
                    asyncio.to_thread(
                        log_turn_input, sid, index, "speech", "thought", "action", None, None
                    )
                    for index in range(1, 21)
                )
            )

            path = SESSIONS_DIR / f"{sid}.debug.jsonl"
            entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            assert len(entries) == 20
            assert {entry["turn_number"] for entry in entries} == set(range(1, 21))
            assert {entry["agent"] for entry in entries} == {"turn_input"}
        finally:
            delete_session(sid)

    def test_timeout_configuration_rejects_invalid_values(self) -> None:
        from src.llm.client import DEFAULT_LLM_TIMEOUT_SECONDS, resolve_llm_timeout

        assert resolve_llm_timeout({"llm_timeout_seconds": 12.5}) == 12.5
        assert resolve_llm_timeout({"llm_timeout_seconds": 0}) == DEFAULT_LLM_TIMEOUT_SECONDS
        assert resolve_llm_timeout({"llm_timeout_seconds": True}) == DEFAULT_LLM_TIMEOUT_SECONDS
        assert resolve_llm_timeout({"llm_timeout_seconds": "slow"}) == DEFAULT_LLM_TIMEOUT_SECONDS
