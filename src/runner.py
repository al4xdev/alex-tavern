"""Runner — stateless orchestrator of the roleplay flow.

Each method loads/saves its own state. Does NOT have ``self.game`` or
``self.turn`` — local variables in each method, avoiding race conditions
between concurrent sessions.
"""

from __future__ import annotations

import copy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from src.agents.character import CharacterOutput
from src.agents.character import act as character_act
from src.agents.narrator import build_narrator_messages, narrate
from src.agents.narrator import suggest as narrator_suggest
from src.agents.summarizer import relevant_character_ids, summarize
from src.compaction import (
    CompactionDraft,
    CompactionProgress,
    CompactionStage,
    CompactionTrigger,
    ProgressSink,
    build_plugin_delta,
    canonical_hash,
    history_hash,
    invert_plugin_delta,
)
from src.llm.debug_log import (
    log_compact,
    log_compaction_status,
    log_effective_turn_input,
    log_restore_compaction,
    log_turn_input,
    log_undo,
)
from src.llm.tokens import estimate_prompt_tokens
from src.models import (
    CompactionStackEntry,
    GameState,
    Player,
    TurnRecord,
    dict_to_turn_record,
)
from src.store.sessions import (
    _get_lock,
    generate_session_id,
    load_compaction_checkpoint,
    load_game,
    next_compaction_id,
    save_game,
    write_compaction_checkpoint,
)

if TYPE_CHECKING:
    from src.plugins.runtime import PluginRuntime


