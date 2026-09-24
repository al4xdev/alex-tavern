from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.llm.schema import JSONSchemaValidationError, validate_json_schema  # noqa: E402

OUT = Path(__file__).resolve().parent
BATTERY = ROOT / "plans/artifacts/repetition-battery"
CONFIG = ROOT / ".data/config.json"
MANIFEST = OUT / "manifest.json"
RUNS = OUT / "runs"
PREREGISTRATION = OUT / "PREREGISTRATION.md"
READER_INSTRUCTION = OUT / "READER-INSTRUCTION.txt"

SEED_CALLS = 640922
SEED_READER = 640923
CASES = {
    "t": ("b11b38dc", 13),
    "p": ("54bcdace", 11),
    "n1": ("00997daa", 33),
    "n2": ("09aabf25", 30),
    "n3": ("21f7c4e1", 26),
}
EXPECTED_A = {"t": False, "p": True, "n1": False, "n2": False, "n3": False}
EXPECTED_B = {"t": True, "p": True, "n1": False, "n2": False, "n3": False}

OLD_WORDING = (
    '- "return_control": true ONLY when this beat ends on a decision, danger,\n'
    "  or direct question aimed at ONE named person, which that person alone\n"
    "  can answer; false while the scene can keep moving on its own.\n"
)
NEW_WORDING = (
    '- "return_control": true when, after this beat\'s events, one named person\'s\n'
    "  answer or voluntary action is the next causal step. This includes an invitation,\n"
    "  request, order, direct question, or immediate danger aimed at that person, even\n"
    "  when other characters also spoke in this beat. Set false when a physical\n"
    "  consequence or another person's already-started action should occur first.\n"
)

