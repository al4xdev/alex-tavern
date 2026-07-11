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
            personality=(
                "Guerreiro estoico e leal. Fala pouco, age com decisão.\n\n"
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
            personality=(
                "Maga élfica curiosa e impulsiva. Fala demais quando nervosa.\n\n"
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
        player=Player(controlled_character_id="C1"),
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

    def test_game_state_load_legacy_without_compaction_fields(self) -> None:
        """Sessão salva antes desta task (sem story_summary/character_notes) carrega
        com os defaults vazios, sem KeyError."""
        original = _make_test_game()
        data = game_state_to_dict(original)
        del data["story_summary"]
        del data["character_notes"]
        restored = dict_to_game_state(data)
        assert restored.story_summary == ""
        assert restored.character_notes == {}

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

    @pytest.mark.asyncio
    async def test_concurrent_save_same_session(self) -> None:
        """Duas saves concorrentes na mesma sessão não corrompem (lock)."""
        original = _make_test_game(self.sid)
        save_game(original)

        async def save_modify(name: str) -> None:
            async with _get_lock(self.sid):
                game = load_game(self.sid)
                assert game is not None
                game.player.controlled_character_id = name
                save_game(game)

        await asyncio.gather(save_modify("A"), save_modify("B"))
        loaded = load_game(self.sid)
        assert loaded is not None
        assert loaded.player.controlled_character_id in ("A", "B")

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
        """start_session com personagem controlado customizado."""
        sid = self.runner.start_session({
            "controlled_character_id": "C2",
        })
        game = load_game(sid)
        assert game is not None
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
            game.characters["C1"].mind.current_mood = "furioso"
            game.scene.physical_facts["door"] = "aberta"
            save_game(game)

        result = await self.runner.undo_turn(sid)
        assert result["undone"] is True

        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            assert len(game.history) == 0, "todos os 4 registros do passo devem sumir"
            assert game.characters["C1"].mind.current_mood == original_mood_c1
            assert game.scene.physical_facts["door"] == "fechada"

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
            runner._append_history(game, "Narrator", "Você entra na taverna.", "narration", 1)
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
            runner._append_history(game, "Narrator", "O vento uiva.", "narration", 1)
            runner._append_history(game, "C1", "Não gosto disso.", "speech", 1)
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
            game.scene.physical_facts["door"] = "entreaberta"
            save_game(game)

        # Turno 2
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 2.", "narration", 2)
            runner._append_history(game, "C1", "Resposta 2.", "speech", 2)
            game.scene.physical_facts["door"] = "aberta"
            save_game(game)

        # Turno 3
        async with _get_lock(sid):
            game = load_game(sid)
            assert game is not None
            runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
            runner._append_history(game, "Narrator", "Turno 3.", "narration", 3)
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
@pytest.mark.llm
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
                # next_speaker deve ser um valor válido (o Narrador não conhece "Player")
                assert result["next_speaker"] in ("C1", "C2", "Narrator")
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
                assert result["next_speaker"] in ("C1", "C2", "Narrator")
            finally:
                delete_session(sid)

    async def test_force_speaker_overrides_narrator(self) -> None:
        """force_speaker faz o personagem indicado agir, mesmo que não-controlado."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                result = await runner.player_turn(
                    session_id=sid,
                    speech="Precisamos decidir o que fazer.",
                    action="Thorn coloca as mãos na mesa e espera.",
                    force_speaker="C2",
                )
                assert "narration" in result
                assert result["next_speaker"] == "C2"
                assert result["character_response"]
            finally:
                delete_session(sid)

    async def test_suggest_actions(self) -> None:
        """suggest_actions devolve sugestões pro personagem controlado sem persistir nada."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                state_before = runner.get_state(sid)
                assert state_before is not None
                result = await runner.suggest_actions(sid)
                assert "suggestions" in result
                assert len(result["suggestions"]) == 3
                for s in result["suggestions"]:
                    assert "speech" in s
                    assert "action" in s
                # suggest_actions não grava nada na sessão
                state_after = runner.get_state(sid)
                assert state_after is not None
                assert len(state_after.history) == len(state_before.history)
            finally:
                delete_session(sid)

    async def test_state_persistence_across_turns(self) -> None:
        """Estado persiste corretamente entre turnos múltiplos."""
        client, runner = await self._make_runner()
        async with client:
            sid = runner.start_session()
            try:
                for turn_count in range(3):
                    speech = f"Fala do turno {turn_count + 1}"
                    await runner.player_turn(session_id=sid, speech=speech, action="")

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
        sid = self.runner.start_session({
            "characters": chars,
            "scene": scene,
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
            scene=Scene(location="x", time_of_day="y", present_characters=[],
                        physical_facts={}),
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
            scene=Scene(location="x", time_of_day="y", present_characters=[],
                        physical_facts={}),
            characters={"C1": _custom_char("Solo")},
            player_controlled_id="C1",
            history=[],
            config={},
        )
        assert result["next_speaker"] == "Narrator"

    @pytest.mark.asyncio
    async def test_debug_log_records_llm_calls(self, monkeypatch) -> None:  # noqa: ANN001
        """Cada chamada REAL ao LLM grava uma linha no log bruto .debug.jsonl da sessão.

        Mocka no nível de ``client.post`` (não em chat_completion_json/chat_completion)
        pra exercitar de verdade a interceptação em src/llm/client.py.
        """
        import json as json_module

        from src.store.sessions import SESSIONS_DIR

        async def mock_post(url, json, **kwargs):  # noqa: ANN001, A002, ARG001
            if json.get("response_format", {}).get("type") == "json_schema":
                content = json_module.dumps({
                    "narration": "A cripta range.",
                    "next_speaker": "C1",
                    "context_for_character": "Você ouve um rangido.",
                    "scene_update": None,
                    "mood_updates": None,
                })
            else:
                content = "Estou pronto."
            req = httpx.Request("POST", url)
            return httpx.Response(
                200, json={"choices": [{"message": {"content": content}}]}, request=req
            )

        monkeypatch.setattr(self.client, "post", mock_post)

        # next_speaker="C1" precisa ser diferente do controlado, senão o
        # runner pausa (agência do jogador) em vez de chamar o Personagem.
        sid = self.runner.start_session({
            "characters": {"C1": _custom_char("Solo"), "C2": _custom_char("Outro")},
            "controlled_character_id": "C2",
        })
        self.created.append(sid)
        result = await self.runner.player_turn(sid, speech="oi")
        assert result["character_response"] == "Estou pronto."

        debug_path = SESSIONS_DIR / f"{sid}.debug.jsonl"
        assert debug_path.exists()
        entries = [
            json_module.loads(line)
            for line in debug_path.read_text(encoding="utf-8").splitlines()
        ]
        assert len(entries) == 2  # uma chamada ao Narrador, uma ao Personagem
        assert entries[0]["session_id"] == sid
        assert entries[0]["turn_number"] == 1
        assert entries[0]["agent"] == "narrator"
        assert entries[0]["response"] is not None
        assert entries[1]["agent"] == "character:Solo"
        assert entries[1]["response"] == "Estou pronto."

    def test_preview_narrator_prompt(self) -> None:
        """preview_narrator_prompt monta messages corretos sem tocar no LLM."""
        sid = self._start_custom()
        messages = self.runner.preview_narrator_prompt(sid, speech="olá", action="acena")
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

    def test_preview_narrator_prompt_missing_session(self) -> None:
        """preview de sessão inexistente retorna lista vazia."""
        assert self.runner.preview_narrator_prompt("naoexiste") == []


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
        assert "Player" not in messages[1]["content"]

    def test_build_summarizer_messages_shows_current_summary_and_notes(self) -> None:
        """Resumo e notas atuais entram no prompt, pra o Resumidor atualizar."""
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
        assert "Desconfia de magia." in user_content
        assert "(none yet)" in user_content  # C2 ainda sem nota

    @pytest.mark.asyncio
    async def test_summarize_returns_only_changed_notes(self, monkeypatch) -> None:  # noqa: ANN001
        """summarize() devolve o resumo + só as notas que o LLM decidiu mudar
        (merge com as notas antigas é responsabilidade de quem chama)."""
        from src.agents import summarizer as summarizer_mod

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            return {
                "story_summary": "Resumo atualizado.",
                "character_notes": {"C1": "Ficou tenso ao ouvir sobre a Guarda de Ferro."},
            }

        monkeypatch.setattr(summarizer_mod, "chat_completion_json", fake_json)

        client = httpx.AsyncClient(base_url="http://localhost:8888")
        summary, changed_notes = await summarizer_mod.summarize(
            client=client,
            characters=DEFAULT_CHARACTERS,
            controlled_id="C1",
            story_summary="Resumo antigo.",
            character_notes={"C1": "nota antiga", "C2": "nota antiga da Lyra"},
            evicted_turns=[],
            config={},
        )
        assert summary == "Resumo atualizado."
        assert changed_notes == {"C1": "Ficou tenso ao ouvir sobre a Guarda de Ferro."}
        assert "C2" not in changed_notes  # não mencionada -> não retorna, runner mantém a antiga
        await client.aclose()


# ═══════════════════════════════════════════════════════════════════════════
# Testes — Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Casos de borda e validações críticas."""

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

    def test_format_history_for_character_only_speech(self) -> None:
        """O Personagem só vê falas — narração e ação são filtradas do histórico."""
        from src.agents.character import _format_history_for_character

        scene = deepcopy_scene(DEFAULT_SCENE)
        history = [
            TurnRecord(turn_number=1, speaker="Player", content="oi",
                       content_type="speech", scene_snapshot=scene),
            TurnRecord(turn_number=1, speaker="Player", content="Thorn acena",
                       content_type="action", scene_snapshot=scene),
            TurnRecord(turn_number=1, speaker="Narrator", content="A porta range.",
                       content_type="narration", scene_snapshot=scene),
            TurnRecord(turn_number=1, speaker="C2", content="Oi Thorn.",
                       content_type="speech", scene_snapshot=scene),
        ]
        text = _format_history_for_character(history, DEFAULT_CHARACTERS, "C1")
        assert "Thorn acena" not in text
        assert "porta range" not in text
        assert "Thorn: oi" in text  # "Player" traduzido pro nome do controlado
        assert "Player" not in text
        assert "Oi Thorn." in text

    def test_append_history_deepcopy(self) -> None:
        """_append_history usa deepcopy — modificar cena posterior não afeta snapshot."""
        game = _make_test_game()
        runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
        runner._append_history(game, "Narrator", "Teste", "narration", 1)
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
            req = httpx.Request("POST", url)
            mock_res = httpx.Response(200, json={
                "choices": [{"message": {"content": "Olá"}}]
            }, request=req)
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
            mock_res = httpx.Response(200, json={
                "choices": [{"message": {"content": "Olá"}}]
            }, request=req)
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
        assert "em dashes" in msgs[0]["content"]
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
            return httpx.Response(200, json={
                "choices": [{"message": {"content": "Olá"}}]
            }, request=req)

        client = httpx.AsyncClient()
        monkeypatch.setattr(client, "post", mock_post)

        await chat_completion(
            client=client,
            messages=[{"role": "system", "content": "Você é o narrador."}],
        )

        assert captured_payload is not None
        content = captured_payload["messages"][0]["content"]
        assert "em dashes" in content
        assert "Always respond and write in" not in content
