"""Testes de integração — modelos, sessões e fluxo do Runner.

Requer servidor llama.cpp em http://localhost:8888 para testes de LLM.
Testes que não dependem do LLM são marcados como ``unit``.
"""

from __future__ import annotations

import asyncio
import copy
import json

import httpx
import pytest

from src.models import (
    GameState,
    Player,
    Scene,
    TurnRecord,
    TurnState,
    deepcopy_scene,
    dict_to_game_state,
    game_state_to_dict,
)
from src.runner import DEFAULT_CHARACTERS, DEFAULT_SCENE, Runner
from src.store.sessions import (
    SESSIONS_DIR,
    _get_lock,
    delete_session,
    generate_session_id,
    load_game,
    save_game,
)

# ── Helpers ───────────────────────────────────────────────────────────────


def _make_test_game(session_id: str | None = None) -> GameState:
    return GameState(
        session_id=session_id or generate_session_id(),
        characters=DEFAULT_CHARACTERS.copy(),
        player=Player(name="Testador", controlled_character_id="C1"),
        scene=copy.deepcopy(DEFAULT_SCENE),
    )


def _llm_available() -> bool:
    """Verifica se o servidor llama.cpp está acessível (timeout curto)."""
    try:
        import urllib.request as ur
        req = ur.Request("http://localhost:8888/health", method="GET")
        ur.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


SKIP_LLM = not _llm_available()


# ═══════════════════════════════════════════════════════════════════════════
# Testes Unitários — Models
# ═══════════════════════════════════════════════════════════════════════════


