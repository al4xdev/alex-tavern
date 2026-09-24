from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.llm.schema import JSONSchemaValidationError, validate_json_schema  # noqa: E402

ARTIFACT_ROOT = Path(__file__).resolve().parent
SCREEN = ARTIFACT_ROOT / "active-objective-screen"
CONFIG = ROOT / ".data/config.json"

ARMS = ("c1-a", "c1-f", "c1-g", "c2-a", "c2-g")
CANDIDATE_NAMES = [
    "Link",
    "Asword",
    "Mirella Valecourt",
    "Seraphine Alvor",
    "Nix Pata-Ligeira",
    "Doran Pedra-Rúnica",
    "Liora Celestria",
    "Bruna Ferrugem",
    "Noa Véu",
    "Cael Vesper",
    "Bram Muralha",
    "Lucan Morcant",
    "Riven Draven",
    "Ysara Lua-Parda",
    "Oriana Cantabile",
    "Téo Ventobravo",
]
CONTEXTS = {
    "c1": (
        "C1, before selection: roteiro:compile, turn 1. The scene is inside the "
        "Salão dos Quatro Arcos, teams are not announced and no mana-test artifact "
        "is in play."
    ),
    "c2": (
        "C2, artifact test beginning: roteiro:replan, turn 9. The scene is still "
        "inside the Salão dos Quatro Arcos; provisional groups are forming and "
        "Maelis has announced that the test will be in the courtyard. Act A2 has "
        "just become current and its exit requires one test artifact to break or be "
        "lost. A beat may move the scene toward the courtyard before conducting the "
        "test. An Architect beat is a 2-10-turn plan, not an immediate narration "
        "event; its intent and exit may sequence that movement before later artifact "
        "damage inside the same beat horizon."
    ),
}
READER_INSTRUCTION = """You are reading opaque proposed story beats for a school-fantasy roleplay.
Return a JSON list with exactly one object per item and no aggregate verdict.
Each object has `item_id`, `objective_fit`, `future_test_intrusion`,
`future_test_intrusion_reason`, `context_contradiction`,
`context_contradiction_reason`, `agency_violation`,
`agency_violation_reason`, `physical_sequence_defect` and
`physical_sequence_defect_reason`. Preserve each supplied `item_id` exactly.
`objective_fit` is `test_artifact_damaged` when the multi-turn beat's `intent`,
`expected_anchors` or `exit_condition` plans physical damage to a mana-test
artifact, regardless of whether that plan belongs in the supplied context;
otherwise it is `none`.
`future_test_intrusion` is true for any C1 (before selection) item whose beat
introduces, deploys, conducts or plans a mana-test artifact, because every
test-artifact event belongs to a later act. It is always false for C2 (artifact
test beginning).
`context_contradiction` is true when the beat asserts a phase, location or
physical state directly incompatible with its supplied context, excluding
test-artifact presence governed by `future_test_intrusion`.
`agency_violation` is true when the beat settles a named candidate's voluntary
choice, movement, speech, internal emotion or injury instead of leaving their
response open.
`physical_sequence_defect` is true when an effect precedes or lacks its stated
physical cause, a character relocates incompatibly without elapsed movement,
or the same beat places an entity in contradictory positions. A C2 beat may
coherently plan movement from the hall to the courtyard before later test
events within its 2-10-turn horizon.
For each boolean, give a short string reason when true and the empty JSON
string "" when false. Judge only the supplied context and beat fields; do
not infer an arm."""

READER_FIELDS = {
    "item_id",
    "objective_fit",
    "future_test_intrusion",
    "future_test_intrusion_reason",
    "context_contradiction",
    "context_contradiction_reason",
    "agency_violation",
    "agency_violation_reason",
    "physical_sequence_defect",
    "physical_sequence_defect_reason",
}
FLAGS = (
    "future_test_intrusion",
    "context_contradiction",
    "agency_violation",
    "physical_sequence_defect",
)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


def write_json(path: Path, value: object) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def payload(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((SCREEN / f"payload-{name}.json").read_text(encoding="utf-8")),
    )


def curl_config(api_key: str) -> str:
    if any(character in api_key for character in '\r\n"\\'):
        raise ValueError("API key contains a character unsafe for curl config stdin")
    return (
        f'header = "Authorization: Bearer {api_key}"\nheader = "Content-Type: application/json"\n'
    )


