"""Atomic file publication shared by every persisted store.

One implementation of the same durability contract: write a hidden temporary
beside the target, flush, ``fsync``, then ``replace``. A reader never observes a
half-written file and a crash never leaves the target truncated. The temporary
is hidden and lives in the destination directory so the rename stays atomic
(same filesystem) and a leftover can never be mistaken for real content.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_bytes(path: Path, payload: bytes) -> None:
    """Publish ``payload`` at ``path`` atomically, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_json(path: Path, value: Any) -> None:
    """Publish ``value`` as indented UTF-8 JSON with the same atomic contract."""
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    write_bytes(path, payload.encode("utf-8"))


def read_json(path: Path) -> Any:
    """Parse ``path`` as JSON, or return ``None`` when it does not exist.

    Decoding and I/O errors propagate: what an unreadable file means belongs to
    the store that owns it (a corrupt session is skipped, a corrupt config is a
    startup error), never to this helper.
    """
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
