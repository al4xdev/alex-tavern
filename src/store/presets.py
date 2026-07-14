"""Forward-only native character preset persistence."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import tempfile
import threading
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from weakref import WeakValueDictionary

from src.models import dict_to_character
from src.paths import PRESETS_DIR

PRESET_SCHEMA_VERSION = 1
MAX_PRESET_NAME_LENGTH = 64
MAX_AVATAR_BYTES = 256 * 1024
_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
_locks: WeakValueDictionary[str, threading.RLock] = WeakValueDictionary()
_locks_guard = threading.Lock()


class PresetError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PresetConflictError(PresetError):
    pass


def validate_preset_name(value: str) -> str:
    name = value.strip()
    if len(name) > MAX_PRESET_NAME_LENGTH or not _NAME_RE.fullmatch(name):
        raise PresetError(
            "invalid_preset_name",
            "Preset name must use 1-64 lowercase letters, numbers, or single hyphens.",
        )
    return name


def _get_lock(name: str) -> threading.RLock:
    with _locks_guard:
        lock = _locks.get(name)
        if lock is None:
            lock = threading.RLock()
            _locks[name] = lock
        return lock


def _path(name: str) -> Path:
    return PRESETS_DIR / f"{name}.json"


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _read(name: str) -> dict[str, Any] | None:
    path = _path(name)
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != PRESET_SCHEMA_VERSION:
        raise PresetError("invalid_preset", f"Preset {name} does not use schema version 1.")
    return value


def _validate_character(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"mind", "body"}:
        raise PresetError("invalid_character", "Character must contain mind and body.")
    try:
        character = dict_to_character(value)
    except (KeyError, TypeError, ValueError) as error:
        raise PresetError(
            "invalid_character", "Character fields are incomplete or invalid."
        ) from error
    if not character.mind.name.strip() or not character.body.name.strip():
        raise PresetError("invalid_character", "Character name cannot be empty.")
    return deepcopy(value)


def _avatar(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"media_type", "data_base64"}:
        raise PresetError("invalid_avatar", "Avatar must contain media_type and data_base64.")
    if value["media_type"] != "image/webp":
        raise PresetError("invalid_avatar", "Avatar must be a WebP image.")
    try:
        data = base64.b64decode(value["data_base64"], validate=True)
    except (TypeError, ValueError, binascii.Error) as error:
        raise PresetError("invalid_avatar", "Avatar data is not valid Base64.") from error
    if len(data) > MAX_AVATAR_BYTES:
        raise PresetError("avatar_too_large", "Processed avatar exceeds 256 KiB.")
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise PresetError("invalid_avatar", "Avatar data is not a WebP image.")
    if int.from_bytes(data[4:8], "little") + 8 != len(data):
        raise PresetError("invalid_avatar", "Avatar WebP container length is invalid.")
    if _webp_dimensions(data) != (256, 256):
        raise PresetError("invalid_avatar", "Avatar must be exactly 256 by 256 pixels.")
    return {
        "media_type": "image/webp",
        "data_base64": base64.b64encode(data).decode("ascii"),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
    }


def _webp_dimensions(data: bytes) -> tuple[int, int] | None:
    position = 12
    while position + 8 <= len(data):
        chunk_type = data[position : position + 4]
        size = int.from_bytes(data[position + 4 : position + 8], "little")
        payload = data[position + 8 : position + 8 + size]
        if len(payload) != size:
            return None
        if chunk_type == b"VP8X" and size >= 10:
            return (
                1 + int.from_bytes(payload[4:7], "little"),
                1 + int.from_bytes(payload[7:10], "little"),
            )
        if chunk_type == b"VP8 " and size >= 10 and payload[3:6] == b"\x9d\x01\x2a":
            return (
                int.from_bytes(payload[6:8], "little") & 0x3FFF,
                int.from_bytes(payload[8:10], "little") & 0x3FFF,
            )
        if chunk_type == b"VP8L" and size >= 5 and payload[0] == 0x2F:
            bits = int.from_bytes(payload[1:5], "little")
            return (1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF))
        position += 8 + size + (size % 2)
    return None


def _public(value: dict[str, Any]) -> dict[str, Any]:
    avatar = value.get("avatar")
    return {key: deepcopy(item) for key, item in value.items() if key != "avatar"} | {
        "avatar": (
            {
                "media_type": avatar["media_type"],
                "sha256": avatar["sha256"],
                "size": avatar["size"],
                "url": f"/presets/{value['preset_name']}/avatar?v={value['revision']}",
            }
            if avatar
            else None
        )
    }


def list_presets() -> list[dict[str, Any]]:
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    result: list[dict[str, Any]] = []
    for path in sorted(PRESETS_DIR.glob("*.json")):
        name = path.stem
        with _get_lock(name):
            value = _read(name)
            if value is None:
                continue
            public = _public(value)
            result.append(
                {
                    "preset_name": public["preset_name"],
                    "display_name": public["character"]["mind"]["name"],
                    "revision": public["revision"],
                    "updated_at": public["updated_at"],
                    "avatar": public["avatar"],
                }
            )
    return result


def load_preset(name: str) -> dict[str, Any] | None:
    name = validate_preset_name(name)
    with _get_lock(name):
        value = _read(name)
        return _public(value) if value is not None else None


def save_preset(
    name: str,
    *,
    character: dict[str, Any],
    avatar: dict[str, Any] | None,
    expected_revision: int | None,
    replace: bool,
) -> dict[str, Any]:
    name = validate_preset_name(name)
    normalized_character = _validate_character(character)
    with _get_lock(name):
        current = _read(name)
        normalized_avatar = _avatar(avatar)
        if normalized_avatar is None and current is not None:
            normalized_avatar = deepcopy(current.get("avatar"))
        now = datetime.now(UTC).isoformat()
        if current is not None:
            if not replace:
                raise PresetConflictError(
                    "replace_confirmation_required",
                    f"Preset '{name}' already exists. Confirm replacement explicitly.",
                )
            if expected_revision != current["revision"]:
                raise PresetConflictError(
                    "revision_conflict",
                    "This preset changed after it was opened. Reload it before replacing.",
                )
            revision = current["revision"] + 1
            created_at = current["created_at"]
        else:
            if expected_revision is not None or replace:
                raise PresetConflictError(
                    "preset_missing", "The preset no longer exists. Save it as a new preset."
                )
            revision = 1
            created_at = now
        value = {
            "schema_version": PRESET_SCHEMA_VERSION,
            "preset_name": name,
            "character": normalized_character,
            "avatar": normalized_avatar,
            "revision": revision,
            "created_at": created_at,
            "updated_at": now,
        }
        _atomic_write(_path(name), value)
        return _public(value)


def delete_preset(name: str, *, expected_revision: int) -> bool:
    name = validate_preset_name(name)
    with _get_lock(name):
        current = _read(name)
        if current is None:
            return False
        if expected_revision != current["revision"]:
            raise PresetConflictError(
                "revision_conflict", "This preset changed. Reload it before deleting."
            )
        _path(name).unlink()
        return True


def load_avatar(name: str) -> tuple[bytes, str] | None:
    name = validate_preset_name(name)
    with _get_lock(name):
        current = _read(name)
        if current is None or current.get("avatar") is None:
            return None
        avatar = current["avatar"]
        return base64.b64decode(avatar["data_base64"]), avatar["sha256"]
