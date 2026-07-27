"""Which build is running — the first question when something misbehaves."""

from __future__ import annotations

import os
from pathlib import Path

UNKNOWN = "unknown"

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parent


def _stamped_commit() -> str | None:
    """The commit the CI wrote into the package, for builds that ship no .git.

    The APK has no repository and no repo root, so the Android workflow stamps
    ``src/version.txt`` before packaging. Without it the app cannot tell which
    code it is running, which is how an APK built from discarded commits went
    unnoticed for days.
    """
    for candidate in (_PACKAGE_DIR / "version.txt", _REPO_ROOT / "version.txt"):
        try:
            if candidate.exists():
                return candidate.read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return None


def _git_commit(git_dir: Path) -> str:
    """Resolve HEAD by reading .git directly, without requiring a git binary."""
    head_file = git_dir / "HEAD"
    try:
        if not head_file.exists():
            return UNKNOWN
        head = head_file.read_text(encoding="utf-8").strip()
        if not head.startswith("ref:"):
            return head  # detached HEAD holds the hash itself
        ref_path = head[4:].strip()
        ref_file = git_dir / ref_path
        if ref_file.exists():
            return ref_file.read_text(encoding="utf-8").strip()
        # A ref that has been packed lives in packed-refs instead of its own file.
        packed_refs = git_dir / "packed-refs"
        if packed_refs.exists():
            for line in packed_refs.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split(None, 1)
                if len(parts) == 2 and parts[1] == ref_path:
                    return parts[0]
    except OSError:
        return UNKNOWN
    return UNKNOWN


def build_commit() -> str:
    """The commit this process is running, or ``"unknown"``."""
    git_dir = _REPO_ROOT / ".git"
    if git_dir.is_dir():
        return _git_commit(git_dir)
    return _stamped_commit() or UNKNOWN


def debug_mode() -> bool:
    """Whether the deployment asked for development behaviour."""
    return os.environ.get("DEBUG", "").strip().casefold() in {"1", "true", "yes", "on"}
