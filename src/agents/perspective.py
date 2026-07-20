"""Perspective agent — per-character subjective identity (Task 29.2, increment 1).

Three responsibilities, deliberately narrow:

- **Initializer** (``perspective:init:<id>``): compile one viewer's scenario priors
  into their identity ledger, ONCE. Ambiguous sheet text gets a single resolution
  here instead of being re-interpreted by every later call.
- **Identity updater** (``perspective:update:<id>``): a small structured call that
  runs only when a deterministic predicate says it can matter (the viewer still
  has strangers around AND new speech became visible to them). It may record a
  learned name — including a false one the viewer believes.
- **Deterministic projection**: viewer-relative speaker labels and context
  rewriting. Canonical names of people the viewer never met, and internal IDs,
  never reach that viewer's prompt. Privacy comes from this selection, not from
  instructions (measured: 7/13 leak with raw labels, 0/13 with projection).
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import (
    Character,
    CharacterPerspective,
    PersonView,
    TurnRecord,
    record_visible_to,
)

FALLBACK_REFERENCE = "an unfamiliar person"


def build_perspective_json_schema(subject_ids: list[str]) -> dict:
    return {
        "name": "perspective_identity",
        "schema": {
            "type": "object",
            "properties": {
                "people": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject_id": {"type": "string", "enum": subject_ids},
                            "known_name": {"type": ["string", "null"]},
                            "reference": {"type": "string"},
                        },
                        "required": ["subject_id", "known_name", "reference"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["people"],
            "additionalProperties": False,
        },
    }


_INIT_SYSTEM = """\
You maintain the private perspective ledger of ONE roleplay character (the VIEWER).
Compile what the VIEWER currently knows about each OTHER person's identity, based
ONLY on the viewer's own personality and knowledge sheet.

Rules:
- The roster's canonical NAME is machine metadata used to resolve your output keys.
  The viewer does NOT know it unless their own sheet shows they know that person.
- If the sheet gives no evidence the viewer knows someone, "known_name" is null and
  "reference" is a short viewer-relative description of that person as the viewer
  would perceive them right now (use the scene language).
- If the sheet shows a relationship (friend, ex, colleague), "known_name" is the
  name the viewer would use for that person.
- Missing evidence means unknown. Never invent acquaintance. The default is
  "known_name": null; a non-null name is allowed ONLY when a sheet line
  explicitly shows the viewer knows that specific person.
"""

_UPDATE_SYSTEM = """\
You maintain the private perspective ledger of ONE roleplay character (the VIEWER).
Given NEW events the viewer just perceived, decide whether the viewer learned the
name of anyone they did not know yet.

Rules:
- Only the listed UNKNOWN people may change. A name is learned ONLY from events the
  viewer perceived: a self-introduction they heard, someone else addressing that
  person by name in their presence.
- If someone stated a name, the viewer believes THAT stated name even when it
  differs from the canonical machine metadata. Report the viewer's belief.
- If no name was learned, return the person with "known_name": null and an
  optionally refreshed short viewer-relative "reference" (scene language).
