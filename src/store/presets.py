"""User preset persistence in JSON with per-name lock and atomic write."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, cast
from weakref import WeakValueDictionary

from src.paths import DEFAULTS_DIR, PRESETS_DIR

_preset_locks: WeakValueDictionary[str, threading.RLock] = WeakValueDictionary()
_preset_locks_guard = threading.Lock()


def _get_lock(name: str) -> threading.RLock:
    """Returns (or creates) the lock for this preset."""
    with _preset_locks_guard:
        lock = _preset_locks.get(name)
        if lock is None:
            lock = threading.RLock()
            _preset_locks[name] = lock
        return lock


def _ensure_dirs() -> None:
    """Ensure the mutable user-preset directory exists."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)


def _preset_path(name: str) -> Path:
    return PRESETS_DIR / f"{name}.json"


def save_preset(name: str, config: dict) -> None:
    """Saves preset in JSON with atomic write."""
    with _get_lock(name):
        _ensure_dirs()
        path = _preset_path(name)

        fd, tmp_name = tempfile.mkstemp(
            dir=str(PRESETS_DIR),
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


def _read_preset(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return None
    except OSError:
        return None


def load_user_preset(name: str) -> dict | None:
    """Load one mutable user preset under its per-name lock."""
    with _get_lock(name):
        return _read_preset(_preset_path(name))


def load_default(name: str) -> dict | None:
    """Load one immutable built-in preset."""
    return _read_preset(DEFAULTS_DIR / f"{name}.json")


def load_preset(name: str) -> dict | None:
    """Load a user preset by name, falling back to an immutable built-in."""
    return load_user_preset(name) or load_default(name)


def delete_preset(name: str) -> bool:
    """Removes the user preset from the filesystem."""
    with _get_lock(name):
        path = _preset_path(name)
        if path.exists():
            path.unlink()
            return True
        return False


def list_presets() -> list[str]:
    """Lists all saved user preset names."""
    _ensure_dirs()
    names: list[str] = []
    for f in PRESETS_DIR.iterdir():
        if f.suffix == ".json":
            names.append(f.stem)
    return sorted(names)


def list_defaults() -> list[str]:
    """Lists all default/builtin preset names."""
    _ensure_dirs()
    names: list[str] = []
    for f in DEFAULTS_DIR.iterdir():
        if f.suffix == ".json":
            names.append(f.stem)
    return sorted(names)
