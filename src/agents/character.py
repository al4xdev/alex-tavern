"""Character Agent — replies with private thought and/or public speech."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import TypedDict

import httpx

from src.agents.perspective import viewer_speaker_label
from src.confidentiality import redact_tokens, secret_tokens_exposed_to, tokens
from src.config import llm_request_options
from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
from src.llm.debug_log import log_whisper_output_guard
from src.models import (
    Character,
    Scene,
    TurnRecord,
    record_visible_to,
    speaker_label,
    trim_history_by_tokens,
)
from src.perception import eligible_witnesses


class CharacterOutput(TypedDict):
    speech: str | None
    thought: str | None
    action_intent: str | None


_PHYSICAL_ACTION_RE = re.compile(
    r"(?:^|[.!?]\s+)(?:eu\s+|i\s+)?(?:"
    r"arrum(?:o|ei)|inclin(?:o|ei)|erg(?:o|ui)|abaix(?:o|ei)|toc(?:o|uei)|"
    r"segur(?:o|ei)|agarr(?:o|ei)|pux(?:o|ei)|empurr(?:o|ei)|levant(?:o|ei)|"
    r"and(?:o|ei)|caminh(?:o|ei)|olh(?:o|ei)|encar(?:o|ei)|vir(?:o|ei)|"
    r"sorr(?:io|i)|pis[cq](?:o|uei)|tamboril(?:o|ei)|"
    r"adjust|tilt|raise|lower|touch|hold|grip|pull|push|stand|walk|look|"
    r"stare|turn|smile|blink|drum|tuck|nod|brush|sit"
    r")\b",
    re.IGNORECASE,
)


def build_character_json_schema() -> dict:
    """Return the provider-enforced shape for one Character response."""
    return {
        "name": "character_response",
        "schema": {
            "type": "object",
            "properties": {
                "speech": {"type": ["string", "null"]},
                "thought": {"type": ["string", "null"]},
                "action_intent": {"type": ["string", "null"]},
            },
            "required": ["speech", "thought", "action_intent"],
            "additionalProperties": False,
        },
    }


def _normalize_output(result: dict) -> CharacterOutput:
    """Normalize nullable fields and reject empty or action-like thoughts."""
    speech_value = result.get("speech")
    thought_value = result.get("thought")
    speech = (
        normalize_generated_text(speech_value.strip())
        if isinstance(speech_value, str) and speech_value.strip()
        else None
    )
    thought = (
        normalize_generated_text(thought_value.strip())
        if isinstance(thought_value, str) and thought_value.strip()
        else None
    )
    intent_value = result.get("action_intent")
    action_intent = (
        normalize_generated_text(intent_value.strip())
        if isinstance(intent_value, str) and intent_value.strip()
        else None
    )
    if speech is None and thought is None and action_intent is None:
        raise ValueError("Character response must contain speech, thought, or an action intent")
    if any(text is not None and _PHYSICAL_ACTION_RE.search(text) for text in (speech, thought)):
        raise ValueError(
            "Character response places physical action in speech/thought; it belongs "
            "in action_intent"
        )
    return {"speech": speech, "thought": thought, "action_intent": action_intent}


def _build_system_prompt(character: Character) -> str:
    """Build the stable Character prefix; changing state belongs in the user suffix."""
    return (
        f"You are {character.mind.name}. Stay in character at all times.\n"
        f"Personality: {character.mind.personality}\n"
        f"Knowledge: {', '.join(character.mind.knowledge)}\n"
        "\n"
        "RULES:\n"
        "- You are a character in a roleplay scene, not the Narrator: never state\n"
        "  the environment or anyone's body/actions as flat, objective fact. You\n"
        "  may react to what you perceive in others, but only as your own\n"
        "  subjective read: what it seems like to you, not what is happening\n"
        '  ("he seems tense", never "he grips the hilt of his sword").\n'
        "- Never perform or describe a physical action, including your own body,\n"
        "  gestures, posture, facial expression, or movement. Physical action belongs\n"
        "  exclusively to the Narrator. A thought such as 'I tuck my hair behind my\n"
        "  ear' is forbidden; 'His voice sounds unusually soft to me' is valid.\n"
        "- Put audible first-person dialogue in speech. Put only your private internal\n"
        "  reaction, opinion, or feeling in thought. Do not use markdown wrappers.\n"
        '- "action_intent": what your body ATTEMPTS to do right now (move, grab,\n'
        "  open, strike), stated as an attempt in the third person infinitive\n"
        '  ("caminhar ate a porta e abri-la"). The world decides the outcome:\n'
        "  never state results, impacts, or others\' reactions. null when you\n"
        "  only speak or think. At least one of the three fields must be filled.\n"
        "- Facts may come only from your Knowledge, What you remember, SCENE CONTEXT,\n"
        "  or RECENT EVENTS. If a detail is absent, omit it or clearly express doubt;\n"
        "  never invent a location, backstory, relationship, or prior event.\n"
        "- Whisper discipline: RECENT EVENTS entries labeled WHISPERED are secrets\n"
        "  known only to the characters who perceived them. Others present did NOT\n"
        "  hear them. Never expose any detail from a whisper (names, code words,\n"
        "  passwords, locations, plans) in speech that anyone outside that whisper\n"
        "  could overhear, and never quote or paraphrase a secret while denying or\n"
        "  discussing knowledge of it: a denial that repeats the secret reveals it.\n"
        "  Deflect without repeating any detail. Your private thought may reference\n"
        "  secrets freely.\n"
        "- Whisper exception: when the turn prompt contains THIS TURN IS A WHISPER,\n"
        "  your reply is itself whispered and stays within that same audience. Only\n"
        "  the listed confidants perceive your speech, so speak shared secrets to\n"
        "  them openly and completely, including repeating exact code words and\n"
        "  full numbers when asked. Without that marker treat your speech as heard\n"
        "  by everyone present.\n"
        "- Never repeat a complete sentence from RECENT EVENTS. Silently proofread\n"
        "  grammar and remove accidental duplicated words before answering.\n"
        "- Pursue a goal, do not merely react. In this scene you WANT something\n"
        "  consistent with your personality (learn why someone is here, get a\n"
        "  decision made, keep someone from leaving, secure the room, settle a\n"
        "  score). Take a concrete step toward that aim THIS turn (ask, prod,\n"
        "  propose, or attempt an action) instead of only commenting on the\n"
        "  moment. Vary how you push; never restate a point you already made.\n"
        "- Keep responses to 1-3 sentences.\n"
        "- You may address other characters directly.\n"
    )


def _ledger_memory_text(viewer_perspective) -> str:  # noqa: ANN001
    """The viewer's durable memory rendered for the prompt (Task 39).

    A batched semantic summary (increment 2) leads when present; the continuous
    deterministic digest follows. Empty when the ledger has no memory yet.
    """
    if viewer_perspective is None:
        return ""
    parts: list[str] = []
    summary = getattr(viewer_perspective, "memory_summary", "").strip()
    if summary:
        parts.append(summary)
    recent = getattr(viewer_perspective, "recent_memory", [])
    parts.extend(recent)
    return "\n".join(parts)


def _build_user_prompt(
    context: str,
    history_text: str,
    current_mood: str,
    whisper_note: str = "",
    ledger_memory: str = "",
) -> str:
    """Put append-only history before the Character's changing state and context.

    ``ledger_memory`` is the viewer's durable, viewer-projected memory (Task 39)
    — the single "What you remember" source.
    """
    memory = ledger_memory.strip() or "(none yet)"
    return (
        "RECENT EVENTS:\n"
        f"{history_text}\n"
        "\n"
        "CURRENT PRIVATE STATE:\n"
        f"Current mood: {current_mood}\n"
        f"What you remember: {memory}\n"
        "\n"
        "SCENE CONTEXT (what you perceive right now):\n"
        f"{context}\n"
        "\n"
        + (f"{whisper_note}\n\n" if whisper_note else "")
        + "Return your audible speech and private thought in the requested fields."
    )


def _whisper_turn_note(
    reply_audience: list[str] | None,
    characters: dict[str, Character],
    controlled_id: str,
    character_id: str,
    viewer_perspective=None,
) -> str:
    """Structural signal that this turn's speech is itself whispered.

    A reply to a whispered turn inherits its audience (see ``runner``), so the
    speech is confidential by construction: only the whisper author (the player's
    controlled character) and the listed audience perceive it. Saying so explicitly
    in the turn prompt removes the ambiguity that made characters withhold a
    secret from their own confidant: "never say it aloud" caution belongs to
    public speech, not to this reply.
    """
    if reply_audience is None:
        return ""
    confidants: list[str] = []
    for cid in [controlled_id, *reply_audience]:
        if cid == character_id or cid not in characters:
            continue
        name = viewer_speaker_label(cid, characters, controlled_id, viewer_perspective)
        if name not in confidants:
            confidants.append(name)
    hearers = ", ".join(confidants) if confidants else "your confidant"
    return (
        "THIS TURN IS A WHISPER: your speech right now is confidential and is "
        f"perceived only by {hearers}. Nobody else present hears any part of it, "
        "and nothing you say now becomes public. With these confidants speak "
        "whispered secrets plainly: when asked, state them fully and exactly, "
        "including complete code words and complete numbers."
    )


# Code-like identifiers (an uppercase word fused to digits: ORQUÍDEA-741,
# LUMEN-17) are the least-compressible, highest-value tokens a session carries.
# Records holding one are PINNED through the token trim: recency may discard
# atmosphere, never a confided code (Task 23 — trim/compaction gap).
_CODE_ANCHOR_RE = re.compile(r"\b[^\W\da-zà-ÿ]{2,}[-–. ]?\d+\b")
_MAX_PINNED_RECORDS = 12


def _format_history_for_character(
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    character_id: str,
    context_max: int | None = None,
    max_tokens_character: int = 1024,
    viewer_perspective=None,
) -> str:
    """Formats the history as linear text for the character.

    The character sees public dialogue, physical actions performed in front of it,
    and only its own private thoughts. Whispered records (``audience`` set) are
    visible only to their audience. It never receives narration (the Narrator's
    omniscient reader-facing prose) or another character's thoughts.
    """
    hist = [
        rec
        for rec in history
        if (rec.content_type in ("speech", "action") and record_visible_to(rec, character_id))
        or (rec.content_type == "thought" and rec.speaker == character_id)
    ]
    if context_max is not None:
        pinned = [
            rec
            for rec in hist
            if rec.content_type in ("speech", "action")
            and _CODE_ANCHOR_RE.search(rec.content)
        ][-_MAX_PINNED_RECORDS:]
        trimmed = trim_history_by_tokens(hist, context_max, max_tokens_character)
        kept = set(map(id, trimmed))
        merged = [rec for rec in hist if id(rec) in kept or rec in pinned]
        hist = merged
    if not hist:
        return "(none)"
    kind_labels = {"thought": "PRIVATE THOUGHT", "action": "ACTION"}
    lines: list[str] = []
    for rec in hist:
        label = viewer_speaker_label(rec.speaker, characters, controlled_id, viewer_perspective)
        kind = kind_labels.get(rec.content_type, "SPEECH")
        if (
            rec.audience is not None
            and rec.content_type in ("speech", "action")
            and getattr(rec, "audience_origin", "whisper") == "whisper"
        ):
            kind = f"WHISPERED {kind} (confidential, not everyone present perceived this)"
        lines.append(f"Turn {rec.turn_number} | TYPE={kind} | SPEAKER={label}: {rec.content}")
    return "\n".join(lines)


_PHYSICAL_ACTION_CORRECTION = (
    "\nCORRECTION: Your previous response was invalid. Physical actions and "
    "gestures belong ONLY in the action_intent field, stated as an attempt. "
    "speech carries audible dialogue; thought carries internal reaction.\n"
)
_WHISPER_LEAK_CORRECTION = (
    "\nCORRECTION: Your previous speech exposed whispered confidential content "
    "aloud where people outside the whisper could hear it. Rephrase your speech "
    "without any detail from the whisper (no names, codes, numbers, or facts "
    "from it); your private thought may keep them.\n"
)
_REPETITION_CORRECTION = (
    "\nCORRECTION: Your previous answer nearly repeated a line already in RECENT "
    "EVENTS (your own earlier words or another character's). Say something new: "
    "a fresh reaction or a next step, never a restatement of what was already "
    "said.\n"
)
_ECHO_THRESHOLD = 0.88
_ECHO_MIN_CHARS = 30


def _echoed_output_field(
    output: CharacterOutput, history: list[TurnRecord], character_id: str
) -> str | None:
    """The output field ('thought'/'speech') that near-echoes a recent line.

    Compares against what this character can see: its own prior thoughts plus
    speech/actions visible to it. Catches self-repetition (a thought rendered
    verbatim two turns apart) and parroting another's line. Thought is preferred
    for removal (less load-bearing than speech). Short lines are exempt to avoid
    firing on common phrasings.
    """
    recent = [
        _normalize_sentence(rec.content)
        for rec in history
        if len(rec.content) >= _ECHO_MIN_CHARS
        and (
            (rec.content_type in ("speech", "action") and record_visible_to(rec, character_id))
            or (rec.content_type == "thought" and rec.speaker == character_id)
        )
    ]
    if not recent:
        return None
    for field in ("thought", "speech"):
        value = output.get(field)
        if not value or len(value) < _ECHO_MIN_CHARS:
            continue
        norm = _normalize_sentence(value)
        if any(SequenceMatcher(None, norm, prior).ratio() >= _ECHO_THRESHOLD for prior in recent):
            return field
    return None


def _normalize_sentence(text: str) -> str:
    return " ".join(text.lower().split())


def _leaked_secret_tokens(
    speech: str | None,
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    character_id: str,
    reply_audience: list[str] | None,
    scene: Scene | None,
) -> set[str]:
    """Secret tokens in ``speech`` that its recorded audience must not receive."""
    if not speech or scene is None:
        return set()
    if reply_audience is not None:
        exposed = set(reply_audience)
    else:
        # Public reply: only characters who can physically perceive the speaker
        # are exposed. Without zones this is everyone present (unchanged); with
        # zones, acoustically isolated characters must not count as listeners.
        exposed = eligible_witnesses(scene, characters, character_id)
    exposed -= {character_id}
    if not exposed:
        return set()
    secret = secret_tokens_exposed_to(
        history, character_id, exposed, characters, scene, controlled_id=controlled_id
    )
    return secret & tokens(speech)


async def act(
    client: httpx.AsyncClient,
    character: Character,
    context: str,
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    character_id: str,
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
    scene: Scene | None = None,
    reply_audience: list[str] | None = None,
    viewer_perspective=None,
) -> CharacterOutput:
    """Build the Character prompt and return separate speech/thought fields.

    Args:
        client: Shared httpx.AsyncClient.
        character: The character (only Mind is used in the prompt).
        context: ``context_for_character`` from the Narrator.
        history: Full session history (used to build the recent events context).
        characters: All characters in the session — only used to translate
                    ``speaker_label`` in the history (never leaks other characters'
                    `body`/personality to the prompt).
        controlled_id: ID of the human-controlled character — only used to
                       translate the internal "Player" marker to the character's name.
        character_id: Canonical ID of the Character being called.
        config: Server config (max_tokens).
        session_id: Passed to the raw LLM call log (see ``src/llm/client.py``).
        turn_number: Passed to the raw call log.
        scene: Current scene, required by the whisper output guard (present set +
               known-fact whitelist). ``None`` disables the guard.
        reply_audience: Audience the reply will be recorded with (``None`` =
               public). The guard blocks whispered secrets from reaching anyone
               this audience exposes that the secret's audience does not cover.
               A non-None value also injects the THIS TURN IS A WHISPER note in
               the turn prompt, so the character speaks secrets in full to its
               confidants instead of hedging.

    Returns:
        Nullable speech/thought fields, with at least one populated. Speech that
        still leaked a whispered secret after one correction retry comes back
        with those tokens redacted.
    """
    max_tokens_character = config.get("max_tokens_character", 1024)
    history_text = _format_history_for_character(
        history,
        characters,
        controlled_id,
        character_id,
        context_max=config.get("context_max"),
        max_tokens_character=max_tokens_character,
        viewer_perspective=viewer_perspective,
    )
    messages = [
        {"role": "system", "content": _build_system_prompt(character)},
        {
            "role": "user",
            "content": _build_user_prompt(
                context,
                history_text,
                character.mind.current_mood,
                whisper_note=_whisper_turn_note(
                    reply_audience,
                    characters,
                    controlled_id,
                    character_id,
                    viewer_perspective=viewer_perspective,
                ),
                ledger_memory=_ledger_memory_text(viewer_perspective),
            ),
        },
    ]

    last_error: ValueError | None = None
    correction: str | None = None
    for attempt in range(2):
        attempt_messages = messages
        if correction is not None:
            attempt_messages = [dict(message) for message in messages]
            attempt_messages[-1]["content"] += correction
        result = await chat_completion_json(
            client,
            attempt_messages,
            model=config.get("model", ""),
            language=config.get("language", ""),
            max_tokens=max_tokens_character,
            timeout=resolve_llm_timeout(config),
            json_schema=build_character_json_schema(),
            session_id=session_id,
            turn_number=turn_number,
            agent=f"character:{character.mind.name}",
            **llm_request_options(config),
        )
        try:
            output = _normalize_output(result)
        except ValueError as exc:
            last_error = exc
            correction = _PHYSICAL_ACTION_CORRECTION
            continue

        # Deterministic whisper guard on the OUTPUT side (mirror of the Narrator
        # context guard): whispered secrets the character knows must never enter a
        # record whose audience does not cover them. One correction retry, then
        # redaction as the guaranteed last resort — never a failed turn.
        leaked = _leaked_secret_tokens(
            output["speech"],
            history,
            characters,
            controlled_id,
            character_id,
            reply_audience,
            scene,
        )
        if leaked:
            if attempt == 0:
                if session_id:
                    log_whisper_output_guard(
                        session_id,
                        turn_number,
                        character_id,
                        outcome="retried",
                        leaked_tokens=sorted(leaked),
                        attempt_number=attempt + 1,
                    )
                correction = _WHISPER_LEAK_CORRECTION
                continue
            if session_id:
                log_whisper_output_guard(
                    session_id,
                    turn_number,
                    character_id,
                    outcome="redacted",
                    leaked_tokens=sorted(leaked),
                    attempt_number=attempt + 1,
                )
            assert output["speech"] is not None
            # Preserve every other field (action_intent included): only the
            # leaking speech is redacted.
            output = {**output, "speech": redact_tokens(output["speech"], leaked)}

        # Anti-repetition guard: a character that echoes its own recent thought
        # verbatim, or parrots another's visible line, is caught here — retry
        # once, then deterministically drop the echoed field if the other
        # survives (never mute the character entirely).
        echoed = _echoed_output_field(output, history, character_id)
        if echoed:
            if attempt == 0:
                correction = _REPETITION_CORRECTION
                continue
            other = "speech" if echoed == "thought" else "thought"
            if output.get(other):
                output = {**output, echoed: None}
        return output
    raise ValueError(f"Invalid Character response after correction: {last_error}")
