"""Process-local lock registries, one per concurrency domain.

Locks are created on demand and held only while some caller references them
(the registry keeps weak values), so a finished session leaves nothing behind.

The deployment supported by this project is a single Uvicorn process, so these
are process-local by design — a multi-process deployment would need a shared
lock service, not a bigger dictionary here.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from typing import Generic, TypeVar
from weakref import WeakValueDictionary

LockT = TypeVar("LockT")


class _LockRegistry(Generic[LockT]):
    """Get-or-create registry of named locks, itself guarded against races."""

    def __init__(self, factory: Callable[[], LockT]) -> None:
        self._factory = factory
        self._locks: WeakValueDictionary[str, LockT] = WeakValueDictionary()
        self._guard = threading.Lock()

    def get(self, key: str) -> LockT:
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = self._factory()
                self._locks[key] = lock
            return lock


_sessions: _LockRegistry[asyncio.Lock] = _LockRegistry(asyncio.Lock)
_named: _LockRegistry[threading.RLock] = _LockRegistry(threading.RLock)
_appends: _LockRegistry[threading.Lock] = _LockRegistry(threading.Lock)


def session_lock(session_id: str) -> asyncio.Lock:
    """The canonical transaction boundary for one session.

    Every turn, suggestion, snapshot, history read, preview, fork, delete, undo,
    compaction and restoration of a session runs inside this lock. Do not add an
    endpoint that reads or changes a session outside it.
    """
    return _sessions.get(session_id)


def named_lock(namespace: str, name: str) -> threading.RLock:
    """Serialize synchronous file operations on one named record."""
    return _named.get(f"{namespace}:{name}")


def append_lock(session_id: str) -> threading.Lock:
    """Serialize appends to (and bounded reads of) one session's debug log."""
    return _appends.get(session_id)
