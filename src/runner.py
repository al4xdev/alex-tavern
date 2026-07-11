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
from src.agents.narrator import build_narrator_messages, narrate
from src.agents.narrator import suggest as narrator_suggest
from src.llm.client import log_undo
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
                            'controlled_character_id', 'narrator_directives'
                            para customizar.

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

        player = Player(controlled_character_id=controlled_id)

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
        force_speaker: str | None = None,
    ) -> dict:
        """Processa um turno do Player.

        Fluxo:
        1. load_game + lock
        2. Persiste a jogada do humano no histórico (marcada "Player" internamente,
           mas nunca renderizada assim em prompt — vira a última entrada do
           HISTORY que o Narrador cego lê)
        3. Chama Narrador
        4. Grava narração no histórico
        5. Quem age a seguir é ``force_speaker`` (gatilho manual, se informado)
           ou o ``next_speaker`` do Narrador. Se for personagem presente e NÃO
           for o controlado → chama personagem. Se for o controlado, pausa e
           devolve o controle ao humano.
        6. Atualiza cena e humor
        7. save_game → retorna resultado

        Args:
            session_id: ID da sessão.
            speech: Fala/pensamento do Player.
            action: Ação física do Player.
            force_speaker: Gatilho manual — id de personagem presente ou
                "Narrator", para forçar quem age a seguir em vez de deixar o
                Narrador decidir.

        Returns:
            Dict com: narration, character_response, next_speaker,
            scene_update, turn_number.
        """
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Sessão {session_id} não encontrada"}

            # Todos os registros desta jogada compartilham o mesmo turn_number
            # (pré-requisito do undo desfazer o passo inteiro).
            step = (game.history[-1].turn_number + 1) if game.history else 1

            # Persiste a jogada ANTES de chamar o Narrador (cego).
            if speech:
                self._append_history(game, "Player", speech, "speech", step)
            if action:
                self._append_history(game, "Player", action, "action", step)

            # Chama Narrador
            narrator_raw = await self._call_narrator(game, step)

            # Avança o turno
            narration = narrator_raw["narration"]
            self._append_history(game, "Narrator", narration, "narration", step)

            valid_force = force_speaker in game.characters or force_speaker == "Narrator"
            speaker = force_speaker if valid_force else narrator_raw["next_speaker"]
            controlled = game.player.controlled_character_id
            character_response: str | None = None

            # O Narrador é cego e pode rotear para o personagem controlado —
            # nesse caso o runner NÃO gera a fala dele; pausa e devolve o
            # controle ao humano (a UI decide o que fazer com next_speaker).
            if speaker in game.characters and speaker != controlled:
                ctx = narrator_raw.get("context_for_character", "")
                character_response = await self._call_character(game, speaker, ctx, step)
                self._append_history(game, speaker, character_response, "speech", step)

            # Atualiza cena
            scene_up = narrator_raw.get("scene_update")
            if scene_up:
                self._update_scene(game, scene_up)

            # Atualiza humor dos personagens
            mood_updates = narrator_raw.get("mood_updates")
            if mood_updates:
                self._update_moods(game, mood_updates)

            save_game(game)

            return {
                "narration": narration,
                "character_response": character_response,
                "next_speaker": speaker,
                "scene_update": scene_up,
                "turn_number": step,
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

    async def undo_turn(self, session_id: str) -> dict:
        """Desfaz o último passo-de-jogador inteiro.

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

            # Sem histórico → nada a desfazer
            if not game.history:
                return {"undone": False}

            # Remove todos os registros do maior turn_number e restaura cena +
            # humor a partir do snapshot.
            last_turn_number = game.history[-1].turn_number
            restore: TurnRecord | None = None
            removed = 0
            while game.history and game.history[-1].turn_number == last_turn_number:
                restore = game.history.pop()
                removed += 1

            assert restore is not None, "loop acima roda ao menos uma vez"
            game.scene = copy.deepcopy(restore.scene_snapshot)
            for cid, mood in restore.mood_snapshot.items():
                if cid in game.characters:
                    game.characters[cid].mind.current_mood = mood

            save_game(game)
            log_undo(session_id, last_turn_number, removed)
            return {"undone": True, "state": game_state_to_dict(game)}

    async def suggest_actions(self, session_id: str) -> dict:
        """Pede ao Narrador (cego) sugestões de jogada para o personagem controlado.

        Gatilho manual "sugira pra mim" (Task 6): não persiste nada — só devolve
        as sugestões para o front preencher as caixas de fala/ação. O Narrador
        não sabe que o personagem-alvo é o humano.

        Returns:
            Dict com ``suggestions`` (lista de ``{"speech", "action"}``).
        """
        game = load_game(session_id)
        if game is None:
            return {"error": f"Sessão {session_id} não encontrada"}

        target_id = game.player.controlled_character_id
        turn_number = game.history[-1].turn_number if game.history else 0
        suggestions = await narrator_suggest(
            client=self.client,
            scene=game.scene,
            characters=game.characters,
            target_id=target_id,
            history=game.history,
            config=self.config,
            narrator_directives=game.narrator_directives,
            session_id=game.session_id,
            turn_number=turn_number,
        )
        return {"suggestions": suggestions}

    # ── Privados ──────────────────────────────────────────────────────────

    async def _call_narrator(self, game: GameState, turn_number: int) -> dict:
        """Chama agente Narrador (cego) com contexto completo. Devolve result."""
        return await narrate(
            client=self.client,
            scene=game.scene,
            characters=game.characters,
            player_controlled_id=game.player.controlled_character_id,
            history=game.history,
            config=self.config,
            narrator_directives=game.narrator_directives,
            session_id=game.session_id,
            turn_number=turn_number,
        )

    async def _call_character(
        self, game: GameState, character_id: str, context: str, turn_number: int
    ) -> str:
        """Chama agente Personagem com contexto filtrado. Devolve o content."""
        return await character_act(
            client=self.client,
            character=game.characters[character_id],
            context=context,
            history=game.history,
            characters=game.characters,
            controlled_id=game.player.controlled_character_id,
            config=self.config,
            session_id=game.session_id,
            turn_number=turn_number,
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
