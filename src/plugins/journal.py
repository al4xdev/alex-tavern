"""Append-only, credential-free plugin observability journal."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from src.paths import PLUGIN_EVENTS_PATH

_lock = threading.Lock()
_SECRET_MARKERS = ("key", "token", "secret", "password", "authorization", "cookie")


def _safe(value: Any, key: str = "") -> Any:
    lowered = key.lower()
    if any(lowered == marker or lowered.endswith(f"_{marker}") for marker in _SECRET_MARKERS):
        return "<redacted>"
    if isinstance(value, dict):
        return {
            str(item_key): _safe(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    if lowered == "url" and isinstance(value, str):
        parts = urlsplit(value)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return value


def emit(event: str, plugin_id: str, **details: Any) -> None:
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        "plugin_id": plugin_id,
        "details": _safe(details),
    }
    line = json.dumps(record, ensure_ascii=False, default=repr) + "\n"
    with _lock:
        PLUGIN_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with PLUGIN_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()


def read(limit: int = 200) -> list[dict[str, Any]]:
    if limit <= 0 or not PLUGIN_EVENTS_PATH.exists():
        return []
    with _lock:
        lines = PLUGIN_EVENTS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records
