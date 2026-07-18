"""Public SDK passed to trusted backend plugin entrypoints."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.paths import PLUGIN_CONFIG_DIR, PLUGIN_STORAGE_DIR
from src.plugins.hooks import Handler, HookKind, HookRegistry
from src.plugins.journal import emit
from src.plugins.manifest import PluginManifest

_config_lock = threading.RLock()


class PluginStorage:
    """A plugin's private, path-safe runtime storage namespace (Task 21).

    Each plugin owns everything under ``.data/plugins/storage/<plugin-id>/`` and
    nothing outside it. The core creates the root, resolves paths safely, and
    rejects any attempt to escape the namespace (absolute paths, ``..``
    traversal, symlink escape); it never interprets the files. The internal
    layout is entirely the plugin's own.
    """

    def __init__(self, plugin_id: str) -> None:
        # Defense in depth (the task forbids relying on manifest validation
        # alone): a malformed id like "../evil" or "a/b" would otherwise make
        # the ROOT itself escape the namespace, and resolve()'s containment
        # check — which compares against that root — could not catch it.
        from src.plugins.manifest import _ID_RE

        if not isinstance(plugin_id, str) or not _ID_RE.fullmatch(plugin_id):
            raise ValueError(f"invalid plugin id for storage namespace: {plugin_id!r}")
        self.plugin_id = plugin_id
        self.root = PLUGIN_STORAGE_DIR / plugin_id

    @property
    def path(self) -> Path:
        """The plugin's storage root, created on first access."""
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def resolve(self, *parts: str) -> Path:
        """Resolve a path inside the namespace, rejecting any escape.

        Every component must be a non-empty relative string; the fully resolved
        path (symlinks included) must stay under the plugin root.
        """
        root = self.root.resolve()
        if not parts:
            return root
        for part in parts:
            if not isinstance(part, str) or not part.strip():
                raise ValueError("storage path components must be non-empty strings")
            if "\x00" in part or os.path.isabs(part):
                raise ValueError(f"unsafe storage path component: {part!r}")
        candidate = self.root.joinpath(*parts).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("storage path escapes the plugin namespace")
        return candidate

    def exists(self, *parts: str) -> bool:
        return self.resolve(*parts).exists()

    def mkdir(self, *parts: str) -> Path:
        target = self.resolve(*parts)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def open(self, *parts: str, mode: str = "r", **kwargs: Any):  # noqa: ANN201
        """Open a file inside the namespace; parent dirs are created for writes."""
        if not parts:
            raise ValueError("open requires at least one path component")
        target = self.resolve(*parts)
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            emit("permission_access", self.plugin_id, permission="storage.write")
            target.parent.mkdir(parents=True, exist_ok=True)
        binary = "b" in mode
        return open(target, mode, **({} if binary else {"encoding": "utf-8"}), **kwargs)

    def remove(self, *parts: str, recursive: bool = False) -> None:
        """Remove a file or directory inside the namespace (no-op if absent)."""
        target = self.resolve(*parts)
        if target == self.root.resolve():
            raise ValueError("cannot remove the storage root itself")
        emit("permission_access", self.plugin_id, permission="storage.write")
        if not target.exists():
            return
        if target.is_dir():
            if not recursive:
                raise ValueError("removing a directory requires recursive=True")
            import shutil

            shutil.rmtree(target)
        else:
            target.unlink()

    def for_session(self, session_id: str) -> Path:
        """Recommended (not mandatory) per-session subdir inside the namespace."""
        return self.mkdir("sessions", session_id)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


class PluginConfig:
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self.path = PLUGIN_CONFIG_DIR / f"{plugin_id}.json"

    def read(self) -> dict[str, Any]:
        emit("permission_access", self.plugin_id, permission="config.read")
        with _config_lock:
            if not self.path.exists():
                return {}
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"Plugin config for {self.plugin_id} must be an object")
            return value

    def write(self, value: dict[str, Any]) -> None:
        emit("permission_access", self.plugin_id, permission="config.write")
        with _config_lock:
            _atomic_json(self.path, value)


class PluginHttp:
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        emit("permission_access", self.plugin_id, permission="network", method=method, url=url)
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, **kwargs)


