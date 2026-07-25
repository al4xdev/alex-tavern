"""Guarantees the backend needs to hold when it runs packaged inside the APK.

None of this is reachable from the desktop suite by accident: under Chaquopy
there is no repo root, no .git, and no meaningful working directory. Each check
here stands in for a failure that otherwise only shows up on a phone.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / ".ci-cd" / "android"


def test_static_mount_resolves_from_the_package_not_the_cwd() -> None:
    """A cwd-relative mount kills the import under Chaquopy, before any bind."""
    source = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    assert 'StaticFiles(directory="src/static"' not in source
    assert "StaticFiles(directory=STATIC_DIR" in source

    # Importing from an unrelated cwd is the actual regression guard.
    subprocess.run(
        [sys.executable, "-c", "import src.main; assert src.main.app"],
        cwd="/",
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin"},
    )


def test_build_commit_is_readable_without_a_git_directory(tmp_path: Path) -> None:
    """The APK ships no .git, so the CI stamp is the only way to identify a build."""
    package = tmp_path / "src"
    shutil.copytree(ROOT / "src", package, ignore=shutil.ignore_patterns("__pycache__"))
    (package / "version.txt").write_text("deadbeefcafe1234\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c", "import src.main; print(src.main.get_git_commit())"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )

    assert result.stdout.strip() == "deadbeefcafe1234"


def test_ci_stamps_the_commit_into_the_packaged_sources() -> None:
    action = (ANDROID / "action.yml").read_text(encoding="utf-8")
    assert "src/version.txt" in action
    assert "github.sha" in action


def test_chaquopy_dependencies_stay_pure_python() -> None:
    """Native wheels have no Android build: Chaquopy cannot compile extensions."""
    gradle = (ANDROID / "app" / "build.gradle").read_text(encoding="utf-8")

    # pydantic 2 pulls pydantic-core (Rust); uvicorn[standard] pulls
    # uvloop/httptools/watchfiles. Both fail the APK build outright.
    assert 'install "pydantic<2"' in gradle
    assert "pydantic>=2" not in gradle
    assert "uvicorn[standard]" not in gradle
