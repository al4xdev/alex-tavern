"""Pydantic v1/v2 shim behaviour.

Written to pass under either major version. The desktop suite exercises the v2
branch; the v1 branch is what the Android APK runs, and can be checked with a
pydantic-1.x interpreter:

    python -m pytest tests/test_pydantic_compat.py
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.pydantic_compat import PYDANTIC_V2, StrictModel, dump, validate


class Sample(StrictModel):
    name: str
    count: int = 0
    note: str | None = None


def test_reports_the_installed_major_version() -> None:
    import pydantic

    assert PYDANTIC_V2 is pydantic.VERSION.startswith("2.")


def test_dump_returns_a_plain_dict() -> None:
    assert dump(Sample(name="ada", count=2)) == {"name": "ada", "count": 2, "note": None}


def test_dump_can_drop_unset_optional_fields() -> None:
    assert dump(Sample(name="ada", count=2), exclude_none=True) == {"name": "ada", "count": 2}


def test_validate_parses_a_mapping() -> None:
    parsed = validate(Sample, {"name": "ada", "count": 2})
    assert isinstance(parsed, Sample)
    assert parsed.count == 2


def test_strict_model_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        validate(Sample, {"name": "ada", "typo": 1})
