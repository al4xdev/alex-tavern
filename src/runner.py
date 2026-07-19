"""Runner — stateless orchestrator of the roleplay flow.

Each method loads/saves its own state. Does NOT have ``self.game`` or
``self.turn`` — local variables in each method, avoiding race conditions
between concurrent sessions.
"""

from __future__ import annotations

import asyncio
import copy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import httpx

from src.agents.character import CharacterOutput
from src.agents.character import act as character_act
from src.agents.narrator import build_narrator_messages, narrate, redact_whisper_leaks
from src.agents.narrator import suggest as narrator_suggest
from src.agents.prose import render_narration
from src.agents.perspective import (
    capture_memory,
    initialize_perspective,
    needs_identity_update,
    needs_memory_revision,
    revise_memory,
    update_identity,
)
from src.drive import evaluate_event_hazard, generate_event_seed
from src.roteiro import (
    ReplanDecision,
    collect_beat_evidence,
    describe_roteiro_for_director,
    evaluate_roteiro,
    generate_roteiro,
    replan_roteiro,
)
from src.perception import eligible_witnesses, render_events_for_viewer, repeats_event_text
from src.agents.summarizer import summarize
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
    log_command_input,
    log_command_result,
    log_compact,
    log_compaction_status,
    log_effective_turn_input,
    log_presence_change,
    log_presence_undo,
    log_drive_decision,
    log_time_skip,
    log_burst,
    log_restore_compaction,
    log_roteiro_decision,
    log_turn_input,
    log_undo,
)
from src.llm.tokens import estimate_prompt_tokens
from src.models import (
    CompactionStackEntry,
    GameState,
    Player,
    PresenceEditEntry,
    TurnRecord,
    default_present_characters,
    dict_to_perspective,
    dict_to_turn_record,
    perspective_to_dict,
    validate_present_characters,
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

# Task 40 v2 — exact invite text validated by replay (position: hint channel).
CLOCK_SKIP_INVITE = (
    "CLOCK SIGNAL: the scene has produced no material change for 2 turns; "
    "only waiting remains. Compress time now (time_skip_ticks) unless "
    "someone is visibly mid-action."
)


class PresenceRevisionConflictError(ValueError):
    """Raised by ``Runner.set_presence`` when the caller's revision is stale."""


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
            # The scenario's own present_characters only means anything paired with
            # its own characters. When the caller supplied custom characters but no
            # scene, borrowing this scene's location/time/facts is fine, but its
            # present_characters would reference IDs foreign to the caller's set —
            # leave it absent so the block below materializes the correct default.
            borrowed_present_characters = (
                list(sdata.get("present_characters", [])) if "characters" not in cfg else []
            )
            scene = Scene(
                location=sdata["location"],
                time_of_day=sdata["time_of_day"],
                present_characters=borrowed_present_characters,
                physical_facts=dict(sdata.get("physical_facts", {})),
            )
        else:
            raise ValueError("No default scene available.")

        # controlled_character_id must exist; otherwise, use the first character.
        controlled_id: str = cfg.get("controlled_character_id") or ""
        if controlled_id not in characters:
            controlled_id = next(iter(characters))

        player = Player(controlled_character_id=controlled_id)

        # present_characters is scene state, not derived registration state. An absent
        # value defaults to "everyone present"; a supplied value is validated, never
        # silently corrected.
        if scene.present_characters:
            scene.present_characters = validate_present_characters(
                scene.present_characters, characters, controlled_id
            )
        else:
            scene.present_characters = default_present_characters(characters)

        character_preset_ids = dict(cfg.get("character_preset_ids", {}))
        if set(character_preset_ids) - set(characters):
            raise ValueError("A preset can only be linked to a character in this session.")
        if character_preset_ids:
            from src.store.presets import load_preset

            for preset_name in character_preset_ids.values():
                if load_preset(preset_name) is None:
                    raise ValueError(f"Character preset '{preset_name}' was not found.")

        game = GameState(
            session_id=session_id,
            characters=characters,
            player=player,
            scene=scene,
            created_at=datetime.now(UTC).isoformat(),
            narrator_directives=cfg.get("narrator_directives", ""),
            character_preset_ids=character_preset_ids,
        )
        if self.plugins is not None:
            game = self.plugins.hooks.filter_sync(
                "session.before_commit", game, {"kind": "start", "runner": self}
            )
        save_game(game)
        if self.plugins is not None:
            self.plugins.hooks.action_sync("session.after_commit", {"game": game, "kind": "start"})
        return session_id

    async def execute_command(
        self, session_id: str, command_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Run a plugin utility command under the session transaction lock.

        Commands receive an isolated state snapshot and cannot advance history,
        revision, or any narrative state.
        """
        from src.plugins.commands import CommandError

        if self.plugins is None:
            raise CommandError("command_not_found", f"Command /{command_name} is not available.")
        registration = self.plugins.commands.get(command_name)
        if registration is None:
            raise CommandError("command_not_found", f"Command /{command_name} is not available.")

        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise CommandError("session_not_found", f"Session {session_id} was not found.")
            turn_number = (game.history[-1].turn_number + 1) if game.history else 1
            operation_id = uuid4().hex
            result_kind = registration.descriptor["result_kind"]
            log_command_input(
                session_id,
                turn_number,
                operation_id=operation_id,
                command=command_name,
                plugin_id=registration.plugin_id,
                plugin_version=registration.plugin_version,
                input_metadata=self.plugins.commands.log_metadata(payload),
            )
            try:
                result = await self.plugins.commands.invoke(
                    registration,
                    payload,
                    {
                        "game": copy.deepcopy(game),
                        "turn_number": turn_number,
                        "runner": self,
                        "operation_id": operation_id,
                    },
                )
            except BaseException as error:
                log_command_result(
                    session_id,
                    turn_number,
                    operation_id=operation_id,
                    command=command_name,
                    plugin_id=registration.plugin_id,
                    plugin_version=registration.plugin_version,
                    status="error",
                    result_kind=result_kind,
                    error_type=type(error).__name__,
                    error=str(error) or repr(error),
                )
                if isinstance(error, CommandError):
                    raise
                public_code = getattr(error, "code", None)
                if isinstance(public_code, str) and public_code:
                    public_field = getattr(error, "field", None)
                    raise CommandError(
                        public_code,
                        str(error) or "The command could not be completed.",
                        field=public_field if isinstance(public_field, str) else None,
                    ) from error
                raise
            log_command_result(
                session_id,
                turn_number,
                operation_id=operation_id,
                command=command_name,
                plugin_id=registration.plugin_id,
                plugin_version=registration.plugin_version,
                status="ok",
                result_kind=result_kind,
            )
            return {
                "status": "ok",
                "operation_id": operation_id,
                "command": command_name,
                "plugin_id": registration.plugin_id,
                "plugin_version": registration.plugin_version,
                "result_kind": result_kind,
                "result": result,
            }

    async def player_turn(
        self,
        session_id: str,
        speech: str = "",
        thought: str = "",
        action: str = "",
        force_speaker: str | None = None,
        narrator_hint: str = "",
        skip: bool = False,
        audience: list[str] | None = None,
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
           or the Narrator's ``next_speakers`` queue. Each present, non-controlled
           entry gets a character call in order, seeing the previous replies.
           The queue stops at the controlled character: control returns to the
           human and the runner never generates their speech.
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
            audience: Optional whisper — character IDs that perceive this turn's
                speech/action (everyone else stays unaware). A character reply in
                the same turn inherits the audience when the speaker belongs to it.

        Returns:
            Dict with: narration, character_responses, next_speakers,
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

            if audience is not None:
                if not speech.strip() and not action.strip():
                    raise ValueError("audience (whisper) requires speech or action")
                if not audience:
                    raise ValueError("audience cannot be an empty list")
                unknown = [cid for cid in audience if cid not in game.characters]
                if unknown:
                    raise ValueError(f"audience references unknown character IDs: {unknown}")
                absent = [cid for cid in audience if cid not in game.scene.present_characters]
                if absent:
                    raise ValueError(f"audience references absent characters: {absent}")
                audience = list(dict.fromkeys(audience))

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

            force_speaker_present = (
                force_speaker in game.characters and force_speaker in game.scene.present_characters
            )
            effective_force_speaker = (
                force_speaker
                if force_speaker and (force_speaker_present or force_speaker == "Narrator")
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
            context_max = self.config.get("context_max")
            if (
                self.config.get("automatic_compaction_enabled", False)
                and isinstance(context_max, int)
            ):
                probe = copy.deepcopy(game)
                if not skip:
                    if speech:
                        self._append_history(probe, "Player", speech, "speech", step)
                    if thought:
                        self._append_history(probe, "Player", thought, "thought", step)
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
                        game,
                        "Player",
                        speech,
                        "speech",
                        step,
                        "speech" in transformed_fields,
                        audience=audience,
                    )
                if thought:
                    self._append_history(
                        game, "Player", thought, "thought", step, "thought" in transformed_fields
                    )
                if action:
                    self._append_history(
                        game,
                        "Player",
                        action,
                        "action",
                        step,
                        "action" in transformed_fields,
                        audience=audience,
                    )

            # Bounded autonomous burst (Task 37): on a bare skip turn the world
            # may play several beats before control returns. Each beat commits
            # as its OWN turn (undo pops one beat; a crash leaves only complete
            # beats). Stop conditions are deterministic; a manual force always
            # means exactly one beat.
            max_beats = 1
            if skip and not effective_force_speaker:
                max_beats = max(1, int(self.config.get("autonomous_burst_max_beats", 1)))
            beats: list[dict[str, Any]] = []
            narrator_only_streak = 0
            burst_event_texts: list[str] = []
            stop_reason = "budget_exhausted"
            for beat_index in range(max_beats):
                if beat_index:
                    step = (game.history[-1].turn_number + 1) if game.history else 1
                # Drive scheduler (Task 33): on a skip turn without a manual hint,
                # CODE decides whether the world receives an autonomous event; a
                # small structured call only writes WHAT the event is. The seed is
                # always an external world event for the blind Narrator — never a
                # move for the human's character.
                injected_event = False
                if beat_index == 0 and skip and not narrator_hint.strip():
                    decision = evaluate_event_hazard(game, self.config)
                    event_seed = ""
                    if decision.fired:
                        event_seed = await generate_event_seed(self.client, game, self.config, step)
                        if event_seed:
                            narrator_hint = event_seed
                            injected_event = True
                    log_drive_decision(
                        game.session_id,
                        step,
                        fired=injected_event,
                        probability=decision.probability,
                        quiet_turns=decision.quiet_turns,
                        roll=decision.roll,
                        event_seed=event_seed,
                    )
                if beat_index == 0 and skip and not narrator_hint.strip():
                    # Time compression invite (Task 40 v2): the player passing is
                    # the human "summary mode" signal. The Director DECIDES the
                    # skip; the code only invites and later clamps the result.
                    # Validated: a live scene never skips even when invited.
                    narrator_hint = CLOCK_SKIP_INVITE

                # Roteiro maintenance (Task 38): CODE decides whether the story
                # direction needs a new rolling beat (coverage/budget/drift over
                # history, with hysteresis); a structured call only writes WHAT
                # the beat says. Runs per beat so bursts stay on-plan too.
                clock_event = await self._maintain_roteiro(game, step)
                if clock_event and not narrator_hint.strip():
                    # The act deadline's world_event stages THIS beat via the
                    # UPCOMING EVENT contract (same channel the drive uses).
                    narrator_hint = clock_event
                    injected_event = True

                # Call Narrator — extra_context/extra_schema let plugins add read-only
                # prompt lines and an optional output key (narrator.context/narrator.schema)
                # without a provider- or plugin-specific branch here.
                extra_context: list[str] = []
                extra_schema_properties: dict[str, Any] = {}
                extra_schema_required: list[str] = []
                if self.plugins is not None:
                    extra_context = await self.plugins.hooks.filter(
                        "narrator.context", [], {"game": game, "turn_number": step, "runner": self}
                    )
                    schema_extension = await self.plugins.hooks.filter(
                        "narrator.schema",
                        {"properties": {}, "required": []},
                        {"game": game, "turn_number": step, "runner": self},
                    )
                    extra_schema_properties = dict(schema_extension.get("properties", {}))
                    extra_schema_required = list(schema_extension.get("required", []))

                if self.plugins is None:
                    narrator_raw = await self._call_narrator(
                        game,
                        step,
                        effective_force_speaker,
                        narrator_hint,
                        extra_context=extra_context,
                        extra_schema_properties=extra_schema_properties,
                        extra_schema_required=extra_schema_required,
                    )
                else:
                    narrator_game = game
                    assert narrator_game is not None
                    narrator_raw = await self.plugins.hooks.call_wrapped(
                        "narrator.call",
                        lambda: self._call_narrator(
                            narrator_game,
                            step,
                            effective_force_speaker,
                            narrator_hint,
                            extra_context=extra_context,
                            extra_schema_properties=extra_schema_properties,
                            extra_schema_required=extra_schema_required,
                        ),
                        {"game": narrator_game, "turn_number": step, "runner": self},
                    )
                if self.plugins is not None:
                    narrator_raw = await self.plugins.hooks.filter(
                        "narrator.output",
                        narrator_raw,
                        {"game": game, "turn_number": step, "runner": self},
                    )

                # Within a burst a stimulus must be resolved once: events that
                # near-duplicate an earlier beat's event are dropped so the
                # renderer never tells the same thud-and-whinny three times
                # (Task 37, critic finding).
                if max_beats > 1:
                    fresh_events = [
                        event
                        for event in narrator_raw["perception_events"]
                        if not repeats_event_text(event["content"], burst_event_texts)
                    ]
                    narrator_raw["perception_events"] = fresh_events
                    burst_event_texts.extend(event["content"] for event in fresh_events)

                # A manual force wins over whatever the Director (or a plugin filter)
                # returned — the queue collapses to the forced speaker alone.
                queue: list[str] = (
                    [effective_force_speaker]
                    if effective_force_speaker
                    else list(narrator_raw["next_speakers"])
                )
                controlled = game.player.controlled_character_id
                character_responses: list[dict[str, Any]] = []

                # Canon applies BEFORE the prose renders (Task 41): the renderer
                # must stage the reconciled scene, not the stale one — rendering
                # old canon against new events made the prose invent its own
                # reconciliation ("he enters the hall" while the event had him
                # racing through the city). Witness clamps were already computed
                # from the pre-move scene inside narrate(), so perception
                # fairness ("arrival counts next beat") is unchanged.
                scene_up = narrator_raw.get("scene_update")
                zone_moves = narrator_raw.get("zone_moves") or {}
                if zone_moves and scene_up and "location" in scene_up:
                    # Partial movement is expressed by zones; the stage location
                    # only changes when the WHOLE scene moves. The model often
                    # emits both (zone split + a location change that would drag
                    # the rest of the cast along in canon) — clamp the location
                    # change unless every present character moved.
                    movers = set(zone_moves)
                    present = {
                        cid
                        for cid in game.scene.present_characters
                        if cid in game.characters
                    }
                    if not present.issubset(movers):
                        scene_up = {k: v for k, v in scene_up.items() if k != "location"}
                if scene_up:
                    self._update_scene(game, scene_up)
                new_zones = [z for z in zone_moves.values() if z not in game.scene.zones]
                if new_zones and not game.scene.zones:
                    # First split of a zone-less stage: everyone else keeps the
                    # current stage as their zone, so the new zone is genuinely
                    # isolated (unplaced characters perceive everything).
                    stage = (game.scene.location or "").strip()[:60] or "palco"
                    game.scene.zones[stage] = []
                    for cid in game.scene.present_characters:
                        if cid in game.characters and cid not in zone_moves:
                            game.scene.positions[cid] = stage
                for zone in new_zones:
                    game.scene.zones.setdefault(zone, [])  # new zones start isolated
                for moved_id, zone in zone_moves.items():
                    game.scene.positions[moved_id] = zone
                for zone, audible in (narrator_raw.get("zone_link_updates") or {}).items():
                    if zone in game.scene.zones:
                        game.scene.zones[zone] = [
                            other for other in audible if other in game.scene.zones
                        ]

                # Time compression (Task 40 v2): the Director may REQUEST a skip;
                # the CODE clamps and applies it. The offstage change enters the
                # world as a typed observation every present character witnesses,
                # so prose, perspectives and history inherit it through the
                # normal channels — the clock itself only ever moves forward.
                raw_ticks = narrator_raw.get("time_skip_ticks")
                skip_ticks = max(0, min(8, raw_ticks)) if isinstance(raw_ticks, int) else 0
                if skip_ticks:
                    skip_summary = str(narrator_raw.get("time_skip_summary") or "").strip()[:300]
                    game.narrative_tick += skip_ticks
                    if skip_summary:
                        narrator_raw["perception_events"].append(
                            {
                                "event_kind": "observation",
                                "subject_id": "Narrator",
                                "content": skip_summary,
                                "witness_ids": [
                                    cid
                                    for cid in game.scene.present_characters
                                    if cid in game.characters
                                ],
                            }
                        )
                    log_time_skip(
                        game.session_id,
                        step,
                        ticks=skip_ticks,
                        summary=skip_summary,
                        narrative_tick_after=game.narrative_tick,
                    )

                # Decision -> Prose split (Task 36): the blind renderer turns the
                # validated events into reader prose CONCURRENTLY with the routed
                # speakers' ledger preparation (they share no data dependency; the
                # latency concentrates at this beat boundary). Deterministic merge:
                # the narration record is always appended before any character
                # record, regardless of completion order.
                prepare_ids = list(
                    dict.fromkeys(
                        speaker
                        for speaker in queue
                        if speaker != controlled
                        and speaker in game.characters
                        and speaker in game.scene.present_characters
                    )
                )
                if max_beats > 1 and not narrator_raw["perception_events"]:
                    # A burst beat with zero novel events narrates NOTHING: the
                    # atmospheric fallback would only re-describe the standing
                    # tableau (a null recap turn). Routed characters still speak.
                    narration = ""
                    await asyncio.gather(
                        *(self._ensure_perspective(game, viewer, step) for viewer in prepare_ids)
                    )
                else:
                    narration, *_ = await asyncio.gather(
                        self._render_narration(game, narrator_raw["perception_events"], step),
                        *(self._ensure_perspective(game, viewer, step) for viewer in prepare_ids),
                    )
                if narration:
                    self._append_history(game, "Narrator", narration, "narration", step)

                # The queue runs sequentially WITHOUT Narrator calls in between: each
                # response is appended to history before the next character call, so a
                # later speaker perceives the earlier ones through the normal visibility
                # filter. The Narrator is blind and can route to the controlled
                # character — the queue stops there and control returns to the human
                # (the runner never generates their speech). A whispered exchange stays
                # whispered: when a replying character is part of the turn's audience,
                # its reply keeps the same audience.
                for position, speaker in enumerate(queue):
                    if speaker == controlled:
                        break
                    if speaker not in game.characters or speaker not in game.scene.present_characters:
                        continue
                    reply_audience = (
                        audience if audience is not None and speaker in audience else None
                    )
                    await self._ensure_perspective(game, speaker, step)
                    # Each speaker receives only the typed perception events they
                    # witness (zone-clamped upstream), projected through their own
                    # identity ledger — the free-prose context_for_character is gone.
                    ctx = render_events_for_viewer(
                        narrator_raw["perception_events"],
                        speaker,
                        game.characters,
                        game.character_perspectives.get(speaker),
                    )
                    if not ctx.strip():
                        # An empty perception void invites the model to hallucinate a
                        # stimulus (an isolated character greeted a visitor that does
                        # not exist). State the deterministic fact instead: nothing
                        # new reached this character's senses.
                        ctx = (
                            "Nothing new reaches your senses right now; you are "
                            "alone with your current activity and thoughts."
                        )
                    # Deterministic guard behind the Narrator's whisper rule: the
                    # "denial that reveals" pattern ("you did not hear the password X")
                    # occasionally leaks whispered content into an event rendered for
                    # a character outside the whisper's audience. Strip it here,
                    # before the character ever sees it; audience members unaffected.
                    ctx = redact_whisper_leaks(ctx, game.history, speaker, game.characters, game.scene)
                    if self.plugins is None:
                        character_response = await self._call_character(
                            game, speaker, ctx, step, reply_audience=reply_audience
                        )
                    else:
                        character_game = game
                        assert character_game is not None
                        character_response = await self.plugins.hooks.call_wrapped(
                            "character.call",
                            lambda g=character_game, s=speaker, c=ctx, ra=reply_audience: (
                                self._call_character(g, s, c, step, reply_audience=ra)
                            ),
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
                            game,
                            speaker,
                            character_response["speech"],
                            "speech",
                            step,
                            audience=reply_audience,
                        )
                    if character_response.get("action_intent"):
                        # An intent is an ATTEMPT: it becomes an action record (the
                        # existing physics — resolved by the next beat's Director),
                        # never an outcome. Zone-scoped audience is computed by
                        # _append_history like any physical act.
                        self._append_history(
                            game,
                            speaker,
                            character_response["action_intent"],
                            "action",
                            step,
                        )
                    character_responses.append({"character_id": speaker, **character_response})

                # Update characters' moods
                mood_updates = narrator_raw.get("mood_updates")
                if mood_updates:
                    self._update_moods(game, mood_updates)

                if self.plugins is not None:
                    # Each plugin validates and applies its own narrator.schema property (if
                    # present in narrator_raw) to this same-turn draft. A plugin that finds
                    # its own proposal invalid returns the draft unchanged instead of raising —
                    # raising here would trip the shared crash policy and disable the plugin,
                    # which is reserved for genuine bugs, not routine LLM validation failures.
                    game = await self.plugins.hooks.filter(
                        "narrator.result",
                        game,
                        {"narrator_output": narrator_raw, "turn_number": step, "runner": self},
                    )
                    game = await self.plugins.hooks.filter(
                        "turn.before_commit", game, {"kind": "turn", "runner": self}
                    )
                game.turns_since_injected_event = (
                    0 if injected_event else game.turns_since_injected_event + 1
                )
                # Roteiro coverage (Task 38): record which of the current beat's
                # anchors this beat actually put in play, measured on the
                # AUTHORITATIVE evidence — the Director's typed events and the
                # characters' own words/acts — not the lossy prose. Audible
                # speech never reaches the renderer, so the prose can never be
                # the coverage surface without punishing the Director for obeying.
                if game.roteiro is not None and game.roteiro.beat is not None:
                    evidence_texts = [
                        event["content"] for event in narrator_raw["perception_events"]
                    ]
                    for response in character_responses:
                        if response.get("speech"):
                            evidence_texts.append(response["speech"])
                        if response.get("action_intent"):
                            evidence_texts.append(response["action_intent"])
                    newly_seen = collect_beat_evidence(game.roteiro, evidence_texts)
                    if newly_seen:
                        game.roteiro.anchors_seen.extend(newly_seen)
                game.narrative_tick += 1
                game.revision += 1
                save_game(game)
                if self.plugins is not None:
                    await self.plugins.hooks.action("turn.after_commit", {"game": game, "kind": "turn"})

                beat_result = {
                    "narration": narration,
                    "character_responses": character_responses,
                    "next_speakers": queue,
                    "scene_update": scene_up,
                    "turn_number": step,
                }
                beats.append(beat_result)
                narrator_hint = ""
                if controlled in queue:
                    stop_reason = "player_addressed"
                    break
                if narrator_raw.get("return_control"):
                    stop_reason = "protagonist_decision"
                    break
                if character_responses:
                    narrator_only_streak = 0
                elif max_beats > 1 and not narrator_raw["perception_events"]:
                    # Nothing new happened and nobody spoke: the beat settled.
                    stop_reason = "beat_settled"
                    break
                else:
                    narrator_only_streak += 1
                    if narrator_only_streak >= 2:
                        stop_reason = "beat_settled"
                        break

            if max_beats > 1:
                log_burst(
                    game.session_id,
                    beats[-1]["turn_number"],
                    beat_count=len(beats),
                    stop_reason=stop_reason,
                    first_turn=beats[0]["turn_number"],
                )
            return {
                **beats[-1],
                "beats": beats,
                "burst_stop_reason": stop_reason if max_beats > 1 else None,
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
            game.character_perspectives = {
                viewer_id: dict_to_perspective(item)
                for viewer_id, item in restore.perspective_snapshot.items()
            }

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
        if (
            trigger == "automatic"
            and estimated_context_tokens is not None
            and threshold_tokens is not None
            and estimated_context_tokens > threshold_tokens
            and len(turn_numbers) <= keep_recent
            and len(turn_numbers) > 8
        ):
            # Under real context pressure the configured retention window must
            # not block the automatic compaction it exists to serve: shrink it
            # adaptively to the most recent half (never below 4 turns), so the
            # session compacts instead of silently trimming history away
            # (Task 23 — trim/compaction gap).
            keep_recent = max(4, len(turn_numbers) // 2)
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
        # One model unit: the world summary. Private memory is the perspective
        # ledger's continuous job now (Task 39) - no per-character fan-out.
        total_units = 1
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
            new_summary = await summarize(
                client=self.client,
                characters=game.characters,
                controlled_id=game.player.controlled_character_id,
                story_summary=game.story_summary,
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
                "after_history_hash": history_hash(compacted.history),
                "after_story_summary_hash": canonical_hash(compacted.story_summary),
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

    async def set_presence(
        self, session_id: str, present_characters: list[str], expected_revision: int
    ) -> dict:
        """Administrative, out-of-band presence edit — no turn, no LLM call, no history.

        Guards against overwriting a concurrent turn/edit via ``expected_revision``
        (the client's whole view of the session). The previous list is pushed onto
        ``presence_edit_stack`` so ``undo_last_presence_edit`` can revert it later.
        """
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}
            if game.revision != expected_revision:
                raise PresenceRevisionConflictError(
                    "Session was modified concurrently; reload and retry with the current revision."
                )
            validated = validate_present_characters(
                present_characters, game.characters, game.player.controlled_character_id
            )
            before = list(game.scene.present_characters)
            changed_ids = sorted(set(before) ^ set(validated))
            entry = PresenceEditEntry(
                edit_id=uuid4().hex[:8],
                created_at=datetime.now(UTC).isoformat(),
                origin="human",
                before=before,
                after=validated,
                committed_revision=game.revision + 1,
            )
            game.scene.present_characters = validated
            game.presence_edit_stack.append(entry)
            game.revision += 1
            save_game(game)
            log_presence_change(
                session_id,
                origin=entry.origin,
                changed_ids=changed_ids,
                revision=game.revision,
                edit_id=entry.edit_id,
            )
            return {
                "changed": True,
                "present_characters": validated,
                "revision": game.revision,
                "edit_id": entry.edit_id,
            }

    async def undo_last_presence_edit(self, session_id: str) -> dict:
        """Undo the newest out-of-band admin presence edit — strictly LIFO.

        Only ever touches ``presence_edit_stack[-1]``. Before restoring, compares
        the CURRENT presence against that entry's recorded ``after`` — the same
        content-divergence check ``restore_last_compaction`` uses (not a revision
        comparison), so a later Narrator ``presence_update`` or another admin edit is
        never silently overwritten; the restore is rejected explicitly instead.
        """
        async with _get_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return {"error": f"Session {session_id} not found"}
            if not game.presence_edit_stack:
                reason = "No presence edit found."
                log_presence_undo(session_id, False, reason)
                return {"restored": False, "reason": reason, "remaining_undo_depth": 0}

            entry = game.presence_edit_stack[-1]
            if list(game.scene.present_characters) != entry.after:
                reason = (
                    "Presence changed again since this edit; undo would overwrite a later change."
                )
                log_presence_undo(session_id, False, reason)
                return {
                    "restored": False,
                    "reason": reason,
                    "remaining_undo_depth": len(game.presence_edit_stack),
                }

            try:
                restored = validate_present_characters(
                    entry.before, game.characters, game.player.controlled_character_id
                )
            except ValueError as error:
                log_presence_undo(session_id, False, str(error))
                return {
                    "restored": False,
                    "reason": str(error),
                    "remaining_undo_depth": len(game.presence_edit_stack),
                }

            game.scene.present_characters = restored
            game.presence_edit_stack.pop()
            game.revision += 1
            save_game(game)
            log_presence_undo(session_id, True, "")
            return {
                "restored": True,
                "present_characters": restored,
                "revision": game.revision,
                "remaining_undo_depth": len(game.presence_edit_stack),
            }

    # ── Private Methods ───────────────────────────────────────────────────

    async def _maintain_roteiro(self, game: GameState, turn_number: int) -> str | None:
        """Compile the roteiro on first need; replan when the code signals say so.

        The replan TRIGGER is deterministic (``evaluate_roteiro``); the LLM only
        writes beat content. Every evaluation is logged so acceptance runs can
        audit that zero triggers came from model self-assessment.
        """
        if not bool(self.config.get("roteiro_enabled", False)):
            return None
        next_turn = (game.history[-1].turn_number + 1) if game.history else 1
        if game.roteiro is None:
            game.roteiro = await generate_roteiro(self.client, game, self.config, turn_number)
            game.roteiro.act_started_tick = game.narrative_tick
            return None

        # Narrative clock (Task 40): when the current act's tick deadline
        # expires, the CODE stages its world_event (returned to the caller as
        # this beat's UPCOMING EVENT) and advances the act - the world never
        # waits for the conversation to finish. Deterministic; the LLM only
        # wrote the event text at planning time.
        act = (
            game.roteiro.acts[game.roteiro.act_index]
            if game.roteiro.act_index < len(game.roteiro.acts)
            else None
        )
        if (
            act is not None
            and act.duration_ticks > 0
            and game.narrative_tick - game.roteiro.act_started_tick >= act.duration_ticks
        ):
            world_event = act.world_event.strip()
            log_roteiro_decision(
                game.session_id,
                turn_number,
                action="act_deadline",
                reason="clock",
                beat_id=game.roteiro.beat.beat_id if game.roteiro.beat else "none",
                anchors_missing=[],
                actors_missing=[],
            )
            # The act advance is CODE-owned: the deadline concluded it, whatever
            # the conversation was doing. The replan only writes the next act's
            # opening beat (its status text says the world_event just happened).
            if game.roteiro.act_index + 1 < len(game.roteiro.acts):
                game.roteiro.act_index += 1
            game.roteiro.act_started_tick = game.narrative_tick
            game.roteiro.beat_replans_in_act = 0
            game.roteiro = await replan_roteiro(
                self.client,
                game,
                ReplanDecision(action="replan_beat", reason="act_deadline"),
                self.config,
                turn_number,
                current_tick=game.narrative_tick,
            )
            return world_event or None
        decision = evaluate_roteiro(
            game.roteiro, game.history, game.player.controlled_character_id, next_turn
        )
        log_roteiro_decision(
            game.session_id,
            turn_number,
            action=decision.action or "none",
            reason=decision.reason,
            beat_id=game.roteiro.beat.beat_id if game.roteiro.beat else "none",
            anchors_missing=list(decision.progress.anchors_missing) if decision.progress else [],
            actors_missing=list(decision.progress.actors_missing) if decision.progress else [],
        )
        if decision.action:
            game.roteiro = await replan_roteiro(
                self.client,
                game,
                decision,
                self.config,
                turn_number,
                current_tick=game.narrative_tick,
            )
        return None

    async def _call_narrator(
        self,
        game: GameState,
        turn_number: int,
        forced_speaker: str | None = None,
        narrator_hint: str = "",
        extra_context: list[str] | None = None,
        extra_schema_properties: dict[str, Any] | None = None,
        extra_schema_required: list[str] | None = None,
    ) -> dict:
        """Calls Narrator agent (blind) with full context. Returns result."""
        # The player initiated this turn (actively or by skipping/passing), so exclude them
        # from being chosen as the next speaker to prevent immediate dialogue loops.
        exclude_speaker = game.player.controlled_character_id

        roteiro_lines = (
            describe_roteiro_for_director(game.roteiro, game.characters)
            if game.roteiro is not None
            else None
        )
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
            extra_context=extra_context,
            extra_schema_properties=extra_schema_properties,
            extra_schema_required=extra_schema_required,
            roteiro_lines=roteiro_lines,
        )

    async def _render_narration(
        self,
        game: GameState,
        events: list[dict[str, Any]],
        turn_number: int,
    ) -> str:
        """Blind prose renderer boundary (Task 36) — injectable like the other agents."""
        return await render_narration(
            self.client,
            game.scene,
            game.characters,
            game.player.controlled_character_id,
            game.history,
            events,
            self.config,
            session_id=game.session_id,
            turn_number=turn_number,
        )

    async def _ensure_perspective(
        self,
        game: GameState,
        viewer_id: str,
        turn_number: int,
    ) -> None:
        """Initialize/refresh one viewer's identity ledger inside the turn draft.

        Lazy and transactional: the ledger is compiled from the viewer's priors
        the first time this viewer is about to speak, and the small identity
        updater runs only when the deterministic predicate says it can matter
        (strangers remain AND new speech became visible to the viewer). Both
        calls commit with the turn or not at all.
        """
        perspective = game.character_perspectives.get(viewer_id)
        if perspective is None:
            perspective = await initialize_perspective(
                self.client,
                viewer_id,
                game.characters,
                game.player.controlled_character_id,
                self.config,
                session_id=game.session_id,
                turn_number=turn_number,
            )
            game.character_perspectives[viewer_id] = perspective
        if needs_identity_update(game.history, viewer_id, perspective):
            await update_identity(
                self.client,
                viewer_id,
                perspective,
                game.history,
                game.characters,
                game.player.controlled_character_id,
                self.config,
                session_id=game.session_id,
                turn_number=turn_number,
            )
        # Durable memory (Task 39): fold what this viewer has perceived since it
        # last spoke into its ledger memory — deterministic, no LLM, so rapport
        # accumulates within the session without waiting for a compaction.
        capture_memory(
            perspective,
            game.history,
            viewer_id,
            game.characters,
            game.player.controlled_character_id,
        )
        if needs_memory_revision(perspective):
            # Semantic revision (Task 39 inc.2): condense the older digest into
            # memory_summary instead of losing it to the MAX bound. Maintenance
            # call - failures are swallowed inside and retried on a later turn.
            await revise_memory(
                self.client,
                viewer_id,
                perspective,
                game.characters,
                self.config,
                session_id=game.session_id,
                turn_number=turn_number,
            )

    async def _call_character(
        self,
        game: GameState,
        character_id: str,
        context: str,
        turn_number: int,
        reply_audience: list[str] | None = None,
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
            scene=game.scene,
            reply_audience=reply_audience,
            viewer_perspective=game.character_perspectives.get(character_id),
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
        audience: list[str] | None = None,
    ) -> None:
        """Creates a TurnRecord with deepcopy of the Scene/moods and adds it to history.

        ```turn_number`` is explicit — all records of the same turn
        (human speech/thought/action, narration, Character speech) share the
        same number and the same snapshot, a pre-requisite for undo to revert
        the entire step (scene and moods).

        With a zone graph, perception is structural: a speech/action record's
        effective audience is computed from who can physically perceive the
        speaker's zone. A supplied whisper audience is intersected with it (you
        cannot whisper to someone who cannot hear you); a public record that not
        everyone can perceive becomes zone-scoped by construction, reusing the
        whisper visibility machinery end to end.
        """
        audience_origin = "whisper" if audience is not None else "zone"
        if game.scene.zones and content_type in ("speech", "action"):
            subject = (
                game.player.controlled_character_id if speaker == "Player" else speaker
            )
            if subject in game.characters:
                eligible = eligible_witnesses(game.scene, game.characters, subject)
                others = {
                    cid
                    for cid in game.scene.present_characters
                    if cid in game.characters and cid != subject
                }
                if audience is None:
                    if eligible != others:
                        audience = sorted(eligible)
                else:
                    audience = sorted(set(audience) & (eligible | {subject}))
        record = TurnRecord(
            turn_number=turn_number,
            speaker=speaker,
            content=content,
            content_type=content_type,
            scene_snapshot=copy.deepcopy(game.scene),
            input_transformed=input_transformed,
            mood_snapshot={cid: ch.mind.current_mood for cid, ch in game.characters.items()},
            plugin_state_snapshot=copy.deepcopy(game.plugin_state),
            audience=list(audience) if audience is not None else None,
            audience_origin=audience_origin,
            perspective_snapshot={
                viewer_id: perspective_to_dict(perspective)
                for viewer_id, perspective in game.character_perspectives.items()
            },
        )
        game.history.append(record)
