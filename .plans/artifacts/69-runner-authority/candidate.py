"""Isolated aperture/crossing authority experiment; never wired into the app."""

from __future__ import annotations

import copy
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from src.agents.prose import prose_events_for_viewers
from src.durable_state import PhysicalTransition, apply_physical_transition
from src.llm.schema import validate_json_schema
from src.models import GameState
from src.roteiro import ReplanDecision, evaluate_roteiro
from src.runner import Runner

Review = Callable[[str, dict[str, Any]], Awaitable[bool]]
FIELDS = {
    "kind": {
        "type": "string",
        "enum": ["aperture_change", "attempt_result"],
        "description": "'aperture_change' changes a portal; 'attempt_result' resolves an attempt.",
    },
    "target": {
        "type": "string",
        "enum": ["portal azul", "portal verde"],
        "description": "Portal addressed by this step.",
    },
    "actor": {
        "type": "string",
        "enum": ["", "Iara", "Bento", "Téo"],
        "description": "Character in 'attempt_result'; '' in 'aperture_change'.",
    },
    "from_state": {
        "type": "string",
        "enum": ["", "closed", "ajar", "open"],
        "description": "Current aperture of 'target' in 'aperture_change'; otherwise ''.",
    },
    "to_state": {
        "type": "string",
        "enum": ["", "closed", "ajar", "open"],
        "description": "New aperture of 'target' in 'aperture_change'; otherwise ''.",
    },
    "result": {
        "type": "string",
        "enum": ["", "blocked", "crossed"],
        "description": "'blocked' keeps 'actor' in place; 'crossed' completes their declared "
        "crossing through open 'target'. Use '' in 'aperture_change'.",
    },
    "cause": {
        "type": "string",
        "description": "New witnessed cause of 'aperture_change', naming 'target'; otherwise ''.",
    },
}
STEPS_SCHEMA = {
    "type": "array",
    "description": "All tracked physical changes and declared attempt results, in causal order. "
    "Use [] when neither occurs. Other events remain in 'perception_events'.",
    "items": {
        "type": "object",
        "properties": FIELDS,
        "required": list(FIELDS),
        "additionalProperties": False,
    },
}


class TurnRejectedError(ValueError):
    """A candidate turn failed admission and must remain uncommitted."""


def fixture_contract(game: GameState) -> dict[str, Any]:
    return game.plugin_state["authority_fixture"]


def project(game: GameState, turn_number: int) -> dict[str, Any]:
    """Public state, with no durable IDs or controlled-character formatting."""
    fixture = fixture_contract(game)
    return {
        "apertures": {
            entity.key: entity.dimensions["aperture"].state
            for entity in game.durable_state.physical_entities.values()
            if entity.key in fixture["routes"]
        },
        "positions": {
            character.mind.name: game.scene.positions[cid]
            for cid, character in game.characters.items()
        },
        "declared_attempts": fixture["attempts_by_turn"].get(str(turn_number), []),
        "accepted_steps": game.plugin_state.get("accepted_physical_steps", []),
        "physical_goals": fixture["goals"],
        "covered_goals": list(game.roteiro.anchors_seen) if game.roteiro else [],
    }


