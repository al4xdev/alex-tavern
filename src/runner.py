"""Runner — orquestrador stateless do fluxo de roleplay.

Cada método carrega/salva seu próprio estado. NÃO tem ``self.game`` ou
``self.turn`` — variáveis locais em cada método, evitando race conditions
entre sessões concorrentes.
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime

import httpx

from src.agents.character import act as character_act
from src.agents.narrator import build_narrator_messages, narrate
from src.models import (
    GameState,
    Player,
    TurnRecord,
)
from src.store.sessions import _get_lock, generate_session_id, load_game, save_game


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
                            'player_name', 'controlled_character_id',
                            'narrator_directives' para customizar.

        Returns:
            session_id (string de 8 caracteres).

        Raises:
            ValueError: Se não houver ao menos um personagem.
        """
        cfg = session_config or {}
        session_id = generate_session_id()

        if "characters" in cfg:
            characters = cfg["characters"]
            if not characters:
                raise ValueError("A sessão precisa de ao menos um personagem.")
        else:
            from src.models import dict_to_character
            from src.store.presets import list_defaults, load_preset
            defaults = list_defaults()
            if not defaults:
                raise ValueError(
                    "A sessão precisa de ao menos um personagem, "
                    "e nenhum preset padrão foi encontrado."
                )
            preset_data = load_preset(defaults[0])
            if not preset_data or "characters" not in preset_data:
                raise ValueError(
                    "A sessão precisa de ao menos um personagem, "
                    "e o preset padrão está corrompido."
                )
            characters = {
                cid: dict_to_character(cdata)
                for cid, cdata in preset_data["characters"].items()
            }

        if "scene" in cfg:
            scene = cfg["scene"]
        else:
            from src.store.presets import list_defaults, load_preset
            defaults = list_defaults()
            if defaults:
                preset_data = load_preset(defaults[0])
                if preset_data and "scene" in preset_data:
                    from src.models import Scene
                    sdata = preset_data["scene"]
                    scene = Scene(
                        location=sdata["location"],
                        time_of_day=sdata["time_of_day"],
                        present_characters=list(sdata.get("present_characters", [])),
                        physical_facts=dict(sdata.get("physical_facts", {})),
                    )
                else:
                    raise ValueError("Nenhuma cena padrão disponível.")
            else:
                raise ValueError("Nenhuma cena padrão disponível.")

        # Não confiar no cliente: present_characters é derivado dos personagens.
        scene.present_characters = [*characters, "Player"]

        # controlled_character_id deve existir; senão, usa o primeiro personagem.
        controlled_id: str = cfg.get("controlled_character_id") or ""
        if controlled_id not in characters:
            controlled_id = next(iter(characters))

        player = Player(
            name=cfg.get("player_name") or "Jogador",
            controlled_character_id=controlled_id,
        )

        game = GameState(
            session_id=session_id,
            characters=characters,
            player=player,
            scene=scene,
            created_at=datetime.now(UTC).isoformat(),
            narrator_directives=cfg.get("narrator_directives", ""),
        )
        save_game(game)
        return session_id

    async def player_turn(
        self,
        session_id: str,
        speech: str = "",
        action: str = "",
        chosen_option: int | None = None,
        debug: bool = False,
    ) -> dict:
        """Processa um turno do Player.

        Fluxo:
        1. load_game + lock
        2. Resolve chosen_option se houver
        3. Persiste a jogada do humano no histórico (marcada "Player" internamente,
           mas nunca renderizada assim em prompt — vira a última entrada do
           HISTORY que o Narrador cego lê)
        4. Chama Narrador
        5. Se Narrador gerou options e player não escolheu → retorna options
        6. Grava narração no histórico
        7. Se next_speaker é personagem presente e NÃO é o controlado → chama
           personagem. Se for o controlado, pausa e devolve o controle ao humano.
        8. Atualiza cena e humor
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

            # Todos os registros desta jogada compartilham o mesmo turn_number
            # (pré-requisito do undo desfazer o passo inteiro).
            step = (game.history[-1].turn_number + 1) if game.history else 1

            # Persiste a jogada ANTES de chamar o Narrador (cego).
            if speech:
                self._append_history(game, "Player", speech, "speech", step)
            if action:
                self._append_history(game, "Player", action, "action", step)

            # Chama Narrador
            narrator_raw, narrator_messages = await self._call_narrator(game)

            # Se Narrador gerou novas options E player não escolheu → pausa
            player_opts = narrator_raw.get("player_options")
            if player_opts and chosen_option is None:
                game.pending_options = player_opts
                save_game(game)
                result: dict = {"type": "options", "options": player_opts}
                if debug:
                    result["debug"] = {
                        "narrator": {
                            "messages": narrator_messages,
                            "raw": json.dumps(narrator_raw, ensure_ascii=False, indent=2),
                        },
                        "character": None,
                    }
                return result

            # Avança o turno
            narration = narrator_raw["narration"]
            self._append_history(game, "Narrator", narration, "narration", step)

            speaker = narrator_raw["next_speaker"]
            controlled = game.player.controlled_character_id
            character_response: str | None = None
            character_messages: list[dict] | None = None

            # O Narrador é cego e pode rotear para o personagem controlado —
            # nesse caso o runner NÃO gera a fala dele; pausa e devolve o
            # controle ao humano (a UI decide o que fazer com next_speaker).
            if speaker in game.characters and speaker != controlled:
                ctx = narrator_raw.get("context_for_character", "")
                character_response, character_messages = await self._call_character(
                    game, speaker, ctx
                )
                self._append_history(game, speaker, character_response, "speech", step)

            # Atualiza cena
            scene_up = narrator_raw.get("scene_update")
            if scene_up:
                self._update_scene(game, scene_up)

            # Atualiza humor dos personagens
            mood_updates = narrator_raw.get("mood_updates")
            if mood_updates:
                self._update_moods(game, mood_updates)

            game.pending_options = None
            save_game(game)

            result = {
                "narration": narration,
                "character_response": character_response,
                "next_speaker": speaker,
                "player_options": player_opts,
                "scene_update": scene_up,
                "turn_number": step,
            }
            if debug:
                char_debug: dict | None = None
                if character_messages is not None:
                    char_debug = {
                        "messages": character_messages,
                        "raw": character_response,
                    }
                result["debug"] = {
                    "narrator": {
                        "messages": narrator_messages,
                        "raw": json.dumps(narrator_raw, ensure_ascii=False, indent=2),
                    },
                    "character": char_debug,
                }
            return result

    def get_state(self, session_id: str) -> GameState | None:
        """Carrega GameState do JSON (sem lock — seguro por atomic write)."""
        return load_game(session_id)

    def get_history(self, session_id: str, limit: int = 50) -> list[TurnRecord]:
        """Retorna últimos N turnos do histórico."""
        game = load_game(session_id)
        if game is None:
            return []
        return game.history[-limit:]

    async def undo_turn(self, session_id: str) -> dict:
        """Desfaz o último passo-de-jogador inteiro (ou limpa pending_options se pausou).

        Desfaz um passo por chamada — chamadas repetidas desfazem múltiplos níveis. Um
        "passo" é todo registro que compartilha o maior ``turn_number`` (jogada do
        humano + narração + fala do Personagem, ver ``_append_history``). Todos eles
        carregam o mesmo ``scene_snapshot``/``mood_snapshot`` (nada muda a cena/humor
        entre os appends de um mesmo passo — só depois, via ``scene_update``/
        ``mood_updates``), então qualquer um serve pra restaurar o estado anterior.

        Returns:
            Dict com ``state`` (GameState serializado) e ``undone`` (bool).
            Se não houver nada a desfazer, retorna ``{"undone": False}``.
        """
        from src.models import game_state_to_dict

        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"undone": False, "error": f"Sessão {session_id} não encontrada"}

            # Caso 1: sessão pausada em options (sem entradas novas no histórico)
            if game.pending_options is not None:
                game.pending_options = None
                save_game(game)
                return {"undone": True, "state": game_state_to_dict(game)}

            # Caso 2: sem histórico → nada a desfazer
            if not game.history:
                return {"undone": False}

            # Caso 3: desfaz o passo inteiro — remove todos os registros do
            # maior turn_number e restaura cena + humor a partir do snapshot.
            last_turn_number = game.history[-1].turn_number
            restore: TurnRecord | None = None
            while game.history and game.history[-1].turn_number == last_turn_number:
                restore = game.history.pop()

            assert restore is not None, "loop acima roda ao menos uma vez"
            game.scene = copy.deepcopy(restore.scene_snapshot)
            for cid, mood in restore.mood_snapshot.items():
                if cid in game.characters:
                    game.characters[cid].mind.current_mood = mood

            game.pending_options = None
            save_game(game)
            return {"undone": True, "state": game_state_to_dict(game)}

    # ── Privados ──────────────────────────────────────────────────────────

    async def _call_narrator(self, game: GameState) -> tuple[dict, list[dict]]:
        """Chama agente Narrador (cego) com contexto completo. Devolve (result, messages)."""
        return await narrate(
            client=self.client,
            scene=game.scene,
            characters=game.characters,
            player_controlled_id=game.player.controlled_character_id,
            history=game.history,
            config=self.config,
            narrator_directives=game.narrator_directives,
        )

    async def _call_character(
        self, game: GameState, character_id: str, context: str
    ) -> tuple[str, list[dict]]:
        """Chama agente Personagem com contexto filtrado. Devolve (content, messages)."""
        return await character_act(
            client=self.client,
            character=game.characters[character_id],
            context=context,
            history=game.history,
            characters=game.characters,
            controlled_id=game.player.controlled_character_id,
            config=self.config,
        )

    def preview_narrator_prompt(
        self, session_id: str, speech: str = "", action: str = ""
    ) -> list[dict]:
        """Monta e retorna os messages do Narrador para o estado atual.

        NÃO chama o LLM nem persiste nada — útil para inspecionar o prompt
        exato offline. Se ``speech``/``action`` forem informados, simula a
        jogada como a última entrada do HISTORY (sem gravar), exatamente como
        aconteceria de verdade.

        Returns:
            Lista de messages (system + user), ou lista vazia se a sessão
            não existir.
        """
        game = load_game(session_id)
        if game is None:
            return []

        history = list(game.history)
        next_turn = (history[-1].turn_number + 1) if history else 1
        if speech:
            history.append(
                TurnRecord(
                    turn_number=next_turn,
                    speaker="Player",
                    content=speech,
                    content_type="speech",
                    scene_snapshot=game.scene,
                )
            )
        if action:
            history.append(
                TurnRecord(
                    turn_number=next_turn,
                    speaker="Player",
                    content=action,
                    content_type="action",
                    scene_snapshot=game.scene,
                )
            )

        return build_narrator_messages(
            scene=game.scene,
            characters=game.characters,
            player_controlled_id=game.player.controlled_character_id,
            history=history,
            narrator_directives=game.narrator_directives,
            context_max=self.config.get("context_max"),
            max_tokens_narrator=self.config.get("max_tokens_narrator", 2048),
        )

    def _update_scene(self, game: GameState, scene_update: dict | None) -> None:
        """Aplica mudanças físicas à Scene. Valor ``None`` remove a chave."""
        if scene_update:
            for key, value in scene_update.items():
                if value is None:
                    game.scene.physical_facts.pop(key, None)
                else:
                    game.scene.physical_facts[key] = value

    def _update_moods(self, game: GameState, mood_updates: dict[str, str]) -> None:
        """Aplica o novo humor decidido pelo Narrador a cada personagem afetado."""
        for character_id, mood in mood_updates.items():
            if character_id in game.characters:
                game.characters[character_id].mind.current_mood = mood

    def _append_history(
        self,
        game: GameState,
        speaker: str,
        content: str,
        content_type: str,
        turn_number: int,
    ) -> None:
        """Cria TurnRecord com deepcopy da Scene/humores e adiciona ao histórico.

        ``turn_number`` é explícito — todos os registros de uma mesma jogada
        (fala/ação do humano, narração, fala do Personagem) compartilham o
        mesmo número e o mesmo snapshot, pré-requisito para o undo desfazer
        o passo inteiro (cena e humor).
        """
        record = TurnRecord(
            turn_number=turn_number,
            speaker=speaker,
            content=content,
            content_type=content_type,
            scene_snapshot=copy.deepcopy(game.scene),
            mood_snapshot={cid: ch.mind.current_mood for cid, ch in game.characters.items()},
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