- The roster's canonical NAME is machine metadata for key resolution only.
"""


def _roster_lines(
    characters: dict[str, Character], viewer_id: str, controlled_id: str
) -> tuple[list[str], list[str]]:
    subject_ids = [cid for cid in characters if cid != viewer_id]
    lines = []
    for cid in subject_ids:
        character = characters[cid]
        role = " (controlled by the player)" if cid == controlled_id else ""
        lines.append(
            f'  {cid}: canonical name "{character.mind.name}"{role} | '
            f"visible appearance: {character.body.physical_description[:160]}"
        )
    return subject_ids, lines


def _canonical_name_in_evidence(canonical: str, evidence_text: str) -> bool:
    first_name = canonical.split(maxsplit=1)[0]
    return bool(
        re.search(
            rf"\b(?:{re.escape(canonical)}|{re.escape(first_name)})\b",
            evidence_text,
            flags=re.IGNORECASE,
        )
    )


def _validated_people(
    result: dict[str, Any],
    allowed_ids: set[str],
    turn_number: int,
    previous: dict[str, PersonView] | None = None,
    evidence_text: str = "",
    canonical_names: dict[str, str] | None = None,
) -> dict[str, PersonView]:
    """Deterministic guard over the model's proposal.

    ``evidence_text`` is the ONLY place a name may legitimately come from (the
    viewer's own sheet at initialization; the newly perceived events on update).
    A proposed ``known_name`` whose tokens do not appear there is clamped to
    unknown — instructions alone measurably fail to stop invented acquaintance.
    A name inside the reference of an unknown person is replaced by the fallback.
    """
    evidence = evidence_text.casefold()
    people: dict[str, PersonView] = {}
    for item in result.get("people", []):
        subject_id = item.get("subject_id")
        if subject_id not in allowed_ids or subject_id in people:
            continue
        known_name = item.get("known_name")
        if known_name is not None:
            known_name = str(known_name).strip()[:80] or None
        if known_name is not None and known_name.casefold() not in evidence:
            known_name = None
        canonical = canonical_names.get(subject_id, "") if canonical_names else ""
        if (
            known_name is None
            and canonical
            and _canonical_name_in_evidence(canonical, evidence_text)
        ):
            # The sheet is canonical private knowledge. If it explicitly names
            # someone, a conservative model response cannot downgrade that
            # established acquaintance to a visual stranger. Accept either the
            # full canonical name or its first-name form used naturally in prose.
            known_name = canonical
        reference = str(item.get("reference", "")).strip()[:200]
        if not reference:
            reference = FALLBACK_REFERENCE
        if (
            known_name is None
            and canonical_names
            and canonical
            and re.search(rf"\b{re.escape(canonical)}\b", reference, flags=re.IGNORECASE)
        ):
            reference = FALLBACK_REFERENCE
        source = turn_number
        if previous is not None and subject_id in previous:
            before = previous[subject_id]
            if before.known_name == known_name and before.reference == reference:
                source = before.source_turn
        people[subject_id] = PersonView(
            known_name=known_name, reference=reference, source_turn=source
        )
    return people


async def initialize_perspective(
    client: httpx.AsyncClient,
    viewer_id: str,
    characters: dict[str, Character],
    controlled_id: str,
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
) -> CharacterPerspective:
    """Compile the viewer's priors into their version-1 identity ledger."""
    viewer = characters[viewer_id]
    subject_ids, roster = _roster_lines(characters, viewer_id, controlled_id)
    if not subject_ids:
        return CharacterPerspective(
            initialized_turn=turn_number, processed_through_turn=turn_number
        )
    user = (
        f"VIEWER: {viewer_id} ({viewer.mind.name})\n"
        f"VIEWER PERSONALITY:\n{viewer.mind.personality}\n"
        f"VIEWER KNOWLEDGE:\n"
        + "\n".join(f"  - {fact}" for fact in viewer.mind.knowledge)
        + "\n\nROSTER (canonical machine metadata):\n"
        + "\n".join(roster)
        + "\n\nReport the viewer's current identity knowledge for every roster person."
    )
    result = await chat_completion_json(
        client,
        [{"role": "system", "content": _INIT_SYSTEM}, {"role": "user", "content": user}],
        model=config.get("model", ""),
        language=config.get("language", ""),
        # A large cast produces one identity entry per other character. The
        # previous fixed 1024-token cap routinely cut the JSON mid-string,
        # making all three retries fail identically. This is a ceiling, not a
        # requested output size: the model stops as soon as the ledger closes.
        max_tokens=max(4096, int(config.get("max_tokens_character", 4096))),
        timeout=resolve_llm_timeout(config),
        json_schema=build_perspective_json_schema(subject_ids),
        session_id=session_id,
        turn_number=turn_number,
        agent=f"perspective:init:{viewer_id}",
        **llm_request_options(config),
    )
    sheet_text = viewer.mind.personality + "\n" + "\n".join(viewer.mind.knowledge)
    people = _validated_people(
        result,
        set(subject_ids),
        turn_number,
        evidence_text=sheet_text,
        canonical_names={cid: characters[cid].mind.name for cid in subject_ids},
    )
    for subject_id in subject_ids:
        if subject_id not in people:
            people[subject_id] = PersonView(
                known_name=None, reference=FALLBACK_REFERENCE, source_turn=turn_number
            )
    return CharacterPerspective(
        initialized_turn=turn_number,
        processed_through_turn=turn_number,
        people=people,
    )


def unprocessed_visible_records(
    history: list[TurnRecord], viewer_id: str, perspective: CharacterPerspective
) -> list[TurnRecord]:
    return [
        record
        for record in history
        if record.turn_number > perspective.processed_through_turn
        and record.content_type in ("speech", "action")
        and record.speaker != viewer_id
        and record_visible_to(record, viewer_id)
    ]


def needs_identity_update(
    history: list[TurnRecord], viewer_id: str, perspective: CharacterPerspective
) -> bool:
    """Deterministic trigger: strangers remain AND new visible speech exists."""
    if not any(view.known_name is None for view in perspective.people.values()):
        return False
    return bool(unprocessed_visible_records(history, viewer_id, perspective))


async def update_identity(
    client: httpx.AsyncClient,
    viewer_id: str,
    perspective: CharacterPerspective,
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
) -> None:
    """Let the viewer learn names from events they perceived. Mutates the ledger."""
    new_records = unprocessed_visible_records(history, viewer_id, perspective)
    unknown = {cid: view for cid, view in perspective.people.items() if view.known_name is None}
    perspective.processed_through_turn = max(
        [perspective.processed_through_turn, *(r.turn_number for r in new_records)]
    )
    if not unknown or not new_records:
        return
    event_lines = []
    for record in new_records:
        label = viewer_speaker_label(record.speaker, characters, controlled_id, perspective)
        event_lines.append(
            f"  Turn {record.turn_number} | {record.content_type.upper()} | "
            f"{label}: {record.content}"
        )
    roster_lines = [
        f'  {cid}: canonical name "{characters[cid].mind.name}" | currently known to the '
        f"viewer as: {view.reference}"
        for cid, view in unknown.items()
        if cid in characters
    ]
    user = (
        f"VIEWER: {viewer_id} ({characters[viewer_id].mind.name})\n"
        "UNKNOWN PEOPLE (canonical machine metadata):\n"
        + "\n".join(roster_lines)
        + "\n\nNEW EVENTS PERCEIVED BY THE VIEWER (oldest to newest):\n"
        + "\n".join(event_lines)
        + "\n\nReport the viewer's updated identity knowledge for the unknown people only."
    )
    result = await chat_completion_json(
        client,
        [{"role": "system", "content": _UPDATE_SYSTEM}, {"role": "user", "content": user}],
        model=config.get("model", ""),
        language=config.get("language", ""),
        # Updates can still contain nearly the whole cast while many identities
        # remain unknown. A fixed 768-token cap truncated those ledgers at the
        # same byte on every retry, so retries could never produce valid JSON.
        # Keep this aligned with initialization's large-cast ceiling.
        max_tokens=max(4096, int(config.get("max_tokens_character", 4096))),
        timeout=resolve_llm_timeout(config),
        json_schema=build_perspective_json_schema(sorted(unknown)),
        session_id=session_id,
        turn_number=turn_number,
        agent=f"perspective:update:{viewer_id}",
        **llm_request_options(config),
    )
    events_text = "\n".join(record.content for record in new_records)
    for subject_id, view in _validated_people(
        result,
        set(unknown),
        turn_number,
        previous=perspective.people,
        evidence_text=events_text,
        canonical_names={cid: characters[cid].mind.name for cid in unknown if cid in characters},
    ).items():
        perspective.people[subject_id] = view


# ---------------------------------------------------------------------------
# Deterministic projection
# ---------------------------------------------------------------------------


def viewer_speaker_label(
    speaker: str,
    characters: dict[str, Character],
    controlled_id: str,
    perspective: CharacterPerspective | None,
) -> str:
    """Viewer-relative replacement for ``speaker_label``.

    Resolves through the viewer's ledger: a known name renders as that name (the
    viewer's belief, possibly false); an unknown person renders as the viewer's
    reference for them. Without a ledger the canonical name is used (Narrator-side
    surfaces keep omniscience).
    """
    subject_id = controlled_id if speaker == "Player" else speaker
    if subject_id not in characters:
        return speaker
    canonical = characters[subject_id].mind.name
    if perspective is None:
        return canonical
    view = perspective.people.get(subject_id)
    if view is None:
        return canonical
    return view.known_name or view.reference


def project_text_for_viewer(
    text: str,
    characters: dict[str, Character],
    perspective: CharacterPerspective | None,
) -> str:
    """Strip identities the viewer never learned from free prose (e.g. narrator
    context): unknown canonical names and raw internal IDs become the viewer's
    reference for that person."""
    if not text or perspective is None:
        return text
    projected = text
    for subject_id, view in perspective.people.items():
        if subject_id not in characters:
            continue
        replacement = view.known_name or view.reference
        projected = re.sub(rf"\b{re.escape(subject_id)}\b", replacement, projected)
        if view.known_name is None:
            canonical = characters[subject_id].mind.name
            projected = re.sub(
                rf"\b{re.escape(canonical)}\b", view.reference, projected, flags=re.IGNORECASE
            )
    return projected


MAX_RECENT_MEMORY = 24
# Semantic revision (Task 39 inc.2): when the raw digest grows past the
# trigger, the older lines are condensed into memory_summary instead of being
# silently truncated at the MAX bound; the newest tail stays raw.
MEMORY_REVISION_TRIGGER = 20
MEMORY_KEEP_RAW_TAIL = 8


def needs_memory_revision(perspective: CharacterPerspective) -> bool:
    """Deterministic trigger: enough raw digest lines to be worth condensing."""
    return len(perspective.recent_memory) >= MEMORY_REVISION_TRIGGER


def build_memory_revision_messages(
    viewer_name: str,
    memory_summary: str,
    older_lines: list[str],
) -> list[dict]:
    """Messages that condense a viewer's older memory into one summary.

    Pure builder (replayable in isolation). The lines are already
    viewer-projected digests; the summary is the character's own durable
    memory, written in their voice.
    """
    system = (
        f"You maintain the private memory of the character {viewer_name}.\n"
        "Merge the CURRENT MEMORY SUMMARY and the OLDER MEMORY LINES into ONE\n"
        "updated summary, in the language of the lines.\n"
        "Rules:\n"
        "- Write in FIRST PERSON (this is your own remembered experience, not a\n"
        "  report): no turn markers, no timestamps, flowing sentences.\n"
        "- Preserve exactly: promises and commitments, relationship changes,\n"
        "  secrets/codes/numbers verbatim, unresolved threads, and who did what\n"
        "  to whom. Drop atmosphere and incidental detail.\n"
        "- Only merge what is given: never invent events, names, or feelings.\n"
        "- Refer to each person EXACTLY as the lines refer to them; never merge\n"
        "  two different references into one person, even if they could match.\n"
        "- At most 120 words.\n"
    )
    user = (
        "CURRENT MEMORY SUMMARY:\n"
        f"{memory_summary.strip() or '(none yet)'}\n\n"
        "OLDER MEMORY LINES (oldest to newest, being condensed away):\n"
        + "\n".join(f"  {line}" for line in older_lines)
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_memory_revision_schema() -> dict:
    return {
        "name": "memory_revision",
        "schema": {
            "type": "object",
            "properties": {"memory_summary": {"type": "string"}},
            "required": ["memory_summary"],
            "additionalProperties": False,
        },
    }


async def revise_memory(
    client: httpx.AsyncClient,
    viewer_id: str,
    perspective: CharacterPerspective,
    characters: dict[str, Character],
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
) -> None:
    """Condense the older raw digest into ``memory_summary`` (mutates the ledger).

    Maintenance, not content: a provider flake must never fail the player's
    turn, so failures are swallowed — the raw lines stay and the trigger simply
    fires again on a later turn.
    """
    older = perspective.recent_memory[:-MEMORY_KEEP_RAW_TAIL]
    if not older:
        return
    viewer_name = characters[viewer_id].mind.name if viewer_id in characters else viewer_id
    messages = build_memory_revision_messages(viewer_name, perspective.memory_summary, older)
    try:
        result = await chat_completion_json(
            client,
            messages,
            model=config.get("model", ""),
            language=config.get("language", ""),
            max_tokens=config.get("summarizer_max_tokens", 1024),
            timeout=resolve_llm_timeout(config),
            json_schema=build_memory_revision_schema(),
            session_id=session_id,
            turn_number=turn_number,
            agent=f"perspective:memory:{viewer_id}",
            **llm_request_options(config),
        )
        revised = str(result.get("memory_summary", "")).strip()
    except Exception:  # noqa: BLE001 - maintenance must never fail the turn
        return
    if not revised:
        return
    perspective.memory_summary = revised
    del perspective.recent_memory[:-MEMORY_KEEP_RAW_TAIL]


def capture_memory(
    perspective: CharacterPerspective,
    history: list[TurnRecord],
    viewer_id: str,
    characters: dict[str, Character],
    controlled_id: str,
) -> None:
    """Fold newly-perceived turns into the viewer's durable memory (Task 39).

    Deterministic and continuous: appends one viewer-projected digest per
    speech/action the viewer witnessed (their own included) since
    ``memory_through_turn``, so rapport accumulates within a session without a
    compaction. No LLM. Bounded to the most recent ``MAX_RECENT_MEMORY`` lines.
    """
    new_records = [
        record
        for record in history
        if record.turn_number > perspective.memory_through_turn
        and record.content_type in ("speech", "action")
        and (record.speaker == viewer_id or record_visible_to(record, viewer_id))
    ]
    if not new_records:
        return
    for record in new_records:
        label = viewer_speaker_label(record.speaker, characters, controlled_id, perspective)
        content = project_text_for_viewer(record.content, characters, perspective)
        verb = "disse" if record.content_type == "speech" else "fez"
        perspective.recent_memory.append(f"T{record.turn_number} {label} {verb}: {content}")
    perspective.memory_through_turn = max(
        perspective.memory_through_turn, *(r.turn_number for r in new_records)
    )
    if len(perspective.recent_memory) > MAX_RECENT_MEMORY:
        del perspective.recent_memory[:-MAX_RECENT_MEMORY]
