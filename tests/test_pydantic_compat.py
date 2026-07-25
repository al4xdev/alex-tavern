"""Pydantic v1/v2 shim behaviour.

Written to pass under either major version. The desktop suite exercises the v2
branch; the v1 branch is what the Android APK runs, and can be checked with a
pydantic-1.x interpreter:

    python -m pytest tests/test_pydantic_compat.py
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.pydantic_compat import PYDANTIC_V2, StrictModel, after_validator, dump, validate


class Sample(StrictModel):
    name: str
    count: int = 0


class Guarded(StrictModel):
    speech: str = ""
    skip: bool = False

    @after_validator
    def require_content(self):  # noqa: ANN001, ANN202 - signature differs per version
        if self.skip and self.speech.strip():
            raise ValueError("skip=True cannot be combined with speech")
        if not self.skip and not self.speech.strip():
            raise ValueError("a turn needs speech")
        return self


def test_reports_the_installed_major_version() -> None:
    import pydantic

    assert PYDANTIC_V2 is pydantic.VERSION.startswith("2.")


def test_dump_returns_a_plain_dict() -> None:
    assert dump(Sample(name="ada", count=2)) == {"name": "ada", "count": 2}


def test_validate_parses_a_mapping() -> None:
    parsed = validate(Sample, {"name": "ada", "count": 2})
    assert isinstance(parsed, Sample)
    assert parsed.count == 2


def test_strict_model_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        validate(Sample, {"name": "ada", "typo": 1})


def test_after_validator_accepts_a_valid_model() -> None:
    assert Guarded(speech="hello").speech == "hello"
    assert Guarded(skip=True).skip is True


def test_after_validator_rejects_conflicting_fields() -> None:
    with pytest.raises(ValidationError):
        validate(Guarded, {"skip": True, "speech": "hello"})


def test_after_validator_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        validate(Guarded, {"speech": "   "})


def test_after_validator_is_skipped_when_a_field_already_failed() -> None:
    """It must not mask the real field error by tripping over a missing value."""
    with pytest.raises(ValidationError) as error:
        validate(Guarded, {"skip": "not-a-bool", "speech": "hello"})
    assert "skip" in str(error.value)