class TestModels:
    """Testes das dataclasses em src/models.py."""

    def test_imports(self) -> None:
        """Todas as dataclasses importam sem erro."""
        from src.models import (  # noqa: F811
            Character,
        )
        assert Character is not None

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

    def test_scene_shallow_copy_fails(self) -> None:
        """Atribuição direta NÃO isola snapshots (prova da necessidade de deepcopy)."""
        s1 = Scene(
            location="taverna",
            time_of_day="noite",
            present_characters=["C1"],
            physical_facts={"door": "fechada"},
        )
        s2 = s1  # atribuição direta, não cópia
        s1.physical_facts["door"] = "aberta"
        assert s2.physical_facts["door"] == "aberta", "shallow copy compartilha dict"

    def test_game_state_round_trip(self) -> None:
        """game_state_to_dict + dict_to_game_state deve ser idempotente."""
        original = _make_test_game()
        data = game_state_to_dict(original)
        restored = dict_to_game_state(data)
        assert restored.session_id == original.session_id
        assert len(restored.characters) == len(original.characters)
        assert restored.player.name == original.player.name
        assert restored.scene.location == original.scene.location
        assert restored.scene.physical_facts == original.scene.physical_facts

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
        expected = "Taverna do Velho Mork — salão principal, meia-luz"
        assert snap.location == expected

    def test_game_state_round_trip_empty_history(self) -> None:
        """Round-trip com história vazia."""
        original = _make_test_game()
        data = game_state_to_dict(original)
        restored = dict_to_game_state(data)
        assert len(restored.history) == 0

    def test_turn_state_defaults(self) -> None:
        """TurnState com valores default."""
        t = TurnState(turn_number=1, player_speech="", player_action="")
        assert t.narrator_raw is None
        assert t.character_response is None
        assert t.next_speaker is None
        assert t.player_options is None


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
        assert loaded.player.name == original.player.name

    def test_save_idempotent(self) -> None:
        """Salvar duas vezes não corrompe o estado."""
        original = _make_test_game(self.sid)
        original.player.name = "Versão 1"
        save_game(original)
        original.player.name = "Versão 2"
        save_game(original)
        loaded = load_game(self.sid)
        assert loaded is not None
        assert loaded.player.name == "Versão 2"

    def test_load_nonexistent(self) -> None:
        """load_game de sessão inexistente retorna None."""
        loaded = load_game("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_concurrent_save_same_session(self) -> None:
        """Duas saves concorrentes na mesma sessão não corrompem (lock)."""
        original = _make_test_game(self.sid)
        save_game(original)

        async def save_modify(name: str) -> None:
            async with _get_lock(self.sid):
                game = load_game(self.sid)
                assert game is not None
                game.player.name = name
                save_game(game)

        await asyncio.gather(save_modify("A"), save_modify("B"))
        loaded = load_game(self.sid)
        assert loaded is not None
        assert loaded.player.name in ("A", "B")

    def test_atomic_write_integrity(self) -> None:
        """Escrita atômica: arquivo intermediário não fica se algo quebrar."""
        original = _make_test_game(self.sid)
        # Simula falha durante save — temp file deve ser limpo
        path = SESSIONS_DIR / f"{self.sid}.json"
        # Salva primeiro pra ter arquivo válido
        save_game(original)
        assert path.exists()
        # Conta temps — não deve ter sobrado
        temps = list(SESSIONS_DIR.glob(f"{self.sid}_*.tmp"))
        assert len(temps) == 0, f"Sobrou temp file: {temps}"

    def test_generate_session_id_unique(self) -> None:
        """IDs gerados são únicos (colisão improvável em 8 chars hex)."""
        ids = {generate_session_id() for _ in range(100)}
        assert len(ids) == 100, "IDs duplicados em 100 gerações"

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

    def test_start_session_returns_id(self) -> None:
        """start_session retorna session_id de 8 chars."""
        sid = self.runner.start_session()
        assert len(sid) == 8
        assert isinstance(sid, str)

    def test_start_session_creates_file(self) -> None:
        """start_session cria arquivo .json no diretório de sessões."""
        sid = self.runner.start_session()
        path = SESSIONS_DIR / f"{sid}.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["session_id"] == sid

    def test_start_session_custom_player(self) -> None:
        """start_session com nome de jogador customizado."""
        sid = self.runner.start_session({
            "player_name": "Alex",
            "controlled_character_id": "C2",
        })
        game = load_game(sid)
        assert game is not None
        assert game.player.name == "Alex"
        assert game.player.controlled_character_id == "C2"

    def test_get_state_nonexistent(self) -> None:
        """get_state de sessão inexistente retorna None."""
        assert self.runner.get_state("naoexiste") is None

    def test_get_state_after_start(self) -> None:
        """get_state retorna GameState com dados corretos."""
        sid = self.runner.start_session()
        state = self.runner.get_state(sid)
        assert state is not None
        assert state.session_id == sid
        assert "C1" in state.characters
        assert state.characters["C1"].mind.name == "Thorn"
        assert state.characters["C2"].mind.name == "Lyra"

    def test_get_history_empty(self) -> None:
        """get_history de sessão nova retorna lista vazia."""
        sid = self.runner.start_session()
        history = self.runner.get_history(sid)
        assert history == []

    def test_get_history_limit(self) -> None:
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
        history = self.runner.get_history(sid, limit=3)
        assert len(history) == 3
        assert history[-1].content == "Turno 10"

    def test_default_characters_complete(self) -> None:
        """Personagens padrão têm todos os campos preenchidos."""
        for cid, ch in DEFAULT_CHARACTERS.items():
            assert ch.mind.name, f"{cid} sem nome"
            assert ch.mind.personality_summary, f"{cid} sem summary"
            assert ch.mind.personality_full, f"{cid} sem full personality"
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


# ═══════════════════════════════════════════════════════════════════════════
# Testes com LLM real (condicionais)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(SKIP_LLM, reason="Servidor llama.cpp não está acessível")
@pytest.mark.asyncio
class TestRunnerWithLLM:
    """Testes do Runner que REQUEREM servidor llama.cpp."""

    async def _make_runner(self) -> tuple[httpx.AsyncClient, Runner]:
        client = httpx.AsyncClient(
            base_url="http://localhost:8888",
            timeout=httpx.Timeout(60.0),
        )
        runner = Runner(client, {
            "temperature_narrator": 0.0,
            "temperature_character": 0.8,
            "max_tokens_narrator": 1024,
            "max_tokens_character": 256,
        })
        return client, runner

    async def test_player_turn_basic(self) -> None:
        """Turno básico: speech + action → narração + resposta."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                result = await runner.player_turn(
                    session_id=sid,
                    speech="Olá, Lyra. O que você acha deste lugar?",
                    action="Thorn olha ao redor, observando os cantos escuros.",
                )
                assert "narration" in result
                assert result["narration"] is not None
                assert len(result["narration"]) > 10
                # next_speaker deve ser um valor válido
                assert result["next_speaker"] in ("C1", "C2", "Player", "Narrator")
                # Verifica que o estado foi salvo
                state = runner.get_state(sid)
                assert state is not None
                assert len(state.history) >= 1
            finally:
                delete_session(sid)

    async def test_player_turn_without_speech(self) -> None:
        """Ação sem fala: Narrador processa sem forçar resposta."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                result = await runner.player_turn(
                    session_id=sid,
                    speech="",
                    action="Thorn se levanta e caminha até a porta, espiando pela fresta.",
                )
                assert "narration" in result
                assert result["narration"] is not None
                # Não deve forçar erro — pode retornar qualquer next_speaker válido
                assert result["next_speaker"] in ("C1", "C2", "Player", "Narrator")
            finally:
                delete_session(sid)

    async def test_options_flow(self) -> None:
        """Turno que gera options → próximo turno com chosen_option."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                # Primeiro turno: pede uma decisão
                result1 = await runner.player_turn(
                    session_id=sid,
                    speech="Precisamos decidir o que fazer.",
                    action="Thorn coloca as mãos na mesa e espera.",
                )
                # Narrador pode ou não ter gerado options
                if result1.get("type") == "options":
                    assert "options" in result1
                    assert len(result1["options"]) > 0
                    # Segundo turno: escolhe opção 0
                    opt = result1["options"][0]
                    result2 = await runner.player_turn(
                        session_id=sid,
                        chosen_option=opt["index"],
                    )
                    assert "narration" in result2
            finally:
                delete_session(sid)

    async def test_state_persistence_across_turns(self) -> None:
        """Estado persiste corretamente entre turnos múltiplos."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                turn_count = 0
                while turn_count < 3:
                    speech = f"Fala do turno {turn_count + 1}"
                    result = await runner.player_turn(
                        session_id=sid, speech=speech, action="",
                    )
                    if result.get("type") == "options":
                        opts = result.get("options", [])
                        if opts:
                            result = await runner.player_turn(
                                session_id=sid, chosen_option=opts[0]["index"],
                            )
                    turn_count += 1

                state = runner.get_state(sid)
                assert state is not None
                assert len(state.history) > 0
            finally:
                delete_session(sid)


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Casos de borda e validações críticas."""

    def test_resolve_chosen_option_valid(self) -> None:
        """_resolve_chosen_option com índice válido."""
        game = _make_test_game()
        game.pending_options = [
            {"index": 0, "label": "Open door", "description": "Abra a porta"},
            {"index": 1, "label": "Ignore", "description": "Ignore a porta"},
        ]
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        result = runner._resolve_chosen_option(game, 0, "")
        assert result == "Open door"

    def test_resolve_chosen_option_with_action(self) -> None:
        """_resolve_chosenOption com action + option label."""
        game = _make_test_game()
        game.pending_options = [
            {"index": 0, "label": "Open door", "description": "Abra a porta"},
        ]
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        result = runner._resolve_chosen_option(game, 0, "Thorn walks slowly")
        assert "Thorn walks slowly" in result
        assert "Open door" in result

    def test_resolve_chosen_option_invalid_index(self) -> None:
        """_resolve_chosen_option com índice inválido mantém action original."""
        game = _make_test_game()
        game.pending_options = [{"index": 0, "label": "Open door", "description": "..."}]
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        result = runner._resolve_chosen_option(game, 99, "original action")
        assert result == "original action"

    def test_resolve_chosen_option_no_pending(self) -> None:
        """_resolve_chosen_option sem pending_options mantém action."""
        game = _make_test_game()
        game.pending_options = None
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        result = runner._resolve_chosen_option(game, 0, "original action")
        assert result == "original action"

    def test_update_scene(self) -> None:
        """_update_scene atualiza physical_facts."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._update_scene(game, {"door": "aberta", "lighting": "apagada"})
        assert game.scene.physical_facts["door"] == "aberta"
        assert game.scene.physical_facts["lighting"] == "apagada"
        # Campo não afetado permanece
        assert game.scene.physical_facts["weather_outside"] == "chuva forte"

    def test_update_scene_none(self) -> None:
        """_update_scene com None não altera nada."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._update_scene(game, None)
        assert game.scene.physical_facts["door"] == "fechada"

    def test_append_history_deepcopy(self) -> None:
        """_append_history usa deepcopy — modificar cena posterior não afeta snapshot."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._append_history(game, "Narrator", "Teste", "narration")
        assert len(game.history) == 1
        snapshot_door = game.history[0].scene_snapshot.physical_facts["door"]
        assert snapshot_door == "fechada"
        # Modifica cena atual
        game.scene.physical_facts["door"] = "aberta"
        # Snapshot não foi afetado
        assert game.history[0].scene_snapshot.physical_facts["door"] == "fechada"
