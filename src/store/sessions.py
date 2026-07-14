"""Forward-only GameState persistence with per-session directories."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any
from weakref import WeakValueDictionary

from src.models import GameState, dict_to_game_state, game_state_to_dict
from src.paths import SESSIONS_DIR

_session_locks: WeakValueDictionary[str, asyncio.Lock] = WeakValueDictionary()
_session_locks_guard = threading.Lock()
_JSON_READ_ERRORS = (json.JSONDecodeError, OSError)


def _get_lock(session_id: str) -> asyncio.Lock:
    """Return the process-local mutation lock for one session."""
    with _session_locks_guard:
        lock = _session_locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            _session_locks[session_id] = lock
        return lock


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


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def save_game(game: GameState) -> None:
    """Atomically persist the complete current schema for a session."""
    _atomic_write_json(session_state_path(game.session_id), game_state_to_dict(game))


def load_game(session_id: str) -> GameState | None:
    path = session_state_path(session_id)
    if not path.exists():
        return None
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return dict_to_game_state(data)


def _backup_candidates(session_id: str) -> list[tuple[int, Path]]:
    directory = session_backups_dir(session_id)
    if not directory.exists():
        return []
    candidates: list[tuple[int, Path]] = []
    for path in directory.glob("state.*.json"):
        try:
            index = int(path.name.removeprefix("state.").removesuffix(".json"))
        except ValueError:
            continue
        candidates.append((index, path))
    return sorted(candidates)


def backup_session(session_id: str) -> str:
    """Create a bit-for-bit backup before a destructive state mutation."""
    path = session_state_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session {session_id} not found for backup.")
    candidates = _backup_candidates(session_id)
    next_index = candidates[-1][0] + 1 if candidates else 0
    backup_path = session_backups_dir(session_id) / f"state.{next_index}.json"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_bytes(path.read_bytes())
    return str(backup_path)


def find_latest_backup(session_id: str) -> Path | None:
    candidates = _backup_candidates(session_id)
    return candidates[-1][1] if candidates else None


def restore_last_backup(session_id: str) -> dict[str, Any]:
    """Restore the newest backup only when doing so cannot discard newer turns."""
    path = session_state_path(session_id)
    if not path.exists():
        return {"error": f"Session {session_id} not found."}
    backup_path = find_latest_backup(session_id)
    if backup_path is None:
        return {"restored": False, "reason": "No compaction backup found."}
    try:
        backup_data: dict[str, Any] = json.loads(backup_path.read_text(encoding="utf-8"))
        live_data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        return {"restored": False, "reason": f"Backup or session corrupted: {error}"}

    backup_max = max((h["turn_number"] for h in backup_data["history"]), default=0)
    live_max = max((h["turn_number"] for h in live_data["history"]), default=0)
    if live_max > backup_max:
        return {
            "restored": False,
            "reason": (
                f"There are more recent turns (up to {live_max}) than the backup "
                f"(up to {backup_max}) — restoring would lose those turns. Nothing was changed."
            ),
        }

    backup_data["revision"] = int(live_data["revision"]) + 1
    _atomic_write_json(path, backup_data)
    backup_path.unlink()
    return {"restored": True, "history_length": len(backup_data["history"])}


async def delete_session(session_id: str) -> bool:
    """Permanently remove every artifact owned by one session."""
    async with _get_lock(session_id):
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
        except _JSON_READ_ERRORS:
            continue
        summaries.append(
            {
                "session_id": data["session_id"],
                "characters": [
                    {"name": character["mind"]["name"]} for character in data["characters"].values()
                ],
                "scene_location": data["scene"]["location"],
                "turn_count": len(data["history"]),
                "created_at": data["created_at"],
                "revision": data["revision"],
            }
        )
    summaries.sort(key=lambda item: item["created_at"], reverse=True)
    return summaries


async def fork_session(session_id: str) -> str | None:
    async with _get_lock(session_id):
        game = load_game(session_id)
        if game is None:
            return None
        new_id = generate_session_id()
        game.session_id = new_id
        game.revision = 0
        save_game(game)
        return new_id
