"""Experience bundles: active plugins, order, configuration, and presentation metadata."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from typing import Any

from src.paths import EXPERIENCES_DIR
from src.plugins.sdk import PluginConfig, _atomic_json
from src.plugins.store import activate, active_pointers, deactivate, installed_plugins

_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_activation_lock = threading.RLock()


class ExperienceError(ValueError):
    pass


_EXPERIENCE_READ_ERRORS = (json.JSONDecodeError, OSError, ExperienceError)


@dataclass(frozen=True, slots=True)
class ExperiencePlugin:
    plugin_id: str
    version: str | None
    config: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Experience:
    experience_id: str
    name: str
    description: str
    image: str
    plugins: tuple[ExperiencePlugin, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "id": self.experience_id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "plugins": [
                {"id": item.plugin_id, "version": item.version, "config": item.config}
                for item in self.plugins
            ],
        }


def parse_experience(value: dict[str, Any]) -> Experience:
    if set(value) != {"schema_version", "id", "name", "description", "image", "plugins"}:
        raise ExperienceError("Experience fields must match the version 1 schema exactly")
    if value["schema_version"] != 1:
        raise ExperienceError("schema_version must be 1")
    experience_id = value["id"]
    if not isinstance(experience_id, str) or not _ID_RE.fullmatch(experience_id):
        raise ExperienceError("id is invalid")
    for field in ("name", "description", "image"):
        if not isinstance(value[field], str):
            raise ExperienceError(f"{field} must be a string")
    raw_plugins = value["plugins"]
    if not isinstance(raw_plugins, list):
        raise ExperienceError("plugins must be an array")
    plugins: list[ExperiencePlugin] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_plugins):
        if not isinstance(raw, dict) or set(raw) != {"id", "version", "config"}:
            raise ExperienceError(f"plugins[{index}] is invalid")
        plugin_id = raw["id"]
        version = raw["version"]
        config = raw["config"]
        if not isinstance(plugin_id, str) or not _ID_RE.fullmatch(plugin_id) or plugin_id in seen:
            raise ExperienceError(f"plugins[{index}].id is invalid or duplicated")
        if version is not None and not isinstance(version, str):
            raise ExperienceError(f"plugins[{index}].version must be string or null")
        if not isinstance(config, dict):
            raise ExperienceError(f"plugins[{index}].config must be an object")
        seen.add(plugin_id)
        plugins.append(ExperiencePlugin(plugin_id, version, config))
    return Experience(
        experience_id,
        value["name"],
        value["description"],
        value["image"],
        tuple(plugins),
    )


def save_experience(value: dict[str, Any]) -> Experience:
    experience = parse_experience(value)
    _atomic_json(EXPERIENCES_DIR / f"{experience.experience_id}.json", value)
    return experience


def list_experiences() -> list[dict[str, Any]]:
    if not EXPERIENCES_DIR.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(EXPERIENCES_DIR.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            result.append(parse_experience(value).public_dict())
        except _EXPERIENCE_READ_ERRORS:
            continue
    return result


def activate_experience(experience_id: str) -> dict[str, Any]:
    with _activation_lock:
        path = EXPERIENCES_DIR / f"{experience_id}.json"
        try:
            experience = parse_experience(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as error:
            raise ExperienceError(f"Cannot load Experience {experience_id}: {error}") from error
        installed_ids = {item["manifest"]["plugin_id"] for item in installed_plugins()}
        missing = [
            item.plugin_id for item in experience.plugins if item.plugin_id not in installed_ids
        ]
        if missing:
            raise ExperienceError(f"Experience requires uninstalled plugins: {', '.join(missing)}")
        desired = {item.plugin_id for item in experience.plugins}
        for pointer in active_pointers():
            if pointer["plugin_id"] not in desired:
                deactivate(pointer["plugin_id"])
        activated: list[dict[str, Any]] = []
        for order, item in enumerate(experience.plugins):
            activated.append(activate(item.plugin_id, item.version, order=order))
            PluginConfig(item.plugin_id).write(item.config)
        return {"experience": experience.public_dict(), "activated": activated, "restart": True}
