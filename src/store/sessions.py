"""Forward-only GameState persistence with per-session directories."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from src.models import (
    SESSION_SCHEMA_VERSION,
    GameState,
    dict_to_game_state,
    game_state_to_dict,
)
from src.paths import SESSIONS_DIR
from src.store.jsonfile import read_json, write_json
from src.store.locks import session_lock

_JSON_READ_ERRORS = (json.JSONDecodeError, OSError)
_SESSION_SCHEMA_ERRORS = (KeyError, TypeError, ValueError, AttributeError)
_SESSION_READ_ERRORS = _JSON_READ_ERRORS + _SESSION_SCHEMA_ERRORS


def generate_session_id() -> str:
    return uuid.uuid4().hex[:8]


def session_dir(session_id: str) -> Path:
    return SESSIONS_DIR / session_id


def session_state_path(session_id: str) -> Path:
    return session_dir(session_id) / "state.json"


def session_debug_path(session_id: str) -> Path:
    return session_dir(session_id) / "debug.jsonl"


def session_backups_dir(session_id: str) -> Path:
    return session_dir(session_id) / "backups"


def save_game(game: GameState) -> None:
    """Atomically persist the complete current schema for a session."""
    write_json(session_state_path(game.session_id), game_state_to_dict(game))


class SessionNotFoundError(LookupError):
    """No session with this id exists (the caller asked for a ghost).

    Raised instead of returning an in-band ``{"error": ...}`` so a single HTTP
    handler answers 404 and no route has to inspect a result dict for a control
    signal that also looks like a payload field.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} not found")


class IncompatibleSessionError(ValueError):
    """A persisted session's schema version does not match the current one.

    This project deliberately does not migrate old sessions (alpha, no legacy):
    an incompatible session can never be opened again — the backend refuses it
    and the frontend flags it in the list. See ``SESSION_SCHEMA_VERSION``.
    """

    def __init__(self, session_id: str, found_version: int) -> None:
        self.session_id = session_id
        self.found_version = found_version
        self.current_version = SESSION_SCHEMA_VERSION
        super().__init__(
            f"Session {session_id} uses schema version {found_version}; this build "
            f"only opens version {SESSION_SCHEMA_VERSION}. Incompatible sessions "
            "cannot be reopened."
        )


def load_game(session_id: str) -> GameState | None:
    data: dict[str, Any] | None = read_json(session_state_path(session_id))
    if data is None:
        return None
    found_version = int(data.get("schema_version", 1))
    if found_version != SESSION_SCHEMA_VERSION:
        raise IncompatibleSessionError(session_id, found_version)
    return dict_to_game_state(data)


def _checkpoint_candidates(session_id: str) -> list[tuple[int, Path]]:
    directory = session_backups_dir(session_id)
    if not directory.exists():
        return []
    candidates: list[tuple[int, Path]] = []
    for path in directory.glob("compaction.c*.json"):
        try:
            index = int(path.name.removeprefix("compaction.c").removesuffix(".json"))
        except ValueError:
            continue
        candidates.append((index, path))
    return sorted(candidates)


def next_compaction_id(session_id: str) -> str:
    candidates = _checkpoint_candidates(session_id)
    next_index = candidates[-1][0] + 1 if candidates else 1
    return f"c{next_index:06d}"


def compaction_checkpoint_path(session_id: str, checkpoint_id: str) -> Path:
    return session_backups_dir(session_id) / f"compaction.{checkpoint_id}.json"


def write_compaction_checkpoint(
    session_id: str, checkpoint_id: str, checkpoint: dict[str, Any]
) -> str:
    path = compaction_checkpoint_path(session_id, checkpoint_id)
    if path.exists():
        raise FileExistsError(f"Compaction checkpoint {checkpoint_id} already exists")
    write_json(path, checkpoint)
    return str(path)


def load_compaction_checkpoint(session_id: str, checkpoint_id: str) -> dict[str, Any]:
    path = compaction_checkpoint_path(session_id, checkpoint_id)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Compaction checkpoint {checkpoint_id} is not an object")
    return value


async def delete_session(session_id: str) -> bool:
    """Permanently remove every artifact owned by one session."""
    async with session_lock(session_id):
        directory = session_dir(session_id)
        if not directory.exists():
            return False
        shutil.rmtree(directory)
        return True


def list_sessions() -> list[dict[str, Any]]:
    """List valid current-schema sessions, newest first."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for directory in SESSIONS_DIR.iterdir():
        if not directory.is_dir():
            continue
        path = directory / "state.json"
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except _SESSION_READ_ERRORS:
            continue
        found_version = int(data.get("schema_version", 1) or 1)
        if found_version != SESSION_SCHEMA_VERSION:
            # Incompatible sessions stay listed (best-effort raw fields) but can
            # never be opened — the frontend renders them locked.
            raw_characters = data.get("characters")
            names = []
            if isinstance(raw_characters, dict):
                for cdata in raw_characters.values():
                    name = (cdata or {}).get("mind", {}).get("name")
                    if isinstance(name, str):
                        names.append({"name": name})
            summaries.append(
                {
                    "session_id": data.get("session_id", directory.name),
                    "characters": names,
                    "scene_location": (data.get("scene") or {}).get("location", ""),
                    "turn_count": len(data.get("history") or []),
                    "created_at": data.get("created_at", ""),
                    "revision": data.get("revision", 0),
                    "compaction_depth": len(data.get("compaction_stack") or []),
                    "schema_version": found_version,
                    "compatible": False,
                }
            )
            continue
        try:
            game = dict_to_game_state(data)
        except _SESSION_READ_ERRORS:
            continue
        summaries.append(
            {
                "session_id": game.session_id,
                "characters": [
                    {"name": character.mind.name} for character in game.characters.values()
                ],
                "scene_location": game.scene.location,
                "turn_count": len(game.history),
                "created_at": game.created_at,
                "revision": game.revision,
                "compaction_depth": len(game.compaction_stack),
                "schema_version": game.schema_version,
                "compatible": True,
            }
        )
    summaries.sort(key=lambda item: item["created_at"], reverse=True)
    return summaries


async def fork_session(session_id: str) -> str | None:
    async with session_lock(session_id):
        game = load_game(session_id)
        if game is None:
            return None
        new_id = generate_session_id()
        for entry in game.compaction_stack:
            checkpoint = load_compaction_checkpoint(session_id, entry.checkpoint_id)
            write_compaction_checkpoint(new_id, entry.checkpoint_id, checkpoint)
        game.session_id = new_id
        game.revision = 0
        save_game(game)
        return new_id
