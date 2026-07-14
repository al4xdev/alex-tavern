"""Dataclasses for the multi-agent roleplay system."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CharacterMind:
    """Visible to the character itself and the Narrator."""

    name: str
    personality: str  # personality description, goes to the Narrator's and character's prompts
    knowledge: list[str]  # facts that the character knows
    current_mood: str  # updated by the Narrator via mood_updates each turn


@dataclass
class CharacterBody:
    """Only the Narrator sees — physical appearance."""

    name: str
    physical_description: str  # physical appearance, body
    outfit: str  # current outfit (mutable)


@dataclass
class Character:
    """Aggregates Mind + Body. No reference to the LLM client."""

    mind: CharacterMind
    body: CharacterBody


@dataclass
class Player:
    """Player agency through the controlled character, without a separate named entity."""

    controlled_character_id: str  # which character the player controls, fixed in the session


@dataclass
class Scene:
    """State of the current scene."""

    location: str
    time_of_day: str
    present_characters: list[str]  # ["C1", "C2", "Player"]
    physical_facts: dict[str, str]  # {"weather": "chuva", "door": "aberta"}


@dataclass
class TurnRecord:
    """An entry in the history — contains a copy of the scene/mood at that moment."""

    turn_number: int
    speaker: str  # "Player", "C1", "C2", "Narrator"
    content: str
    content_type: str  # "speech", "thought", "narration", "action"
    scene_snapshot: Scene  # deepcopy of the scene in that turn
    input_transformed: bool = False
    mood_snapshot: dict[str, str] = field(default_factory=dict)  # {cid: current_mood}
    plugin_state_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class GameState:
    """Persists between turns in the session JSON."""

    session_id: str
    characters: dict[str, Character]  # {"C1": Character, "C2": Character}
    player: Player
    scene: Scene
    history: list[TurnRecord] = field(default_factory=list)
    created_at: str = ""  # ISO timestamp
    narrator_directives: str = ""  # world/tone/extra rule instructions for the Narrator
    story_summary: str = ""  # world summary of compacted turns — only the Narrator sees
    # {cid: note} — each character only receives their own note, never another's
    character_notes: dict[str, str] = field(default_factory=dict)
    revision: int = 0
    plugin_state: dict[str, Any] = field(default_factory=dict)


def trim_history_by_tokens(
    history: list[TurnRecord], context_max: int, reserved_tokens: int
) -> list[TurnRecord]:
    """Selects, from most recent to oldest, the turns that fit in the budget.

    Budget = ~70% of ``context_max`` minus ``reserved_tokens`` (reserved space
    for the LLM response). Token estimation is ``len(text) // 4``.
    Never cuts by number of turns — only by proximity to the token limit.
    Always includes at least the most recent turn, even if it alone exceeds the budget.
    """
    budget = int(context_max * 0.7) - reserved_tokens
    if budget <= 0 or not history:
        return []
    selected: list[TurnRecord] = []
    used = 0
    for rec in reversed(history):
        cost = len(rec.content) // 4
        if selected and used + cost > budget:
            break
        selected.append(rec)
        used += cost
    selected.reverse()
    return selected


def deepcopy_scene(scene: Scene) -> Scene:
    """Returns a deep copy of the Scene (required for snapshots)."""
    return copy.deepcopy(scene)


def speaker_label(speaker: str, characters: dict[str, Character], controlled_id: str) -> str:
    """Translates the stored ``speaker`` to the label to display in any LLM prompt.

    ```"Player"`` is the internal marker for the human's turn — it should never reach
    an LLM (Narrator or Character). It is always translated to the controlled
    character's name. Other speakers (character IDs, "Narrator") are returned as is.
    """
    if speaker == "Player":
        controlled = characters.get(controlled_id)
        if controlled is not None:
            return controlled.mind.name
    return speaker


def game_state_to_dict(game: GameState) -> dict[str, Any]:
    """Converts GameState to a JSON-serializable dict."""
    return asdict(game)


def dict_to_character(data: dict[str, Any]) -> Character:
    """Builds a Character from a dict with ``mind`` and ``body`` keys.

    Reusable in both persistence round-trip and creation API.
    """
    mind_data = data["mind"]
    body_data = data["body"]
    return Character(
        mind=CharacterMind(
            name=mind_data["name"],
            personality=str(mind_data["personality"]),
            knowledge=list(mind_data["knowledge"]),
            current_mood=mind_data["current_mood"],
        ),
        body=CharacterBody(
            name=body_data["name"],
            physical_description=body_data["physical_description"],
            outfit=body_data["outfit"],
        ),
    )


def dict_to_game_state(data: dict[str, Any]) -> GameState:
    """Reconstructs GameState from a dict (loaded from JSON).

    Explicit manual construction — no magic serialization dependencies.
    """
    chars_raw: dict[str, Any] = data["characters"]
    characters: dict[str, Character] = {
        cid: dict_to_character(cdata) for cid, cdata in chars_raw.items()
    }

    player_data = data["player"]
    player = Player(
        controlled_character_id=player_data["controlled_character_id"],
    )

    scene_data = data["scene"]
    scene = Scene(
        location=scene_data["location"],
        time_of_day=scene_data["time_of_day"],
        present_characters=list(scene_data["present_characters"]),
        physical_facts=dict(scene_data["physical_facts"]),
    )

    history_raw: list[dict[str, Any]] = data.get("history", [])
    history: list[TurnRecord] = []
    for h in history_raw:
        snap = h["scene_snapshot"]
        scene_snap = Scene(
            location=snap["location"],
            time_of_day=snap["time_of_day"],
            present_characters=list(snap["present_characters"]),
            physical_facts=dict(snap["physical_facts"]),
        )
        history.append(
            TurnRecord(
                turn_number=h["turn_number"],
                speaker=h["speaker"],
                content=h["content"],
                content_type=h["content_type"],
                scene_snapshot=scene_snap,
                input_transformed=h["input_transformed"],
                mood_snapshot=dict(h["mood_snapshot"]),
                plugin_state_snapshot=copy.deepcopy(h["plugin_state_snapshot"]),
            )
        )

    return GameState(
        session_id=data["session_id"],
        characters=characters,
        player=player,
        scene=scene,
        history=history,
        created_at=data["created_at"],
        narrator_directives=data["narrator_directives"],
        story_summary=data["story_summary"],
        character_notes=dict(data["character_notes"]),
        revision=data["revision"],
        plugin_state=copy.deepcopy(data["plugin_state"]),
    )
