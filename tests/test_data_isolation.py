"""Regression tests for pytest data isolation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.paths import (
    BUILTIN_SCENARIOS_DIR,
    CONFIG_PATH,
    DATA_DIR,
    EXPERIENCES_DIR,
    PLUGINS_DIR,
    SCENARIOS_DIR,
    SESSIONS_DIR,
)
from tests.conftest import REAL_DATA_DIR, TEST_DATA_DIR, assert_safe_test_data_root


def test_all_mutable_paths_are_inside_temporary_data_root() -> None:
    assert DATA_DIR.resolve() == TEST_DATA_DIR.resolve()
    for path in (CONFIG_PATH, SCENARIOS_DIR, SESSIONS_DIR, PLUGINS_DIR, EXPERIENCES_DIR):
        assert DATA_DIR.resolve() in path.resolve().parents
        assert REAL_DATA_DIR not in path.resolve().parents
    assert BUILTIN_SCENARIOS_DIR.resolve() == (
        Path(__file__).resolve().parents[1] / "src" / "scenarios"
    )


def test_guard_rejects_real_data_and_nested_paths() -> None:
    with pytest.raises(pytest.UsageError, match="Refusing"):
        assert_safe_test_data_root(REAL_DATA_DIR)
    with pytest.raises(pytest.UsageError, match="Refusing"):
        assert_safe_test_data_root(REAL_DATA_DIR / "sessions")


def test_guard_accepts_unrelated_temporary_path(tmp_path: Path) -> None:
    assert_safe_test_data_root(tmp_path)
