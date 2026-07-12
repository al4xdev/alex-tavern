"""Strict local validator for the JSON Schema subset used by role agents."""

from __future__ import annotations

import re
from typing import Any


class JSONSchemaValidationError(ValueError):
    """Raised when output or its requested schema violates the supported contract."""


_SUPPORTED_KEYWORDS = frozenset(
    {
        "type",
        "enum",
        "const",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "maximum",
        "description",
        "title",
    }
)
_SUPPORTED_TYPES = frozenset({"object", "array", "string", "null", "boolean", "integer", "number"})


def _validate_definition(schema: dict[str, Any], path: str) -> None:
    unsupported = sorted(set(schema) - _SUPPORTED_KEYWORDS)
    if unsupported:
        raise JSONSchemaValidationError(f"{path} uses unsupported keywords {unsupported!r}")

    raw_type = schema.get("type")
    if raw_type is not None:
        types = raw_type if isinstance(raw_type, list) else [raw_type]
        if not types or not all(isinstance(item, str) for item in types):
            raise JSONSchemaValidationError(
                f"{path}.type must be a string or non-empty string list"
            )
        unknown_types = sorted(set(types) - _SUPPORTED_TYPES)
        if unknown_types:
            raise JSONSchemaValidationError(
                f"{path}.type contains unsupported types {unknown_types!r}"
            )

    enum = schema.get("enum")
    if enum is not None and not isinstance(enum, list):
        raise JSONSchemaValidationError(f"{path}.enum must be an array")

    properties = schema.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            raise JSONSchemaValidationError(f"{path}.properties must be an object")
        for key, child in properties.items():
            if not isinstance(key, str) or not isinstance(child, dict):
                raise JSONSchemaValidationError(
                    f"{path}.properties entries must map strings to schemas"
                )
            _validate_definition(child, f"{path}.properties.{key}")

    required = schema.get("required")
    if required is not None and (
        not isinstance(required, list) or not all(isinstance(item, str) for item in required)
    ):
        raise JSONSchemaValidationError(f"{path}.required must be an array of strings")

    additional = schema.get("additionalProperties")
    if additional is not None and not isinstance(additional, (bool, dict)):
        raise JSONSchemaValidationError(f"{path}.additionalProperties must be boolean or a schema")
    if isinstance(additional, dict):
        _validate_definition(additional, f"{path}.additionalProperties")

    items = schema.get("items")
    if items is not None:
        if not isinstance(items, dict):
            raise JSONSchemaValidationError(f"{path}.items must be a schema object")
        _validate_definition(items, f"{path}.items")

    for keyword in ("minItems", "maxItems", "minLength", "maxLength"):
        value = schema.get(keyword)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise JSONSchemaValidationError(f"{path}.{keyword} must be a non-negative integer")
    for minimum, maximum in (("minItems", "maxItems"), ("minLength", "maxLength")):
        if minimum in schema and maximum in schema and schema[minimum] > schema[maximum]:
            raise JSONSchemaValidationError(f"{path}.{minimum} cannot exceed {maximum}")

    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            raise JSONSchemaValidationError(f"{path}.pattern must be a string")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise JSONSchemaValidationError(f"{path}.pattern is invalid: {exc}") from exc

    for keyword in ("minimum", "maximum"):
        value = schema.get(keyword)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise JSONSchemaValidationError(f"{path}.{keyword} must be a number")
    if "minimum" in schema and "maximum" in schema and schema["minimum"] > schema["maximum"]:
        raise JSONSchemaValidationError(f"{path}.minimum cannot exceed maximum")


def _matches_type(value: object, expected: str) -> bool:
    mapping = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "null": lambda item: item is None,
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
    }
    return mapping[expected](value)


def _validate_value(value: object, schema: dict[str, Any], path: str) -> None:
    raw_types = schema.get("type")
    type_candidates = raw_types if isinstance(raw_types, list) else [raw_types]
    expected_types = [item for item in type_candidates if isinstance(item, str)]
    if expected_types and not any(_matches_type(value, item) for item in expected_types):
        raise JSONSchemaValidationError(
            f"{path} must have type {' or '.join(expected_types)}, got {type(value).__name__}"
        )
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        raise JSONSchemaValidationError(f"{path} must be one of {enum!r}")
    if "const" in schema and value != schema["const"]:
        raise JSONSchemaValidationError(f"{path} must equal {schema['const']!r}")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise JSONSchemaValidationError(f"{path} must contain at least {minimum} characters")
        if isinstance(maximum, int) and len(value) > maximum:
            raise JSONSchemaValidationError(f"{path} must contain at most {maximum} characters")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            raise JSONSchemaValidationError(f"{path} must match pattern {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise JSONSchemaValidationError(f"{path} must be at least {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise JSONSchemaValidationError(f"{path} must be at most {maximum}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        properties = properties if isinstance(properties, dict) else {}
        required = schema.get("required", [])
        if isinstance(required, list):
            missing = [key for key in required if key not in value]
            if missing:
                raise JSONSchemaValidationError(f"{path} is missing required keys {missing!r}")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            child_schema = properties.get(key)
            if child_schema is None:
                if additional is False:
                    raise JSONSchemaValidationError(f"{path} contains unexpected key {key!r}")
                child_schema = additional if isinstance(additional, dict) else None
            if isinstance(child_schema, dict):
                _validate_value(item, child_schema, f"{path}.{key}")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise JSONSchemaValidationError(f"{path} must contain at least {minimum} items")
        if isinstance(maximum, int) and len(value) > maximum:
            raise JSONSchemaValidationError(f"{path} must contain at most {maximum} items")
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                _validate_value(item, items, f"{path}[{index}]")


def validate_json_schema(value: object, schema: dict[str, Any], path: str = "$") -> None:
    """Validate output or reject schema features this validator cannot enforce."""
    _validate_definition(schema, "$schema")
    _validate_value(value, schema, path)