READER_TEXT = """You are a clean reader judging causal handoff points in roleplay scenes.
You do not know which character, if any, is controlled by a human. Do not infer one.
For every opaque item, decide the expected value of return_control from its frozen
source context and the Director output. The output deliberately omits the model's
own return_control value.

Apply this precedence exactly:
1. false if an already-started action by another person or an immediate physical
   consequence must occur before anyone can answer;
2. otherwise true if a named person's answer or voluntary action is the next
   causal step;
3. otherwise false.

Return only a JSON array with exactly 40 objects. Each object has exactly item_id,
expected_return_control, and reason. Preserve every item_id exactly;
expected_return_control is a JSON boolean and reason is a non-empty string.
"""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


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


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def session_dir(session_id: str) -> Path:
    matches = sorted(BATTERY.glob(f"*/sessions/{session_id}"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one session directory for {session_id}, found {matches}")
    return matches[0]


def archived_record(source: Path, turn_number: int) -> tuple[int, dict[str, Any]]:
    matches: list[tuple[int, dict[str, Any]]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        record = cast(dict[str, Any], json.loads(line))
        if (
            record.get("agent") != "director"
            or record.get("turn_number") != turn_number
            or record.get("error") is not None
        ):
            continue
        response = record.get("response")
        if not isinstance(response, str):
            continue
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            matches.append((line_number, record))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one valid Director record at {source}:{turn_number}, found {len(matches)}"
        )
    return matches[0]


def request_body(record: dict[str, Any]) -> dict[str, Any]:
    request = cast(dict[str, Any], record["request"])
    provider_options = cast(dict[str, Any], request["provider_options"])
    if provider_options.get("thinking_enabled") is not False:
        raise RuntimeError("archived request did not disable thinking")
    return {
        "model": record["model"],
        "messages": copy.deepcopy(request["messages"]),
        "max_tokens": request["max_tokens"],
        "response_format": copy.deepcopy(request["response_format"]),
        "thinking": {"type": "disabled"},
    }


def replace_wording(body: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(body)
    messages = cast(list[dict[str, Any]], candidate["messages"])
    occurrences = sum(str(message.get("content", "")).count(OLD_WORDING) for message in messages)
    if occurrences != 1:
        raise RuntimeError(f"expected one return_control wording block, found {occurrences}")
    for message in messages:
        content = message.get("content")
        if isinstance(content, str) and OLD_WORDING in content:
            message["content"] = content.replace(OLD_WORDING, NEW_WORDING, 1)
    return candidate


def extract_reader_context(body: dict[str, Any]) -> str:
    messages = cast(list[dict[str, Any]], body["messages"])
    user_messages = [message for message in messages if message.get("role") == "user"]
    if not user_messages or not isinstance(user_messages[-1].get("content"), str):
        raise RuntimeError("request lacks a final user message")
    content = cast(str, user_messages[-1]["content"])
    start_marker = "HISTORY:\n"
    end_marker = "\nROTEIRO ("
    if content.count(start_marker) != 1 or content.count(end_marker) != 1:
        raise RuntimeError("reader context boundaries are not unique")
    start = content.index(start_marker)
    end = content.index(end_marker, start)
    return content[start:end].rstrip() + "\n"


def assert_only_wording_changed(original: dict[str, Any], candidate: dict[str, Any]) -> None:
    restored = copy.deepcopy(candidate)
    messages = cast(list[dict[str, Any]], restored["messages"])
    occurrences = sum(str(message.get("content", "")).count(NEW_WORDING) for message in messages)
    if occurrences != 1:
        raise RuntimeError(f"expected one candidate wording block, found {occurrences}")
    for message in messages:
        content = message.get("content")
        if isinstance(content, str) and NEW_WORDING in content:
            message["content"] = content.replace(NEW_WORDING, OLD_WORDING, 1)
    if restored != original:
        raise RuntimeError("candidate request differs outside return_control wording")


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("preserve the existing manifest")
    if not PREREGISTRATION.exists():
        raise RuntimeError("preregistration must exist before preparation")
    if READER_INSTRUCTION.exists():
        raise RuntimeError("preserve the existing reader instruction")
    atomic_write(READER_INSTRUCTION, READER_TEXT)

    prepared: dict[str, Any] = {}
    for label, (session_id, turn_number) in CASES.items():
        directory = session_dir(session_id)
        state = load_json(directory / "state.json")
        if turn_number > int(state["revision"]):
            raise RuntimeError(f"{session_id} T{turn_number} is not committed")
        source = directory / "debug.jsonl"
        line_number, record = archived_record(source, turn_number)
        arm_a = request_body(record)
        arm_b = replace_wording(arm_a)
        assert_only_wording_changed(arm_a, arm_b)
        context_path = OUT / f"reader-context-{label}.txt"
        if context_path.exists():
            raise RuntimeError(f"preserve existing {context_path.name}")
        atomic_write(context_path, extract_reader_context(arm_a))
        reconstructed = json.dumps(arm_a, ensure_ascii=False, sort_keys=True).encode()
        prepared[label] = {
            "session_id": session_id,
            "turn_number": turn_number,
            "source": str(source.relative_to(ROOT)),
            "source_sha256": digest(source.read_bytes()),
            "source_line": line_number,
            "arm_a_reconstructed_sha256": digest(reconstructed),
            "reader_context": context_path.name,
            "reader_context_sha256": digest(context_path.read_bytes()),
            "arms": {"a": arm_a, "b": arm_b},
        }

    write_json(
        MANIFEST,
        {
            "preregistration_sha256": digest(PREREGISTRATION.read_bytes()),
            "reader_instruction_sha256": digest(READER_INSTRUCTION.read_bytes()),
            "call_seed": SEED_CALLS,
            "reader_seed": SEED_READER,
            "cases": prepared,
        },
    )


def curl_config(api_key: str) -> str:
    if any(character in api_key for character in '\r\n"\\'):
        raise ValueError("API key contains a character unsafe for curl config stdin")
    return (
        f'header = "Authorization: Bearer {api_key}"\n'
        'header = "Content-Type: application/json"\n'
    )


def collect_one(
    label: str,
    arm: str,
    repeat: int,
    request: dict[str, Any],
    api_url: str,
    api_key: str,
    timeout: float,
    stopped: threading.Event,
) -> dict[str, Any]:
    stem = f"{label}-{arm}-{repeat}"
    request_path = RUNS / f"{stem}.request.json"
    write_json(request_path, request)
    attempts: list[dict[str, Any]] = []
    if stopped.is_set():
        metadata = {"case": label, "arm": arm, "repeat": repeat, "error": "not_dispatched"}
        write_json(RUNS / f"{stem}.http.json", metadata)
        return metadata

    for attempt in range(1, 4):
        raw_path = RUNS / f"{stem}.attempt-{attempt}.raw.json"
        command = [
            "curl",
            "-q",
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
            f"@{request_path}",
            "--output",
            str(raw_path),
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
        attempts.append(
            {
                "attempt": attempt,
                "http_status": status,
                "curl_returncode": completed.returncode,
                "stderr": completed.stderr.strip().replace(api_key, "[REDACTED]"),
                "raw_file": raw_path.name,
            }
        )
        if status in (401, 402, 403):
            stopped.set()
        retryable = completed.returncode != 0 or status == 429 or 500 <= status <= 599
        if not retryable:
            break

    metadata = {
        "case": label,
        "arm": arm,
        "repeat": repeat,
        "request_file": request_path.name,
        "request_sha256": digest(request_path.read_bytes()),
        "attempts": attempts,
        "final": attempts[-1],
    }
    write_json(RUNS / f"{stem}.http.json", metadata)
    return metadata


def collect() -> None:
    if RUNS.exists():
        raise RuntimeError("preserve the existing runs directory")
    manifest = load_json(MANIFEST)
    if digest(PREREGISTRATION.read_bytes()) != manifest["preregistration_sha256"]:
        raise RuntimeError("preregistration changed after preparation")
    if digest(READER_INSTRUCTION.read_bytes()) != manifest["reader_instruction_sha256"]:
        raise RuntimeError("reader instruction changed after preparation")
    RUNS.mkdir()
    (RUNS / "executed-script.py").write_bytes(Path(__file__).read_bytes())

    config = load_json(CONFIG)
    provider = cast(dict[str, Any], config["providers"]["deepseek"])
    api_key = provider.get("api_key")
    api_base = provider.get("api_base")
    if not isinstance(api_key, str) or not api_key:
        raise RuntimeError("DeepSeek API key is absent")
    if not isinstance(api_base, str) or not api_base:
        raise RuntimeError("DeepSeek API base is absent")
    timeout = float(provider["llm_timeout_seconds"])
    api_url = f"{api_base.rstrip('/')}/chat/completions"

    jobs = [
        (label, arm, repeat, case["arms"][arm])
        for label, case in cast(dict[str, dict[str, Any]], manifest["cases"]).items()
        for arm in ("a", "b")
        for repeat in range(1, 5)
    ]
    random.Random(SEED_CALLS).shuffle(jobs)
    stopped = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(
                collect_one,
                label,
                arm,
                repeat,
                request,
                api_url,
                api_key,
                timeout,
                stopped,
            )
            for label, arm, repeat, request in jobs
        ]
        results = [future.result() for future in futures]
    results.sort(key=lambda item: (item["case"], item["arm"], item["repeat"]))
    write_json(RUNS / "collection.json", results)


def strip_one_fence(content: str) -> str:
    stripped = content.strip()
    match = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", stripped, flags=re.DOTALL)
    return match.group(1).strip() if match else stripped


def embedded_schema(request: dict[str, Any]) -> dict[str, Any]:
    messages = cast(list[dict[str, Any]], request["messages"])
    system = next(message for message in messages if message.get("role") == "system")
    for line in cast(str, system["content"]).splitlines():
        if line.startswith('{"type":"object","properties":'):
            return cast(dict[str, Any], json.loads(line))
    raise ValueError("embedded JSON Schema not found")


def inspect_result(http_path: Path) -> dict[str, Any]:
    metadata = load_json(http_path)
    result: dict[str, Any] = {
        "case": metadata.get("case"),
        "arm": metadata.get("arm"),
        "repeat": metadata.get("repeat"),
        "valid": False,
    }
    try:
        final = cast(dict[str, Any], metadata["final"])
        if final["curl_returncode"] != 0 or final["http_status"] != 200:
            raise ValueError("curl or HTTP status was not successful")
        raw_path = RUNS / cast(str, final["raw_file"])
        envelope = load_json(raw_path)
        content = envelope["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("choices[0].message.content is not a string")
        parsed = cast(dict[str, Any], json.loads(strip_one_fence(content)))
        request = load_json(RUNS / cast(str, metadata["request_file"]))
        validate_json_schema(parsed, embedded_schema(request))
        stem = http_path.name.removesuffix(".http.json")
        parsed_path = RUNS / f"{stem}.parsed.json"
        write_json(parsed_path, parsed)
        result.update(
            valid=True,
            parsed_file=parsed_path.name,
            return_control_present="return_control" in parsed,
            return_control=bool(parsed.get("return_control", False)),
        )
    except (
        OSError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        JSONSchemaValidationError,
    ) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def direction_pass(count_true: int, expected: bool) -> bool:
    return count_true >= 3 if expected else (4 - count_true) >= 3


def evaluate() -> None:
    paths = sorted(RUNS.glob("*.http.json"))
    if len(paths) != 40:
        raise RuntimeError(f"expected 40 HTTP records, found {len(paths)}")
    observations = [inspect_result(path) for path in paths]
    observations.sort(key=lambda item: (item["case"], item["arm"], item["repeat"]))
    technical_pass = all(item["valid"] for item in observations)
    cells: dict[str, dict[str, Any]] = {}
    for label in CASES:
        for arm in ("a", "b"):
            selected = [
                item for item in observations if item["case"] == label and item["arm"] == arm
            ]
            true_count = sum(item.get("return_control") is True for item in selected)
            cells[f"{label}-{arm}"] = {
                "valid": sum(item["valid"] is True for item in selected),
                "return_control_true": true_count,
                "return_control_present": sum(
                    item.get("return_control_present") is True for item in selected
                ),
            }
    baseline_conditions = {
        label: direction_pass(cast(int, cells[f"{label}-a"]["return_control_true"]), expected)
        for label, expected in EXPECTED_A.items()
    }
    candidate_conditions = {
        label: direction_pass(cast(int, cells[f"{label}-b"]["return_control_true"]), expected)
        for label, expected in EXPECTED_B.items()
    }
    summary = {
        "technical_pass": technical_pass,
        "baseline_conditions": baseline_conditions,
        "baseline_pass": technical_pass and all(baseline_conditions.values()),
        "candidate_conditions": candidate_conditions,
        "candidate_mechanical_pass": (
            technical_pass
            and all(baseline_conditions.values())
            and all(candidate_conditions.values())
        ),
        "cells": cells,
        "observations": observations,
    }
    write_json(OUT / "mechanical-summary.json", summary)


def blind() -> None:
    summary = load_json(OUT / "mechanical-summary.json")
    observations = cast(list[dict[str, Any]], summary["observations"])
    if not summary["technical_pass"] or len(observations) != 40:
        raise RuntimeError("blind packet requires all 40 technically valid observations")
    manifest = load_json(MANIFEST)
    cases = cast(dict[str, dict[str, Any]], manifest["cases"])

    shuffled = observations[:]
    random.Random(SEED_READER).shuffle(shuffled)
    case_order = list(CASES)
    random.Random(SEED_READER + 1).shuffle(case_order)
    context_ids = {label: f"Q{index:02d}" for index, label in enumerate(case_order, 1)}
    contexts = [
        {
            "context_id": context_ids[label],
            "text": (OUT / cast(str, cases[label]["reader_context"])).read_text(encoding="utf-8"),
        }
        for label in case_order
    ]
    items: list[dict[str, Any]] = []
    key: dict[str, Any] = {}
    for index, observation in enumerate(shuffled, 1):
        item_id = f"I{index:02d}"
        parsed = load_json(RUNS / cast(str, observation["parsed_file"]))
        hidden_boolean = bool(parsed.pop("return_control", False))
        items.append(
            {
                "item_id": item_id,
                "context_id": context_ids[cast(str, observation["case"])],
                "director_output_without_return_control": parsed,
            }
        )
        key[item_id] = {
            "case": observation["case"],
            "arm": observation["arm"],
            "repeat": observation["repeat"],
            "model_return_control": hidden_boolean,
        }
    write_json(OUT / "blind-reader-key.json", key)
    write_json(OUT / "blind-reader-items.json", {"contexts": contexts, "items": items})
    prompt = (
        READER_INSTRUCTION.read_text(encoding="utf-8")
        + "\nCONTEXTS AND ITEMS:\n"
        + json.dumps({"contexts": contexts, "items": items}, ensure_ascii=False, indent=2)
        + "\n"
    )
    atomic_write(OUT / "blind-reader-prompt.txt", prompt)
    atomic_write(Path("/tmp/task64-blind-reader-prompt.txt"), prompt)


def evaluate_reader() -> None:
    verdict_path = OUT / "blind-reader-verdict.json"
    raw = json.loads(verdict_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or len(raw) != 40:
        raise RuntimeError("reader verdict must be a JSON list of exactly 40 objects")
    key = load_json(OUT / "blind-reader-key.json")
    expected_ids = set(key)
    seen: set[str] = set()
    joined: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {
            "item_id",
            "expected_return_control",
            "reason",
        }:
            raise RuntimeError("reader item has wrong fields")
        item_id = item["item_id"]
        if not isinstance(item_id, str) or item_id not in expected_ids or item_id in seen:
            raise RuntimeError(f"reader item has invalid or duplicate ID: {item_id!r}")
        if not isinstance(item["expected_return_control"], bool):
            raise RuntimeError(f"reader item {item_id} has a non-boolean verdict")
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise RuntimeError(f"reader item {item_id} has an empty reason")
        seen.add(item_id)
        joined.append({**cast(dict[str, Any], key[item_id]), **item})
    if seen != expected_ids:
        raise RuntimeError("reader verdict does not preserve the exact item IDs")

    cells: dict[str, dict[str, Any]] = {}
    for label in CASES:
        for arm in ("a", "b"):
            selected = [item for item in joined if item["case"] == label and item["arm"] == arm]
            expected_direction = EXPECTED_A[label] if arm == "a" else EXPECTED_B[label]
            reader_direction_count = sum(
                item["expected_return_control"] is expected_direction for item in selected
            )
            pairwise_count = sum(
                item["expected_return_control"] is expected_direction
                and item["model_return_control"] is expected_direction
                for item in selected
            )
            cells[f"{label}-{arm}"] = {
                "reader_expected_direction": reader_direction_count,
                "model_reader_pairwise_expected_direction": pairwise_count,
            }
    baseline_semantic_pass = all(
        cells[f"{label}-a"]["reader_expected_direction"] >= 3 for label in CASES
    )
    candidate_content_pass = all(
        cells[f"{label}-b"]["model_reader_pairwise_expected_direction"] >= 3 for label in CASES
    )
    mechanical = load_json(OUT / "mechanical-summary.json")
    write_json(
        OUT / "reader-summary.json",
        {
            "baseline_semantic_pass": baseline_semantic_pass,
            "candidate_content_pass": candidate_content_pass,
            "screen_pass": (
                mechanical["candidate_mechanical_pass"]
                and baseline_semantic_pass
                and candidate_content_pass
            ),
            "cells": cells,
            "joined": joined,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "collect", "evaluate", "blind", "reader"))
    arguments = parser.parse_args()
    commands = {
        "prepare": prepare,
        "collect": collect,
        "evaluate": evaluate,
        "blind": blind,
        "reader": evaluate_reader,
    }
    commands[arguments.command]()
