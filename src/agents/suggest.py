"""Three coordinated editable alternatives using the normal Character prompt."""

from __future__ import annotations

import httpx

from src.agents.character import (
    _echoed_output_field,
    _leaked_secret_tokens,
    _normalize_output,
    _promote_physical_sentences,
    build_character_json_schema,
    build_character_messages,
)
from src.agents.perspective import project_text_for_viewer
from src.confidentiality import redact_tokens
from src.llm.client import call_agent
from src.models import Character, CharacterPerspective, Scene, TurnRecord

_ALTERNATIVES = """For this request, return THREE alternative next moves for yourself,
not one response and not a sequence of events. Each uses the normal speech,
thought and action_intent fields. None of these moves has happened.
Choose three materially different intentions that fit your personality and
what is happening NOW. They must not repeat the same question, warning or
promise in different words. Include a conversational option, a physical
attempt, and a reflective or observant option when appropriate to this scene.
A quiet option may have only thought; do not force speech into every option.
Your thought explains your immediate personal motivation, rather than reciting
your biography. Your action_intent never determines another person's action
or assumes success. Return the three options in the suggestions array.
"""


def build_suggestion_context(
    scene: Scene,
    characters: dict[str, Character],
    target_id: str,
    narrator_directives: str = "",
    viewer_perspective: CharacterPerspective | None = None,
) -> str:
    """Keep the helper's shared setting; omit unscoped facts in split scenes."""
    context = f"Current setting: {scene.location} | {scene.time_of_day}"
    # In a flat scene the existing helper treats these as shared surroundings.
    # A split scene has no per-fact witness metadata; do not hand every room's
    # facts to a single character. Their perceived history and memory remain.
    if not scene.zones and scene.physical_facts:
        context += "\nCurrent surroundings:\n" + "\n".join(
            f"- {key}: {value}" for key, value in scene.physical_facts.items()
        )
    if narrator_directives.strip():
        context += "\nWORLD RULES (tone and setting):\n" + narrator_directives.strip()
    return project_text_for_viewer(context, characters, viewer_perspective, viewer_id=target_id)


def build_suggestion_schema() -> dict:
    return {
        "name": "character_move_suggestions",
        "schema": {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": build_character_json_schema()["schema"],
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
            "required": ["suggestions"],
            "additionalProperties": False,
        },
    }


async def suggest_moves(
    client: httpx.AsyncClient,
    scene: Scene,
    characters: dict[str, Character],
    target_id: str,
    history: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
    session_id: str = "",
    turn_number: int = 0,
    viewer_perspective: CharacterPerspective | None = None,
    dispositions=None,  # noqa: ANN001 — same state accepted by Character.act
) -> list[dict[str, str]]:
    """Three speech/thought/action drafts. Persists no state and executes nothing."""
    context = build_suggestion_context(
        scene, characters, target_id, narrator_directives, viewer_perspective
    )
    messages = build_character_messages(
        characters[target_id],
        context,
        history,
        characters,
        target_id,
        target_id,
        config,
        scene=scene,
        viewer_perspective=viewer_perspective,
        dispositions=dispositions,
    )
    messages[-1]["content"] += "\n\n" + _ALTERNATIVES
    correction = ""
    for attempt in range(2):
        request = [dict(message) for message in messages]
        request[-1]["content"] += correction
        result = await call_agent(
            client,
            config,
            request,
            agent="suggest_moves",
            json_schema=build_suggestion_schema(),
            max_tokens=3 * config.get("max_tokens_character", 1024),
            session_id=session_id,
            turn_number=turn_number,
            guard_retry="suggestion_output" if correction else "",
        )
        outputs = []
        issues = []
        for item in result["suggestions"]:
            try:
                output = _normalize_output(item)
            except ValueError:
                if attempt == 0:
                    issues.append("Keep movement only in action_intent; fill at least one field.")
                    continue
                output = _normalize_output(_promote_physical_sentences(item))
            leaked = _leaked_secret_tokens(
                output["speech"], history, characters, target_id, target_id, None, scene
            )
            echoed = _echoed_output_field(output, history, target_id)
            if attempt == 0 and (leaked or echoed):
                issues.append(
                    "Do not expose whispered secrets in speech or repeat recent sentences."
                )
            elif leaked:
                output = {**output, "speech": redact_tokens(output["speech"] or "", leaked)}
            if attempt == 1 and echoed:
                other = "speech" if echoed == "thought" else "thought"
                if output.get(other):
                    if echoed == "thought":
                        output["thought"] = None
                    else:
                        output["speech"] = None
            outputs.append(output)
        if issues:
            correction = "\nCORRECTION:\n" + "\n".join(dict.fromkeys(issues))
            continue
        return [
            {
                "speech": item["speech"] or "",
                "thought": item["thought"] or "",
                "action": item["action_intent"] or "",
            }
            for item in outputs
        ]
    raise ValueError("Invalid Character suggestions after correction")