class PluginModel:
    """Provider-neutral structured model calls with core-owned secrets and logging."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id

    async def call_json(
        self,
        hook_context: dict[str, Any],
        *,
        messages: list[dict[str, Any]],
        json_schema: dict[str, Any],
        max_tokens: int = 1024,
        use_configured_language: bool = True,
    ) -> dict[str, Any]:
        if not isinstance(hook_context, dict):
            raise TypeError("hook_context must be an object")
        runner = hook_context.get("runner")
        game = hook_context.get("game")
        turn_number = hook_context.get("turn_number")
        if runner is None or game is None:
            raise ValueError("model.call_json requires runner and game in hook_context")
        if isinstance(turn_number, bool) or not isinstance(turn_number, int) or turn_number <= 0:
            raise ValueError("model.call_json requires a positive turn_number in hook_context")
        session_id = getattr(game, "session_id", None)
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("model.call_json requires a session-bound GameState")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty array")
        if not isinstance(json_schema, dict) or not isinstance(json_schema.get("schema"), dict):
            raise ValueError("json_schema must contain a schema object")

        config = runner.config
        emit(
            "permission_access",
            self.plugin_id,
            permission="model.call",
            session_id=session_id,
            turn_number=turn_number,
            max_tokens=max_tokens,
            schema=json_schema.get("name", ""),
        )
        return await chat_completion_json(
            client=runner.client,
            messages=messages,
            model=config.get("model", ""),
            language=config.get("language", "") if use_configured_language else "",
            max_tokens=max_tokens,
            json_schema=json_schema,
            timeout=resolve_llm_timeout(config),
            session_id=session_id,
            turn_number=turn_number,
            agent=f"plugin:{self.plugin_id}",
            **llm_request_options(config),
        )


@dataclass(slots=True)
class UnsafeAccess:
    """Explicit escape hatch: trusted plugins may reach and replace arbitrary objects."""

    plugin_id: str
    runtime: Any

    def get(self, name: str) -> Any:
        emit("permission_access", self.plugin_id, permission="unsafe", object=name)
        return getattr(self.runtime, name)

    def set(self, name: str, value: Any) -> None:
        emit("permission_access", self.plugin_id, permission="unsafe", object=name, mutation=True)
        setattr(self.runtime, name, value)


class PluginContext:
    """Stable SDK surface used from a plugin's ``setup(context)`` function."""

    def __init__(
        self,
        manifest: PluginManifest,
        hooks: HookRegistry,
        runtime: Any,
        default_before: tuple[str, ...] = (),
    ) -> None:
        self.manifest = manifest
        self.plugin_id = manifest.plugin_id
        self.config = PluginConfig(self.plugin_id)
        self.storage = PluginStorage(self.plugin_id)
        self.http = PluginHttp(self.plugin_id)
        self.model = PluginModel(self.plugin_id)
        self.unsafe = UnsafeAccess(self.plugin_id, runtime)
        self._hooks = hooks
        self._default_before = default_before

    def register(
        self,
        hook: str,
        kind: HookKind,
        handler: Handler,
        *,
        priority: int | None = None,
        before: tuple[str, ...] | None = None,
        after: tuple[str, ...] | None = None,
    ) -> None:
        self._hooks.register(
            self.plugin_id,
            hook,
            kind,
            handler,
            priority=self.manifest.priority if priority is None else priority,
            before=(self.manifest.before + self._default_before) if before is None else before,
            after=self.manifest.after if after is None else after,
        )

    def action(self, hook: str, handler: Callable[..., Any], **order: Any) -> None:
        self.register(hook, "action", handler, **order)

    def filter(self, hook: str, handler: Callable[..., Any], **order: Any) -> None:
        self.register(hook, "filter", handler, **order)

    def wrapper(self, hook: str, handler: Callable[..., Any], **order: Any) -> None:
        self.register(hook, "wrapper", handler, **order)

    def contribute(self, slot: str, value: Any) -> None:
        self._hooks.contribute(self.plugin_id, slot, value)

    def command(self, descriptor: dict[str, Any], handler: Callable[..., Any]) -> None:
        """Register one executable utility command in the global slash namespace."""
        self.unsafe.runtime.commands.register(
            self.plugin_id, self.manifest.name, self.manifest.version, descriptor, handler
        )

    def event(self, name: str, **details: Any) -> None:
        emit(name, self.plugin_id, **details)
