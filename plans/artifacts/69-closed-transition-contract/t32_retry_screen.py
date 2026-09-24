from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "plans/artifacts/p1-archive/drive-P1-r1/sessions/5c994c42/debug.jsonl"
PREREG = HERE / "T32-RETRY-V2-PREREGISTRATION.md"
MANIFEST = HERE / "t32-retry-manifest.json"
RUNS = HERE / "t32-retry-runs"
FIRST_SOURCE_LINE = 377
SECOND_SOURCE_LINE = 379
RUNS_PER_ARM = 4
ARM_LABELS = ("A", "B")
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"narration": {"type": "string"}},
    "required": ["narration"],
    "additionalProperties": False,
}
CORRECTION_SUFFIX = (
    " Keep the confirmed events and current PHYSICAL FACTS authoritative; "
    "change wording without changing their physical outcomes."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_row(line_number: int) -> dict[str, Any]:
    rows = SOURCE.read_text(encoding="utf-8").splitlines()
    if len(rows) < line_number:
        raise RuntimeError(f"Source has no line {line_number}")
    row = cast(dict[str, Any], json.loads(rows[line_number - 1]))
    if (
        row.get("session_id") != "5c994c42"
        or row.get("turn_number") != 32
        or row.get("agent") != "prose"
        or row.get("model") != "deepseek-v4-flash"
        or row.get("error") is not None
    ):
        raise RuntimeError(f"Source line {line_number} is not the accepted T32 prose row")
    request = row.get("request")
    if not isinstance(request, dict) or not isinstance(request.get("messages"), list):
        raise RuntimeError(f"Source line {line_number} has no request messages")
    return row


def accepted_rows() -> tuple[dict[str, Any], dict[str, Any]]:
    first = source_row(FIRST_SOURCE_LINE)
    second = source_row(SECOND_SOURCE_LINE)
    first_messages = first["request"]["messages"]
    second_messages = second["request"]["messages"]
    if len(first_messages) != 2 or len(second_messages) != 3:
        raise RuntimeError("T32 source message structure changed")
    if second_messages[:2] != first_messages:
        raise RuntimeError("T32 retry does not preserve the first call's base messages")
    if second_messages[-1].get("role") != "user" or not str(
        second_messages[-1].get("content", "")
    ).startswith("CORRECTION:"):
        raise RuntimeError("T32 retry correction is not the expected final user message")
    return first, second


def arm_messages() -> dict[str, list[dict[str, str]]]:
    _, second = accepted_rows()
    base = cast(list[dict[str, str]], copy.deepcopy(second["request"]["messages"]))
    variant = copy.deepcopy(base)
    variant[-1]["content"] += CORRECTION_SUFFIX
    return {"A": base, "B": variant}


def expected_cases(provider: dict[str, Any]) -> list[dict[str, Any]]:
    model = cast(str, provider["model"])
    max_tokens = int(provider["max_tokens_narrator"])
    cases: list[dict[str, Any]] = []
    for arm, messages in arm_messages().items():
        cases.append(
            {
                "arm": arm,
                "repeat": list(range(1, RUNS_PER_ARM + 1)),
                "request": {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                    "thinking": {"type": "disabled"},
                },
            }
        )
    return cases


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve the existing T32 manifest or run directory")
    config = cast(dict[str, Any], json.loads((ROOT / ".data/config.json").read_text()))
    provider = cast(dict[str, Any], config["providers"]["deepseek"])
    first, second = accepted_rows()
    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "source_session_id": "5c994c42",
        "source_turn": 32,
        "first_prose_source_line": FIRST_SOURCE_LINE,
        "first_prose_response_sha256": sha256_text(cast(str, first["response"])),
        "retry_source_line": SECOND_SOURCE_LINE,
        "retry_response_sha256": sha256_text(cast(str, second["response"])),
        "script": str(Path(__file__).relative_to(ROOT)),
        "script_sha256": sha256(Path(__file__)),
        "preregistration": str(PREREG.relative_to(ROOT)),
        "preregistration_sha256": sha256(PREREG),
        "runs_per_arm": RUNS_PER_ARM,
        "arms": expected_cases(provider),
        "schema": SCHEMA,
    }
    write_json(MANIFEST, manifest)
    print("Prepared exactly two frozen T32 retry arms")


def curl_config(api_key: str) -> bytes:
    if any(char in api_key for char in '\r\n\\"'):
        raise ValueError("API key contains a character unsafe for curl config stdin")
    return f'header = "Authorization: Bearer {api_key}"\n'.encode()


