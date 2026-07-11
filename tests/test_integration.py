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
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    TurnState,
    deepcopy_scene,
    dict_to_game_state,
    game_state_to_dict,
)
from src.runner import Runner
from src.store.sessions import (
    SESSIONS_DIR,
    _get_lock,
    delete_session,
    fork_session,
    generate_session_id,
    list_sessions,
    load_game,
    save_game,
)

DEFAULT_CHARACTERS: dict[str, Character] = {
    "C1": Character(
        mind=CharacterMind(
            name="Thorn",
            personality_summary="Guerreiro estoico e leal. Fala pouco, age com decisão.",
            personality_full=(
                "Thorn é um guerreiro veterano de 40 anos que serviu na Guarda de Ferro "
                "por duas décadas. Estoico, leal até a morte, e desconfiado de magia. "
                "Fala em frases curtas e diretas. Protege os mais fracos por instinto. "
                "Carrega culpa por não ter salvo seu irmão mais novo numa emboscada anos atrás."
            ),
            knowledge=[
                "A Guarda de Ferro foi dissolvida há 3 anos",
                "A taverna do Velho Mork é um ponto de encontro de mercenários",
                "Lyra é uma maga que ele conheceu há 2 semanas",
            ],
            current_mood="cauteloso",
        ),
        body=CharacterBody(
            name="Thorn",
            physical_description="Alto, musculoso, cicatriz no queixo, cabelo grisalho curto",
            outfit="Armadura de couro reforçada, espada longa na cintura",
        ),
    ),
    "C2": Character(
        mind=CharacterMind(
            name="Lyra",
            personality_summary="Maga élfica curiosa e impulsiva. Fala demais quando nervosa.",
            personality_full=(
                "Lyra é uma maga élfica de 120 anos (jovem pra um elfo). Curiosa ao ponto "
                "de se meter em perigo. Impulsiva — age primeiro, pensa depois. Quando "
                "nervosa, fala sem parar. Tem um senso de humor sarcástico. Trata magia "
                "como ciência, não misticismo. Saiu da torre dos magos porque se entediou "
                "com teoria."
            ),
            knowledge=[
                "A floresta ao norte está corrompida por magia negra",
                "O medalhão que encontraram emite uma aura arcana fraca",
                "Thorn é um guerreiro que ela conheceu há 2 semanas",
            ],
            current_mood="curiosa",
        ),
        body=CharacterBody(
            name="Lyra",
            physical_description="Esguia, orelhas pontudas, olhos violeta, cabelo prateado longo",
            outfit="Túnica azul escura com runas bordadas, cajado de carvalho",
        ),
    ),
}

