"""User scenario persistence in JSON with per-name lock and atomic write."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, cast

from src.paths import BUILTIN_SCENARIOS_DIR, SCENARIOS_DIR
from src.store.jsonfile import read_json, write_json
from src.store.locks import named_lock


def _scenario_lock(name: str) -> threading.RLock:
    """Returns (or creates) the lock for this scenario."""
    return named_lock("scenario", name)


def _ensure_dirs() -> None:
    """Ensure the mutable user-scenario directory exists."""
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


def _scenario_path(name: str) -> Path:
    return SCENARIOS_DIR / f"{name}.json"


def save_scenario(name: str, config: dict) -> None:
    """Saves scenario in JSON with atomic write."""
    with _scenario_lock(name):
        _ensure_dirs()
        write_json(_scenario_path(name), config)


def _read_scenario(path: Path) -> dict | None:
    try:
        return cast("dict[str, Any] | None", read_json(path))
    except json.JSONDecodeError:
        return None
    except OSError:
        return None


def load_user_scenario(name: str) -> dict | None:
    """Load one mutable user scenario under its per-name lock."""
    with _scenario_lock(name):
        return _read_scenario(_scenario_path(name))


def load_builtin_scenario(name: str) -> dict | None:
    """Load one immutable built-in scenario."""
    return _read_scenario(BUILTIN_SCENARIOS_DIR / f"{name}.json")


def load_scenario(name: str) -> dict | None:
    """Load a user scenario by name, falling back to an immutable built-in."""
    return load_user_scenario(name) or load_builtin_scenario(name)


def delete_scenario(name: str) -> bool:
    """Removes the user scenario from the filesystem."""
    with _scenario_lock(name):
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
