"""Local technical screen for the preregistered Director-to-prose cases."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "plans/artifacts/p1-archive/drive-P1-r1/sessions/5c994c42/debug.jsonl"
PREREG = HERE / "PROSE-FIDELITY-LOCAL-PREREGISTRATION.md"
MANIFEST = HERE / "prose-fidelity-manifest.json"
RUNS = HERE / "prose-fidelity-runs"
RUNS_PER_CASE = 4
CASE_LABELS = ("P1", "P2", "P3")
INTERNAL_ID = re.compile(r"\bC\d+\b")

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["consistent", "contradicts", "uncertain"]},
        "director_quote": {"type": "string"},
        "prose_quote": {"type": "string"},
    },
    "required": ["verdict", "director_quote", "prose_quote"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You compare an accepted Director's confirmed physical events and scene update with one "
    "reader-facing narration. Return contradicts only if the narration positively asserts a "
    "physical end state incompatible with the Director's asserted end state. Omission, "
    "figurative comparison, and uncertain viewpoint are not contradictions; return uncertain "
    "if you cannot tell. Ground your decision in a short quote from each side. Do not infer "
    "unstated facts. Return only one JSON object matching this schema: "
    + json.dumps(SCHEMA, ensure_ascii=False, separators=(",", ":"))
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_at(line_number: int) -> dict[str, Any]:
    rows = SOURCE.read_text(encoding="utf-8").splitlines()
    if len(rows) < line_number:
        raise RuntimeError(f"Source has no line {line_number}")
    row = cast(dict[str, Any], json.loads(rows[line_number - 1]))
    if row.get("session_id") != "5c994c42" or row.get("error") is not None:
        raise RuntimeError(f"Source line {line_number} is not an accepted record")
    if row.get("model") != "deepseek-v4-flash":
        raise RuntimeError(f"Source line {line_number} has an unexpected model")
    if not isinstance(row.get("response"), str):
        raise RuntimeError(f"Source line {line_number} has no response")
    request = row.get("request")
    if not isinstance(request, dict) or not isinstance(request.get("messages"), list):
        raise RuntimeError(f"Source line {line_number} has no request messages")
    return row


def accepted_sources() -> dict[str, tuple[int, dict[str, Any]]]:
    selected = {
        "P1_director": (80, row_at(80)),
        "P1_prose": (84, row_at(84)),
        "P2_director": (375, row_at(375)),
        "P2_prose": (377, row_at(377)),
        "P3_director": (375, row_at(375)),
        "P3_prose": (379, row_at(379)),
    }
    checks = {
        "P1_director": ("director", 8),
        "P1_prose": ("prose", 8),
        "P2_director": ("director", 32),
        "P2_prose": ("prose", 32),
        "P3_director": ("director", 32),
        "P3_prose": ("prose", 32),
    }
    for label, (agent, turn) in checks.items():
        row = selected[label][1]
        if row.get("agent") != agent or row.get("turn_number") != turn:
            raise RuntimeError(f"Source identity mismatch for {label}")
    p2_messages = selected["P2_prose"][1]["request"]["messages"]
    p3_messages = selected["P3_prose"][1]["request"]["messages"]
    if len(p2_messages) != 2 or len(p3_messages) != 3 or p3_messages[:2] != p2_messages:
        raise RuntimeError("P2/P3 renderer messages do not preserve the first two messages")
    correction = p3_messages[2]
    if correction.get("role") != "user" or not str(correction.get("content", "")).startswith(
        "CORRECTION:"
    ):
        raise RuntimeError("P3 does not contain the expected appended correction")
    return selected


def projection(director: dict[str, Any], prose: dict[str, Any]) -> dict[str, Any]:
    response = cast(dict[str, Any], json.loads(cast(str, director["response"])))
    prose_response = cast(dict[str, Any], json.loads(cast(str, prose["response"])))
    events = response.get("perception_events")
    scene_update = response.get("scene_update")
    narration = prose_response.get("narration")
    if not isinstance(events, list) or not isinstance(scene_update, dict):
        raise RuntimeError("Director response lacks perception_events or scene_update")
    if not isinstance(narration, str):
        raise RuntimeError("Prose response lacks narration")
    projected_events: list[dict[str, str]] = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("content"), str):
            raise RuntimeError("Director event lacks content")
        projected_events.append({"content": event["content"]})
    projected = {
        "perception_events": projected_events,
        "scene_update": scene_update,
        "prose": narration,
    }
    serialized = json.dumps(projected, ensure_ascii=False)
    if INTERNAL_ID.search(serialized) or re.search(r"\bPlayer\b", serialized, re.IGNORECASE):
        raise AssertionError("Projected case contains an internal ID or Player marker")
    return projected


def expected_cases(provider: dict[str, Any]) -> list[dict[str, Any]]:
    source = accepted_sources()
    pairs = {
        "P1": (source["P1_director"], source["P1_prose"]),
        "P2": (source["P2_director"], source["P2_prose"]),
        "P3": (source["P3_director"], source["P3_prose"]),
    }
    cases: list[dict[str, Any]] = []
    for label in CASE_LABELS:
        (director_line, director), (prose_line, prose) = pairs[label]
        user = projection(director, prose)
        cases.append(
            {
                "case": label,
                "director_source_line": director_line,
                "prose_source_line": prose_line,
                "request": {
                    "model": provider["model"],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(user, ensure_ascii=False, indent=2)},
                    ],
                    "max_tokens": int(provider["max_tokens_narrator"]),
                    "response_format": {"type": "json_object"},
                    "thinking": {"type": "disabled"},
                },
            }
        )
    return cases


def config() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
            "deepseek"
        ],
    )


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing manifest or run directory")
    provider = config()
    if provider.get("model") != "deepseek-v4-flash":
        raise RuntimeError("Configured provider is not DeepSeek V4 Flash")
    cases = expected_cases(provider)
    write_json(
        MANIFEST,
        {
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(SOURCE),
            "script": str(Path(__file__).relative_to(ROOT)),
            "script_sha256": sha256(Path(__file__)),
            "preregistration": str(PREREG.relative_to(ROOT)),
            "preregistration_sha256": sha256(PREREG),
            "session_id": "5c994c42",
            "cases": cases,
            "runs_per_case": RUNS_PER_CASE,
            "schema": SCHEMA,
            "system_prompt": SYSTEM_PROMPT,
        },
    )
    print("Prepared exactly three frozen Director-to-prose cases")


def curl_config(api_key: str) -> bytes:
    if any(char in api_key for char in '\r\n\\"'):
        raise ValueError("API key contains a character unsafe for curl config stdin")
    return f'header = "Authorization: Bearer {api_key}"\n'.encode()


async def call_one(case: dict[str, Any], repeat: int, provider: dict[str, Any]) -> None:
    label = f"{case['case']}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    envelope_path = RUNS / f"{label}.envelope.json"
    result_path = RUNS / f"{label}.result.json"
    write_json(request_path, case["request"])
    result: dict[str, Any] = {
        "case": case["case"],
        "repeat": repeat,
        "request_file": request_path.name,
        "request_sha256": sha256(request_path),
        "valid": False,
    }
    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-q",
        "--silent",
        "--show-error",
        "--max-time",
        str(provider["llm_timeout_seconds"]),
        "--config",
        "-",
        "--request",
        "POST",
        "--header",
        "Content-Type: application/json",
        "--data-binary",
        f"@{request_path}",
        "--output",
        str(raw_path),
        "--write-out",
        "%{http_code}",
        f"{str(provider['api_base']).rstrip('/')}/chat/completions",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    started = time.monotonic()
    stdout, stderr = await proc.communicate(curl_config(cast(str, provider["api_key"])))
    result.update(
        http_status=stdout.decode().strip(),
        curl_returncode=proc.returncode,
        duration_ms=round((time.monotonic() - started) * 1000),
        stderr=stderr.decode().replace(cast(str, provider["api_key"]), "[REDACTED]").strip(),
        raw_file=raw_path.name,
    )
    try:
        envelope = cast(dict[str, Any], json.loads(raw_path.read_text(encoding="utf-8")))
        write_json(envelope_path, envelope)
        result.update(envelope_file=envelope_path.name, response_id=envelope.get("id"))
        if result["http_status"] != "200" or proc.returncode != 0:
            raise ValueError("provider or transport error")
        content = envelope["choices"][0]["message"]["content"]
        parsed = cast(dict[str, Any], json.loads(cast(str, content)))
        sys.path.insert(0, str(ROOT))
        from src.llm.schema import validate_json_schema

        validate_json_schema(parsed, SCHEMA)
        result.update(parsed=parsed, valid=True)
    except Exception as exc:  # Invalid calls are retained and never replaced.
        result["error"] = f"{type(exc).__name__}: {exc}"
    write_json(result_path, result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Run prepare first and preserve any existing run directory")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    provider = config()
    for key, path in (
        ("source_sha256", SOURCE),
        ("script_sha256", Path(__file__)),
        ("preregistration_sha256", PREREG),
    ):
        if manifest[key] != sha256(path):
            raise RuntimeError(f"Frozen {key} changed after prepare")
    if manifest["cases"] != expected_cases(provider) or manifest["schema"] != SCHEMA:
        raise RuntimeError("Frozen request or schema changed after prepare")
    if manifest["runs_per_case"] != RUNS_PER_CASE:
        raise RuntimeError("Frozen run count changed after prepare")
    RUNS.mkdir()
    write_json(
        RUNS / "run.json",
        {
            "script_sha256": sha256(Path(__file__)),
            "manifest_sha256": sha256(MANIFEST),
            "preregistration_sha256": sha256(PREREG),
            "started_unix": time.time(),
            "model": provider["model"],
            "api_base": provider["api_base"],
            "calls": 12,
        },
    )
    if not provider.get("api_key") or not provider.get("api_base"):
        raise RuntimeError("DeepSeek configuration is incomplete")
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await call_one(case, repeat, provider)

    await asyncio.gather(
        *[limited(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    )
    print("Completed exactly twelve fresh calls")


def technical_grade() -> None:
    if not RUNS.exists():
        raise RuntimeError("Run the screen first")
    results = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(RUNS.glob("P[123]-*.result.json"))
    ]
    valid = [row for row in results if row.get("valid") is True and row.get("response_id")]
    outcome = {
        "total_results": len(results),
        "schema_valid_with_response_id": len(valid),
        "expected_count": len(CASE_LABELS) * RUNS_PER_CASE,
        "technical_complete": len(results) == 12 and len(valid) == 12,
        "cases": {
            label: sum(1 for row in valid if row.get("case") == label) for label in CASE_LABELS
        },
        "semantic_grading": "deferred",
    }
    write_json(RUNS / "technical-grade.json", outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "technical_grade"))
    args = parser.parse_args()
    if args.command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[args.command])()
