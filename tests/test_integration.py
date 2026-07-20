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
    session_backups_dir,
    session_debug_path,
    session_dir,
    session_state_path,
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


def _sec_headers() -> dict:
    from tests.conftest import sec_headers

    return sec_headers()


@pytest.fixture(autouse=True)
def _stub_perspective_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep legacy Runner tests isolated from new internal LLM boundaries."""
    import src.runner as runner_mod
    from src.models import CharacterPerspective, PersonView

    async def fake_initialize(
        client,
        viewer_id,
        characters,
        controlled_id,
        config,
        **kwargs,  # noqa: ANN001, ANN003
    ) -> CharacterPerspective:
        turn_number = kwargs.get("turn_number", 0)
        return CharacterPerspective(
            initialized_turn=turn_number,
            processed_through_turn=turn_number,
            people={
                character_id: PersonView(
                    known_name=character.mind.name,
                    reference=character.mind.name,
                    source_turn=turn_number,
                )
                for character_id, character in characters.items()
                if character_id != viewer_id
            },
        )

    async def fake_update(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
        return None

    async def fake_render_narration(*args, **kwargs) -> str:  # noqa: ANN002, ANN003
        return "Rendered narration."

    monkeypatch.setattr(runner_mod, "initialize_perspective", fake_initialize)
    monkeypatch.setattr(runner_mod, "update_identity", fake_update)
    monkeypatch.setattr(Runner, "_render_narration", fake_render_narration)


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
    import shutil

    directory = session_dir(session_id)
    if directory.exists():
        shutil.rmtree(directory)


def _perception_event(
    content: str,
    *witness_ids: str,
    subject_id: str = "Narrator",
) -> dict[str, object]:
    return {
        "event_kind": "observation",
        "subject_id": subject_id,
        "content": content,
        "witness_ids": list(witness_ids),
    }


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
        data = game_state_to_dict(original)
        restored = dict_to_game_state(data)
        assert restored.session_id == original.session_id
        assert len(restored.characters) == len(original.characters)
        assert restored.player.controlled_character_id == original.player.controlled_character_id
        assert restored.scene.location == original.scene.location
        assert restored.scene.physical_facts == original.scene.physical_facts
        assert restored.story_summary == original.story_summary

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

    def test_game_state_round_trip_with_presence_edit_stack(self) -> None:
        """presence_edit_stack sobrevive ao round-trip como CompactionStackEntry."""
        from src.models import PresenceEditEntry

        original = _make_test_game()
        original.presence_edit_stack.append(
            PresenceEditEntry(
                edit_id="e0000001",
                created_at="2026-01-01T00:00:00+00:00",
                origin="human",
                before=["C1", "C2", "Player"],
                after=["C1", "Player"],
                committed_revision=1,
            )
        )
        data = game_state_to_dict(original)
        restored = dict_to_game_state(data)
        assert len(restored.presence_edit_stack) == 1
        entry = restored.presence_edit_stack[0]
        assert entry.edit_id == "e0000001"
        assert entry.before == ["C1", "C2", "Player"]
        assert entry.after == ["C1", "Player"]
        assert entry.committed_revision == 1


class TestPresenceContract:
    """validate_present_characters / default_present_characters — src/models.py."""

    def test_default_present_characters_includes_everyone_and_player(self) -> None:
        from src.models import default_present_characters

        assert default_present_characters(DEFAULT_CHARACTERS) == ["C1", "C2", "Player"]

    def test_validate_accepts_a_well_formed_list(self) -> None:
        from src.models import validate_present_characters

        result = validate_present_characters(["C1", "C2", "Player"], DEFAULT_CHARACTERS, "C1")
        assert result == ["C1", "C2", "Player"]

    def test_validate_accepts_a_partial_list_when_controlled_stays_present(self) -> None:
        from src.models import validate_present_characters

        result = validate_present_characters(["C1", "Player"], DEFAULT_CHARACTERS, "C1")
        assert result == ["C1", "Player"]

    def test_validate_rejects_empty_list(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="empty"):
            validate_present_characters([], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_missing_player_marker(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="Player"):
            validate_present_characters(["C1", "C2"], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_player_marker_not_at_the_end(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="Player"):
            validate_present_characters(["Player", "C1", "C2"], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_duplicate_player_marker(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="Player"):
            validate_present_characters(["C1", "C2", "Player", "Player"], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_duplicate_character_id(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="duplicate"):
            validate_present_characters(["C1", "C1", "Player"], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_unknown_character_id(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="unknown"):
            validate_present_characters(["C1", "C9", "Player"], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_out_of_order_ids(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="canonical order"):
            validate_present_characters(["C2", "C1", "Player"], DEFAULT_CHARACTERS, "C1")

    def test_validate_rejects_absent_controlled_character(self) -> None:
        from src.models import validate_present_characters

        with pytest.raises(ValueError, match="controlled character"):
            validate_present_characters(["C2", "Player"], DEFAULT_CHARACTERS, "C1")


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

    def test_list_sessions_rejects_incompatible_schema_without_crashing(self) -> None:
        valid = _make_test_game()
        save_game(valid)
        legacy = game_state_to_dict(_make_test_game("legacy"))
        legacy.pop("compaction_stack")
        legacy_path = session_state_path("legacy")
        legacy_path.parent.mkdir(parents=True)
        legacy_path.write_text(json.dumps(legacy), encoding="utf-8")

        result = list_sessions()

        assert valid.session_id in {item["session_id"] for item in result}
        assert "legacy" not in {item["session_id"] for item in result}
        assert "compaction_stack" not in json.loads(legacy_path.read_text(encoding="utf-8"))

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
        path = session_state_path(self.sid)
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
        """Delete serializes with turns and removes state, log, and checkpoints."""
        save_game(_make_test_game(self.sid))
        session_debug_path(self.sid).write_text("{}\n", encoding="utf-8")
        backups = session_backups_dir(self.sid)
        backups.mkdir(parents=True)
        (backups / "compaction.c000001.json").write_text("{}", encoding="utf-8")
        lock = _get_lock(self.sid)
        await lock.acquire()
        task = asyncio.create_task(delete_session_async(self.sid))
        await asyncio.sleep(0)
        assert not task.done()
        lock.release()
        assert await task is True
        assert not session_dir(self.sid).exists()


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
        path = session_state_path(sid)
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
    async def test_undo_turn_restores_presence_changed_within_that_turn(self) -> None:
        """A narrator.result-style in-turn presence change is reverted by undo_turn.

        Unlike the admin presence_edit_stack, a Narrator-driven change is applied
        directly to the same-turn draft and captured by the ordinary scene_snapshot —
        undo_turn reverts it without any presence-specific code.
        """
        sid = self.runner.start_session()
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            original_present = list(game.scene.present_characters)
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Player", "oi", "speech", 1)
            runner._append_history(game, "Narrator", "C2 slips away.", "narration", 1)
            # Applied after the turn's history records, mirroring where narrator.result
            # runs in player_turn (after scene_update/mood_updates, before commit).
            game.scene.present_characters = ["C1", "Player"]
            save_game(game)

        persisted = load_game(sid)
        assert persisted is not None
        assert persisted.scene.present_characters == ["C1", "Player"]

        result = await self.runner.undo_turn(sid)
        assert result["undone"] is True

        restored = load_game(sid)
        assert restored is not None
        assert restored.scene.present_characters == original_present

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
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "zone_moves": None,
                "zone_link_updates": None,
                "return_control": False,
            }

        monkeypatch.setattr(runner_mod, "narrate", fake_narrate)

        game = _make_test_game()
        game.story_summary = "Resumo de teste."
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        await runner._call_narrator(game, 1)
        assert captured["story_summary"] == "Resumo de teste."

    @pytest.mark.asyncio
    async def test_call_narrator_forwards_plugin_extensions_to_narrate(self, monkeypatch) -> None:  # noqa: ANN001
        """_call_narrator threads narrator.context/schema results into narrate()."""
        from src import runner as runner_mod

        captured: dict = {}

        async def fake_narrate(**kwargs):  # noqa: ANN003, ANN202
            captured.update(kwargs)
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "zone_moves": None,
                "zone_link_updates": None,
                "return_control": False,
            }

        monkeypatch.setattr(runner_mod, "narrate", fake_narrate)

        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        await runner._call_narrator(
            game,
            1,
            extra_context=["PRESENCE: C2 stepped out."],
            extra_schema_properties={"presence_update": {"type": "object"}},
            extra_schema_required=["presence_update"],
        )
        assert captured["extra_context"] == ["PRESENCE: C2 stepped out."]
        assert captured["extra_schema_properties"] == {"presence_update": {"type": "object"}}
        assert captured["extra_schema_required"] == ["presence_update"]

    @pytest.mark.asyncio
    async def test_player_turn_collects_narrator_context_and_schema_hooks(  # noqa: ANN001
        self, monkeypatch
    ) -> None:
        """narrator.context/narrator.schema filters registered by a plugin reach _call_narrator."""
        from src.plugins.runtime import PluginRuntime

        plugins = PluginRuntime()

        def add_context(lines, _context):  # noqa: ANN001, ANN202
            lines.append("PRESENCE: C2 is elsewhere.")
            return lines

        def extend_schema(schema, _context):  # noqa: ANN001, ANN202
            schema["properties"]["presence_update"] = {
                "type": "object",
                "properties": {"present_character_ids": {"type": "array"}},
                "required": ["present_character_ids"],
                "additionalProperties": False,
            }
            schema["required"].append("presence_update")
            return schema

        plugins.hooks.register("dev.test.presence", "narrator.context", "filter", add_context)
        plugins.hooks.register("dev.test.presence", "narrator.schema", "filter", extend_schema)

        runner = Runner(self.client, {}, plugins=plugins)
        sid = runner.start_session()
        captured: dict = {}

        async def fake_call_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",  # noqa: ANN001
            extra_context=None,
            extra_schema_properties=None,
            extra_schema_required=None,  # noqa: ANN001
            exclude_controlled=True,  # noqa: ANN001
        ):
            captured["extra_context"] = extra_context
            captured["extra_schema_properties"] = extra_schema_properties
            captured["extra_schema_required"] = extra_schema_required
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "zone_moves": None,
                "zone_link_updates": None,
                "return_control": False,
            }

        monkeypatch.setattr(runner, "_call_narrator", fake_call_narrator)
        await runner.player_turn(sid, speech="Oi.")

        assert captured["extra_context"] == ["PRESENCE: C2 is elsewhere."]
        assert "presence_update" in captured["extra_schema_properties"]
        assert "presence_update" in captured["extra_schema_required"]
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_narrator_result_hook_applies_plugin_change_to_same_turn_draft(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        """narrator.result validates+applies its own key to the draft, same turn, under lock."""
        from src.plugins.runtime import PluginRuntime

        plugins = PluginRuntime()

        def apply_presence(game, context):  # noqa: ANN001, ANN202
            proposal = context["narrator_output"].get("presence_update")
            if proposal:
                game.scene.present_characters = [*proposal["present_character_ids"], "Player"]
            return game

        plugins.hooks.register("dev.test.presence", "narrator.result", "filter", apply_presence)

        runner = Runner(self.client, {}, plugins=plugins)
        sid = runner.start_session(
            {
                "characters": DEFAULT_CHARACTERS.copy(),
                "controlled_character_id": "C1",
            }
        )

        async def fake_call_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "presence_update": {"present_character_ids": ["C1"]},
            }

        monkeypatch.setattr(runner, "_call_narrator", fake_call_narrator)
        await runner.player_turn(sid, speech="Oi.")

        game = await runner.get_state(sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "Player"]
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_narrator_result_hook_can_discard_an_invalid_proposal_without_aborting_turn(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        """A plugin rejecting its own proposal returns the draft unchanged; turn still commits."""
        from src.plugins.runtime import PluginRuntime

        plugins = PluginRuntime()

        def reject_removing_controlled(game, context):  # noqa: ANN001, ANN202
            proposal = context["narrator_output"].get("presence_update")
            controlled = game.player.controlled_character_id
            if proposal and controlled not in proposal["present_character_ids"]:
                return game  # discarded — controlled character can never be removed
            if proposal:
                game.scene.present_characters = [*proposal["present_character_ids"], "Player"]
            return game

        plugins.hooks.register(
            "dev.test.presence", "narrator.result", "filter", reject_removing_controlled
        )

        runner = Runner(self.client, {}, plugins=plugins)
        sid = runner.start_session(
            {
                "characters": DEFAULT_CHARACTERS.copy(),
                "controlled_character_id": "C1",
            }
        )

        async def fake_call_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "presence_update": {"present_character_ids": ["C2"]},  # drops controlled C1
            }

        monkeypatch.setattr(runner, "_call_narrator", fake_call_narrator)
        result = await runner.player_turn(sid, speech="Oi.")

        assert result["narration"] == "Rendered narration."
        game = await runner.get_state(sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "Player"]  # unchanged
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_absent_next_speaker_never_receives_a_character_call(self, monkeypatch) -> None:  # noqa: ANN001
        """The Narrator routing to an absent character must not trigger a Character call."""
        sid = self.runner.start_session(
            {
                "characters": DEFAULT_CHARACTERS.copy(),
                "controlled_character_id": "C1",
                "scene": Scene(
                    location="Taverna",
                    time_of_day="noite",
                    present_characters=["C1", "Player"],  # C2 absent
                    physical_facts={},
                ),
            }
        )

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return {
                "next_speakers": ["C2"],  # hallucinated/absent — must be gated
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        async def forbidden_character(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            raise AssertionError("An absent character must never receive a Character call")

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_call_character", forbidden_character)

        result = await self.runner.player_turn(sid, speech="Oi.")
        assert result["character_responses"] == []
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_force_speaker_on_an_absent_character_falls_back_to_narrator_choice(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        """force_speaker naming an absent (but existing) character is ignored, not honored."""
        sid = self.runner.start_session(
            {
                "characters": DEFAULT_CHARACTERS.copy(),
                "controlled_character_id": "C1",
                "scene": Scene(
                    location="Taverna",
                    time_of_day="noite",
                    present_characters=["C1", "Player"],  # C2 absent
                    physical_facts={},
                ),
            }
        )

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN202
            assert forced_speaker is None  # C2 is absent, so the force is dropped
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "zone_moves": None,
                "zone_link_updates": None,
                "return_control": False,
            }

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        result = await self.runner.player_turn(sid, speech="Oi.", force_speaker="C2")
        assert result["next_speakers"] == ["Narrator"]
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_force_speaker_is_known_before_character_context_is_built(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        sid = self.runner.start_session()
        captured: dict[str, object] = {}

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["forced_speaker"] = forced_speaker
            return {
                "next_speakers": ["C1"],
                "perception_events": [
                    _perception_event(f"Context filtered for {forced_speaker}", "C2")
                ],
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["character_id"] = character_id
            captured["context"] = context
            return {"speech": "I answer.", "thought": None, "action_intent": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_call_character", fake_character)

        result = await self.runner.player_turn(
            sid,
            speech="Answer me.",
            force_speaker="C2",
        )

        assert result["next_speakers"] == ["C2"]
        assert captured == {
            "forced_speaker": "C2",
            "character_id": "C2",
            "context": "Context filtered for C2",
        }

        debug_path = session_debug_path(sid)
        markers = [json.loads(line) for line in debug_path.read_text(encoding="utf-8").splitlines()]
        assert markers[0]["agent"] == "turn_input"
        assert markers[0]["input"] == {
            "speech": "Answer me.",
            "thought": "",
            "action": "",
            "force_speaker": "C2",
            "narrator_hint": "",
            "skip": False,
        }
        assert markers[1]["agent"] == "turn_input_effective"
        assert markers[1]["effective_force_speaker"] == "C2"
        delete_session(sid)

    @pytest.mark.asyncio
    async def test_call_character_passes_own_perspective_only(self, monkeypatch) -> None:  # noqa: ANN001
        """_call_character repassa só a perspective do PRÓPRIO personagem."""
        from src import runner as runner_mod
        from src.models import CharacterPerspective

        captured: dict = {}

        async def fake_act(**kwargs):  # noqa: ANN003, ANN202
            captured.update(kwargs)
            return {"speech": "fala", "thought": None, "action_intent": None}

        monkeypatch.setattr(runner_mod, "character_act", fake_act)

        game = _make_test_game()
        own = CharacterPerspective(
            initialized_turn=0, processed_through_turn=0, recent_memory=["so minha memoria"]
        )
        other = CharacterPerspective(
            initialized_turn=0, processed_through_turn=0, recent_memory=["memoria alheia"]
        )
        game.character_perspectives = {"C1": own, "C2": other}
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        await runner._call_character(game, "C1", "ctx", 1)
        assert captured["viewer_perspective"] is own

    @pytest.mark.asyncio
    async def test_private_thought_only_turn_calls_narrator_without_leaking_thought(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        sid = self.runner.start_session()

        async def fake_narrator(game, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
            assert game.history[-1].content_type == "thought"
            assert game.history[-1].content == "Não devo demonstrar preocupação."
            return {
                "next_speakers": [],
                "perception_events": [
                    _perception_event("A chuva começa a bater nas janelas.", "C1")
                ],
                "scene_update": None,
                "mood_updates": None,
                "zone_moves": None,
                "zone_link_updates": None,
                "return_control": True,
            }

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A chuva começa a bater nas janelas."

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_render_narration", fake_prose)
        result = await self.runner.player_turn(
            sid,
            thought="Não devo demonstrar preocupação.",
        )
        game = await self.runner.get_state(sid)
        assert game is not None
        assert result["narration"] == "A chuva começa a bater nas janelas."
        assert [(record.content_type, record.content) for record in game.history] == [
            ("thought", "Não devo demonstrar preocupação."),
            ("narration", "A chuva começa a bater nas janelas."),
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
        for f in session_backups_dir(self.sid).glob("compaction.c*.json"):
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
            return "Resumo dos turnos antigos."

        monkeypatch.setattr(runner_mod, "summarize", fake_summarize)

    @pytest.mark.asyncio
    async def test_compact_below_window_does_nothing(self, monkeypatch) -> None:  # noqa: ANN001
        """Histórico menor ou igual à janela → compacted=False, nada muda no disco."""
        self._mock_summarize(monkeypatch)
        self._seed_history(5)  # 5 <= compaction_keep_recent_turns (8)

        result = await self.runner.compact_session(self.sid)
        assert result["compacted"] is False

        assert list(session_backups_dir(self.sid).glob("compaction.c*.json")) == []
        game = load_game(self.sid)
        assert game is not None
        assert len(game.history) == 10  # 5 passos * 2 registros, intocado

    @pytest.mark.asyncio
    async def test_compact_above_window_writes_incremental_checkpoint(
        self,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """Histórico maior que a janela produz um checkpoint incremental reversível."""
        self._mock_summarize(monkeypatch)
        self._seed_history(12)  # 12 passos, janela = 8 -> compacta os 4 mais antigos

        result = await self.runner.compact_session(self.sid)
        assert result["compacted"] is True
        assert result["compaction_id"] == "c000001"
        assert result["evicted_records"] == 8  # 4 passos evictados * 2 registros
        assert result["kept_records"] == 16  # 8 passos mantidos * 2 registros
        assert result["undo_depth"] == 1

        checkpoint_path = session_backups_dir(self.sid) / "compaction.c000001.json"
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        assert checkpoint["checkpoint_id"] == "c000001"
        assert checkpoint["parent_id"] is None
        assert len(checkpoint["evicted_history"]) == 8
        assert "characters" not in checkpoint

        # Sessão real foi reescrita: histórico menor, resumo/notas preenchidos
        game = load_game(self.sid)
        assert game is not None
        assert len(game.history) == 16
        assert game.history[0].turn_number == 5  # os 4 primeiros passos saíram
        assert game.story_summary == "Resumo dos turnos antigos."
        assert [entry.checkpoint_id for entry in game.compaction_stack] == ["c000001"]

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
    async def test_turn_after_compaction_uses_world_summary(self, monkeypatch) -> None:  # noqa: ANN001
        from src import runner as runner_mod

        async def fake_summarize(**kwargs):  # noqa: ANN003, ANN202
            return "Durable world summary."

        captured: dict[str, str] = {}

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["summary"] = game.story_summary
            return {
                "next_speakers": ["C2"],
                "perception_events": [_perception_event("The sealed gate is visible.", "C2")],
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202
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
        assert result["character_responses"] == [
            {"character_id": "C2", "speech": "I remember this gate.", "thought": None}
        ]
        assert captured == {
            "summary": "Durable world summary.",
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
        for f in session_backups_dir(self.sid).glob("compaction.c*.json"):
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
            return "Resumo."

        monkeypatch.setattr(runner_mod, "summarize", fake_summarize)

    @pytest.mark.asyncio
    async def test_restore_after_compaction_with_no_new_turns(self, monkeypatch) -> None:  # noqa: ANN001
        """Nada mudou desde a compactação: histórico volta e journal permanece."""
        self._mock_summarize(monkeypatch)
        self._seed_history(12)
        pre_compaction_bytes = (session_state_path(self.sid)).read_bytes()

        compact_result = await self.runner.compact_session(self.sid)
        assert compact_result["compacted"] is True

        result = await self.runner.restore_last_compaction(self.sid)
        assert result["restored"] is True
        assert result["history_length"] == 12

        restored_data = json.loads(session_state_path(self.sid).read_text(encoding="utf-8"))
        original_data = json.loads(pre_compaction_bytes)
        assert restored_data == {**original_data, "revision": original_data["revision"] + 2}
        assert restored_data["compaction_stack"] == []
        assert len(list(session_backups_dir(self.sid).glob("compaction.c*.json"))) == 1

    @pytest.mark.asyncio
    async def test_restore_preserves_new_turns_played_after_compaction(
        self,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """Jogadas posteriores sobrevivem ao undo do checkpoint."""
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
        result = await self.runner.restore_last_compaction(self.sid)
        assert result["restored"] is True
        assert result["preserved_through_turn"] == 13
        restored = load_game(self.sid)
        assert restored is not None
        assert [record.turn_number for record in restored.history] == list(range(1, 14))
        assert restored.history[-1].content == "Ação nova pós-compactação."
        assert len(list(session_backups_dir(self.sid).glob("compaction.c*.json"))) == 1

    @pytest.mark.asyncio
    async def test_restore_no_backup_available(self) -> None:
        """Sem nenhuma compactação feita -> recusa por falta de backup."""
        self._seed_history(3)
        result = await self.runner.restore_last_compaction(self.sid)
        assert result["restored"] is False
        assert "No compaction checkpoint" in result["reason"]

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
        """Checkpoints podem ser desfeitos em LIFO sem perder turnos posteriores."""
        self._mock_summarize(monkeypatch)
        self._seed_history(20)

        first_compact = await self.runner.compact_session(self.sid)
        assert first_compact["compacted"] is True  # evicta 1-12, mantém 13-20 (8 turnos)

        # Sem mais turnos, 8 <= janela(8) -> uma segunda compactação não faria
        # nada. Joga mais 12 pra passar da janela de novo antes de compactar.
        self._append_turns(12)
        second_compact = await self.runner.compact_session(self.sid)
        assert second_compact["compacted"] is True  # evicta 13-24, mantém 25-32
        assert second_compact["compaction_id"] == "c000002"
        assert len(list(session_backups_dir(self.sid).glob("compaction.c*.json"))) == 2

        # Restaura a compactação mais recente -> turnos 13-32 voltam.
        r1 = await self.runner.restore_last_compaction(self.sid)
        assert r1["restored"] is True
        assert r1["remaining_undo_depth"] == 1

        # O checkpoint anterior volta 1-12 e mantém 21-32 como cauda posterior.
        r2 = await self.runner.restore_last_compaction(self.sid)
        assert r2["restored"] is True
        assert r2["remaining_undo_depth"] == 0
        restored = load_game(self.sid)
        assert restored is not None
        assert [record.turn_number for record in restored.history] == list(range(1, 33))
        assert len(list(session_backups_dir(self.sid).glob("compaction.c*.json"))) == 2


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Mutação administrativa de presença (sem turno, sem LLM)
# ═══════════════════════════════════════════════════════════════════════════


class TestPresenceAdmin:
    """Runner.set_presence / undo_last_presence_edit — LIFO, revision, divergência."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, {})
        save_game(_make_test_game(self.sid))

    def teardown_method(self) -> None:
        delete_session(self.sid)

    @pytest.mark.asyncio
    async def test_set_presence_applies_and_pushes_stack_entry(self) -> None:
        result = await self.runner.set_presence(self.sid, ["C1", "Player"], expected_revision=0)
        assert result["changed"] is True
        assert result["present_characters"] == ["C1", "Player"]
        assert result["revision"] == 1
        game = load_game(self.sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "Player"]
        assert len(game.presence_edit_stack) == 1
        entry = game.presence_edit_stack[0]
        assert entry.origin == "human"
        assert entry.before == ["C1", "C2", "Player"]
        assert entry.after == ["C1", "Player"]
        assert entry.committed_revision == 1

    @pytest.mark.asyncio
    async def test_set_presence_rejects_stale_revision(self) -> None:
        from src.runner import PresenceRevisionConflictError

        with pytest.raises(PresenceRevisionConflictError):
            await self.runner.set_presence(self.sid, ["C1", "Player"], expected_revision=5)
        game = load_game(self.sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "Player"]
        assert game.revision == 0

    @pytest.mark.asyncio
    async def test_set_presence_rejects_removing_controlled_character(self) -> None:
        with pytest.raises(ValueError, match="controlled character"):
            await self.runner.set_presence(self.sid, ["C2", "Player"], expected_revision=0)
        game = load_game(self.sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "Player"]

    @pytest.mark.asyncio
    async def test_set_presence_rejects_unknown_character_id(self) -> None:
        with pytest.raises(ValueError, match="unknown"):
            await self.runner.set_presence(self.sid, ["C1", "C9", "Player"], expected_revision=0)

    @pytest.mark.asyncio
    async def test_undo_last_presence_edit_restores_previous_list(self) -> None:
        await self.runner.set_presence(self.sid, ["C1", "Player"], expected_revision=0)
        result = await self.runner.undo_last_presence_edit(self.sid)
        assert result["restored"] is True
        assert result["present_characters"] == ["C1", "C2", "Player"]
        assert result["remaining_undo_depth"] == 0
        game = load_game(self.sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "Player"]
        assert game.presence_edit_stack == []

    @pytest.mark.asyncio
    async def test_undo_with_empty_stack_is_a_no_op(self) -> None:
        result = await self.runner.undo_last_presence_edit(self.sid)
        assert result["restored"] is False
        assert "No presence edit" in result["reason"]
        game = load_game(self.sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "Player"]

    @pytest.mark.asyncio
    async def test_undo_is_strictly_lifo_across_two_edits(self) -> None:
        await self.runner.set_presence(self.sid, ["C1", "Player"], expected_revision=0)
        await self.runner.set_presence(self.sid, ["C1", "C2", "Player"], expected_revision=1)

        first_undo = await self.runner.undo_last_presence_edit(self.sid)
        assert first_undo["restored"] is True
        assert first_undo["present_characters"] == ["C1", "Player"]
        assert first_undo["remaining_undo_depth"] == 1

        second_undo = await self.runner.undo_last_presence_edit(self.sid)
        assert second_undo["restored"] is True
        assert second_undo["present_characters"] == ["C1", "C2", "Player"]
        assert second_undo["remaining_undo_depth"] == 0

    @pytest.mark.asyncio
    async def test_undo_rejects_when_presence_diverged_since(self) -> None:
        """A later change (e.g. a Narrator presence_update) must never be silently overwritten."""
        await self.runner.set_presence(self.sid, ["C1", "Player"], expected_revision=0)

        # Simulates a later, independent change to presence (e.g. applied by the
        # Narrator's narrator.result hook during a subsequent turn) that never
        # touched presence_edit_stack.
        game = load_game(self.sid)
        assert game is not None
        game.scene.present_characters = ["C1", "C2", "Player"]
        game.revision += 1
        save_game(game)

        result = await self.runner.undo_last_presence_edit(self.sid)
        assert result["restored"] is False
        assert "changed again" in result["reason"]
        game_after = load_game(self.sid)
        assert game_after is not None
        assert game_after.scene.present_characters == ["C1", "C2", "Player"]
        assert len(game_after.presence_edit_stack) == 1  # not popped

    @pytest.mark.asyncio
    async def test_set_presence_missing_session_returns_error(self) -> None:
        result = await self.runner.set_presence(
            "nonexistent", ["C1", "Player"], expected_revision=0
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_undo_missing_session_returns_error(self) -> None:
        result = await self.runner.undo_last_presence_edit("nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_set_presence_concurrent_with_turn_is_rejected_not_overwritten(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        """A turn committed between the client's read and its presence edit must win."""
        from src.runner import PresenceRevisionConflictError

        async def fake_narrator(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        # Client "read" revision 0, then a turn commits concurrently (revision -> 1).
        await self.runner.player_turn(self.sid, speech="Oi.")
        with pytest.raises(PresenceRevisionConflictError):
            await self.runner.set_presence(self.sid, ["C1", "Player"], expected_revision=0)
        game = load_game(self.sid)
        assert game is not None
        assert game.scene.present_characters == ["C1", "C2", "Player"]


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
        assert "C1, C2, C3" in prompt
        assert "Narration is rendered separately and is never a speaker." in prompt
        assert "DIALOGUE OWNERSHIP" in prompt
        assert '"scene_blocking": REQUIRED spatial draft' in prompt
        assert "SILENT SCENE BLOCKING" in prompt
        assert "1. PLACE EVERYONE." in prompt
        assert "5. ROUTE FROM PERCEPTION." in prompt
        assert 'Use ["Narrator"]' not in prompt
        assert "Player" not in prompt
        assert "Regras do mundo aqui." in prompt

    def test_build_system_prompt_no_directives(self) -> None:
        """Sem diretivas, não anexa o bloco de WORLD DIRECTIVES."""
        from src.agents.narrator import _build_system_prompt, build_narrator_json_schema

        prompt = _build_system_prompt(["C1"], "")
        assert "WORLD DIRECTIVES" not in prompt
        speakers = build_narrator_json_schema(["C1", "C2"])["schema"]["properties"][
            "next_speakers"
        ]["items"]["enum"]
        assert speakers == ["C1", "C2"]
        schema = build_narrator_json_schema(["C1", "C2"])["schema"]
        assert list(schema["properties"])[0] == "scene_blocking"
        assert schema["required"][0] == "scene_blocking"
        assert schema["properties"]["next_speakers"]["minItems"] == 0

    @pytest.mark.asyncio
    async def test_valid_speakers_accepts_custom_id(self, monkeypatch) -> None:  # noqa: ANN001
        """valid_speakers aceita IDs custom (C3) e não faz fallback."""
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "next_speakers": ["C3"],
                "perception_events": [_perception_event("ctx", "C3")],
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        chars = {"C3": _custom_char("Caius")}
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(
                location="x",
                time_of_day="y",
                present_characters=["C3", "Player"],
                physical_facts={},
            ),
            characters=chars,
            player_controlled_id="C3",
            history=[],
            config={},
        )
        assert result["next_speakers"] == ["C3"]

    @pytest.mark.asyncio
    async def test_valid_speakers_fallback_invalid(self, monkeypatch) -> None:  # noqa: ANN001
        """next_speaker inválido cai para Narrator (o Narrador não conhece "Player")."""
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "next_speakers": ["Fantasma"],
                "perception_events": [],
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(
                location="x",
                time_of_day="y",
                present_characters=["C1", "Player"],
                physical_facts={},
            ),
            characters={"C1": _custom_char("Solo")},
            player_controlled_id="C1",
            history=[],
            config={},
        )
        assert result["next_speakers"] == ["Narrator"]

    @pytest.mark.asyncio
    async def test_forced_speaker_constrains_schema_and_context_target(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import narrator as narrator_mod

        captured: dict[str, object] = {}

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            captured["messages"] = messages
            captured["json_schema"] = kwargs["json_schema"]
            return {
                "next_speakers": ["C1"],
                "perception_events": [_perception_event("Only C2 can perceive this.", "C2")],
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        result = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(
                location="x",
                time_of_day="y",
                present_characters=["C1", "C2", "Player"],
                physical_facts={},
            ),
            characters={"C1": _custom_char("One"), "C2": _custom_char("Two")},
            player_controlled_id="C1",
            history=[],
            config={},
            forced_speaker="C2",
        )

        schema = captured["json_schema"]
        assert isinstance(schema, dict)
        next_speakers = schema["schema"]["properties"]["next_speakers"]
        assert next_speakers["items"]["enum"] == ["C2"]
        assert next_speakers["minItems"] == 1
        assert next_speakers["maxItems"] == 3
        messages = captured["messages"]
        assert isinstance(messages, list)
        assert 'next_speakers is fixed as ["C2"]' in messages[1]["content"]
        assert "what C2 needs to react to" in messages[1]["content"]
        assert result["next_speakers"] == ["C2"]

    @pytest.mark.asyncio
    async def test_forced_narrator_collapses_queue(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
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

        assert result["next_speakers"] == ["Narrator"]
        assert result["perception_events"] == []

    @pytest.mark.asyncio
    async def test_debug_log_records_llm_calls(self, monkeypatch) -> None:  # noqa: ANN001
        """Cada chamada REAL ao LLM grava uma linha no log bruto .debug.jsonl da sessão.

        Mocka no nível de ``client.post`` (não em chat_completion_json/chat_completion)
        pra exercitar de verdade a interceptação em src/llm/client.py.
        """
        import json as json_module

        async def mock_post(url, json, **kwargs):  # noqa: ANN001, A002, ARG001
            schema_name = json.get("response_format", {}).get("json_schema", {}).get("name")
            if schema_name == "narrator_turn":
                content = json_module.dumps(
                    {
                        "scene_blocking": {
                            "character_zones": {"C1": "taverna", "C2": "taverna"},
                            "action_location": "taverna",
                            "spatial_constraints": [],
                            "destination_reachable_this_beat": True,
                        },
                        "next_speakers": ["C1"],
                        "perception_events": [_perception_event("Você ouve um rangido.", "C1")],
                        "scene_update": None,
                        "mood_updates": None,
                        "zone_moves": None,
                        "zone_link_updates": None,
                        "time_skip_ticks": 0,
                        "time_skip_summary": "",
                    }
                )
            else:
                content = json_module.dumps(
                    {"speech": "Estou pronto.", "thought": None, "action_intent": None}
                )
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
        assert result["character_responses"] == [
            {
                "character_id": "C1",
                "speech": "Estou pronto.",
                "thought": None,
                "action_intent": None,
            }
        ]

        debug_path = session_debug_path(sid)
        assert debug_path.exists()
        entries = [
            json_module.loads(line) for line in debug_path.read_text(encoding="utf-8").splitlines()
        ]
        assert len(entries) == 4  # input bruto, input efetivo, Narrador e Personagem
        assert entries[0]["session_id"] == sid
        assert entries[0]["turn_number"] == 1
        assert entries[0]["agent"] == "turn_input"
        assert entries[0]["input"]["speech"] == "oi"
        assert entries[1]["agent"] == "turn_input_effective"
        assert entries[1]["input"]["speech"] == "oi"
        assert entries[1]["transformed_fields"] == []
        assert entries[2]["agent"] == "director"
        assert entries[2]["response"] is not None
        assert entries[3]["agent"] == "character:Solo"
        assert json_module.loads(entries[3]["response"]) == {
            "speech": "Estou pronto.",
            "thought": None,
            "action_intent": None,
        }


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

    def test_summarizer_has_no_private_memory_surface(self) -> None:
        """Task 39 inc.2: o summarizer é world-only; nenhum parâmetro/prompt de
        notas privadas existe mais (a memória privada é o ledger)."""
        import inspect

        from src.agents import summarizer as summarizer_mod

        assert not hasattr(summarizer_mod, "build_private_memory_messages")
        assert "character_notes" not in str(inspect.signature(summarizer_mod.summarize))

    @pytest.mark.asyncio
    async def test_summarize_world_only_returns_summary(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import summarizer as summarizer_mod

        agents: list[str] = []

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            agents.append(kwargs["agent"])
            return {"story_summary": "Resumo atualizado."}

        monkeypatch.setattr(summarizer_mod, "chat_completion_json", fake_json)
        client = httpx.AsyncClient(base_url="http://localhost:8888")
        summary = await summarizer_mod.summarize(
            client=client,
            characters=DEFAULT_CHARACTERS,
            controlled_id="C1",
            story_summary="Resumo antigo.",
            evicted_turns=[],
            config={},
        )
        assert summary == "Resumo atualizado."
        assert agents == ["summarizer:world"]
        await client.aclose()

    def test_summarizer_schema_is_public_only(self) -> None:
        from src.agents.summarizer import build_summarizer_json_schema

        schema = build_summarizer_json_schema()["schema"]
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

    def test_format_history_for_character_sees_speech_actions_and_own_thought(self) -> None:
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
        assert "TYPE=ACTION | SPEAKER=Thorn: Thorn acena" in text  # ação testemunhada
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

    def test_narrator_prompt_includes_hint(self) -> None:
        """narrator_hint populates an UPCOMING EVENT section."""
        from src.agents.narrator import _build_user_prompt

        prompt = _build_user_prompt(
            scene=DEFAULT_SCENE,
            characters=DEFAULT_CHARACTERS,
            player_controlled_id="C1",
            history=[],
            narrator_hint="A storm approaches from the east.",
        )
        assert "UPCOMING EVENT" in prompt
        assert "A storm approaches from the east." in prompt

    def test_narrator_prompt_omits_hint_when_empty(self) -> None:
        """Empty narrator_hint does not pollute the prompt."""
        from src.agents.narrator import _build_user_prompt

        prompt = _build_user_prompt(
            scene=DEFAULT_SCENE,
            characters=DEFAULT_CHARACTERS,
            player_controlled_id="C1",
            history=[],
        )
        assert "UPCOMING EVENT" not in prompt

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

    def test_narrator_prompt_receives_thoughts_labeled_private(self) -> None:
        """Task 41: the Director is omniscient — thoughts arrive, explicitly
        labeled as private, so it can shape timing/pressure without ever
        staging their content (deterministic guard + prompt rules)."""
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
        assert "Segredo do Thorn." in prompt
        thought_line = next(ln for ln in prompt.splitlines() if "Segredo do Thorn." in ln)
        assert "PRIVATE THOUGHT" in thought_line
        assert "only you perceive this" in thought_line
        assert "Pode me ouvir?" in prompt

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (
                {"speech": "Olá.", "thought": None},
                {"speech": "Olá.", "thought": None, "action_intent": None},
            ),
            (
                {"speech": None, "thought": "Isso parece errado."},
                {"speech": None, "thought": "Isso parece errado.", "action_intent": None},
            ),
            (
                {"speech": "Olá.", "thought": "Preciso ter cuidado."},
                {"speech": "Olá.", "thought": "Preciso ter cuidado.", "action_intent": None},
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
                {"speech": "Oi.", "thought": "Inclino a cabeça.", "action_intent": None},
                {"speech": "Oi.", "thought": "Ele parece cansado para mim.", "action_intent": None},
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
        assert output == {
            "speech": "Oi.",
            "thought": "Ele parece cansado para mim.",
            "action_intent": None,
        }

    def test_character_prompt_includes_ledger_memory(self) -> None:
        """A memória do ledger vira a linha 'What you remember' no prompt."""
        from src.agents.character import _build_user_prompt

        thorn = DEFAULT_CHARACTERS["C1"]
        prompt = _build_user_prompt(
            "Contexto.",
            "(none)",
            thorn.mind.current_mood,
            ledger_memory="Ficou tenso ao ouvir sobre a Guarda de Ferro.",
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
            "Contexto.",
            "(none)",
            thorn.mind.current_mood,
            ledger_memory="Memoria exclusiva do Thorn.",
        )
        assert "Memoria exclusiva do Thorn." in prompt
        assert "memoria da Lyra" not in prompt  # nunca foi passada, nem podia vazar

    def test_character_prompt_marks_empty_notes_explicitly(self) -> None:
        """Sem nota, o estado privado explicita que ainda não há memória compactada."""
        from src.agents.character import _build_user_prompt

        thorn = DEFAULT_CHARACTERS["C1"]
        prompt = _build_user_prompt("Contexto.", "(none)", thorn.mind.current_mood)
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

    @pytest.mark.asyncio
    async def test_narrator_hint_propagates_to_narrator(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # noqa: ANN001
        """narrator_hint passado no player_turn chega ao _call_narrator."""

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["narrator_hint"] = narrator_hint
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        sid = runner.start_session()
        try:
            await runner.player_turn(
                session_id=sid,
                speech="Hello.",
                narrator_hint="A storm approaches from the east.",
            )
            assert captured.get("narrator_hint") == "A storm approaches from the east."
        finally:
            delete_session(sid)

    @pytest.mark.asyncio
    async def test_narrator_hint_only_turn_no_speech(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """narrator_hint como único conteúdo do turno não é rejeitado e chega ao narrador."""
        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["narrator_hint"] = narrator_hint
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        sid = runner.start_session()
        try:
            await runner.player_turn(
                session_id=sid,
                narrator_hint="Wind picks up.",
            )
            assert captured.get("narrator_hint") == "Wind picks up."
            assert captured.get("narrator_hint")  # non-empty
        finally:
            delete_session(sid)

    def test_pydantic_turn_request_accepts_narrator_hint(self) -> None:
        """PlayerTurnRequest deserializa narrator_hint e skip corretamente."""
        from src.main import PlayerTurnRequest

        body = PlayerTurnRequest(
            narrator_hint="Something is coming.",
        )
        assert body.narrator_hint == "Something is coming."
        assert body.skip is False

    def test_pydantic_turn_request_accepts_skip_without_content(self) -> None:
        """PlayerTurnRequest com skip=true não precisa de speech/thought/action/hint."""
        from src.main import PlayerTurnRequest

        body = PlayerTurnRequest(skip=True)
        assert body.skip is True
        # não levanta — skip=true bypassa o validator

    def test_pydantic_turn_request_rejects_empty(self) -> None:
        """PlayerTurnRequest totalmente vazio ainda é rejeitado."""
        from src.main import PlayerTurnRequest

        with pytest.raises(ValueError, match="needs speech, thought, action, or narrator_hint"):
            PlayerTurnRequest()

    def test_pydantic_turn_request_logs_narrator_hint(self) -> None:
        """PlayerTurnRequest com narrator_hint preenche o campo no debug log input."""
        from src.main import PlayerTurnRequest

        body = PlayerTurnRequest(narrator_hint="A storm approaches.")
        assert body.narrator_hint == "A storm approaches."

    def test_pydantic_turn_request_rejects_unknown_field(self) -> None:
        """Campo desconhecido é rejeitado por extra='forbid'."""
        from pydantic import ValidationError

        from src.main import PlayerTurnRequest

        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            PlayerTurnRequest(**{"speech": "Hi", "narrator_hnit": "typo"})

    def test_pydantic_turn_request_rejects_skip_with_speech(self) -> None:
        """skip=True + speech lança erro."""
        from src.main import PlayerTurnRequest

        with pytest.raises(ValueError, match="skip=True cannot be combined"):
            PlayerTurnRequest(skip=True, speech="Don't ignore me")

    def test_pydantic_turn_request_rejects_skip_with_thought(self) -> None:
        """skip=True + thought lança erro."""
        from src.main import PlayerTurnRequest

        with pytest.raises(ValueError, match="skip=True cannot be combined"):
            PlayerTurnRequest(skip=True, thought="I think")

    def test_pydantic_turn_request_rejects_skip_with_action(self) -> None:
        """skip=True + action lança erro."""
        from src.main import PlayerTurnRequest

        with pytest.raises(ValueError, match="skip=True cannot be combined"):
            PlayerTurnRequest(skip=True, action="Move")

    def test_pydantic_turn_request_accepts_skip_with_hint(self) -> None:
        """skip=True + narrator_hint é aceito."""
        from src.main import PlayerTurnRequest

        body = PlayerTurnRequest(skip=True, narrator_hint="Storm passes.")
        assert body.skip is True
        assert body.narrator_hint == "Storm passes."


class TestHttpBoundary:
    """Testes da fronteira HTTP com ASGITransport — Pydantic → route → Runner."""

    @pytest.mark.asyncio
    async def test_hint_only_reaches_runner(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """narrator_hint como único conteúdo via HTTP chega ao Runner."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["narrator_hint"] = narrator_hint
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            # Start session
            start_resp = await http.post("/session/start", json={})
            assert start_resp.status_code == 200
            sid = start_resp.json()["session_id"]

            # Turn with only narrator_hint
            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={"narrator_hint": "A storm approaches."},
            )
            assert turn_resp.status_code == 200
            await llm_client.aclose()

        delete_session(sid)
        assert captured.get("narrator_hint") == "A storm approaches."

    @pytest.mark.asyncio
    async def test_skip_only_reaches_runner(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """skip=true via HTTP chega ao Runner."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["called"] = True
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {"auto_event_enabled": False})
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={"skip": True},
            )
            assert turn_resp.status_code == 200
            await llm_client.aclose()

        delete_session(sid)
        assert captured.get("called") is True

    @pytest.mark.asyncio
    async def test_action_and_hint_via_http(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """action + narrator_hint via HTTP: ambos chegam ao Runner."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["narrator_hint"] = narrator_hint
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={
                    "action": "Draws sword",
                    "narrator_hint": "A bird screeches.",
                },
            )
            assert turn_resp.status_code == 200
            await llm_client.aclose()

        delete_session(sid)
        assert captured.get("narrator_hint") == "A bird screeches."

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self) -> None:
        """POST /session/X/turn com body vazio retorna 422."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={},
            )
            assert turn_resp.status_code == 422
            await llm_client.aclose()

        delete_session(sid)

    @pytest.mark.asyncio
    async def test_unknown_field_returns_422(self) -> None:
        """Campo desconhecido no body do turn retorna 422 (extra='forbid')."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={"speech": "Hi", "narrator_hnit": "typo"},
            )
            assert turn_resp.status_code == 422
            await llm_client.aclose()

        delete_session(sid)

    @pytest.mark.asyncio
    async def test_skip_with_speech_returns_422(self) -> None:
        """skip=true + speech retorna 422."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={"skip": True, "speech": "Don't ignore me"},
            )
            assert turn_resp.status_code == 422
            await llm_client.aclose()

        delete_session(sid)

    @pytest.mark.asyncio
    async def test_skip_with_hint_is_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """skip=true + narrator_hint é aceito (422-free)."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["narrator_hint"] = narrator_hint
            captured["called"] = True
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={"skip": True, "narrator_hint": "Storm fades."},
            )
            assert turn_resp.status_code == 200
            await llm_client.aclose()

        delete_session(sid)
        assert captured.get("called") is True
        assert captured.get("narrator_hint") == "Storm fades."

    @pytest.mark.asyncio
    async def test_thought_with_hint_calls_narrator(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """thought + narrator_hint NÃO faz early return — Narrador é chamado."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["narrator_hint"] = narrator_hint
            captured["called"] = True
            return {
                "next_speakers": ["C1"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={
                    "thought": "I am afraid.",
                    "narrator_hint": "A storm begins.",
                },
            )
            assert turn_resp.status_code == 200
            await llm_client.aclose()

        delete_session(sid)
        assert captured.get("called") is True
        assert captured.get("narrator_hint") == "A storm begins."

    @pytest.mark.asyncio
    async def test_hint_only_with_force_speaker(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
        """hint-only + force_speaker preserva o speaker via HTTP."""
        from src.main import RuntimeState, app
        from src.runner import Runner

        captured: dict[str, object] = {}

        async def fake_narrator(
            game,
            turn_number,
            forced_speaker=None,
            narrator_hint="",
            **kwargs,  # noqa: ANN001, ANN003, ANN202
        ) -> dict:
            captured["forced_speaker"] = forced_speaker
            captured["narrator_hint"] = narrator_hint
            return {
                "next_speakers": ["C1"],
                "perception_events": [_perception_event("Lyra approaches you.", "C2")],
                "scene_update": None,
                "mood_updates": None,
            }

        llm_client = httpx.AsyncClient()
        runner = Runner(llm_client, {})
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)

        async def fake_character(
            game,
            character_id,
            context,
            turn_number,  # noqa: ANN001, ANN202
            **kwargs,  # noqa: ANN003
        ) -> dict:
            return {"speech": "Yes?", "thought": None}

        monkeypatch.setattr(runner, "_call_character", fake_character)
        app.state.runtime = RuntimeState(
            stored_config={"provider": "llama_cpp", "providers": {"llama_cpp": {}}},
            server_config={},
            llm_client=llm_client,
            runner=runner,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            start_resp = await http.post("/session/start", json={})
            sid = start_resp.json()["session_id"]

            turn_resp = await http.post(
                f"/session/{sid}/turn",
                json={
                    "narrator_hint": "Lyra enters.",
                    "force_speaker": "C2",
                },
            )
            assert turn_resp.status_code == 200, turn_resp.json()
            await llm_client.aclose()

        delete_session(sid)
        assert captured.get("forced_speaker") == "C2"
        assert captured.get("narrator_hint") == "Lyra enters."

    @pytest.mark.asyncio
    async def test_version_endpoint(self) -> None:
        """GET /version retorna a informação do commit hash do git."""
        from src.main import app

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=_sec_headers()
        ) as http:
            resp = await http.get("/version")
            assert resp.status_code == 200
            data = resp.json()
            assert "commit" in data
            assert isinstance(data["commit"], str)


class TestDynamicConfigAndScenarios:
    """Testes para o novo sistema de configuração dinâmica e scenarios no servidor."""

    def setup_method(self) -> None:
        from src.store.scenarios import SCENARIOS_DIR

        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        self.temp_scenario_name = "temp_test_scenario"

    def teardown_method(self) -> None:
        from src.store.scenarios import delete_scenario

        delete_scenario(self.temp_scenario_name)

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
        """The API has one scenario/session character shape and no flat legacy branch."""
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

    def test_scenarios_store_crud(self) -> None:
        """Verifica as operações de CRUD diretamente no scenarios store."""
        from src.store.scenarios import (
            delete_scenario,
            list_scenarios,
            load_scenario,
            save_scenario,
        )

        scenario_data = {"test_key": "test_value"}
        save_scenario(self.temp_scenario_name, scenario_data)

        scenarios = list_scenarios()
        assert self.temp_scenario_name in scenarios

        loaded = load_scenario(self.temp_scenario_name)
        assert loaded == scenario_data

        success = delete_scenario(self.temp_scenario_name)
        assert success is True
        assert self.temp_scenario_name not in list_scenarios()

    @pytest.mark.asyncio
    async def test_concurrent_scenario_writes_remain_complete(self) -> None:
        """Per-name locking keeps concurrent atomic writes as complete JSON documents."""
        from src.store.scenarios import load_user_scenario, save_scenario

        first = {"controlled_character_id": "C1", "characters": {"C1": {"version": 1}}}
        second = {"controlled_character_id": "C2", "characters": {"C2": {"version": 2}}}
        await asyncio.gather(
            asyncio.to_thread(save_scenario, self.temp_scenario_name, first),
            asyncio.to_thread(save_scenario, self.temp_scenario_name, second),
        )
        assert load_user_scenario(self.temp_scenario_name) in (first, second)

    def test_scenarios_defaults_fallback(self) -> None:
        """Built-ins são assets imutáveis e usam o mesmo formato canônico."""
        from src.store.scenarios import load_builtin_scenario, load_scenario

        loaded = load_builtin_scenario("thorn-lyra")
        assert loaded is not None
        assert loaded == load_scenario("thorn-lyra")
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
                                        "action_intent": None,
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

            assert output == {
                "speech": "Wait, listen between doors 1-3.",
                "thought": None,
                "action_intent": None,
            }
            path = session_debug_path(sid)
            raw_entry = json.loads(path.read_text(encoding="utf-8"))
            assert json.loads(raw_entry["response"]) == {
                "speech": "Wait — listen between doors 1–3.",
                "thought": None,
                "action_intent": None,
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

            path = session_debug_path(sid)
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
            path = session_debug_path(sid)
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

            path = session_debug_path(sid)
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
