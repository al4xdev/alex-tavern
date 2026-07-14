"""Executable, session-bound utility commands registered by trusted plugins."""

from __future__ import annotations

import base64
import binascii
import inspect
import json
import re
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

_COMMAND_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$|^[a-z]$")
_FIELD_TYPES = {"text", "textarea", "file"}

CommandHandler = Callable[[dict[str, Any], dict[str, Any]], Any]


class CommandError(ValueError):
    """A safe command failure that can be returned directly to the client."""

    def __init__(self, code: str, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


@dataclass(frozen=True, slots=True)
class CommandRegistration:
    plugin_id: str
    plugin_version: str
    descriptor: dict[str, Any]
    handler: CommandHandler


def _localized(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"en", "pt-BR"}:
        raise ValueError(f"{label} must contain exactly en and pt-BR")
    result = {key: str(item).strip() for key, item in value.items()}
    if not all(result.values()):
        raise ValueError(f"{label} translations cannot be empty")
    return result


def validate_descriptor(value: Any) -> dict[str, Any]:
    """Validate the forward-only JSON command descriptor exposed to browsers."""
    if not isinstance(value, dict):
        raise ValueError("command descriptor must be an object")
    allowed = {"name", "summary", "usage", "arguments", "fields", "result_kind"}
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"unknown command descriptor fields: {', '.join(sorted(unknown))}")
    name = value.get("name")
    if not isinstance(name, str) or not _COMMAND_RE.fullmatch(name):
        raise ValueError("command name must be a lowercase kebab-case identifier")
    summary = _localized(value.get("summary"), "summary")
    usage = str(value.get("usage", "")).strip()
    if not usage.startswith(f"/{name}"):
        raise ValueError(f"usage must start with /{name}")
    result_kind = str(value.get("result_kind", "")).strip()
    if not result_kind:
        raise ValueError("result_kind cannot be empty")

    arguments: list[dict[str, Any]] = []
    argument_names: set[str] = set()
    for index, item in enumerate(value.get("arguments", [])):
        if not isinstance(item, dict) or set(item) - {"name", "required", "label", "hint"}:
            raise ValueError(f"arguments[{index}] has an invalid shape")
        arg_name = item.get("name")
        if not isinstance(arg_name, str) or not _COMMAND_RE.fullmatch(arg_name):
            raise ValueError(f"arguments[{index}].name is invalid")
        if arg_name in argument_names:
            raise ValueError(f"duplicate argument {arg_name}")
        argument_names.add(arg_name)
        arguments.append(
            {
                "name": arg_name,
                "required": bool(item.get("required", False)),
                "label": _localized(item.get("label"), f"arguments[{index}].label"),
                "hint": _localized(item.get("hint"), f"arguments[{index}].hint"),
            }
        )

    fields: list[dict[str, Any]] = []
    field_names: set[str] = set()
    for index, item in enumerate(value.get("fields", [])):
        allowed_field = {
            "name",
            "type",
            "required",
            "label",
            "hint",
            "accept",
            "max_bytes",
        }
        if not isinstance(item, dict) or set(item) - allowed_field:
            raise ValueError(f"fields[{index}] has an invalid shape")
        field_name = item.get("name")
        field_type = item.get("type")
        if not isinstance(field_name, str) or not _COMMAND_RE.fullmatch(field_name):
            raise ValueError(f"fields[{index}].name is invalid")
        if field_name in field_names:
            raise ValueError(f"duplicate field {field_name}")
        if field_type not in _FIELD_TYPES:
            raise ValueError(f"fields[{index}].type must be text, textarea, or file")
        field_names.add(field_name)
        normalized: dict[str, Any] = {
            "name": field_name,
            "type": field_type,
            "required": bool(item.get("required", False)),
            "label": _localized(item.get("label"), f"fields[{index}].label"),
            "hint": _localized(item.get("hint"), f"fields[{index}].hint"),
        }
        if field_type == "file":
            accept = item.get("accept")
            max_bytes = item.get("max_bytes")
            if (
                not isinstance(accept, list)
                or not accept
                or not all(isinstance(entry, str) and entry for entry in accept)
            ):
                raise ValueError(f"fields[{index}].accept must be a non-empty string array")
            if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
                raise ValueError(f"fields[{index}].max_bytes must be a positive integer")
            normalized.update({"accept": accept, "max_bytes": max_bytes})
        fields.append(normalized)

    normalized_descriptor = {
        "name": name,
        "summary": summary,
        "usage": usage,
        "arguments": arguments,
        "fields": fields,
        "result_kind": result_kind,
    }
    json.dumps(normalized_descriptor, ensure_ascii=False)
    return normalized_descriptor


