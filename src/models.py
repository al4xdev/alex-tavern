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
# audience model on TurnRecord (Tasks 22/24/25); 3 = per-character perspective
# ledger (viewer-relative identity) with per-record snapshots (Task 29.2);
# 4 = zone graph on Scene + typed perception events replacing
# context_for_character (Task 29.2, increment 2); 5 = autonomous event
# scheduler counter (Task 33); 6 = audience_origin on TurnRecord separating
# intentional whispers (secrecy) from zone-computed scoping (physics);
# 7 = roteiro (premise + act skeleton + rolling beat contract) on GameState;
# 8 = memory dimension on CharacterPerspective (recent_memory + memory_summary);
# 9 = character_notes removed — the perspective ledger is the ONLY private
# memory (continuous capture + semantic revision); compaction keeps only the
# world summarizer and checkpoints drop the notes fields (Task 39 inc.2);
# 10 = identity ledgers treat canonical names explicitly present in a viewer's
# private sheet as known, preventing established acquaintances from becoming
# visual strangers.
SESSION_SCHEMA_VERSION = 10


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
    # Zone graph v1 (Task 29.2 inc. 2): zones maps a zone id to the OTHER zone
    # ids audible from it (directed edges; same-zone perception is implicit).
    # positions maps character ids to their zone. Empty dicts mean one shared
    # space where everyone perceives everything (previous behavior). Positions
    # are static in v1; movement belongs to a future Resolver increment.
    zones: dict[str, list[str]] = field(default_factory=dict)
    positions: dict[str, str] = field(default_factory=dict)


@dataclass
class PersonView:
    """What ONE viewer currently believes about ONE other person's identity.

    ``known_name`` is the viewer's belief, not canonical truth: it stays ``None``
    until the viewer learns a name through events they perceived, and it may hold
    a false or partial name. ``reference`` is the viewer-relative description used
    in that viewer's prompts while (or wherever) no name is known — canonical
    names and internal IDs never reach a prompt through this structure.
    """

    known_name: str | None
    reference: str
    source_turn: int


@dataclass
class CharacterPerspective:
    """Per-character subjective identity ledger (Task 29.2, increment 1).

    Compiled ONCE from the character's own priors (mind.knowledge/personality)
    when the viewer first needs it, then updated only from events the viewer
    perceived. This is the single resolution of ambiguous priors: every prompt
    surface renders from here instead of re-interpreting raw sheet text.
    """

    initialized_turn: int
    processed_through_turn: int
    people: dict[str, PersonView] = field(default_factory=dict)
    # Durable private memory (Task 39, schema v8). ``recent_memory`` is a
    # deterministic, continuous digest of what this viewer actually perceived
    # (viewer-projected, bounded), so rapport accumulates within a session
    # without waiting for a compaction. ``memory_summary`` is reserved for the
    # batched LLM revision (increment 2); empty until then.
    recent_memory: list[str] = field(default_factory=list)
    memory_summary: str = ""
    # Cursor: highest turn already folded into recent_memory (own capture cadence,
    # independent of the identity updater's processed_through_turn).
    memory_through_turn: int = 0


def perspective_to_dict(perspective: CharacterPerspective) -> dict[str, Any]:
    return asdict(perspective)


def dict_to_perspective(data: dict[str, Any]) -> CharacterPerspective:
    return CharacterPerspective(
        initialized_turn=int(data["initialized_turn"]),
        processed_through_turn=int(data["processed_through_turn"]),
        recent_memory=list(data.get("recent_memory", [])),
        memory_summary=str(data.get("memory_summary", "")),
        memory_through_turn=int(data.get("memory_through_turn", 0)),
        people={
            subject_id: PersonView(
                known_name=item["known_name"],
                reference=str(item["reference"]),
                source_turn=int(item["source_turn"]),
            )
            for subject_id, item in data["people"].items()
        },
    )


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
    # character IDs limits perception to those characters (plus the speaker).
    # Applies to speech/action records.
    audience: list[str] | None = None
    # How a non-None audience originated. "whisper" = intentional confidence
    # (player whisper or inherited reply): its rare tokens are SECRETS the
    # guards protect. "zone" = physically computed scoping (who could hear):
    # perception-only, never a secrecy source — repeating something you said
    # in one room in front of a newcomer is not leaking a confidence.
    audience_origin: str = "whisper"
    # Perspective ledgers as they were when this record was created — the undo
    # anchor for identity state (mirrors scene_snapshot/mood_snapshot).
    perspective_snapshot: dict[str, Any] = field(default_factory=dict)


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
class RoteiroBeat:
    """Rolling next-beat contract consumed by the Director (Task 38).

    Typed and measurable: ``expected_actors``/``expected_anchors`` are what the
    deterministic replan engine checks against history; ``exit_condition`` and
    ``intent`` are creative guidance for the Director, never a trigger.
    """

    beat_id: str
    intent: str
    expected_actors: list[str] = field(default_factory=list)
    expected_anchors: list[str] = field(default_factory=list)
    exit_condition: str = ""
    budget_turns: int = 6


