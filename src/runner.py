"""Runner — stateless orchestrator of the roleplay flow.

Each method loads/saves its own state. Does NOT have ``self.game`` or
``self.turn`` — local variables in each method, avoiding race conditions
between concurrent sessions.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import httpx

from src.agents.character import CharacterOutput
from src.agents.character import act as character_act
from src.agents.narrator import narrate
from src.agents.narrator import suggest as narrator_suggest
from src.agents.summarizer import summarize
from src.llm.debug_log import log_compact, log_restore_compaction, log_turn_input, log_undo
from src.models import (
    GameState,
    Player,
    TurnRecord,
)
from src.store.sessions import (
    _get_lock,
    backup_session,
    generate_session_id,
    load_game,
    restore_last_backup,
    save_game,
)


class Runner:
    """Stateless orchestrator. Each method loads/saves its own state."""

    def __init__(self, llm_client: httpx.AsyncClient, config: dict) -> None:
        self.client = llm_client
        self.config = config

    # ── Public Methods ────────────────────────────────────────────────────

    def start_session(self, session_config: dict | None = None) -> str:
        """Creates GameState with default (or custom) characters, scene, and Player.

        Synchronous — only file writing, no LLM call.

        Args:
            session_config: Optional. Can contain 'characters', 'scene',
                            'controlled_character_id', 'narrator_directives'
                            keys to customize.

        Returns:
            session_id (8-character string).

        Raises:
            ValueError: If there is not at least one character.
        """
        cfg = session_config or {}
        session_id = generate_session_id()
        preset_data: dict | None = None

        if "characters" not in cfg or "scene" not in cfg:
            from src.store.presets import list_defaults, load_default

            defaults = list_defaults()
            if defaults:
                preset_data = load_default(defaults[0])

        if "characters" in cfg:
            characters = cfg["characters"]
            if not characters:
                raise ValueError("The session needs at least one character.")
        else:
            from src.models import dict_to_character

            if preset_data is None:
                raise ValueError(
                    "The session needs at least one character, and no default preset was found."
                )
            if not preset_data or "characters" not in preset_data:
                raise ValueError(
                    "The session needs at least one character, and the default preset is corrupted."
                )
            characters = {
                cid: dict_to_character(cdata) for cid, cdata in preset_data["characters"].items()
            }
        if "scene" in cfg:
            scene = cfg["scene"]
        elif preset_data and "scene" in preset_data:
            from src.models import Scene

            sdata = preset_data["scene"]
            scene = Scene(
                location=sdata["location"],
                time_of_day=sdata["time_of_day"],
                present_characters=list(sdata.get("present_characters", [])),
                physical_facts=dict(sdata.get("physical_facts", {})),
            )
        else:
            raise ValueError("No default scene available.")

        # Do not trust the client: present_characters is derived from the characters.
        scene.present_characters = [*characters, "Player"]

        # controlled_character_id must exist; otherwise, use the first character.
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
        thought: str = "",
        action: str = "",
        force_speaker: str | None = None,
        narrator_hint: str = "",
        skip: bool = False,
    ) -> dict:
        """Processes a Player's turn.

        Flow:
        1. load_game + lock
        2. Persists the human's speech/thought/action in the history (marked "Player" internally,
           but never rendered this way in prompts — turns into the last entry of
           HISTORY read by the blind Narrator)
        3. Calls Narrator
        4. Records narration in history
        5. Who acts next is ``force_speaker`` (manual override, if provided)
           or the Narrator's ``next_speaker``. If it is a present character and NOT
           the controlled one → calls the character. If it is the controlled one, pauses and
           returns control to the human.
        6. Updates scene and moods
        7. save_game → returns results

        Args:
            session_id: Session ID.
            speech: Player's audible speech.
            thought: Player character's private thought.
            action: Player's physical action.
            force_speaker: Manual trigger — ID of a present character or
                "Narrator", to force who acts next instead of letting the
                Narrator decide.

        Returns:
            Dict with: narration, character_response, next_speaker,
            scene_update, turn_number.
        """
        if not skip and not any(
            value.strip() for value in (speech, thought, action, narrator_hint)
        ):
            raise ValueError("A turn needs speech, thought, action, narrator_hint, or skip")
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}

            # All records from this turn share the same turn_number
            # (pre-requisite for undo to revert the entire step).
            step = (game.history[-1].turn_number + 1) if game.history else 1

            effective_force_speaker = (
                force_speaker
                if force_speaker
                and (force_speaker in game.characters or force_speaker == "Narrator")
                else None
            )
            log_turn_input(
                session_id=session_id,
                turn_number=step,
                speech=speech,
                thought=thought,
                action=action,
                requested_force_speaker=force_speaker,
                effective_force_speaker=effective_force_speaker,
                narrator_hint=narrator_hint,
                skip=skip,
            )

            # Persist the turn BEFORE calling the Narrator (blind).
            # Skip: no player input to persist — Narrator reacts to current state alone.
            if not skip:
                if speech:
                    self._append_history(game, "Player", speech, "speech", step)
                if thought:
                    self._append_history(game, "Player", thought, "thought", step)
                if action:
                    self._append_history(game, "Player", action, "action", step)

                # A private thought has no observable event for the Narrator to
                # resolve — unless there's also a narrator_hint providing external
                # context. Persist it as a complete step without replaying the
                # previous public event or inventing a reaction to hidden content.
                if thought and not speech and not action and not narrator_hint.strip():
                    save_game(game)
                    return {
                        "narration": None,
                        "character_response": None,
                        "next_speaker": game.player.controlled_character_id,
                        "scene_update": None,
                        "turn_number": step,
                    }

            # Call Narrator
            narrator_raw = await self._call_narrator(
                game, step, effective_force_speaker, narrator_hint
            )

            # Advance the turn
            narration = narrator_raw["narration"]
            self._append_history(game, "Narrator", narration, "narration", step)

            speaker = effective_force_speaker or narrator_raw["next_speaker"]
            controlled = game.player.controlled_character_id
            character_response: CharacterOutput | None = None

            # The Narrator is blind and can route to the controlled character —
            # in this case, the runner does NOT generate their speech; pauses and returns
            # control to the human (the UI decides what to do with next_speaker).
            if speaker in game.characters and speaker != controlled:
                ctx = narrator_raw.get("context_for_character", "")
                character_response = await self._call_character(game, speaker, ctx, step)
                if character_response["thought"]:
                    self._append_history(
                        game, speaker, character_response["thought"], "thought", step
                    )
                if character_response["speech"]:
                    self._append_history(
                        game, speaker, character_response["speech"], "speech", step
                    )

            # Update scene
            scene_up = narrator_raw.get("scene_update")
            if scene_up:
                self._update_scene(game, scene_up)

            # Update characters' moods
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

    async def get_state(self, session_id: str) -> GameState | None:
        """Load one consistent state snapshot after active mutations finish."""
        async with _get_lock(session_id):
            return load_game(session_id)

    async def get_history(self, session_id: str, limit: int = 50) -> list[TurnRecord]:
        """Return the last N records from a transactionally consistent snapshot."""
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return []
            return game.history[-limit:]

    async def undo_turn(self, session_id: str) -> dict:
        """Undoes the entire last player turn step.

        Undoes one step per call — repeated calls undo multiple levels. A
        "step" is every record sharing the highest ``turn_number`` (human move
        + narration + Character reply, see ``_append_history``). All of them
        carry the same ``scene_snapshot``/``mood_snapshot`` (nothing changes scene/mood
        between appends within the same step — only afterwards, via ``scene_update``/
        ``mood_updates``), so any of them can be used to restore the previous state.

        Returns:
            Dict with ``state`` (serialized GameState) and ``undone`` (bool).
            If there is nothing to undo, returns ``{"undone": False}``.
        """
        from src.models import game_state_to_dict

        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"undone": False, "error": f"Session {session_id} not found"}

            # No history -> nothing to undo
            if not game.history:
                return {"undone": False}

            # Remove all records sharing the highest turn_number and restore scene +
            # moods from snapshot.
            last_turn_number = game.history[-1].turn_number
            restore: TurnRecord | None = None
            removed = 0
            while game.history and game.history[-1].turn_number == last_turn_number:
                restore = game.history.pop()
                removed += 1

            assert restore is not None, "loop above runs at least once"
            game.scene = copy.deepcopy(restore.scene_snapshot)
            for cid, mood in restore.mood_snapshot.items():
                if cid in game.characters:
                    game.characters[cid].mind.current_mood = mood

            save_game(game)
            log_undo(session_id, last_turn_number, removed)
            return {"undone": True, "state": game_state_to_dict(game)}

    async def suggest_actions(self, session_id: str) -> dict:
        """Asks the (blind) Narrator for possible move suggestions for the controlled character.

        Manual trigger "suggest to me" (Task 6): does not persist anything — just returns
        suggestions for the frontend to fill the speech/action input boxes. The Narrator
        does not know the target character is the human.

        Returns:
            Dict with ``suggestions`` (list of ``{"speech", "action"}``).
        """
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}

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

    async def compact_session(self, session_id: str) -> dict:
        """Session compaction — discrete and manual event (Task 3 of the plan).

        Keeps the last ``compaction_keep_recent_turns`` turns verbatim
        (distinct turn_numbers) and summarizes everything before that in an
        updated ``story_summary``/``character_notes``, via the Summarizer agent
        (blind, same as the Narrator). Backups the original file BEFORE
        any changes (``backup_session``) — after compaction, ``undo`` can no longer
        reach the summarized turns; recovery is only possible by manually restoring
        a ``{session_id}.kb_N.json``.

        Returns:
            If there is nothing to compact (history is smaller than the window):
            ``{"compacted": False, "reason": "..."}``.
            Otherwise: ``{"compacted": True, "backup_path", "evicted_turns",
            "kept_turns"}``.
        """
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}

            keep_recent = self.config.get("compaction_keep_recent_turns", 200)
            turn_numbers = list(dict.fromkeys(rec.turn_number for rec in game.history))
            if len(turn_numbers) <= keep_recent:
                return {
                    "compacted": False,
                    "reason": "History smaller than the window — nothing to compact.",
                }

            cutoff = turn_numbers[-keep_recent]
            evicted = [rec for rec in game.history if rec.turn_number < cutoff]
            kept = [rec for rec in game.history if rec.turn_number >= cutoff]

            # Backup BEFORE changing anything — disk still reflects the
            # pre-compaction state at this point (we only modified `game` in memory).
            backup_path = backup_session(session_id)

            new_summary, changed_notes = await summarize(
                client=self.client,
                characters=game.characters,
                controlled_id=game.player.controlled_character_id,
                story_summary=game.story_summary,
                character_notes=game.character_notes,
                evicted_turns=evicted,
                config=self.config,
                narrator_directives=game.narrator_directives,
                session_id=game.session_id,
                turn_number=cutoff,
            )

            game.character_notes.update(changed_notes)
            game.story_summary = new_summary
            game.history = kept

            save_game(game)
            log_compact(session_id, cutoff, len(evicted), len(kept))

            return {
                "compacted": True,
                "backup_path": backup_path,
                "evicted_turns": len(evicted),
                "kept_turns": len(kept),
            }

    async def restore_last_compaction(self, session_id: str) -> dict:
        """Undoes the last compaction, restoring the most recent backup — only if safe.

        ⚠️ Risky operation: only allowed if NO new turns have been played
        since that compaction — otherwise restoring would permanently delete those turns
        (they do not exist in the backup). See the lock in
        ``store.sessions.restore_last_backup``, which performs the check and
        refuses (changing nothing) instead of trying to merge the two
        histories. Logs the attempt (success or refusal) in the raw log.

        Returns:
            ``{"restored": False, "reason": "..."}`` if refused/no backup.
            ``{"restored": True, "history_length": N}`` if restored.
        """
        async with _get_lock(session_id):
            result = restore_last_backup(session_id)
            log_restore_compaction(
                session_id, result.get("restored", False), result.get("reason", "")
            )
            return result

    # ── Private Methods ───────────────────────────────────────────────────

    async def _call_narrator(
        self,
        game: GameState,
        turn_number: int,
        forced_speaker: str | None = None,
        narrator_hint: str = "",
    ) -> dict:
        """Calls Narrator agent (blind) with full context. Returns result."""
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
            story_summary=game.story_summary,
            forced_speaker=forced_speaker,
            narrator_hint=narrator_hint,
        )

    async def _call_character(
        self, game: GameState, character_id: str, context: str, turn_number: int
    ) -> CharacterOutput:
        """Calls Character agent with filtered context. Returns the content."""
        return await character_act(
            client=self.client,
            character=game.characters[character_id],
            context=context,
            history=game.history,
            characters=game.characters,
            controlled_id=game.player.controlled_character_id,
            character_id=character_id,
            config=self.config,
            session_id=game.session_id,
            turn_number=turn_number,
            notes=game.character_notes.get(character_id, ""),
        )

    def _update_scene(self, game: GameState, scene_update: dict | None) -> None:
        """Applies reserved Scene fields and physical-fact deltas.

        ``location`` and ``time_of_day`` belong to ``Scene`` itself and must
        never be persisted as physical facts. Moving to a different location
        also discards facts from the previous scene before applying the new
        delta. A ``None`` value removes a physical fact, but cannot erase a
        required reserved field.
        """
        if not scene_update:
            return

        location = scene_update.get("location")
        if isinstance(location, str) and location.strip():
            normalized_location = location.strip()
            if normalized_location != game.scene.location:
                game.scene.location = normalized_location
                game.scene.physical_facts.clear()

        time_of_day = scene_update.get("time_of_day")
        if isinstance(time_of_day, str) and time_of_day.strip():
            game.scene.time_of_day = time_of_day.strip()

        for key, value in scene_update.items():
            if key in {"location", "time_of_day"}:
                continue
            if value is None:
                game.scene.physical_facts.pop(key, None)
            else:
                game.scene.physical_facts[key] = value

    def _update_moods(self, game: GameState, mood_updates: dict[str, str]) -> None:
        """Applies the new mood decided by the Narrator to each affected character."""
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
        """Creates a TurnRecord with deepcopy of the Scene/moods and adds it to history.

        ```turn_number`` is explicit — all records of the same turn
        (human speech/thought/action, narration, Character speech) share the
        same number and the same snapshot, a pre-requisite for undo to revert
        the entire step (scene and moods).
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