class CommandRegistry:
    """Strict command namespace shared by all active backend plugins."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandRegistration] = {}

    def register(
        self,
        plugin_id: str,
        plugin_version: str,
        descriptor: dict[str, Any],
        handler: CommandHandler,
    ) -> None:
        if not callable(handler):
            raise TypeError("command handler must be callable")
        normalized = validate_descriptor(descriptor)
        name = normalized["name"]
        existing = self._commands.get(name)
        if existing is not None:
            raise ValueError(f"command /{name} is already registered by {existing.plugin_id}")
        self._commands[name] = CommandRegistration(
            plugin_id=plugin_id,
            plugin_version=plugin_version,
            descriptor=normalized,
            handler=handler,
        )

    def remove_plugin(self, plugin_id: str) -> None:
        self._commands = {
            name: registration
            for name, registration in self._commands.items()
            if registration.plugin_id != plugin_id
        }

    def public_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                **deepcopy(registration.descriptor),
                "plugin_id": registration.plugin_id,
                "plugin_version": registration.plugin_version,
            }
            for _, registration in sorted(self._commands.items())
        ]

    def get(self, name: str) -> CommandRegistration | None:
        return self._commands.get(name)

    @staticmethod
    def _validated_payload(
        registration: CommandRegistration, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) != {"arguments", "fields", "files"}:
            raise CommandError("invalid_payload", "Command input has an invalid shape.")
        arguments = payload["arguments"]
        fields = payload["fields"]
        files = payload["files"]
        if not all(isinstance(item, dict) for item in (arguments, fields, files)):
            raise CommandError("invalid_payload", "Command input sections must be objects.")

        argument_specs = {item["name"]: item for item in registration.descriptor["arguments"]}
        field_specs = {item["name"]: item for item in registration.descriptor["fields"]}
        if set(arguments) - set(argument_specs):
            raise CommandError("unknown_argument", "The command contains an unknown argument.")
        if set(fields) - set(field_specs):
            raise CommandError("unknown_field", "The command contains an unknown field.")
        if set(files) - set(field_specs):
            raise CommandError("unknown_file", "The command contains an unknown file field.")

        normalized_arguments: dict[str, str] = {}
        for name, spec in argument_specs.items():
            value = arguments.get(name, "")
            if not isinstance(value, str):
                raise CommandError("invalid_argument", "Argument must be text.", field=name)
            value = value.strip()
            if spec["required"] and not value:
                raise CommandError("required", "This argument is required.", field=name)
            normalized_arguments[name] = value

        normalized_fields: dict[str, str] = {}
        normalized_files: dict[str, dict[str, Any]] = {}
        for name, spec in field_specs.items():
            if spec["type"] == "file":
                raw = files.get(name)
                if raw is None:
                    if spec["required"]:
                        raise CommandError("required", "This file is required.", field=name)
                    continue
                if not isinstance(raw, dict) or set(raw) != {
                    "name",
                    "media_type",
                    "data_base64",
                }:
                    raise CommandError("invalid_file", "The selected file is invalid.", field=name)
                try:
                    data = base64.b64decode(raw["data_base64"], validate=True)
                except (TypeError, ValueError, binascii.Error) as error:
                    raise CommandError(
                        "invalid_file", "The selected file could not be read.", field=name
                    ) from error
                if len(data) > spec["max_bytes"]:
                    raise CommandError(
                        "file_too_large",
                        f"The selected file exceeds {spec['max_bytes']} bytes.",
                        field=name,
                    )
                normalized_files[name] = {
                    "name": str(raw["name"]),
                    "media_type": str(raw["media_type"]),
                    "data": data,
                }
                continue
            value = fields.get(name, "")
            if not isinstance(value, str):
                raise CommandError("invalid_field", "Field must be text.", field=name)
            value = value.strip()
            if spec["required"] and not value:
                raise CommandError("required", "This field is required.", field=name)
            normalized_fields[name] = value

        return {
            "arguments": normalized_arguments,
            "fields": normalized_fields,
            "files": normalized_files,
        }

    async def invoke(
        self, registration: CommandRegistration, payload: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        normalized = self._validated_payload(registration, payload)
        result = registration.handler(normalized, context)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, dict):
            raise TypeError("command handler must return an object")
        json.dumps(result, ensure_ascii=False)
        return result

    @staticmethod
    def log_metadata(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "arguments": deepcopy(payload.get("arguments", {})),
            "fields": {
                name: {"characters": len(value)}
                for name, value in payload.get("fields", {}).items()
                if isinstance(value, str)
            },
            "files": {
                name: {
                    "name": str(value.get("name", "")),
                    "media_type": str(value.get("media_type", "")),
                    "encoded_characters": len(str(value.get("data_base64", ""))),
                }
                for name, value in payload.get("files", {}).items()
                if isinstance(value, dict)
            },
        }
