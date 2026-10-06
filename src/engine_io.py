"""Typed conversation boundaries; text transforms never own wire structure or canon."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Literal

Operation = Literal["turn", "history", "state", "suggestions", "opening-suggestions"]
TEXT_FIELDS = ("speech", "thought", "action", "event")


@dataclass(slots=True)
class EngineInput:
    """One submitted turn, from the first filter through routing resolution."""

    speech: str
    thought: str
    action: str
    force_speaker: str | None
    event: str
    skip: bool
    audience: list[str] | None
    transformed_fields: list[str] = field(default_factory=list)
    effective_force_speaker: str | None = None

    @property
    def texts(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in TEXT_FIELDS}

    def replace_texts(self, texts: dict[str, str]) -> None:
        if set(texts) != set(TEXT_FIELDS):
            raise ValueError("EngineInput text fields must be preserved")
        for name, value in texts.items():
            if not isinstance(value, str):
                raise TypeError("EngineInput texts must be strings")
            setattr(self, name, value)

    @property
    def effective_input(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in TEXT_FIELDS[:3]}

    def logged_input(self) -> dict[str, Any]:
        return {**self.texts, "force_speaker": self.force_speaker, "skip": self.skip}

    def validate_transform(self, candidate: Any) -> None:
        if not isinstance(candidate, EngineInput):
            raise TypeError("engine.input must return EngineInput")
        for name in (
            "force_speaker",
            "skip",
            "audience",
            "transformed_fields",
            "effective_force_speaker",
        ):
            if getattr(candidate, name) != getattr(self, name):
                raise ValueError(f"engine.input cannot change {name}")
        _validate_texts(self.texts, candidate.texts)


@dataclass(frozen=True, slots=True)
class EngineOutput:
    """Only selected reader texts, never the mutable response or canonical state."""

    operation: Operation
    viewer_id: str
    texts: dict[str, str]

    def validate_transform(self, candidate: Any) -> None:
        if not isinstance(candidate, EngineOutput):
            raise TypeError("engine.output must return EngineOutput")
        if (candidate.operation, candidate.viewer_id) != (self.operation, self.viewer_id):
            raise ValueError("engine.output cannot change operation or viewer")
        _validate_texts(self.texts, candidate.texts)


def _validate_texts(original: dict[str, str], candidate: dict[str, str]) -> None:
    if not isinstance(candidate, dict) or set(candidate) != set(original):
        raise ValueError("Conversation transforms must preserve text keys")
    for key, value in candidate.items():
        if not isinstance(value, str):
            raise TypeError("Conversation texts must be strings")
        if bool(original[key].strip()) != bool(value.strip()):
            raise ValueError("Conversation transforms cannot populate or erase a field")


class OutputProjection:
    """Host-owned wire shape plus an explicit map of its translatable leaves."""

    def __init__(self, operation: Operation, viewer_id: str, payload: Any) -> None:
        self.payload = deepcopy(payload)
        self.paths: dict[str, tuple[str | int, ...]] = {}
        texts: dict[str, str] = {}

        def add(*path: str | int) -> None:
            value = self.payload
            for part in path:
                value = value[part]
            if isinstance(value, str):
                key = "/".join(str(part) for part in path)
                self.paths[key] = path
                texts[key] = value

        def history(prefix: tuple[str | int, ...], records: list[dict[str, Any]]) -> None:
            for index in range(len(records)):
                add(*prefix, index, "content")

        def beat(prefix: tuple[str | int, ...], value: dict[str, Any]) -> None:
            if "narration" in value:
                add(*prefix, "narration")
            for index, entry in enumerate(value.get("character_responses", [])):
                for name in ("speech", "thought", "action_intent"):
                    if name in entry:
                        add(*prefix, "character_responses", index, name)

        if operation == "turn":
            beat((), self.payload)
            for index, value in enumerate(self.payload.get("beats") or []):
                beat(("beats", index), value)
            if self.payload.get("effective_input"):
                for name in TEXT_FIELDS[:3]:
                    add("effective_input", name)
        elif operation == "history":
            history((), self.payload)
        elif operation == "state":
            history(("history",), self.payload["history"])
        elif operation == "suggestions":
            for index, suggestion in enumerate(self.payload["suggestions"]):
                for name in TEXT_FIELDS[:3]:
                    if name in suggestion:
                        add("suggestions", index, name)
        elif operation == "opening-suggestions":
            for index in range(len(self.payload["suggestions"])):
                add("suggestions", index)
        self.output = EngineOutput(operation, viewer_id, texts)

    def render(self, output: EngineOutput) -> Any:
        self.output.validate_transform(output)
        for key, path in self.paths.items():
            parent = self.payload
            for part in path[:-1]:
                parent = parent[part]
            parent[path[-1]] = output.texts[key]
        return self.payload


class EngineBoundaryError(RuntimeError):
    """A required transform failed; only presentation reads may be retried."""

    def __init__(
        self,
        phase: Literal["input", "output"],
        operation: Operation,
        *,
        operation_id: str | None = None,
        committed: bool = False,
    ) -> None:
        self.phase = phase
        self.operation = operation
        self.operation_id = operation_id
        self.committed = committed
        super().__init__(f"The required {phase} transformation failed. Try again.")


class PresentationUnavailableError(LookupError):
    """A recovery response was superseded or its canonical revision changed."""