DEFAULT_SCENE = Scene(
    location="Taverna do Velho Mork — salão principal, meia-luz",
    time_of_day="noite",
    present_characters=["C1", "C2", "Player"],
    physical_facts={
        "lighting": "velas fracas",
        "crowd": "meia dúzia de bêbados",
        "weather_outside": "chuva forte",
        "door": "fechada",
    },
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

    # ── List / Fork / Delete ─────────────────────────────────────────

    def test_list_sessions_empty(self) -> None:
        """list_sessions retorna [] quando não há sessões."""
        # Limpa diretório temporário (apenas arquivos .json de teste)
        for f in SESSIONS_DIR.iterdir():
            if f.suffix == ".json":
                f.unlink()
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

    def test_fork_session(self) -> None:
        """fork_session copia sessão com novo ID."""
        original = _make_test_game(self.sid)
        history_item = TurnRecord(
            turn_number=1, speaker="Narrator", content="Teste",
            content_type="narration", scene_snapshot=copy.deepcopy(DEFAULT_SCENE),
        )
        original.history.append(history_item)
        save_game(original)

        new_id = fork_session(self.sid)
        assert new_id is not None
        assert new_id != self.sid

        loaded = load_game(new_id)
        assert loaded is not None
        assert loaded.session_id == new_id
        assert len(loaded.history) == 1
        assert loaded.history[0].content == "Teste"
        # Limpa
        delete_session(new_id)

    def test_fork_nonexistent(self) -> None:
        """fork_session em sessão inexistente retorna None."""
        assert fork_session("ffffffff") is None

    def test_fork_idempotent(self) -> None:
        """fork_session pode ser chamada 2x — cria 2 cópias distintas."""
        original = _make_test_game(self.sid)
        save_game(original)
        n1 = fork_session(self.sid)
        n2 = fork_session(self.sid)
        assert n1 is not None
        assert n2 is not None
        assert n1 != n2
        delete_session(n1)
        delete_session(n2)

    def test_delete_session(self) -> None:
        """delete_session remove o arquivo."""
        g = _make_test_game(self.sid)
        save_game(g)
        path = SESSIONS_DIR / f"{self.sid}.json"
        assert path.exists()
        delete_session(self.sid)
        assert not path.exists()

    def test_delete_nonexistent(self) -> None:
        """delete_session em ID inexistente não levanta erro."""
        delete_session("ffffffff")  # não deve levantar


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

    # ── Undo ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_undo_pending_options(self) -> None:
        """Undo em sessão pausada em options limpa pending_options."""
        sid = self.runner.start_session()
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            game.pending_options = [{"index": 0, "label": "Abrir porta", "description": "..."}]
            save_game(game)
        result = await self.runner.undo_turn(sid)
        assert result["undone"] is True
        # pending_options foi limpo
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert game.pending_options is None

    @pytest.mark.asyncio
    async def test_undo_simple_turn(self) -> None:
        """Undo de um turno com narrador apenas — history fica vazio, cena restaurada."""
        sid = self.runner.start_session()
        # Simula um turno: add narração ao histórico e atualiza cena
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            original_door = game.scene.physical_facts["door"]
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Você entra na taverna.", "narration")
            # Modifica cena após o turno
            game.scene.physical_facts["door"] = "aberta"
            save_game(game)

        result = await self.runner.undo_turn(sid)
        assert result["undone"] is True

        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 0
            assert game.scene.physical_facts["door"] == original_door

    @pytest.mark.asyncio
    async def test_undo_with_character(self) -> None:
        """Undo de turno com narrador + personagem remove ambos."""
        sid = self.runner.start_session()
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            original_door = game.scene.physical_facts["door"]
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "O vento uiva.", "narration")
            runner._append_history(game, "C1", "Não gosto disso.", "speech")
            game.scene.physical_facts["door"] = "aberta"
            save_game(game)

        result = await self.runner.undo_turn(sid)
        assert result["undone"] is True

        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 0
            assert game.scene.physical_facts["door"] == original_door

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
            runner._append_history(game, "Narrator", "Teste.", "narration")
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
            runner._append_history(game, "Narrator", "Turno 1.", "narration")
            game.scene.physical_facts["door"] = "entreaberta"
            save_game(game)

        # Turno 2
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 2.", "narration")
            runner._append_history(game, "C1", "Resposta 2.", "speech")
            game.scene.physical_facts["door"] = "aberta"
            save_game(game)

        # Turno 3
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 3.", "narration")
            game.scene.physical_facts["door"] = "escancarada"
            save_game(game)

        # Undo turno 3
        r = await self.runner.undo_turn(sid)
        assert r["undone"] is True
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 3  # Narrador 1 + Narrador 2 + C1
            assert game.scene.physical_facts["door"] == "aberta"

        # Undo turno 2
        r = await self.runner.undo_turn(sid)
        assert r["undone"] is True
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 1  # Narrador 1
            assert game.scene.physical_facts["door"] == "entreaberta"

        # Undo turno 1
        r = await self.runner.undo_turn(sid)
        assert r["undone"] is True
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 0
            assert game.scene.physical_facts["door"] == "fechada"  # original


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
                if result.get("type") == "options":
                    assert "options" in result
                    opt = result["options"][0]
                    result = await runner.player_turn(
                        session_id=sid,
                        chosen_option=opt["index"],
                    )
                assert "narration" in result
                assert result["narration"] is not None
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
# Testes — Config customizada + Debug (LLM mockado)
# ═══════════════════════════════════════════════════════════════════════════


