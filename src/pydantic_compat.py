"""Pydantic v1/v2 compatibility shim.

The desktop and Docker builds run pydantic v2 (``pyproject.toml``). The Android
build cannot: Chaquopy has no Android wheel for ``pydantic-core`` — a Rust
extension — so it falls back to the sdist, which needs a Rust toolchain that the
Chaquopy build environment does not have. The APK therefore installs pydantic
1.x, and this module is the single place that knows the difference.

``src/main.py`` is the only module under ``src/`` that touches pydantic at all;
``src/config.py`` validates by hand and the domain rules live in the Runner, so
this shim only has to bridge shape and serialization. Keep it that way: it is
the only seam, and the smaller it is the less of it goes untested on desktop.
"""

from __future__ import annotations

from typing import Any, TypeVar, cast

import pydantic
from pydantic import BaseModel

PYDANTIC_V2 = pydantic.VERSION.startswith("2.")

ModelT = TypeVar("ModelT", bound=BaseModel)


def dump(model: BaseModel, *, exclude_none: bool = False) -> dict[str, Any]:
    """Model to plain dict, on either pydantic major version."""
    if PYDANTIC_V2:
        return cast(dict[str, Any], model.model_dump(exclude_none=exclude_none))
    return cast(dict[str, Any], model.dict(exclude_none=exclude_none))


def validate(model_type: type[ModelT], data: Any) -> ModelT:
    """Parse ``data`` into ``model_type``, on either pydantic major version."""
    if PYDANTIC_V2:
        return cast(ModelT, model_type.model_validate(data))
    return cast(ModelT, model_type.parse_obj(data))


if PYDANTIC_V2:
    from pydantic import ConfigDict

    class StrictModel(BaseModel):
        """Rejects unknown fields, so a typo in a request body is a 422."""

        model_config = ConfigDict(extra="forbid")

else:  # pragma: no cover - exercised only on the Android build

    class StrictModel(BaseModel):  # type: ignore[no-redef]
        """Rejects unknown fields, so a typo in a request body is a 422."""

        class Config:
            extra = "forbid"