async def call_one(arm_case: dict[str, Any], repeat: int, cfg: dict[str, Any]) -> None:
    arm = cast(str, arm_case["arm"])
    label = f"{arm}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    envelope_path = RUNS / f"{label}.envelope.json"
    result_path = RUNS / f"{label}.result.json"
    write_json(request_path, arm_case["request"])
    result: dict[str, Any] = {
        "arm": arm,
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
        str(cfg["llm_timeout_seconds"]),
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
        f"{str(cfg['api_base']).rstrip('/')}/chat/completions",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    started = time.monotonic()
    stdout, stderr = await proc.communicate(curl_config(cast(str, cfg["api_key"])))
    result.update(
        http_status=stdout.decode().strip(),
        curl_returncode=proc.returncode,
        duration_ms=round((time.monotonic() - started) * 1000),
        stderr=stderr.decode().replace(cast(str, cfg["api_key"]), "[REDACTED]").strip(),
        raw_file=raw_path.name,
    )
    try:
        envelope = cast(dict[str, Any], json.loads(raw_path.read_text(encoding="utf-8")))
        write_json(envelope_path, envelope)
        result["envelope_file"] = envelope_path.name
        result["response_id"] = envelope.get("id")
        if result["http_status"] != "200" or proc.returncode != 0:
            raise ValueError("provider or transport error")
        content = envelope["choices"][0]["message"]["content"]
        parsed = cast(dict[str, Any], json.loads(cast(str, content)))
        sys.path.insert(0, str(ROOT))
        from src.llm.schema import validate_json_schema

        validate_json_schema(parsed, SCHEMA)
        result.update(parsed=parsed, valid=True)
    except Exception as exc:  # one invalid call is recorded; never replaced
        result["error"] = f"{type(exc).__name__}: {exc}"
    write_json(result_path, result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Run prepare first and preserve any existing run directory")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    config = cast(dict[str, Any], json.loads((ROOT / ".data/config.json").read_text()))
    cfg = cast(dict[str, Any], config["providers"]["deepseek"])
    for key, path in (
        ("source_sha256", SOURCE),
        ("script_sha256", Path(__file__)),
        ("preregistration_sha256", PREREG),
    ):
        if manifest[key] != sha256(path):
            raise RuntimeError(f"Frozen {key} changed after prepare")
    first, second = accepted_rows()
    if (
        manifest["first_prose_source_line"] != FIRST_SOURCE_LINE
        or manifest["retry_source_line"] != SECOND_SOURCE_LINE
    ):
        raise RuntimeError("Frozen source rows changed")
    if manifest["first_prose_response_sha256"] != sha256_text(cast(str, first["response"])):
        raise RuntimeError("Frozen first prose evidence changed")
    if manifest["retry_response_sha256"] != sha256_text(cast(str, second["response"])):
        raise RuntimeError("Frozen retry source changed")
    if manifest["arms"] != expected_cases(cfg) or manifest["schema"] != SCHEMA:
        raise RuntimeError("Frozen request or schema changed after prepare")
    if manifest["runs_per_arm"] != RUNS_PER_ARM or [
        case["arm"] for case in manifest["arms"]
    ] != list(ARM_LABELS):
        raise RuntimeError("Frozen run scope changed")
    RUNS.mkdir()
    write_json(
        RUNS / "run.json",
        {
            "script_sha256": sha256(Path(__file__)),
            "manifest_sha256": sha256(MANIFEST),
            "preregistration_sha256": sha256(PREREG),
            "started_unix": time.time(),
            "model": cfg["model"],
            "api_base": cfg["api_base"],
            "calls": len(ARM_LABELS) * RUNS_PER_ARM,
        },
    )
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration is incomplete")
    semaphore = asyncio.Semaphore(4)

    async def limited_call(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await call_one(case, repeat, cfg)

    jobs = [
        limited_call(case, repeat)
        for case in manifest["arms"]
        for repeat in range(1, RUNS_PER_ARM + 1)
    ]
    await asyncio.gather(*jobs)
    print("Completed exactly four fresh calls for each T32 arm")


def technical_grade() -> None:
    if not RUNS.exists():
        raise RuntimeError("Run the screen first")
    results = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(RUNS.glob("[AB]-*.result.json"))
    ]
    valid = [row for row in results if row.get("valid") is True]
    outcome = {
        "total_results": len(results),
        "schema_valid_count": len(valid),
        "expected_count": len(ARM_LABELS) * RUNS_PER_ARM,
        "technical_complete": len(results) == 8 and len(valid) == 8,
        "arms": {arm: sum(1 for row in valid if row.get("arm") == arm) for arm in ARM_LABELS},
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
