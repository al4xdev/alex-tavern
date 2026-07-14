"""Pure compaction contracts, progress events, guards, and plugin-state deltas."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, Literal

from src.models import TurnRecord

CompactionTrigger = Literal["manual", "automatic"]
CompactionStage = Literal[
    "checking",
    "summarizing",
    "model_completed",
    "before_commit",
    "checkpointing",
    "committing",
    "completed",
    "skipped",
    "failed",
]


@dataclass(frozen=True, slots=True)
class CompactionProgress:
    operation_id: str
    sequence: int
    stage: CompactionStage
    completed_units: int
    total_units: int
    agent: str | None = None
    result: dict[str, Any] | None = None
    error_type: str | None = None


ProgressSink = Callable[[CompactionProgress], None]


@dataclass(slots=True)
class CompactionDraft:
    """Only state domains a pre-commit compaction plugin may mutate."""

    history: list[TurnRecord]
    story_summary: str
    character_notes: dict[str, str]
    plugin_state: dict[str, Any]


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def history_hash(records: list[TurnRecord]) -> str:
    return canonical_hash([asdict(record) for record in records])


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _plugin_delta(
    before: Any,
    after: Any,
    path: tuple[str, ...],
    operations: list[dict[str, Any]],
) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            child = (*path, key)
            if key not in before:
                operations.append(
                    {
                        "path": "/" + "/".join(_escape_pointer(part) for part in child),
                        "before_exists": False,
                        "before": None,
                        "after_exists": True,
                        "after": copy.deepcopy(after[key]),
                    }
                )
            elif key not in after:
                operations.append(
                    {
                        "path": "/" + "/".join(_escape_pointer(part) for part in child),
                        "before_exists": True,
                        "before": copy.deepcopy(before[key]),
                        "after_exists": False,
                        "after": None,
                    }
                )
            else:
                _plugin_delta(before[key], after[key], child, operations)
        return
    if before != after:
        operations.append(
            {
                "path": "/" + "/".join(_escape_pointer(part) for part in path),
                "before_exists": True,
                "before": copy.deepcopy(before),
                "after_exists": True,
                "after": copy.deepcopy(after),
            }
        )


def build_plugin_delta(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    _plugin_delta(before, after, (), operations)
    return operations


def _pointer_parts(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(f"Invalid JSON Pointer: {pointer!r}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def _lookup(root: dict[str, Any], parts: list[str]) -> tuple[bool, Any]:
    current: Any = root
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _assign(root: dict[str, Any], parts: list[str], exists: bool, value: Any) -> None:
    if not parts:
        raise ValueError("Plugin delta cannot replace the plugin_state root")
    current = root
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    if exists:
        current[parts[-1]] = copy.deepcopy(value)
    else:
        current.pop(parts[-1], None)


def invert_plugin_delta(
    current: dict[str, Any], operations: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Invert non-conflicting paths and return conflicts grouped by plugin id."""
    merged = copy.deepcopy(current)
    conflicts: dict[str, list[str]] = {}
    for operation in reversed(operations):
        pointer = str(operation["path"])
        parts = _pointer_parts(pointer)
        exists, value = _lookup(merged, parts)
        if exists != bool(operation["after_exists"]) or (exists and value != operation["after"]):
            plugin_id = parts[0] if parts else ""
            conflicts.setdefault(plugin_id, []).append(pointer)
            continue
        _assign(
            merged,
            parts,
            bool(operation["before_exists"]),
            operation["before"],
        )
    return merged, conflicts