class AuthorityRunner(Runner):
    """Candidate owner of explicit fixture state, not an automatic goal extractor."""

    def __init__(self, client: httpx.AsyncClient, config: dict, review: Review) -> None:
        super().__init__(client, config)
        self.review = review

    def _evaluate_roteiro(self, game: GameState, next_turn: int) -> ReplanDecision:
        assert game.roteiro is not None
        return evaluate_roteiro(
            game.roteiro,
            game.history,
            game.player.controlled_character_id,
            next_turn,
            authoritative_anchors={goal["anchor"] for goal in fixture_contract(game)["goals"]},
        )

    async def _call_narrator(
        self,
        game: GameState,
        turn_number: int,
        forced_speaker: str | None = None,
        narrator_hint: str = "",
        **kwargs: Any,
    ) -> dict:
        context = list(kwargs.pop("extra_context", None) or [])
        context.append(
            "PHYSICAL CONTRACT: 'committed_physical' is already true; history may describe older "
            "states. Only 'physical_steps' proposes tracked aperture changes and crossings. "
            "An ajar gap is too narrow to cross. Do not invent attempts or new causes. "
            "Do not restage a completed crossing. Preserve all other events and their audiences "
            "in 'perception_events'. Parallel 'scene_update' and 'zone_moves' must agree with "
            "these steps.\ncommitted_physical: "
            + json.dumps(project(game, turn_number), ensure_ascii=False)
        )
        properties = dict(kwargs.pop("extra_schema_properties", None) or {})
        properties["physical_steps"] = STEPS_SCHEMA
        required = [*(kwargs.pop("extra_schema_required", None) or []), "physical_steps"]
        result = await super()._call_narrator(
            game,
            turn_number,
            forced_speaker,
            narrator_hint,
            extra_context=context,
            extra_schema_properties=properties,
            extra_schema_required=required,
            **kwargs,
        )
        if not await self.review(
            "director",
            {"start": project(game, turn_number), "candidate": result},
        ):
            raise TurnRejectedError("Director semantic review refused the complete candidate")
        return result

    def _apply_canon(
        self, game: GameState, narrator_raw: dict[str, Any], step: int = 0
    ) -> dict[str, Any] | None:
        """Validate the complete proposal on a copy before touching the turn draft."""
        steps = narrator_raw["physical_steps"]
        validate_json_schema(steps, STEPS_SCHEMA)
        candidate = copy.deepcopy(game)
        fixture = fixture_contract(candidate)
        entities = {
            entity.key: entity for entity in candidate.durable_state.physical_entities.values()
        }
        actors = {character.mind.name: cid for cid, character in candidate.characters.items()}
        attempts = {
            (item["actor"], item["target"]): item
            for item in fixture["attempts_by_turn"].get(str(step), [])
        }
        resolved: set[tuple[str, str]] = set()
        for index, operation in enumerate(steps):
            target = operation["target"]
            entity = entities[target]
            if operation["kind"] == "aperture_change":
                if operation["actor"] or operation["result"] or not operation["cause"].strip():
                    raise TurnRejectedError("Invalid aperture-change fields")
                apply_physical_transition(
                    candidate.durable_state,
                    PhysicalTransition(
                        transition_id=f"candidate:{step}:{index}",
                        entity_id=entity.entity_id,
                        key=target,
                        dimension="aperture",
                        from_state=operation["from_state"],
                        to_state=operation["to_state"],
                        turn_number=step,
                        update_id=f"candidate:{step}",
                    ),
                    expected_turn_number=step,
                )
                # The validator replaces the entity map atomically.
                entities = {
                    entity.key: entity
                    for entity in candidate.durable_state.physical_entities.values()
                }
            else:
                if operation["from_state"] or operation["to_state"] or operation["cause"]:
                    raise TurnRejectedError("Invalid attempt-result fields")
                pair = (operation["actor"], target)
                if pair not in attempts or pair in resolved:
                    raise TurnRejectedError("Undeclared or repeated crossing attempt")
                attempt = attempts[pair]
                route = fixture["routes"][target]
                cid = actors[operation["actor"]]
                if (
                    attempt["origin"] != route["origin"]
                    or attempt["destination"] != route["destination"]
                    or candidate.scene.positions[cid] != attempt["origin"]
                ):
                    raise TurnRejectedError("Crossing origin or destination does not match")
                aperture = entities[target].dimensions["aperture"].state
                if operation["result"] == "crossed":
                    if aperture != "open":
                        raise TurnRejectedError("Crossing needs an open portal at this step")
                    candidate.scene.positions[cid] = attempt["destination"]
                elif operation["result"] != "blocked" or aperture == "open":
                    raise TurnRejectedError("Blocked result unsupported by this fixture")
                resolved.add(pair)
        if resolved != set(attempts):
            raise TurnRejectedError("Not every declared attempt was resolved")

        scene_up = copy.deepcopy(narrator_raw.get("scene_update"))
        if scene_up:
            for target in fixture["routes"]:
                if (
                    target in scene_up
                    and scene_up[target] != entities[target].dimensions["aperture"].state
                ):
                    raise TurnRejectedError("Descriptive fact contradicts authoritative aperture")
            if "location" in scene_up and scene_up["location"] != candidate.scene.location:
                raise TurnRejectedError("Whole-scene relocation is outside this candidate")
            if "zones" in scene_up and scene_up["zones"] != candidate.scene.zones:
                raise TurnRejectedError("Zone graph replacement is outside this candidate")
            if (
                "present_characters" in scene_up
                and scene_up["present_characters"] != candidate.scene.present_characters
            ):
                raise TurnRejectedError("Roster replacement is outside this candidate")
        for cid, zone in (narrator_raw.get("zone_moves") or {}).items():
            if cid not in candidate.characters or zone != candidate.scene.positions[cid]:
                raise TurnRejectedError("Parallel movement disagrees with the typed outcome")

        reconciled = super()._apply_canon(candidate, narrator_raw, step)
        # Project every owned aperture after the ordinary descriptive update.
        for target in fixture["routes"]:
            candidate.scene.physical_facts[target] = entities[target].dimensions["aperture"].state
        candidate.plugin_state.setdefault("accepted_physical_steps", []).append(
            {"turn_number": step, "steps": copy.deepcopy(steps)}
        )
        game.scene = candidate.scene
        game.durable_state = candidate.durable_state
        game.plugin_state = candidate.plugin_state
        return reconciled

    def _collect_beat_evidence(
        self,
        game: GameState,
        narrator_raw: dict[str, Any],
        character_responses: list[dict[str, Any]],
        scene_up: dict[str, Any] | None,
    ) -> list[str]:
        if game.roteiro is None or game.roteiro.beat is None:
            return []
        goals = fixture_contract(game)["goals"]
        physical_anchors = {goal["anchor"] for goal in goals}
        descriptive_game = copy.deepcopy(game)
        assert descriptive_game.roteiro is not None and descriptive_game.roteiro.beat is not None
        descriptive_game.roteiro.beat.expected_anchors = [
            anchor
            for anchor in game.roteiro.beat.expected_anchors
            if anchor not in physical_anchors
        ]
        result = super()._collect_beat_evidence(
            descriptive_game, narrator_raw, character_responses, scene_up
        )
        state = project(game, 0)
        for goal in goals:
            if (
                goal["anchor"] not in game.roteiro.beat.expected_anchors
                or goal["anchor"] in game.roteiro.anchors_seen
            ):
                continue
            if goal["kind"] == "aperture":
                fulfilled = state["apertures"][goal["target"]] == goal["state"]
            else:
                fulfilled = state["positions"][goal["actor"]] == goal["destination"] and any(
                    operation["kind"] == "attempt_result"
                    and operation["target"] == goal["target"]
                    and operation["actor"] == goal["actor"]
                    and operation["result"] == "crossed"
                    for transaction in state["accepted_steps"]
                    for operation in transaction["steps"]
                )
            if fulfilled:
                result.append(goal["anchor"])
        return result

    async def _generate_prose(
        self, game: GameState, events: list[dict[str, Any]], turn_number: int, **kwargs: Any
    ) -> str:
        return await super()._render_narration(game, events, turn_number, **kwargs)

    async def _render_narration(
        self,
        game: GameState,
        events: list[dict[str, Any]],
        turn_number: int,
        viewers: set[str] | None = None,
        **kwargs: Any,
    ) -> str:
        prose = await self._generate_prose(game, events, turn_number, viewers=viewers, **kwargs)
        if not await self.review(
            "prose",
            {
                "state": project(game, turn_number),
                "events": copy.deepcopy(prose_events_for_viewers(events, viewers)),
                "viewers": sorted(viewers) if viewers is not None else None,
                "prose": prose,
            },
        ):
            raise TurnRejectedError("Final viewer prose review refused the candidate")
        return prose