class Runner:
    """Stateless orchestrator. Each method loads/saves its own state."""

    def __init__(
        self,
        llm_client: httpx.AsyncClient,
        config: dict,
        plugins: PluginRuntime | None = None,
    ) -> None:
        self.client = llm_client
        self.config = config
        self.plugins = plugins

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
        cfg = copy.deepcopy(session_config or {})
        if self.plugins is not None:
            cfg = self.plugins.hooks.filter_sync("session.start", cfg, {"runner": self})
        session_id = generate_session_id()
        scenario_data: dict | None = None

        if "characters" not in cfg or "scene" not in cfg:
            from src.store.scenarios import list_builtin_scenarios, load_builtin_scenario

            defaults = list_builtin_scenarios()
            if defaults:
                scenario_data = load_builtin_scenario(defaults[0])

        if "characters" in cfg:
            characters = cfg["characters"]
            if not characters:
                raise ValueError("The session needs at least one character.")
        else:
            from src.models import dict_to_character

            if scenario_data is None:
                raise ValueError(
                    "The session needs at least one character, and no default scenario was found."
                )
            if not scenario_data or "characters" not in scenario_data:
                raise ValueError(
                    "The session needs at least one character, and the default "
                    "scenario is corrupted."
                )
            characters = {
                cid: dict_to_character(cdata) for cid, cdata in scenario_data["characters"].items()
            }
        if "scene" in cfg:
            scene = cfg["scene"]
        elif scenario_data and "scene" in scenario_data:
            from src.models import Scene

            sdata = scenario_data["scene"]
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
        if self.plugins is not None:
            game = self.plugins.hooks.filter_sync(
                "session.before_commit", game, {"kind": "start", "runner": self}
            )
        save_game(game)
        if self.plugins is not None:
            self.plugins.hooks.action_sync("session.after_commit", {"game": game, "kind": "start"})
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

            turn_input: dict[str, Any] = {
                "speech": speech,
                "thought": thought,
                "action": action,
                "force_speaker": force_speaker,
                "narrator_hint": narrator_hint,
                "skip": skip,
            }
            original_input = copy.deepcopy(turn_input)

            # All records and model calls from this step share one number.
            step = (game.history[-1].turn_number + 1) if game.history else 1
            log_turn_input(
                session_id=session_id,
                turn_number=step,
                speech=speech,
                thought=thought,
                action=action,
                requested_force_speaker=force_speaker,
                narrator_hint=narrator_hint,
                skip=skip,
            )
            if self.plugins is not None:
                turn_input = await self.plugins.hooks.filter(
                    "turn.input",
                    turn_input,
                    {"game": game, "turn_number": step, "runner": self},
                )
                speech = str(turn_input["speech"])
                thought = str(turn_input["thought"])
                action = str(turn_input["action"])
                raw_force = turn_input["force_speaker"]
                force_speaker = str(raw_force) if raw_force is not None else None
                narrator_hint = str(turn_input["narrator_hint"])
                skip = bool(turn_input["skip"])

            effective_force_speaker = (
                force_speaker
                if force_speaker
                and (force_speaker in game.characters or force_speaker == "Narrator")
                else None
            )
            transformed_fields = [
                field
                for field in ("speech", "thought", "action")
                if turn_input[field] != original_input[field]
            ]
            log_effective_turn_input(
                session_id,
                step,
                turn_input,
                effective_force_speaker=effective_force_speaker,
                transformed_fields=transformed_fields,
            )
            effective_input = {
                field: str(turn_input[field]) for field in ("speech", "thought", "action")
            }

            automatic_compaction: dict[str, Any] | None = None
            private_thought_only = bool(
                effective_input["thought"]
                and not effective_input["speech"]
                and not effective_input["action"]
                and not narrator_hint.strip()
            )
            context_max = self.config.get("context_max")
            if (
                self.config.get("automatic_compaction_enabled", False)
                and not private_thought_only
                and isinstance(context_max, int)
            ):
                probe = copy.deepcopy(game)
                if not skip:
                    if speech:
                        self._append_history(probe, "Player", speech, "speech", step)
                    if action:
                        self._append_history(probe, "Player", action, "action", step)
                max_tokens = int(self.config.get("max_tokens_narrator", 2048))
                messages = build_narrator_messages(
                    scene=probe.scene,
                    characters=probe.characters,
                    player_controlled_id=probe.player.controlled_character_id,
                    history=probe.history,
                    narrator_directives=probe.narrator_directives,
                    context_max=None,
                    max_tokens_narrator=max_tokens,
                    story_summary=probe.story_summary,
                    forced_speaker=effective_force_speaker,
                    narrator_hint=narrator_hint,
                )
                estimated_context_tokens = estimate_prompt_tokens(messages) + max_tokens
                threshold_tokens = int(
                    context_max
                    * int(self.config.get("automatic_compaction_threshold_percent", 80))
                    / 100
                )
                if estimated_context_tokens >= threshold_tokens:
                    try:
                        automatic_compaction = await self._compact_loaded_game(
                            game,
                            trigger="automatic",
                            turn_number=step,
                            estimated_context_tokens=estimated_context_tokens,
                            threshold_tokens=threshold_tokens,
                        )
                    except Exception as error:
                        reason = "Automatic compaction failed before commit."
                        automatic_compaction = {
                            "status": "failed",
                            "trigger": "automatic",
                            "compacted": False,
                            "reason": reason,
                            "estimated_context_tokens": estimated_context_tokens,
                            "threshold_tokens": threshold_tokens,
                            "context_max": context_max,
                            "undo_depth": len(game.compaction_stack),
                        }
                        log_compaction_status(
                            session_id,
                            step,
                            status="failed",
                            trigger="automatic",
                            estimated_context_tokens=estimated_context_tokens,
                            threshold_tokens=threshold_tokens,
                            reason=reason,
                            error=error,
                        )
                else:
                    reason = "Estimated context remains below the threshold."
                    automatic_compaction = {
                        "status": "not_needed",
                        "trigger": "automatic",
                        "compacted": False,
                        "reason": reason,
                        "estimated_context_tokens": estimated_context_tokens,
                        "threshold_tokens": threshold_tokens,
                        "context_max": context_max,
                        "undo_depth": len(game.compaction_stack),
                    }
                    log_compaction_status(
                        session_id,
                        step,
                        status="not_needed",
                        trigger="automatic",
                        estimated_context_tokens=estimated_context_tokens,
                        threshold_tokens=threshold_tokens,
                        reason=reason,
                    )

            # Persist the turn BEFORE calling the Narrator (blind).
            # Skip: no player input to persist — Narrator reacts to current state alone.
            if not skip:
                if speech:
                    self._append_history(
                        game, "Player", speech, "speech", step, "speech" in transformed_fields
                    )
                if thought:
                    self._append_history(
                        game, "Player", thought, "thought", step, "thought" in transformed_fields
                    )
                if action:
                    self._append_history(
                        game, "Player", action, "action", step, "action" in transformed_fields
                    )

                # A private thought has no observable event for the Narrator to
                # resolve — unless there's also a narrator_hint providing external
                # context. Persist it as a complete step without replaying the
                # previous public event or inventing a reaction to hidden content.
                if thought and not speech and not action and not narrator_hint.strip():
                    if self.plugins is not None:
                        game = await self.plugins.hooks.filter(
                            "turn.before_commit", game, {"kind": "private_thought", "runner": self}
                        )
                    game.revision += 1
                    save_game(game)
                    if self.plugins is not None:
                        await self.plugins.hooks.action(
                            "turn.after_commit", {"game": game, "kind": "private_thought"}
                        )
                    return {
                        "narration": None,
                        "character_response": None,
                        "next_speaker": game.player.controlled_character_id,
                        "scene_update": None,
                        "turn_number": step,
                        "effective_input": effective_input,
                        "transformed_fields": transformed_fields,
                        "automatic_compaction": automatic_compaction,
                    }

            # Call Narrator
            if self.plugins is None:
                narrator_raw = await self._call_narrator(
                    game, step, effective_force_speaker, narrator_hint
                )
            else:
                narrator_game = game
                assert narrator_game is not None
                narrator_raw = await self.plugins.hooks.call_wrapped(
                    "narrator.call",
                    lambda: self._call_narrator(
                        narrator_game, step, effective_force_speaker, narrator_hint
                    ),
                    {"game": narrator_game, "turn_number": step, "runner": self},
                )
            if self.plugins is not None:
                narrator_raw = await self.plugins.hooks.filter(
                    "narrator.output",
                    narrator_raw,
                    {"game": game, "turn_number": step, "runner": self},
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
                if self.plugins is None:
                    character_response = await self._call_character(game, speaker, ctx, step)
                else:
                    character_game = game
                    assert character_game is not None
                    character_response = await self.plugins.hooks.call_wrapped(
                        "character.call",
                        lambda: self._call_character(character_game, speaker, ctx, step),
                        {
                            "game": character_game,
                            "character_id": speaker,
                            "turn_number": step,
                            "runner": self,
                        },
                    )
                if self.plugins is not None:
                    character_response = await self.plugins.hooks.filter(
                        "character.output",
                        character_response,
                        {
                            "game": game,
                            "character_id": speaker,
                            "turn_number": step,
                            "runner": self,
                        },
                    )
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

            if self.plugins is not None:
                game = await self.plugins.hooks.filter(
                    "turn.before_commit", game, {"kind": "turn", "runner": self}
                )
            game.revision += 1
            save_game(game)
            if self.plugins is not None:
                await self.plugins.hooks.action("turn.after_commit", {"game": game, "kind": "turn"})

            return {
                "narration": narration,
                "character_response": character_response,
                "next_speaker": speaker,
                "scene_update": scene_up,
                "turn_number": step,
                "effective_input": effective_input,
                "transformed_fields": transformed_fields,
                "automatic_compaction": automatic_compaction,
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
            game.plugin_state = copy.deepcopy(restore.plugin_state_snapshot)

            if self.plugins is not None:
                game = await self.plugins.hooks.filter(
                    "undo.before_commit",
                    game,
                    {"turn_number": last_turn_number, "removed": removed, "runner": self},
                )
            game.revision += 1
            save_game(game)
            if self.plugins is not None:
                await self.plugins.hooks.action(
                    "undo.after_commit",
                    {"game": game, "turn_number": last_turn_number, "removed": removed},
                )
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
            if self.plugins is not None:
                suggestions = await self.plugins.hooks.filter(
                    "suggestions.output",
                    suggestions,
                    {"game": game, "target_id": target_id, "runner": self},
                )
            return {"suggestions": suggestions}

    async def compact_session(
        self,
        session_id: str,
        *,
        progress: ProgressSink | None = None,
    ) -> dict[str, Any]:
        """Compact one session under its canonical transaction lock."""
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}
            return await self._compact_loaded_game(game, trigger="manual", progress=progress)

    async def _compact_loaded_game(
        self,
        game: GameState,
        *,
        trigger: CompactionTrigger,
        turn_number: int | None = None,
        estimated_context_tokens: int | None = None,
        threshold_tokens: int | None = None,
        progress: ProgressSink | None = None,
    ) -> dict[str, Any]:
        """Compact an already-loaded game while the caller owns its session lock."""
        checkpoint_id = next_compaction_id(game.session_id)
        sequence = 0

        def emit(
            stage: CompactionStage,
            completed: int = 0,
            total: int = 0,
            *,
            agent: str | None = None,
            result: dict[str, Any] | None = None,
            error: BaseException | None = None,
        ) -> None:
            nonlocal sequence
            if progress is None:
                return
            sequence += 1
            progress(
                CompactionProgress(
                    operation_id=checkpoint_id,
                    sequence=sequence,
                    stage=stage,
                    completed_units=completed,
                    total_units=total,
                    agent=agent,
                    result=result,
                    error_type=type(error).__name__ if error is not None else None,
                )
            )

        emit("checking")
        keep_recent = self.config.get("compaction_keep_recent_turns", 200)
        turn_numbers = list(dict.fromkeys(record.turn_number for record in game.history))
        if len(turn_numbers) <= keep_recent:
            status = (
                "blocked_by_retention_window"
                if trigger == "automatic" and estimated_context_tokens is not None
                else "not_needed"
            )
            result = {
                "status": status,
                "trigger": trigger,
                "compacted": False,
                "reason": "History smaller than the retained window.",
                "estimated_context_tokens": estimated_context_tokens,
                "threshold_tokens": threshold_tokens,
                "context_max": self.config.get("context_max"),
                "undo_depth": len(game.compaction_stack),
            }
            if trigger == "automatic":
                log_compaction_status(
                    game.session_id,
                    turn_number or (turn_numbers[-1] if turn_numbers else 0),
                    status=status,
                    trigger=trigger,
                    estimated_context_tokens=estimated_context_tokens,
                    threshold_tokens=threshold_tokens,
                    reason=str(result["reason"]),
                )
            emit("skipped", result=result)
            return result

        cutoff = turn_numbers[-keep_recent]
        evicted = [record for record in game.history if record.turn_number < cutoff]
        kept = [record for record in game.history if record.turn_number >= cutoff]
        relevant_ids = relevant_character_ids(
            game.characters,
            game.player.controlled_character_id,
            evicted,
        )
        total_units = 1 + len(relevant_ids)
        completed_units = 0
        emit("summarizing", completed_units, total_units)

        def model_completed(agent: str) -> None:
            nonlocal completed_units
            completed_units += 1
            emit(
                "model_completed",
                completed_units,
                total_units,
                agent=agent,
            )

        try:
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
                turn_number=turn_number if turn_number is not None else cutoff,
                on_model_completed=model_completed,
            )

            draft = CompactionDraft(
                history=copy.deepcopy(kept),
                story_summary=new_summary,
                character_notes={**game.character_notes, **changed_notes},
                plugin_state=copy.deepcopy(game.plugin_state),
            )
            emit("before_commit", completed_units, total_units)
            if self.plugins is not None:
                draft = await self.plugins.hooks.filter_strict(
                    "compaction.before_commit",
                    draft,
                    {"cutoff": cutoff, "evicted": copy.deepcopy(evicted), "runner": self},
                )
            if not isinstance(draft, CompactionDraft):
                raise TypeError("compaction.before_commit must return CompactionDraft")

            compacted = copy.deepcopy(game)
            compacted.history = copy.deepcopy(draft.history)
            compacted.story_summary = draft.story_summary
            compacted.character_notes = copy.deepcopy(draft.character_notes)
            compacted.plugin_state = copy.deepcopy(draft.plugin_state)
            committed_revision = game.revision + 1
            parent_id = game.compaction_stack[-1].checkpoint_id if game.compaction_stack else None
            checkpoint = {
                "schema_version": 1,
                "checkpoint_id": checkpoint_id,
                "parent_id": parent_id,
                "trigger": trigger,
                "created_at": datetime.now(UTC).isoformat(),
                "base_revision": game.revision,
                "cutoff_turn_number": cutoff,
                "max_turn_number": turn_numbers[-1],
                "evicted_history": [asdict(record) for record in evicted],
                "before_story_summary": game.story_summary,
                "before_character_notes": copy.deepcopy(game.character_notes),
                "after_history_hash": history_hash(compacted.history),
                "after_story_summary_hash": canonical_hash(compacted.story_summary),
                "after_character_notes_hash": canonical_hash(compacted.character_notes),
                "plugin_state_delta": build_plugin_delta(game.plugin_state, compacted.plugin_state),
            }
            emit("checkpointing", completed_units, total_units)
            checkpoint_path = Path(
                write_compaction_checkpoint(game.session_id, checkpoint_id, checkpoint)
            )
            compacted.compaction_stack.append(
                CompactionStackEntry(
                    checkpoint_id=checkpoint_id,
                    parent_id=parent_id,
                    trigger=trigger,
                    created_at=checkpoint["created_at"],
                    cutoff_turn_number=cutoff,
                    max_turn_number=turn_numbers[-1],
                    committed_revision=committed_revision,
                )
            )
            compacted.revision = committed_revision
            emit("committing", completed_units, total_units)
            try:
                save_game(compacted)
            except BaseException:
                checkpoint_path.unlink(missing_ok=True)
                raise
            game.__dict__.update(copy.deepcopy(compacted.__dict__))

            result = {
                "status": "compacted",
                "trigger": trigger,
                "compaction_id": checkpoint_id,
                "compacted": True,
                "reason": None,
                "cutoff_turn_number": cutoff,
                "evicted_records": len(evicted),
                "kept_records": len(compacted.history),
                "estimated_context_tokens": estimated_context_tokens,
                "threshold_tokens": threshold_tokens,
                "context_max": self.config.get("context_max"),
                "undo_depth": len(compacted.compaction_stack),
            }
            log_compact(
                game.session_id,
                cutoff,
                len(evicted),
                len(compacted.history),
                checkpoint_id=checkpoint_id,
                trigger=trigger,
                estimated_context_tokens=estimated_context_tokens,
                threshold_tokens=threshold_tokens,
            )
            if self.plugins is not None:
                await self.plugins.hooks.action(
                    "compaction.after_commit",
                    {
                        "game": compacted,
                        "cutoff": cutoff,
                        "evicted": len(evicted),
                        "result": result,
                    },
                )
            emit("completed", completed_units, total_units, result=result)
            return result
        except BaseException as error:
            emit("failed", completed_units, total_units, error=error)
            raise

    async def restore_last_compaction(self, session_id: str) -> dict:
        """Undo the newest compaction while preserving every later turn."""
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}
            result: dict[str, Any]
            if not game.compaction_stack:
                result = {
                    "restored": False,
                    "undone": False,
                    "reason": "No compaction checkpoint found.",
                    "remaining_undo_depth": 0,
                }
                log_restore_compaction(session_id, False, result["reason"])
                return result

            entry = game.compaction_stack[-1]
            try:
                checkpoint = load_compaction_checkpoint(session_id, entry.checkpoint_id)
                if checkpoint["schema_version"] != 1:
                    raise ValueError("Unsupported compaction checkpoint schema")
                if checkpoint["checkpoint_id"] != entry.checkpoint_id:
                    raise ValueError("Compaction checkpoint identity mismatch")
                expected_parent = (
                    game.compaction_stack[-2].checkpoint_id
                    if len(game.compaction_stack) > 1
                    else None
                )
                if checkpoint["parent_id"] != expected_parent:
                    raise ValueError("Compaction checkpoint parent mismatch")

                max_turn = int(checkpoint["max_turn_number"])
                compacted_prefix = [
                    record for record in game.history if record.turn_number <= max_turn
                ]
                later = [record for record in game.history if record.turn_number > max_turn]
                if history_hash(compacted_prefix) != checkpoint["after_history_hash"]:
                    raise ValueError("Compacted history prefix diverged")
                if canonical_hash(game.story_summary) != checkpoint["after_story_summary_hash"]:
                    raise ValueError("Story summary diverged after compaction")
                if canonical_hash(game.character_notes) != checkpoint["after_character_notes_hash"]:
                    raise ValueError("Character notes diverged after compaction")

                restored_plugin_state, conflicts = invert_plugin_delta(
                    game.plugin_state, checkpoint["plugin_state_delta"]
                )
                unresolved: dict[str, list[str]] = {}
                for plugin_id, paths in conflicts.items():
                    if self.plugins is None or not self.plugins.hooks.has_registration(
                        "compaction.undo_conflict", "filter", plugin_id
                    ):
                        unresolved[plugin_id] = paths
                        continue
                    current_namespace = copy.deepcopy(game.plugin_state.get(plugin_id))
                    resolved = await self.plugins.hooks.filter_for_plugin(
                        "compaction.undo_conflict",
                        plugin_id,
                        current_namespace,
                        {
                            "paths": paths,
                            "checkpoint_id": entry.checkpoint_id,
                            "runner": self,
                        },
                    )
                    if resolved is None:
                        restored_plugin_state.pop(plugin_id, None)
                    else:
                        restored_plugin_state[plugin_id] = resolved
                if unresolved:
                    reason = "Plugin state changed after compaction; undo requires a resolver."
                    result = {
                        "restored": False,
                        "undone": False,
                        "reason": reason,
                        "plugin_conflicts": sorted(unresolved),
                        "remaining_undo_depth": len(game.compaction_stack),
                    }
                    log_restore_compaction(session_id, False, reason)
                    return result

                evicted = [dict_to_turn_record(record) for record in checkpoint["evicted_history"]]
                draft = copy.deepcopy(game)
                draft.history = [*evicted, *compacted_prefix, *later]
                draft.story_summary = str(checkpoint["before_story_summary"])
                draft.character_notes = copy.deepcopy(checkpoint["before_character_notes"])
                draft.plugin_state = restored_plugin_state
                draft.compaction_stack.pop()
                draft.revision += 1
                save_game(draft)
                result = {
                    "restored": True,
                    "undone": True,
                    "compaction_id": entry.checkpoint_id,
                    "restored_records": len(evicted),
                    "history_length": len(draft.history),
                    "preserved_through_turn": max(
                        (record.turn_number for record in later), default=max_turn
                    ),
                    "remaining_undo_depth": len(draft.compaction_stack),
                    "plugin_conflicts": [],
                }
            except (KeyError, OSError, ValueError) as error:
                result = {
                    "restored": False,
                    "undone": False,
                    "reason": str(error),
                    "remaining_undo_depth": len(game.compaction_stack),
                }
            log_restore_compaction(
                session_id, result.get("restored", False), result.get("reason", "")
            )
            if self.plugins is not None and result.get("restored"):
                await self.plugins.hooks.action(
                    "compaction.restore_after_commit",
                    {"game": load_game(session_id), "result": result},
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
        # The player initiated this turn (actively or by skipping/passing), so exclude them
        # from being chosen as the next speaker to prevent immediate dialogue loops.
        exclude_speaker = game.player.controlled_character_id

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
            exclude_speaker=exclude_speaker,
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
        input_transformed: bool = False,
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
            input_transformed=input_transformed,
            mood_snapshot={cid: ch.mind.current_mood for cid, ch in game.characters.items()},
            plugin_state_snapshot=copy.deepcopy(game.plugin_state),
        )
        game.history.append(record)
