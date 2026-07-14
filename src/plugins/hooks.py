"""Deterministic actions, filters, wrappers, and contribution registries."""

from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

HookKind = Literal["action", "filter", "wrapper"]
Handler = Callable[..., Any]
ErrorHandler = Callable[[str, str, BaseException], Awaitable[None] | None]


class HookOrderError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Registration:
    plugin_id: str
    hook: str
    kind: HookKind
    handler: Handler
    priority: int
    before: tuple[str, ...]
    after: tuple[str, ...]
    sequence: int


async def _await(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


class HookRegistry:
    """Runtime registry whose order is stable across machines and boots."""

    def __init__(self, on_error: ErrorHandler | None = None) -> None:
        self._registrations: dict[str, list[Registration]] = defaultdict(list)
        self._contributions: dict[str, list[tuple[str, Any]]] = defaultdict(list)
        self._sequence = 0
        self._on_error = on_error

    def register(
        self,
        plugin_id: str,
        hook: str,
        kind: HookKind,
        handler: Handler,
        *,
        priority: int = 0,
        before: tuple[str, ...] = (),
        after: tuple[str, ...] = (),
    ) -> None:
        self._sequence += 1
        registration = Registration(
            plugin_id, hook, kind, handler, priority, before, after, self._sequence
        )
        self._registrations[hook].append(registration)
        try:
            self.ordered(hook, kind)
        except BaseException:
            self._registrations[hook].remove(registration)
            raise

    def contribute(self, plugin_id: str, slot: str, value: Any) -> None:
        self._contributions[slot].append((plugin_id, value))

    def contributions(self, slot: str) -> list[dict[str, Any]]:
        return [
            {"plugin_id": plugin_id, "value": value}
            for plugin_id, value in self._contributions[slot]
        ]

    def remove_plugin(self, plugin_id: str) -> None:
        for hook in self._registrations:
            self._registrations[hook] = [
                registration
                for registration in self._registrations[hook]
                if registration.plugin_id != plugin_id
            ]
        for slot in self._contributions:
            self._contributions[slot] = [
                item for item in self._contributions[slot] if item[0] != plugin_id
            ]

    def ordered(self, hook: str, kind: HookKind) -> list[Registration]:
        nodes = [item for item in self._registrations[hook] if item.kind == kind]
        by_id: dict[str, list[int]] = defaultdict(list)
        for index, node in enumerate(nodes):
            by_id[node.plugin_id].append(index)
        edges: dict[int, set[int]] = defaultdict(set)
        incoming = [0] * len(nodes)
        for index, node in enumerate(nodes):
            for target_id in node.before:
                for target in by_id.get(target_id, []):
                    if target not in edges[index]:
                        edges[index].add(target)
                        incoming[target] += 1
            for source_id in node.after:
                for source in by_id.get(source_id, []):
                    if index not in edges[source]:
                        edges[source].add(index)
                        incoming[index] += 1

        def key(index: int) -> tuple[int, str, int]:
            node = nodes[index]
            return (-node.priority, node.plugin_id, node.sequence)

        ready = sorted((index for index, degree in enumerate(incoming) if degree == 0), key=key)
        result: list[Registration] = []
        while ready:
            index = ready.pop(0)
            result.append(nodes[index])
            for target in sorted(edges[index], key=key):
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
                    ready.sort(key=key)
        if len(result) != len(nodes):
            involved = sorted({node.plugin_id for i, node in enumerate(nodes) if incoming[i]})
            raise HookOrderError(f"Hook order cycle for {hook}: {', '.join(involved)}")
        return result

    async def _failed(self, registration: Registration, error: BaseException) -> None:
        if self._on_error is not None:
            await _await(self._on_error(registration.plugin_id, registration.hook, error))

    def _failed_sync(self, registration: Registration, error: BaseException) -> None:
        if self._on_error is None:
            return
        result = self._on_error(registration.plugin_id, registration.hook, error)
        if inspect.isawaitable(result):
            raise TypeError("Async plugin error handlers cannot run from synchronous hooks")

    def action_sync(self, hook: str, context: Any) -> None:
        for registration in self.ordered(hook, "action"):
            try:
                result = registration.handler(context)
                if inspect.isawaitable(result):
                    raise TypeError(f"{hook} is synchronous but returned an awaitable")
            except BaseException as error:
                self._failed_sync(registration, error)

    def filter_sync(self, hook: str, value: Any, context: Any) -> Any:
        current = value
        for registration in self.ordered(hook, "filter"):
            draft = deepcopy(current)
            try:
                candidate = registration.handler(draft, context)
                if inspect.isawaitable(candidate):
                    raise TypeError(f"{hook} is synchronous but returned an awaitable")
            except BaseException as error:
                self._failed_sync(registration, error)
                continue
            current = draft if candidate is None else candidate
        return current

    async def action(self, hook: str, context: Any) -> None:
        for registration in self.ordered(hook, "action"):
            try:
                await _await(registration.handler(context))
            except BaseException as error:
                await self._failed(registration, error)

    async def filter(self, hook: str, value: Any, context: Any) -> Any:
        current = value
        for registration in self.ordered(hook, "filter"):
            draft = deepcopy(current)
            try:
                candidate = await _await(registration.handler(draft, context))
            except BaseException as error:
                await self._failed(registration, error)
                continue
            current = draft if candidate is None else candidate
        return current

    async def call_wrapped(self, hook: str, operation: Handler, context: Any) -> Any:
        wrapped = operation
        for registration in reversed(self.ordered(hook, "wrapper")):
            inner = wrapped

            async def layer(
                *args: Any, _registration=registration, _inner=inner, **kwargs: Any
            ) -> Any:
                try:
                    return await _await(_registration.handler(_inner, context, *args, **kwargs))
                except BaseException as error:
                    await self._failed(_registration, error)
                    return await _await(_inner(*args, **kwargs))

            wrapped = layer
        return await _await(wrapped())
