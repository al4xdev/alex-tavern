"""Runner — orquestrador stateless do fluxo de roleplay.

Cada método carrega/salva seu próprio estado. NÃO tem ``self.game`` ou
``self.turn`` — variáveis locais em cada método, evitando race conditions
entre sessões concorrentes.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import httpx

from src.agents.character import act as character_act
from src.agents.narrator import narrate
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    TurnState,
)
from src.store.sessions import _get_lock, generate_session_id, load_game, save_game

# ── Personagens padrão (MVP) ──────────────────────────────────────────────

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


class Runner:
    """Orquestrador stateless. Cada método carrega/salva seu próprio estado."""

    def __init__(self, llm_client: httpx.AsyncClient, config: dict) -> None:
        self.client = llm_client
        self.config = config

    # ── Públicos ──────────────────────────────────────────────────────────

    def start_session(self, session_config: dict | None = None) -> str:
        """Cria GameState com personagens, cena e Player padrão (ou custom).

        Síncrono — só escrita de arquivo, sem chamada LLM.

        Args:
            session_config: Opcional. Pode conter chaves 'characters', 'scene',
                            'player' para customizar.

        Returns:
            session_id (string de 8 caracteres).
        """
        cfg = session_config or {}
        session_id = generate_session_id()

        characters = DEFAULT_CHARACTERS.copy()
        if "characters" in cfg:
            characters = cfg["characters"]

        scene = DEFAULT_SCENE
        if "scene" in cfg:
            scene = cfg["scene"]

        player = Player(
            name=cfg.get("player_name", "Jogador"),
            controlled_character_id=cfg.get("controlled_character_id", "C1"),
        )

        game = GameState(
            session_id=session_id,
            characters=characters,
            player=player,
            scene=scene,
            created_at=datetime.now(UTC).isoformat(),
        )
        save_game(game)
        return session_id

    async def player_turn(
        self,
        session_id: str,
        speech: str = "",
        action: str = "",
        chosen_option: int | None = None,
    ) -> dict:
        """Processa um turno do Player.

        Fluxo:
        1. load_game + lock
        2. Resolve chosen_option se houver
        3. Cria TurnState local
        4. Chama Narrador
        5. Se Narrador gerou options e player não escolheu → retorna options
        6. Grava narração no histórico
        7. Se next_speaker é personagem → chama personagem
        8. Atualiza cena
        9. save_game → retorna resultado

        Args:
            session_id: ID da sessão.
            speech: Fala/pensamento do Player.
            action: Ação física do Player.
            chosen_option: Índice da opção escolhida (se veio de pending_options).

        Returns:
            Dict com: narration, character_response, next_speaker,
            player_options, scene_update, turn_number.
        """
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Sessão {session_id} não encontrada"}

            # Resolve pending_options do turno anterior
            if game.pending_options and chosen_option is not None:
                action = self._resolve_chosen_option(game, chosen_option, action)

            turn = TurnState(
                turn_number=len(game.history) + 1,
                player_speech=speech,
                player_action=action,
            )

            # Chama Narrador
            narrator_raw = await self._call_narrator(game, turn)

            # Se Narrador gerou novas options E player não escolheu → pausa
            player_opts = narrator_raw.get("player_options")
            if player_opts and chosen_option is None:
                game.pending_options = player_opts
                save_game(game)
                return {"type": "options", "options": player_opts}

            # Avança o turno
            narration = narrator_raw["narration"]
            self._append_history(game, "Narrator", narration, "narration")

            speaker = narrator_raw["next_speaker"]
            character_response: str | None = None

            if speaker in game.characters:
                ctx = narrator_raw.get("context_for_character", "")
                character_response = await self._call_character(game, speaker, ctx)
                self._append_history(game, speaker, character_response, "speech")

            # Atualiza cena
            scene_up = narrator_raw.get("scene_update")
            if scene_up:
                self._update_scene(game, scene_up)

            game.pending_options = None
            save_game(game)

            return {
                "narration": narration,
                "character_response": character_response,
                "next_speaker": speaker,
                "player_options": player_opts,
                "scene_update": scene_up,
                "turn_number": turn.turn_number,
            }

    def get_state(self, session_id: str) -> GameState | None:
        """Carrega GameState do JSON (sem lock — seguro por atomic write)."""
        return load_game(session_id)

    def get_history(self, session_id: str, limit: int = 50) -> list[TurnRecord]:
        """Retorna últimos N turnos do histórico."""
        game = load_game(session_id)
        if game is None:
            return []
        return game.history[-limit:]

    # ── Privados ──────────────────────────────────────────────────────────

    async def _call_narrator(self, game: GameState, turn: TurnState) -> dict:
        """Chama agente Narrador com contexto completo."""
        return await narrate(
            client=self.client,
            scene=game.scene,
            characters=game.characters,
            player_speech=turn.player_speech,
            player_action=turn.player_action,
            player_controlled_id=game.player.controlled_character_id,
            history=game.history,
            config=self.config,
        )

    async def _call_character(
        self, game: GameState, character_id: str, context: str
    ) -> str:
        """Chama agente Personagem com contexto filtrado."""
        return await character_act(
            client=self.client,
            character=game.characters[character_id],
            context=context,
            history=game.history,
            config=self.config,
        )

    def _update_scene(self, game: GameState, scene_update: dict | None) -> None:
        """Aplica mudanças físicas à Scene."""
        if scene_update:
            game.scene.physical_facts.update(scene_update)

    def _append_history(
        self,
        game: GameState,
        speaker: str,
        content: str,
        content_type: str,
    ) -> None:
        """Cria TurnRecord com deepcopy da Scene e adiciona ao histórico."""
        record = TurnRecord(
            turn_number=len(game.history) + 1,
            speaker=speaker,
            content=content,
            content_type=content_type,
            scene_snapshot=copy.deepcopy(game.scene),
        )
        game.history.append(record)

    def _resolve_chosen_option(
        self, game: GameState, chosen_option: int, action: str
    ) -> str:
        """Resolve índice da option escolhida → injeta label no action."""
        opts = game.pending_options
        if not opts or chosen_option >= len(opts):
            return action  # índice inválido, mantém action original

        label = str(opts[chosen_option]["label"])
        if action:
            return f"{action} [Chose: {label}]"
        return label