def _custom_char(name: str, mood: str = "neutro") -> Character:
    from src.models import CharacterBody, CharacterMind

    return Character(
        mind=CharacterMind(
            name=name,
            personality_summary=f"{name} resumo",
            personality_full=f"{name} personalidade completa",
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
        sid = self.runner.start_session({
            "characters": chars,
            "scene": scene,
            "player_name": "Alex",
            "controlled_character_id": "C2",
            "narrator_directives": "Mundo de horror gótico. Tom sombrio.",
        })
        self.created.append(sid)
        return sid

    def test_start_session_custom_round_trip(self) -> None:
        """Personagens custom + narrator_directives fazem round-trip via load_game."""
        sid = self._start_custom()
        game = load_game(sid)
        assert game is not None
        assert set(game.characters) == {"C1", "C2", "C3"}
        assert game.characters["C1"].mind.name == "Aria"
        assert game.player.name == "Alex"
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
        with pytest.raises(ValueError, match="ao menos um personagem"):
            self.runner.start_session({"characters": {}})

    def test_start_session_invalid_controlled_fallback(self) -> None:
        """controlled_character_id inexistente cai no primeiro personagem."""
        sid = self.runner.start_session({
            "characters": {"C1": _custom_char("Solo")},
            "controlled_character_id": "C9",
        })
        self.created.append(sid)
        game = load_game(sid)
        assert game is not None
        assert game.player.controlled_character_id == "C1"

    def test_build_system_prompt_dynamic_ids_and_directives(self) -> None:
        """_build_system_prompt enumera IDs dinâmicos e anexa diretivas."""
        from src.agents.narrator import _build_system_prompt

        prompt = _build_system_prompt(["C1", "C2", "C3"], "Regras do mundo aqui.")
        assert "C1, C2, C3, Player, Narrator" in prompt
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
        result, messages = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(location="x", time_of_day="y", present_characters=[],
                        physical_facts={}),
            characters=chars,
            player_speech="oi",
            player_action="",
            player_controlled_id="C3",
            history=[],
            config={},
        )
        assert result["next_speaker"] == "C3"
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_valid_speakers_fallback_invalid(self, monkeypatch) -> None:  # noqa: ANN001
        """next_speaker inválido cai para Player."""
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "narration": "Algo acontece.",
                "next_speaker": "Fantasma",
                "context_for_character": "",
            }

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        result, _ = await narrator_mod.narrate(
            client=self.client,
            scene=Scene(location="x", time_of_day="y", present_characters=[],
                        physical_facts={}),
            characters={"C1": _custom_char("Solo")},
            player_speech="oi",
            player_action="",
            player_controlled_id="C1",
            history=[],
            config={},
        )
        assert result["next_speaker"] == "Player"

    @pytest.mark.asyncio
    async def test_player_turn_debug_returns_messages(self, monkeypatch) -> None:  # noqa: ANN001
        """player_turn(debug=True) retorna debug.narrator.messages não vazio."""
        from src.agents import character as character_mod
        from src.agents import narrator as narrator_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "narration": "A cripta range.",
                "next_speaker": "C1",
                "context_for_character": "Você ouve um rangido.",
            }

        async def fake_chat(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return "Estou pronto."

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        monkeypatch.setattr(character_mod, "chat_completion", fake_chat)

        sid = self.runner.start_session({"characters": {"C1": _custom_char("Solo")}})
        self.created.append(sid)
        result = await self.runner.player_turn(sid, speech="oi", debug=True)
        assert "debug" in result
        assert result["debug"]["narrator"]["messages"]
        assert result["debug"]["narrator"]["raw"]
        assert result["debug"]["character"] is not None
        assert result["debug"]["character"]["messages"]
        assert result["debug"]["character"]["raw"] == "Estou pronto."

    def test_preview_narrator_prompt(self) -> None:
        """preview_narrator_prompt monta messages corretos sem tocar no LLM."""
        sid = self._start_custom()
        messages = self.runner.preview_narrator_prompt(sid, speech="olá", action="acena")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        # IDs dinâmicos + diretivas no system prompt
        assert "C1, C2, C3, Player, Narrator" in messages[0]["content"]
        assert "horror gótico" in messages[0]["content"]
        # input do player no user prompt
        assert "olá" in messages[1]["content"]
        assert "acena" in messages[1]["content"]

    def test_preview_narrator_prompt_missing_session(self) -> None:
        """preview de sessão inexistente retorna lista vazia."""
        assert self.runner.preview_narrator_prompt("naoexiste") == []


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


class TestDynamicConfigAndPresets:
    """Testes para o novo sistema de configuração dinâmica e presets no servidor."""

    def setup_method(self) -> None:
        from src.store.presets import DEFAULTS_DIR, PRESETS_DIR
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.temp_preset_name = "temp_test_preset"
        self.temp_default_name = "temp_default_preset"

    def teardown_method(self) -> None:
        from src.store.presets import DEFAULTS_DIR, delete_preset
        delete_preset(self.temp_preset_name)
        # Limpa defaults temporários
        default_file = DEFAULTS_DIR / f"{self.temp_default_name}.json"
        if default_file.exists():
            default_file.unlink()

    def test_config_load_and_fallback(self) -> None:
        """Verifica se load_config carrega defaults e cria arquivo se inexistente."""
        from src.main import CONFIG_PATH, load_config

        existing_config = None
        if CONFIG_PATH.exists():
            existing_config = CONFIG_PATH.read_text(encoding="utf-8")
            CONFIG_PATH.unlink()

        try:
            cfg = load_config()
            assert cfg["llm_host"] == "http://localhost:8888"
            assert cfg["model"] == ""
            assert CONFIG_PATH.exists()
        finally:
            if existing_config is not None:
                CONFIG_PATH.write_text(existing_config, encoding="utf-8")

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

    def test_presets_defaults_fallback(self) -> None:
        """Verifica fallback para diretório de defaults no load_preset."""
        import json

        from src.store.presets import DEFAULTS_DIR, load_preset

        preset_data = {"characters": {}, "scene": {"location": "Lugar Padrão"}}
        default_file = DEFAULTS_DIR / f"{self.temp_default_name}.json"
        default_file.write_text(json.dumps(preset_data), encoding="utf-8")

        loaded = load_preset(self.temp_default_name)
        assert loaded == preset_data


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
            mock_res = httpx.Response(200, json={
                "choices": [{"message": {"content": "Olá"}}]
            })
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
            mock_res = httpx.Response(200, json={
                "choices": [{"message": {"content": "Olá"}}]
            })
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
        assert msgs[0]["content"] == "- Always respond and write in French."
        assert msgs[1]["role"] == "user"
