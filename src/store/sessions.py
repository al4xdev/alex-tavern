"""GameState persistence in JSON with session lock and atomic write."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

from src.models import GameState, dict_to_game_state, game_state_to_dict
from src.paths import SESSIONS_DIR

_session_locks: dict[str, asyncio.Lock] = {}

# Tech debt: _session_locks grows indefinitely (acceptable for MVP)


def _get_lock(session_id: str) -> asyncio.Lock:
    """Returns (or creates) the lock for this session."""
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


def generate_session_id() -> str:
    """Short UUID4 (first 8 hex characters)."""
    return uuid.uuid4().hex[:8]


def _ensure_sessions_dir() -> None:
    """Ensures the sessions directory exists."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def save_game(game: GameState) -> None:
    """Saves GameState in JSON with atomic write (temp + fsync + rename).

    MUST be called within an ``async with _get_lock(session_id)``.

    Args:
        game: GameState to be saved.
    """
    _ensure_sessions_dir()
    data: dict[str, Any] = game_state_to_dict(game)
    path = _session_path(game.session_id)

    # Atomic write-to-temp-then-rename
    fd, tmp_name = tempfile.mkstemp(
        dir=str(SESSIONS_DIR),
        prefix=f"{game.session_id}_",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(fd)
        tmp_path.replace(path)
    except BaseException:
        # Clean up temp if something fails
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def load_game(session_id: str) -> GameState | None:
    """Loads GameState from the session JSON.

    MUST be called within an ``async with _get_lock(session_id)``.

    Args:
        session_id: Session ID.

    Returns:
        GameState or None if the file does not exist.
    """
    path = _session_path(session_id)
    if not path.exists():
        return None

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return dict_to_game_state(data)


def backup_session(session_id: str) -> str:
    """Copies the current {session_id}.json to {session_id}.kb_N.json (incremental N).

    Done BEFORE any destructive edits (e.g. compaction) to allow manual recovery.
    Raw byte copy, no re-serialization — the backup is bit-for-bit identical to the
    original file at the time of the call.

    Returns:
        Path (string) of the created backup file.

    Raises:
        FileNotFoundError: if the session does not exist.
    """
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session {session_id} not found for backup.")

    _ensure_sessions_dir()
    pattern = re.compile(rf"^{re.escape(session_id)}\.kb_(\d+)\.json$")
    indices = [int(m.group(1)) for f in SESSIONS_DIR.iterdir() if (m := pattern.match(f.name))]
    next_index = max(indices, default=-1) + 1
    backup_path = SESSIONS_DIR / f"{session_id}.kb_{next_index}.json"
    backup_path.write_bytes(path.read_bytes())
    return str(backup_path)


def find_latest_backup(session_id: str) -> Path | None:
    """Finds the most recent compaction backup (highest N in {session_id}.kb_N.json).

    Returns:
        Path of the backup, or None if none exists.
    """
    _ensure_sessions_dir()
    pattern = re.compile(rf"^{re.escape(session_id)}\.kb_(\d+)\.json$")
    candidates = [
        (int(m.group(1)), f) for f in SESSIONS_DIR.iterdir() if (m := pattern.match(f.name))
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[-1][1]


def restore_last_backup(session_id: str) -> dict:
    """Undoes the last compaction, restoring the most recent backup — IF safe.

    ⚠️ Risky operation: only restores if NO new turns have been played
    since that compaction (the highest ``turn_number`` of the active session
    cannot be greater than the highest ``turn_number`` of the backup itself) — otherwise,
    restoring would permanently discard those new turns (they do not exist in the
    backup, which is prior to them). In that case, the operation REFUSES, changing
    nothing — it never tries to "merge" the two histories.

    MUST be called within an ``async with _get_lock(session_id)``.
    Operates on raw JSON dicts (without round-trip through dataclass) to
    minimize the chance of a (de)serialization bug masking the check.

    Returns:
        ``{"error": "..."}`` if the session does not exist (same format as
        ``undo_turn``/``compact_session``, for the endpoint to return 404).
        ``{"restored": False, "reason": "..."}`` if there is no backup, or it is not
        safe to restore (nothing is modified in this case).
        ``{"restored": True, "history_length": N}`` if restored — the consumed backup
        is deleted; a new call, if there is another older backup, restores that one
        (same spirit as undo: one call at a time).
    """
    path = _session_path(session_id)
    if not path.exists():
        return {"error": f"Session {session_id} not found."}

    backup_path = find_latest_backup(session_id)
    if backup_path is None:
        return {"restored": False, "reason": "No compaction backup found."}

    try:
        backup_data: dict[str, Any] = json.loads(backup_path.read_text(encoding="utf-8"))
        live_data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return {"restored": False, "reason": f"Backup or session corrupted: {e}"}

    backup_max_turn = max((h["turn_number"] for h in backup_data.get("history", [])), default=0)
    live_max_turn = max((h["turn_number"] for h in live_data.get("history", [])), default=0)
    if live_max_turn > backup_max_turn:
        return {
            "restored": False,
            "reason": (
                f"There are more recent turns (up to {live_max_turn}) than the backup "
                f"(up to {backup_max_turn}) — restoring would lose those turns. "
                "Nothing was changed."
            ),
        }

    path.write_bytes(backup_path.read_bytes())
    backup_path.unlink()
    return {"restored": True, "history_length": len(backup_data.get("history", []))}


def delete_session(session_id: str) -> None:
    """Removes the session file and the raw LLM call log. Used in tests."""
    path = _session_path(session_id)
    if path.exists():
        path.unlink()
    debug_path = SESSIONS_DIR / f"{session_id}.debug.jsonl"
    if debug_path.exists():
        debug_path.unlink()
    _session_locks.pop(session_id, None)


def list_sessions() -> list[dict]:
    """Lists all sessions with a summary (characters, scene, turns, date).

    Returns:
        List of dicts ordered by descending ``created_at``.
        Each dict: {session_id, characters: [{name}], scene_location,
                    turn_count, created_at}
    """
    _ensure_sessions_dir()
    summaries: list[dict] = []
    for fpath in sorted(SESSIONS_DIR.iterdir(), reverse=True):
        if fpath.suffix != ".json":
            continue
        try:
            data: dict[str, Any] = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue  # skip corrupted files

        chars = data.get("characters", {})
        char_names = [{"name": ch.get("mind", {}).get("name", "")} for ch in chars.values()]
        scene = data.get("scene", {})
        history = data.get("history", [])

        summaries.append(
            {
                "session_id": data.get("session_id", fpath.stem),
                "characters": char_names,
                "scene_location": scene.get("location", ""),
                "turn_count": len(history),
                "created_at": data.get("created_at", ""),
            }
        )
    # Sort by descending created_at (most recent first)
    summaries.sort(key=lambda s: s["created_at"], reverse=True)
    return summaries


def fork_session(session_id: str) -> str | None:
    """Creates a copy of the session with a new ID.

    Args:
        session_id: ID of the original session.

    Returns:
        New session_id, or None if the original session does not exist.
    """
    game = load_game(session_id)
    if game is None:
        return None

    new_id = generate_session_id()
    game.session_id = new_id
    save_game(game)
    return new_id
