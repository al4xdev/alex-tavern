"""User preset persistence in JSON with per-name lock and atomic write."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

from src.paths import DEFAULTS_DIR, PRESETS_DIR

_preset_locks: dict[str, asyncio.Lock] = {}


def _get_lock(name: str) -> asyncio.Lock:
    """Returns (or creates) the lock for this preset."""
    if name not in _preset_locks:
        _preset_locks[name] = asyncio.Lock()
    return _preset_locks[name]


def _ensure_dirs() -> None:
    """Ensures the presets and defaults directories exist."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULTS_DIR.mkdir(parents=True, exist_ok=True)


def _preset_path(name: str) -> Path:
    return PRESETS_DIR / f"{name}.json"


def save_preset(name: str, config: dict) -> None:
    """Saves preset in JSON with atomic write."""
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


def load_preset(name: str) -> dict | None:
    """Loads user preset, falling back to the defaults directory."""
    path = _preset_path(name)
    if not path.exists():
        path = DEFAULTS_DIR / f"{name}.json"
        if not path.exists():
            return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def delete_preset(name: str) -> bool:
    """Removes the user preset from the filesystem."""
    path = _preset_path(name)
    if path.exists():
        path.unlink()
        _preset_locks.pop(name, None)
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
    names = sorted(names)
    if "thorn-lyra" in names:
        names.remove("thorn-lyra")
        names.insert(0, "thorn-lyra")
    return names
