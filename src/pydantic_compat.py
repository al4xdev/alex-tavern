"""Pydantic v1/v2 compatibility shim.

The desktop and Docker builds run pydantic v2 (``pyproject.toml``). The Android
build cannot: Chaquopy has no Android wheel for ``pydantic-core`` — a Rust
extension — so it falls back to the sdist, which needs a Rust toolchain that the
Chaquopy build environment does not have. The APK therefore installs pydantic
1.x, and this module is the single place that knows the difference.

``src/main.py`` is the only module under ``src/`` that touches pydantic at all;
``src/config.py`` validates by hand. Keep it that way, so this shim stays the
only seam.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

import pydantic
from pydantic import BaseModel

PYDANTIC_V2 = pydantic.VERSION.startswith("2.")

ModelT = TypeVar("ModelT", bound=BaseModel)


def dump(model: BaseModel) -> dict[str, Any]:
    """Model to plain dict, on either pydantic major version."""
    if PYDANTIC_V2:
        return cast(dict[str, Any], model.model_dump())
    return cast(dict[str, Any], model.dict())


def validate(model_type: type[ModelT], data: Any) -> ModelT:
    """Parse ``data`` into ``model_type``, on either pydantic major version."""
    if PYDANTIC_V2:
        return cast(ModelT, model_type.model_validate(data))
    return cast(ModelT, model_type.parse_obj(data))


if PYDANTIC_V2:
    from pydantic import ConfigDict, model_validator

    class StrictModel(BaseModel):
        """Rejects unknown fields, so a typo in a request body is a 422."""

        model_config = ConfigDict(extra="forbid")

    def after_validator(func: Callable[..., Any]) -> Any:
        """Whole-model validator that runs after per-field validation."""
        return model_validator(mode="after")(func)

else:  # pragma: no cover - exercised only on the Android build
    from pydantic import root_validator

    class StrictModel(BaseModel):  # type: ignore[no-redef]
        """Rejects unknown fields, so a typo in a request body is a 422."""

        class Config:
            extra = "forbid"

    class _ValuesProxy:
        """Presents a v1 ``root_validator`` values dict as attributes.

        A v2 ``mode="after"`` validator is handed the model instance and reads
        ``self.field``; v1 hands the validator a plain dict. This proxy lets one
        function body serve both. Writes pass through to the dict, so a
        validator that normalizes a field behaves the same on either version.
        """

        def __init__(self, values: dict[str, Any]) -> None:
            object.__setattr__(self, "_values", values)

        def __getattr__(self, name: str) -> Any:
            values: dict[str, Any] = object.__getattribute__(self, "_values")
            try:
                return values[name]
            except KeyError as exc:
                raise AttributeError(name) from exc

        def __setattr__(self, name: str, value: Any) -> None:
            values: dict[str, Any] = object.__getattribute__(self, "_values")
            values[name] = value

    def after_validator(func: Callable[..., Any]) -> Any:
        """Whole-model validator that runs after per-field validation.

        ``skip_on_failure=True`` mirrors v2: when a field already failed, the
        whole-model check is skipped instead of tripping over missing values.
        """

        def _run(cls: type[BaseModel], values: dict[str, Any]) -> dict[str, Any]:
            func(_ValuesProxy(values))
            return values

        _run.__name__ = func.__name__
        _run.__qualname__ = func.__qualname__
        return root_validator(skip_on_failure=True, allow_reuse=True)(_run)