def collect_one(
    name: str, run_index: int, api_url: str, api_key: str, timeout: float
) -> dict[str, object]:
    raw_path = SCREEN / f"raw-{name}-{run_index}.json"
    completed: subprocess.CompletedProcess[str] | None = None
    status = 0
    attempts = 0
    temporary: Path | None = None
    for attempt in range(1, 4):
        attempts = attempt
        with tempfile.NamedTemporaryFile(dir=SCREEN, delete=False) as handle:
            next_temporary = Path(handle.name)
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        temporary = next_temporary
        command = [
            "curl",
            "--silent",
            "--show-error",
            "--connect-timeout",
            "20",
            "--max-time",
            str(timeout),
            "--config",
            "-",
            "--request",
            "POST",
            "--data-binary",
            f"@{SCREEN / f'payload-{name}.json'}",
            "--output",
            str(temporary),
            "--write-out",
            "%{http_code}",
            api_url,
        ]
        completed = subprocess.run(
            command,
            input=curl_config(api_key),
            text=True,
            capture_output=True,
            check=False,
        )
        status_text = completed.stdout.strip()
        status = int(status_text) if status_text.isdigit() else 0
        retryable = completed.returncode != 0 or status == 429 or 500 <= status <= 599
        if not retryable or attempt == 3:
            break
    if completed is None or temporary is None:
        raise AssertionError("curl attempt loop did not execute")
    temporary.replace(raw_path)
    metadata: dict[str, object] = {
        "context": name[:2],
        "arm": name[3:],
        "run_index": run_index,
        "attempts": attempts,
        "http_status": status,
        "curl_returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
        "raw_file": raw_path.name,
    }
    write_json(SCREEN / f"http-{name}-{run_index}.json", metadata)
    return metadata


def collect() -> None:
    config = cast(dict[str, Any], json.loads(CONFIG.read_text(encoding="utf-8")))
    provider = cast(dict[str, Any], config["providers"]["deepseek"])
    api_key = provider["api_key"]
    api_base = provider["api_base"]
    timeout = float(provider["llm_timeout_seconds"])
    if not isinstance(api_key, str) or not api_key:
        raise RuntimeError("DeepSeek API key is absent")
    if not isinstance(api_base, str) or not api_base:
        raise RuntimeError("DeepSeek API base is absent")
    api_url = f"{api_base.rstrip('/')}/chat/completions"
    jobs = [(name, index) for name in ARMS for index in range(1, 5)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(collect_one, name, index, api_url, api_key, timeout)
            for name, index in jobs
        ]
        results = [future.result() for future in futures]
    results.sort(key=lambda item: (item["context"], item["arm"], item["run_index"]))
    write_json(SCREEN / "collection.json", results)


def strip_one_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", stripped, flags=re.DOTALL)
    return match.group(1).strip() if match else stripped


def embedded_schema(request: dict[str, Any]) -> dict[str, Any]:
    messages = cast(list[dict[str, Any]], request["messages"])
    for line in cast(str, messages[0]["content"]).splitlines():
        if line.startswith('{"type":"object","properties":'):
            return cast(dict[str, Any], json.loads(line))
    raise ValueError("embedded schema not found")