@dataclass
class RoteiroAct:
    """One act of the stable skeleton (rarely rewritten)."""

    act_id: str
    summary: str
    exit_condition: str = ""


@dataclass
class Roteiro:
    """Hierarchical story direction: stable premise/acts + one rolling beat.

    Confidentiality invariant: this object reaches ONLY Director-side prompts —
    never a character, never the prose renderer (it contains future secrets).
    """

    premise: str
    acts: list[RoteiroAct] = field(default_factory=list)
    act_index: int = 0
    beat: RoteiroBeat | None = None
    beat_started_turn: int = 0
    # Anchors of the CURRENT beat already witnessed in play, accumulated from
    # the authoritative evidence as it happens (the Director's typed events and
    # the characters' own words/acts). Reset on every replan. Prose is a lossy
    # downstream paraphrase and must never be the coverage surface: audible
    # speech events, for one, never reach the renderer at all (Task 37).
    anchors_seen: list[str] = field(default_factory=list)
    # Replans are blocked until this turn number (hysteresis after any replan).
    cooldown_until_turn: int = 0
    # Consecutive stall/drift replans inside the current act (act-replan input).
    beat_replans_in_act: int = 0
    # "beat_id: outcome" entries, oldest first — context for the next-beat call.
    beat_log: list[str] = field(default_factory=list)


def roteiro_to_dict(roteiro: Roteiro) -> dict[str, Any]:
    return asdict(roteiro)


def dict_to_roteiro(data: dict[str, Any]) -> Roteiro:
    beat_data = data.get("beat")
    return Roteiro(
        premise=str(data["premise"]),
        acts=[
            RoteiroAct(
                act_id=str(item["act_id"]),
                summary=str(item["summary"]),
                exit_condition=str(item.get("exit_condition", "")),
            )
            for item in data.get("acts", [])
        ],
        act_index=int(data.get("act_index", 0)),
        beat=(
            RoteiroBeat(
                beat_id=str(beat_data["beat_id"]),
                intent=str(beat_data["intent"]),
                expected_actors=list(beat_data.get("expected_actors", [])),
                expected_anchors=list(beat_data.get("expected_anchors", [])),
                exit_condition=str(beat_data.get("exit_condition", "")),
                budget_turns=int(beat_data.get("budget_turns", 6)),
            )
            if beat_data
            else None
        ),
        beat_started_turn=int(data.get("beat_started_turn", 0)),
        anchors_seen=list(data.get("anchors_seen", [])),
        cooldown_until_turn=int(data.get("cooldown_until_turn", 0)),
        beat_replans_in_act=int(data.get("beat_replans_in_act", 0)),
        beat_log=list(data.get("beat_log", [])),
    )


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
    revision: int = 0
    plugin_state: dict[str, Any] = field(default_factory=dict)
    compaction_stack: list[CompactionStackEntry] = field(default_factory=list)
    # Character -> native preset identity. Avatar bytes remain outside session state.
    character_preset_ids: dict[str, str] = field(default_factory=dict)
    presence_edit_stack: list[PresenceEditEntry] = field(default_factory=list)
    # {viewer_id: CharacterPerspective} — each character's subjective identity
    # ledger. Absent until that viewer first needs it (lazy initialization).
    character_perspectives: dict[str, CharacterPerspective] = field(default_factory=dict)
    # Completed narrating turns since the drive scheduler last injected an
    # event (Task 33 hazard function input). Reset to 0 on injection.
    turns_since_injected_event: int = 0
    # Director-only story direction (Task 38). None when disabled or not yet
    # generated; NEVER rendered into character or prose prompts.
    roteiro: Roteiro | None = None
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
            zones={zone: list(audible) for zone, audible in snap.get("zones", {}).items()},
            positions=dict(snap.get("positions", {})),
        ),
        input_transformed=data["input_transformed"],
        mood_snapshot=dict(data["mood_snapshot"]),
        plugin_state_snapshot=copy.deepcopy(data["plugin_state_snapshot"]),
        audience=list(data["audience"]) if data.get("audience") is not None else None,
        audience_origin=str(data.get("audience_origin", "whisper")),
        perspective_snapshot=copy.deepcopy(data.get("perspective_snapshot", {})),
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
        zones={zone: list(audible) for zone, audible in scene_data.get("zones", {}).items()},
        positions=dict(scene_data.get("positions", {})),
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
        revision=data["revision"],
        plugin_state=copy.deepcopy(data["plugin_state"]),
        compaction_stack=compaction_stack,
        character_preset_ids=dict(data["character_preset_ids"]),
        presence_edit_stack=presence_edit_stack,
        character_perspectives={
            viewer_id: dict_to_perspective(item)
            for viewer_id, item in data.get("character_perspectives", {}).items()
        },
        turns_since_injected_event=int(data.get("turns_since_injected_event", 0)),
        roteiro=dict_to_roteiro(data["roteiro"]) if data.get("roteiro") else None,
        schema_version=int(data.get("schema_version", 1)),
    )
