"""Executable, session-bound utility commands registered by trusted plugins."""

from __future__ import annotations

import base64
import binascii
import inspect
import json
import re
import unicodedata
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

_COMMAND_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$|^[a-z]$")
_FIELD_TYPES = {"text", "textarea", "file"}
_LOCALES = {"en", "pt-BR"}

# The core owns these names and localized aliases even though its actions execute
# in the browser. Reserving them here makes the combined slash namespace honest.
BUILTIN_COMMAND_NAMES = frozenset(
    {
        "help",
        "ajuda",
        "plugins",
        "settings",
        "configuracoes",
        "sessions",
        "sessoes",
        "new",
        "novo",
        "suggest",
        "sugestao",
        "hint",
        "dica",
        "undo",
        "desfazer",
        "skip",
        "pular",
        "compact",
        "compactar",
        "restore",
        "restaurar",
    }
)

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
    plugin_name: str
    plugin_version: str
    descriptor: dict[str, Any]
    handler: CommandHandler


def _localized_text(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != _LOCALES:
        raise ValueError(f"{label} must contain exactly en and pt-BR")
    result = {key: str(item).strip() for key, item in value.items()}
    if not all(result.values()):
        raise ValueError(f"{label} translations cannot be empty")
    return result


def _localized_terms(value: Any, label: str) -> dict[str, list[str]]:
    if not isinstance(value, dict) or set(value) != _LOCALES:
        raise ValueError(f"{label} must contain exactly en and pt-BR")
    result: dict[str, list[str]] = {}
    for locale, terms in value.items():
        if not isinstance(terms, list) or not all(
            isinstance(term, str) and term.strip() for term in terms
        ):
            raise ValueError(f"{label}.{locale} must be a string array")
        normalized = [term.strip() for term in terms]
        if len(normalized) != len(set(normalized)):
            raise ValueError(f"{label}.{locale} cannot contain duplicates")
        result[locale] = normalized
    return result


def _namespace_token(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


def validate_descriptor(value: Any) -> dict[str, Any]:
    """Validate the forward-only schema-v2 command descriptor exposed to browsers."""
    if not isinstance(value, dict):
        raise ValueError("command descriptor must be an object")
    legacy = {"usage", "arguments", "fields"} & set(value)
    if legacy:
        raise ValueError("command descriptor schema v1 is unsupported; use schema v2 inputs")
    allowed = {
        "name",
        "title",
        "summary",
        "icon",
        "aliases",
        "keywords",
        "inputs",
        "result_kind",
    }
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"unknown command descriptor fields: {', '.join(sorted(unknown))}")
    missing = allowed - set(value)
    if missing:
        raise ValueError(f"missing command descriptor fields: {', '.join(sorted(missing))}")

    name = value.get("name")
    if not isinstance(name, str) or not _COMMAND_RE.fullmatch(name):
        raise ValueError("command name must be a lowercase kebab-case identifier")
    title = _localized_text(value.get("title"), "title")
    summary = _localized_text(value.get("summary"), "summary")
    icon = value.get("icon")
    if not isinstance(icon, str) or not icon.strip() or len(icon) > 32:
        raise ValueError("icon must be a non-empty string of at most 32 characters")
    aliases = _localized_terms(value.get("aliases"), "aliases")
    keywords = _localized_terms(value.get("keywords"), "keywords")

    alias_tokens: set[str] = set()
    for locale, terms in aliases.items():
        for alias in terms:
            token = _namespace_token(alias)
            if not _COMMAND_RE.fullmatch(token) or alias != alias.lower():
                raise ValueError(f"aliases.{locale} must use lowercase kebab-case identifiers")
            if token == name or token in alias_tokens:
                raise ValueError(f"duplicate command name or alias {alias}")
            alias_tokens.add(token)

    result_kind = value.get("result_kind")
    if not isinstance(result_kind, str) or "/" not in result_kind or result_kind.endswith("/"):
        raise ValueError("result_kind must be a namespaced identifier")

    inputs: list[dict[str, Any]] = []
    input_names: set[str] = set()
    raw_inputs = value.get("inputs")
    if not isinstance(raw_inputs, list):
        raise ValueError("inputs must be an array")
    for index, item in enumerate(raw_inputs):
        allowed_input = {"name", "type", "required", "label", "hint", "accept", "max_bytes"}
        if not isinstance(item, dict) or set(item) - allowed_input:
            raise ValueError(f"inputs[{index}] has an invalid shape")
        input_name = item.get("name")
        input_type = item.get("type")
        if not isinstance(input_name, str) or not _COMMAND_RE.fullmatch(input_name):
            raise ValueError(f"inputs[{index}].name is invalid")
        if input_name in input_names:
            raise ValueError(f"duplicate input {input_name}")
        if input_type not in _FIELD_TYPES:
            raise ValueError(f"inputs[{index}].type must be text, textarea, or file")
        input_names.add(input_name)
        normalized: dict[str, Any] = {
            "name": input_name,
            "type": input_type,
            "required": bool(item.get("required", False)),
            "label": _localized_text(item.get("label"), f"inputs[{index}].label"),
            "hint": _localized_text(item.get("hint"), f"inputs[{index}].hint"),
        }
        if input_type == "file":
            accept = item.get("accept")
            max_bytes = item.get("max_bytes")
            if (
                not isinstance(accept, list)
                or not accept
                or not all(isinstance(entry, str) and entry for entry in accept)
            ):
                raise ValueError(f"inputs[{index}].accept must be a non-empty string array")
            if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
                raise ValueError(f"inputs[{index}].max_bytes must be a positive integer")
            normalized.update({"accept": accept, "max_bytes": max_bytes})
        elif set(item) & {"accept", "max_bytes"}:
            raise ValueError(f"inputs[{index}] file constraints require type=file")
        inputs.append(normalized)

    normalized_descriptor = {
        "name": name,
        "title": title,
        "summary": summary,
        "icon": icon.strip(),
        "aliases": aliases,
        "keywords": keywords,
        "inputs": inputs,
        "result_kind": result_kind,
    }
    json.dumps(normalized_descriptor, ensure_ascii=False)
    return normalized_descriptor


class CommandRegistry:
    """Strict command namespace shared by core actions and active backend plugins."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandRegistration] = {}
        self._owners: dict[str, str] = dict.fromkeys(BUILTIN_COMMAND_NAMES, "Alex Tavern")

    def register(
        self,
        plugin_id: str,
        plugin_name: str,
        plugin_version: str,
        descriptor: dict[str, Any],
        handler: CommandHandler,
    ) -> None:
        if not callable(handler):
            raise TypeError("command handler must be callable")
        normalized = validate_descriptor(descriptor)
        result_kind = normalized["result_kind"]
        if not (result_kind.startswith("core/") or result_kind.startswith(f"{plugin_id}/")):
            raise ValueError(f"result_kind must use core/ or {plugin_id}/ namespace")
        names = {normalized["name"]}
        names.update(
            _namespace_token(alias)
            for aliases in normalized["aliases"].values()
            for alias in aliases
        )
        for name in sorted(names):
            if name in self._owners:
                raise ValueError(
                    f"command name or alias /{name} is already reserved by {self._owners[name]}"
                )
        registration = CommandRegistration(
            plugin_id=plugin_id,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            descriptor=normalized,
            handler=handler,
        )
        self._commands[normalized["name"]] = registration
        for name in names:
            self._owners[name] = plugin_id

    def remove_plugin(self, plugin_id: str) -> None:
        self._commands = {
            name: registration
            for name, registration in self._commands.items()
            if registration.plugin_id != plugin_id
        }
        self._owners = {name: owner for name, owner in self._owners.items() if owner != plugin_id}

    def public_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                **deepcopy(registration.descriptor),
                "plugin_id": registration.plugin_id,
                "plugin_name": registration.plugin_name,
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
        if not isinstance(payload, dict) or set(payload) != {"values", "files"}:
            raise CommandError("invalid_payload", "Command input has an invalid shape.")
        values = payload["values"]
        files = payload["files"]
        if not isinstance(values, dict) or not isinstance(files, dict):
            raise CommandError("invalid_payload", "Command input sections must be objects.")

        specs = {item["name"]: item for item in registration.descriptor["inputs"]}
        value_specs = {name: spec for name, spec in specs.items() if spec["type"] != "file"}
        file_specs = {name: spec for name, spec in specs.items() if spec["type"] == "file"}
        if set(values) - set(value_specs):
            raise CommandError("unknown_value", "The command contains an unknown value.")
        if set(files) - set(file_specs):
            raise CommandError("unknown_file", "The command contains an unknown file field.")

        normalized_values: dict[str, str] = {}
        normalized_files: dict[str, dict[str, Any]] = {}
        for name, spec in value_specs.items():
            value = values.get(name, "")
            if not isinstance(value, str):
                raise CommandError("invalid_value", "Input must be text.", field=name)
            value = value.strip()
            if spec["required"] and not value:
                raise CommandError("required", "This input is required.", field=name)
            normalized_values[name] = value
        for name, spec in file_specs.items():
            raw = files.get(name)
            if raw is None:
                if spec["required"]:
                    raise CommandError("required", "This file is required.", field=name)
                continue
            if not isinstance(raw, dict) or set(raw) != {"name", "media_type", "data_base64"}:
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
        return {"values": normalized_values, "files": normalized_files}

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
            "values": {
                name: {"characters": len(value)}
                for name, value in payload.get("values", {}).items()
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