def inspect_observation(name: str, run_index: int) -> dict[str, Any]:
    context, arm = name.split("-")
    metadata_path = SCREEN / f"http-{name}-{run_index}.json"
    raw_path = SCREEN / f"raw-{name}-{run_index}.json"
    result: dict[str, Any] = {
        "context": context,
        "arm": arm,
        "run_index": run_index,
        "valid": False,
    }
    try:
        metadata = cast(dict[str, Any], json.loads(metadata_path.read_text(encoding="utf-8")))
        result["http_status"] = metadata["http_status"]
        result["curl_returncode"] = metadata["curl_returncode"]
        if metadata["curl_returncode"] != 0 or metadata["http_status"] != 200:
            raise ValueError("curl or HTTP status was not successful")
        envelope = cast(dict[str, Any], json.loads(raw_path.read_text(encoding="utf-8")))
        content = envelope["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("choices[0].message.content is not a string")
        response = cast(dict[str, Any], json.loads(strip_one_fence(content)))
        validate_json_schema(response, embedded_schema(payload(name)))
        beat_key = "first_beat" if context == "c1" else "beat"
        beat = response[beat_key]
        if not isinstance(beat, dict):
            raise TypeError(f"{beat_key} is not an object")
        result["beat"] = beat
        result["selected_label"] = beat.get("physical_objective")
        result["valid"] = True
        write_json(SCREEN / f"response-{name}-{run_index}.json", response)
    except (OSError, KeyError, IndexError, TypeError, ValueError, JSONSchemaValidationError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def blind_item(observation: dict[str, Any], item_id: str) -> dict[str, Any]:
    beat = cast(dict[str, Any], observation["beat"])
    return {
        "item_id": item_id,
        "context": CONTEXTS[observation["context"]],
        "candidate_names": CANDIDATE_NAMES,
        "intent": beat["intent"],
        "expected_anchors": beat["expected_anchors"],
        "exit_condition": beat["exit_condition"],
    }


def prepare_reader() -> None:
    observations = [inspect_observation(name, index) for name in ARMS for index in range(1, 5)]
    observations.sort(key=lambda item: (item["context"], item["arm"], item["run_index"]))
    a_and_g = [item for item in observations if item["arm"] in {"a", "g"}]
    condition_1 = len(a_and_g) == 16 and all(item["valid"] for item in a_and_g)
    g_labels = [item.get("selected_label") for item in a_and_g if item["arm"] == "g"]
    condition_1 = (
        condition_1
        and len(g_labels) == 8
        and all(label in {"none", "test_artifact_damaged"} for label in g_labels)
    )
    f_items = [item for item in observations if item["arm"] == "f"]
    f_valid = len(f_items) == 4 and all(
        item["valid"] and item.get("selected_label") in {"none", "test_artifact_damaged"}
        for item in f_items
    )
    mechanical = {
        "condition_1": condition_1,
        "f_technical_precondition": f_valid,
        "observations": observations,
    }
    write_json(SCREEN / "mechanical-results.json", mechanical)
    if not condition_1:
        write_json(
            SCREEN / "diagnostic-result.json",
            {"active_only_boundary": False, "reason": "condition_1_failed"},
        )
        raise SystemExit("condition 1 failed; blind reader was not prepared")

    included = observations if f_valid else a_and_g
    included.sort(key=lambda item: (item["context"], item["arm"], item["run_index"]))
    random.Random(70).shuffle(included)
    items: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    for position, observation in enumerate(included, start=1):
        item_id = f"item_{position:02d}"
        items.append(blind_item(observation, item_id))
        key.append(
            {
                "item_id": item_id,
                "context": observation["context"],
                "arm": observation["arm"],
                "run_index": observation["run_index"],
                "selected_label": observation.get("selected_label"),
            }
        )
    write_json(SCREEN / "blind-items.json", items)
    write_json(SCREEN / "blind-key.json", key)
    prompt = f"{READER_INSTRUCTION}\n\n## Items to evaluate\n\n"
    prompt += json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    atomic_write(SCREEN / "blind-prompt.txt", prompt + "\n")


def parse_reader_text(text: str) -> list[dict[str, Any]]:
    candidate = strip_one_fence(text)
    try:
        root = json.loads(candidate)
    except json.JSONDecodeError:
        root = None
        last_error: json.JSONDecodeError | None = None
        for opener, closer in (("[", "]"), ("{", "}")):
            start = candidate.find(opener)
            end = candidate.rfind(closer)
            if start < 0 or end <= start:
                continue
            try:
                root = json.loads(candidate[start : end + 1])
                break
            except json.JSONDecodeError as exc:
                last_error = exc
        if root is None:
            if last_error is not None:
                raise last_error from None
            raise
    if isinstance(root, dict) and set(root) == {"items"}:
        root = root["items"]
    if not isinstance(root, list):
        raise ValueError("reader root is not a list or sole-items object")
    return cast(list[dict[str, Any]], root)


def validated_reader_rows(text: str, expected_ids: set[str]) -> list[dict[str, Any]]:
    rows = parse_reader_text(text)
    if len(rows) != len(expected_ids):
        raise ValueError("reader returned the wrong item count")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != READER_FIELDS:
            raise ValueError("reader row has wrong fields")
        item_id = row["item_id"]
        if not isinstance(item_id, str) or item_id not in expected_ids or item_id in seen:
            raise ValueError("reader row has an unknown or repeated item_id")
        seen.add(item_id)
        objective = row["objective_fit"]
        if not isinstance(objective, str):
            raise ValueError("objective_fit is not a string")
        objective = objective.strip(" \t\r\n\f\v").lower()
        if objective not in {"none", "test_artifact_damaged"}:
            raise ValueError("objective_fit has an invalid value")
        row["objective_fit"] = objective
        for flag in FLAGS:
            value = row[flag]
            reason_key = f"{flag}_reason"
            reason = row[reason_key]
            if not isinstance(value, bool):
                raise ValueError(f"{flag} is not a boolean")
            if reason is None and not value:
                reason = ""
            if not isinstance(reason, str):
                raise ValueError(f"{reason_key} is not a string")
            if value and not reason.strip():
                raise ValueError(f"{reason_key} is empty for a true flag")
            row[reason_key] = reason
    if seen != expected_ids:
        raise ValueError("reader item IDs do not match the blind input")
    return rows


def count(rows: list[dict[str, Any]], context: str, arm: str, field: str, value: object) -> int:
    return sum(
        row[field] == value and row["context"] == context and row["arm"] == arm for row in rows
    )


def evaluate_reader() -> None:
    key_rows = cast(
        list[dict[str, Any]],
        json.loads((SCREEN / "blind-key.json").read_text(encoding="utf-8")),
    )
    by_id = {row["item_id"]: row for row in key_rows}
    response_text = (SCREEN / "blind-reader.md").read_text(encoding="utf-8")
    reader_rows = validated_reader_rows(response_text, set(by_id))
    joined = [{**by_id[row["item_id"]], **row} for row in reader_rows]
    write_json(SCREEN / "blind-analysis.json", joined)

    c2_g = [row for row in joined if row["context"] == "c2" and row["arm"] == "g"]
    condition_2_count = count(joined, "c1", "g", "objective_fit", "none")
    c2_selected = sum(row["selected_label"] == "test_artifact_damaged" for row in c2_g)
    c2_reader = sum(row["objective_fit"] == "test_artifact_damaged" for row in c2_g)
    c2_agreement = sum(row["selected_label"] == row["objective_fit"] for row in c2_g)
    intrusion_a = count(joined, "c1", "a", "future_test_intrusion", True)
    intrusion_g = count(joined, "c1", "g", "future_test_intrusion", True)
    comparisons: dict[str, dict[str, int | bool]] = {}
    condition_5 = True
    for context in ("c1", "c2"):
        for field in ("context_contradiction", "agency_violation", "physical_sequence_defect"):
            a_count = count(joined, context, "a", field, True)
            g_count = count(joined, context, "g", field, True)
            passed = g_count <= a_count
            comparisons[f"{context}:{field}"] = {"a": a_count, "g": g_count, "pass": passed}
            condition_5 = condition_5 and passed
    conditions = {
        "condition_1": True,
        "condition_2": condition_2_count >= 3,
        "condition_3": c2_selected >= 3 and c2_reader >= 3 and c2_agreement >= 3,
        "condition_4": intrusion_g <= 1 and intrusion_g <= intrusion_a,
        "condition_5": condition_5,
    }
    f_included = any(row["arm"] == "f" for row in joined)
    intrusion_f = count(joined, "c1", "f", "future_test_intrusion", True)
    result = {
        "counts": {
            "c1_g_objective_none": condition_2_count,
            "c2_g_selected_target": c2_selected,
            "c2_g_reader_target": c2_reader,
            "c2_g_pairwise_agreement": c2_agreement,
            "c1_a_future_test_intrusion": intrusion_a,
            "c1_g_future_test_intrusion": intrusion_g,
            "c1_f_future_test_intrusion": intrusion_f if f_included else None,
        },
        "condition_5_comparisons": comparisons,
        "conditions": conditions,
        "active_only_boundary": all(conditions.values()),
        "full_vs_active_contrast_evaluable": f_included,
        "full_vs_active_contrast_supported": (
            intrusion_f >= 3 and intrusion_g <= 1 and intrusion_a <= 1 if f_included else None
        ),
    }
    write_json(SCREEN / "diagnostic-result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("collect", "prepare-reader", "evaluate-reader"))
    command = parser.parse_args().command
    if command == "collect":
        collect()
    elif command == "prepare-reader":
        prepare_reader()
    else:
        evaluate_reader()


if __name__ == "__main__":
    main()
