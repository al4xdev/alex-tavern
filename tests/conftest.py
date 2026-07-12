"""Keep every pytest data mutation away from the repository's real ``.data``."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

DATA_DIR_ENV = "ROLEPLAY_DATA_DIR"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REAL_DATA_DIR = (REPOSITORY_ROOT / ".data").resolve()
TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="roleplay-pytest-data-"))


def assert_safe_test_data_root(data_dir: Path) -> None:
    """Reject the real data directory and every path nested under it."""
    resolved = data_dir.resolve()
    if resolved == REAL_DATA_DIR or REAL_DATA_DIR in resolved.parents:
        raise pytest.UsageError(f"Refusing to run tests against real data: {resolved}")


assert_safe_test_data_root(TEST_DATA_DIR)
os.environ[DATA_DIR_ENV] = str(TEST_DATA_DIR)


@pytest.fixture(scope="session", autouse=True)
def _guard_test_data_root() -> None:
    """Fail before tests if imports resolved storage anywhere under real data."""
    from src import paths

    assert_safe_test_data_root(paths.DATA_DIR)
    assert paths.DATA_DIR.resolve() == TEST_DATA_DIR.resolve()
