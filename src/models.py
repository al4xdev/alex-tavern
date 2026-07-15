"""Dataclasses for the multi-agent roleplay system."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any

# Version of the persisted session schema. Bump it whenever GameState/TurnRecord
# semantics change in a way old sessions cannot honor (new fields with behavioral
# meaning, changed visibility rules, ...). Sessions persisted with a different
# version are refused at load and flagged incompatible in listings — this project
# deliberately does NOT migrate old sessions (alpha, no legacy): agents should
# bump the version and move on instead of carrying compatibility shims.
# History: 1 = pre-audience sessions (implicit, field absent); 2 = whisper
# audience model on TurnRecord (Tasks 22/24/25).
SESSION_SCHEMA_VERSION = 2


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
    # Who perceives this record. None = everyone present (public). A list of
    # character IDs makes the record whispered: only those characters (plus the
    # speaker) ever see it in their context. Applies to speech/action records.
    audience: list[str] | None = None


def record_visible_to(record: TurnRecord, character_id: str) -> bool:
    """Whether ``character_id`` perceives a speech/action record.

    Public records (``audience is None``) are visible to everyone present; a
    whispered record is visible only to its audience and to its own speaker.
    """
    if record.audience is None:
        return True
    return character_id in record.audience or record.speaker == character_id


@dataclass(frozen=True)
class CompactionStackEntry:
    """Reference to one durable, incrementally reversible compaction."""

    checkpoint_id: str
    parent_id: str | None
    trigger: str
    created_at: str
    cutoff_turn_number: int
    max_turn_number: int
    committed_revision: int


@dataclass(frozen=True)
class PresenceEditEntry:
    """Reference to one durable, undoable out-of-band admin presence edit.

    Only the human presence control (outside any turn) pushes here — Narrator-driven
    presence changes happen inside a turn and are already covered by that turn's
    ``TurnRecord.scene_snapshot``, so ``undo_turn`` reverts them on its own.
    """

    edit_id: str
    created_at: str
    origin: str  # "human" in schema_version 1
    before: list[str]
    after: list[str]
    committed_revision: int


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
    compaction_stack: list[CompactionStackEntry] = field(default_factory=list)
    # Character -> native preset identity. Avatar bytes remain outside session state.
    character_preset_ids: dict[str, str] = field(default_factory=dict)
    presence_edit_stack: list[PresenceEditEntry] = field(default_factory=list)
    schema_version: int = SESSION_SCHEMA_VERSION


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


def default_present_characters(characters: dict[str, Character]) -> list[str]:
    """Canonical "everyone present" list, used only to fill an absent value."""
    return [*characters, "Player"]


def validate_present_characters(
    present: list[str],
    characters: dict[str, Character],
    controlled_id: str,
) -> list[str]:
    """Validates a ``Scene.present_characters`` candidate against the canonical contract.

    Rejects invalid input outright (unknown ID, duplicate, out-of-order IDs, missing
    or misplaced ``"Player"`` sentinel, absent controlled character) instead of
    filtering or completing it silently. Returns the list unchanged when valid.
    """
    if not present:
        raise ValueError("present_characters cannot be empty.")
    if present.count("Player") != 1 or present[-1] != "Player":
        raise ValueError('present_characters must end with exactly one "Player" marker.')

    character_ids = list(present[:-1])
    if len(set(character_ids)) != len(character_ids):
        raise ValueError("present_characters contains duplicate character IDs.")

    unknown = [cid for cid in character_ids if cid not in characters]
    if unknown:
        raise ValueError(f"present_characters references unknown character IDs: {unknown}")

    canonical_order = [cid for cid in characters if cid in character_ids]
    if character_ids != canonical_order:
        raise ValueError("present_characters must preserve the canonical order of characters.")

    if controlled_id not in character_ids:
        raise ValueError("The controlled character must always be present.")

    return list(present)


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


def dict_to_turn_record(data: dict[str, Any]) -> TurnRecord:
    """Build the current forward-only TurnRecord representation."""
    snap = data["scene_snapshot"]
    return TurnRecord(
        turn_number=data["turn_number"],
        speaker=data["speaker"],
        content=data["content"],
        content_type=data["content_type"],
        scene_snapshot=Scene(
            location=snap["location"],
            time_of_day=snap["time_of_day"],
            present_characters=list(snap["present_characters"]),
            physical_facts=dict(snap["physical_facts"]),
        ),
        input_transformed=data["input_transformed"],
        mood_snapshot=dict(data["mood_snapshot"]),
        plugin_state_snapshot=copy.deepcopy(data["plugin_state_snapshot"]),
        audience=list(data["audience"]) if data.get("audience") is not None else None,
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

    history = [dict_to_turn_record(item) for item in data["history"]]
    compaction_stack = [
        CompactionStackEntry(
            checkpoint_id=item["checkpoint_id"],
            parent_id=item["parent_id"],
            trigger=item["trigger"],
            created_at=item["created_at"],
            cutoff_turn_number=item["cutoff_turn_number"],
            max_turn_number=item["max_turn_number"],
            committed_revision=item["committed_revision"],
        )
        for item in data["compaction_stack"]
    ]
    presence_edit_stack = [
        PresenceEditEntry(
            edit_id=item["edit_id"],
            created_at=item["created_at"],
            origin=item["origin"],
            before=list(item["before"]),
            after=list(item["after"]),
            committed_revision=item["committed_revision"],
        )
        for item in data["presence_edit_stack"]
    ]

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
        compaction_stack=compaction_stack,
        character_preset_ids=dict(data["character_preset_ids"]),
        presence_edit_stack=presence_edit_stack,
        schema_version=int(data.get("schema_version", 1)),
    )
