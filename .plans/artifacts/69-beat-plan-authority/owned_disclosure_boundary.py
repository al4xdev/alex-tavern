"""Experimental author-owned disclosure boundary; not a runtime input contract."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReadAuthorization:
    """Lab surrogate for an explicit human operation, never model-produced."""

    session_id: str
    actor_id: str
    turn_number: int
    source_key: str
    listener_ids: tuple[str, ...]


def prepare_disclosure(
    game: Any,
    draft: dict[str, Any],
    turn_number: int,
    authorization: ReadAuthorization | None,
    source_key: str,
    listener_ids: tuple[str, ...],
    canonical_sources: Mapping[str, str],
) -> dict[str, Any]:
    """Keep model briefs out of human voice; derive disclosure from owned source.

    Must run before any renderer or Character context. This prototype deliberately
    does not infer authorization from speech/action text, event labels or a model.
    Caller supplies an explicit author-owned operation. Source text comes only
    from canonical lab sources; draft speech content cannot append commentary.
    """
    from src.perception import eligible_witnesses

    actor = game.player.controlled_character_id
    result = copy.deepcopy(draft)
    result["perception_events"] = [
        event
        for event in result["perception_events"]
        if not (event["event_kind"] == "audible_speech" and event["subject_id"] == actor)
    ]
    if authorization is None:
        return result
    if (
        authorization.session_id != game.session_id
        or authorization.actor_id != actor
        or authorization.turn_number != turn_number
        or authorization.source_key != source_key
        or set(listener_ids) != set(authorization.listener_ids)
    ):
        raise ValueError("Disclosure operation does not match authorization")
    if not set(listener_ids).issubset(eligible_witnesses(game.scene, game.characters, actor)):
        raise ValueError("Disclosure audience is not reachable")
    content = canonical_sources.get(source_key)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("No canonical source content")
    result["perception_events"].append(
        {
            "event_kind": "observation",
            "subject_id": "Narrator",
            "content": "A leitura em voz alta revela o conteúdo do documento: " + content,
            "witness_ids": [actor, *listener_ids],
        }
    )
    return result
