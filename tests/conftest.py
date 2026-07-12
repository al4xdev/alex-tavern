"""Keep every pytest data mutation away from the repository's real ``.data``."""

from __future__ import annotations

import json
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


def _seed_default_preset() -> None:
    defaults_dir = TEST_DATA_DIR / "defaults"
    defaults_dir.mkdir(parents=True, exist_ok=True)
    preset = {
        "characters": {
            "C1": {
                "mind": {
                    "name": "Thorn",
                    "personality": "Stoic and loyal veteran warrior.",
                    "knowledge": ["Lyra is a mage he met two weeks ago"],
                    "current_mood": "cautious",
                },
                "body": {
                    "name": "Thorn",
                    "physical_description": "Tall veteran warrior",
                    "outfit": "Reinforced leather armor",
                },
            },
            "C2": {
                "mind": {
                    "name": "Lyra",
                    "personality": "Curious and impulsive elf mage.",
                    "knowledge": ["The forest to the north is corrupted"],
                    "current_mood": "curious",
                },
                "body": {
                    "name": "Lyra",
                    "physical_description": "Silver-haired elf mage",
                    "outfit": "Dark blue robe",
                },
            },
        },
        "scene": {
            "location": "Old Mork's Tavern — main hall, dim lighting",
            "time_of_day": "night",
            "present_characters": ["C1", "C2", "Player"],
            "physical_facts": {"door": "closed", "lighting": "dim candles"},
        },
    }
    (defaults_dir / "thorn-lyra.json").write_text(
        json.dumps(preset, ensure_ascii=False), encoding="utf-8"
    )


_seed_default_preset()


@pytest.fixture(scope="session", autouse=True)
def _guard_test_data_root() -> None:
    """Fail before tests if imports resolved storage anywhere under real data."""
    from src import paths

    assert_safe_test_data_root(paths.DATA_DIR)
    assert paths.DATA_DIR.resolve() == TEST_DATA_DIR.resolve()
