"""User scenario persistence in JSON with per-name lock and atomic write."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, cast
from weakref import WeakValueDictionary

from src.paths import BUILTIN_SCENARIOS_DIR, SCENARIOS_DIR

_scenario_locks: WeakValueDictionary[str, threading.RLock] = WeakValueDictionary()
_scenario_locks_guard = threading.Lock()


def _get_lock(name: str) -> threading.RLock:
    """Returns (or creates) the lock for this scenario."""
    with _scenario_locks_guard:
        lock = _scenario_locks.get(name)
        if lock is None:
            lock = threading.RLock()
            _scenario_locks[name] = lock
        return lock


def _ensure_dirs() -> None:
    """Ensure the mutable user-scenario directory exists."""
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


def _scenario_path(name: str) -> Path:
    return SCENARIOS_DIR / f"{name}.json"


def save_scenario(name: str, config: dict) -> None:
    """Saves scenario in JSON with atomic write."""
    with _get_lock(name):
        _ensure_dirs()
        path = _scenario_path(name)

        fd, tmp_name = tempfile.mkstemp(
            dir=str(SCENARIOS_DIR),
            prefix=f"{name}_",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(fd)
            tmp_path.replace(path)
        except BaseException:
            if tmp_path.exists():
                tmp_path.unlink()
            raise


def _read_scenario(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return None
    except OSError:
        return None


def load_user_scenario(name: str) -> dict | None:
    """Load one mutable user scenario under its per-name lock."""
    with _get_lock(name):
        return _read_scenario(_scenario_path(name))


def load_builtin_scenario(name: str) -> dict | None:
    """Load one immutable built-in scenario."""
    return _read_scenario(BUILTIN_SCENARIOS_DIR / f"{name}.json")


def load_scenario(name: str) -> dict | None:
    """Load a user scenario by name, falling back to an immutable built-in."""
    return load_user_scenario(name) or load_builtin_scenario(name)


def delete_scenario(name: str) -> bool:
    """Removes the user scenario from the filesystem."""
    with _get_lock(name):
        path = _scenario_path(name)
        if path.exists():
            path.unlink()
            return True
        return False


def list_scenarios() -> list[str]:
    """Lists all saved user scenario names."""
    _ensure_dirs()
    names: list[str] = []
    for f in SCENARIOS_DIR.iterdir():
        if f.suffix == ".json":
            names.append(f.stem)
    return sorted(names)


def list_builtin_scenarios() -> list[str]:
    """Lists all default/builtin scenario names."""
    _ensure_dirs()
    names: list[str] = []
    for f in BUILTIN_SCENARIOS_DIR.iterdir():
        if f.suffix == ".json":
            names.append(f.stem)
    return sorted(names)
