from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / ".data/sessions/20d4cdb3/debug.jsonl"
OUT = Path(__file__).resolve().parent / "objective-catalog-screen"

CATALOGUE = """

PHYSICAL OBJECTIVE CATALOGUE (scenario-authorized; choose exactly one label for this beat):
- none: this beat does not complete an authorized physical objective.
- test_artifact_damaged: one mana-test artifact is physically damaged during the courtyard test.
Set physical_objective to the matching label. A label is a planning target, not permission to
claim it already happened before the beat, and never requires a character decision.
"""


def source_records() -> dict[str, dict[str, Any]]:
    wanted = {("roteiro:compile", 1): "c1", ("roteiro:replan", 9): "c2"}
    found: dict[str, dict[str, Any]] = {}
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        record = cast(dict[str, Any], json.loads(line))
        agent = record.get("agent")
        turn_number = record.get("turn_number")
        if not isinstance(agent, str) or not isinstance(turn_number, int):
            continue
        label = wanted.get((agent, turn_number))
        if label is not None:
            found[label] = record
    if set(found) != {"c1", "c2"}:
        raise RuntimeError("frozen roteiro records not found")
    return found


def add_objective_to_schema(schema: dict[str, Any], beat_property: str) -> None:
    beat = schema["properties"][beat_property]
    beat["properties"]["physical_objective"] = {
        "type": "string",
        "enum": ["none", "test_artifact_damaged"],
    }
    beat["required"].append("physical_objective")


def candidate_messages(messages: list[dict[str, Any]], beat_property: str) -> list[dict[str, Any]]:
    result = copy.deepcopy(messages)
    system = result[0]["content"]
    language_marker = "\n- Always respond and write in "
    before_language, marker, after_language = system.partition(language_marker)
    if not marker:
        raise RuntimeError("shared language instruction marker not found")
    system = before_language + CATALOGUE + marker + after_language

    lines = system.splitlines()
    schema_index = next(
        index
        for index, line in enumerate(lines)
        if line.startswith('{"type":"object","properties":')
    )
    schema = cast(dict[str, Any], json.loads(lines[schema_index]))
    add_objective_to_schema(schema, beat_property)
    lines[schema_index] = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    result[0]["content"] = "\n".join(lines)
    return result


def provider_payload(record: dict[str, Any]) -> dict[str, Any]:
    request = copy.deepcopy(record["request"])
    provider_options = request.pop("provider_options", {})
    return {
        **request,
        "model": record["model"],
        "thinking": {
            "type": "enabled" if provider_options.get("thinking_enabled") else "disabled"
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for context, record in source_records().items():
        baseline = provider_payload(record)
        beat_property = "first_beat" if context == "c1" else "beat"
        candidate = copy.deepcopy(baseline)
        candidate["messages"] = candidate_messages(candidate["messages"], beat_property)
        response_format = candidate.get("response_format", {})
        if response_format.get("type") == "json_schema":
            add_objective_to_schema(response_format["json_schema"]["schema"], beat_property)
        for arm, payload in (("a", baseline), ("b", candidate)):
            (OUT / f"payload-{context}-{arm}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
