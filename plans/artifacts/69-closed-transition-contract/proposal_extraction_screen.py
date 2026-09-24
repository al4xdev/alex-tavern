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
SOURCE = ROOT / "plans/artifacts/p1-archive/base-P1-r2/sessions/8bd4d0f1/debug.jsonl"
PREREG = HERE / "PROPOSAL-EXTRACTION-PREREGISTRATION.md"
MANIFEST = HERE / "proposal-extraction-manifest.json"
RUNS = HERE / "proposal-extraction-runs"
ID_PATTERN = re.compile(r"\bC\d+\b")
LABELS = ("change", "no_change", "uncertain")

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pillar": {"type": "string", "enum": list(LABELS)},
        "gap": {"type": "string", "enum": list(LABELS)},
    },
    "required": ["pillar", "gap"],
    "additionalProperties": False,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_rows() -> dict[int, tuple[int, dict[str, Any]]]:
    selected: dict[int, tuple[int, dict[str, Any]]] = {}
    for line_number, line in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(), 1):
        row = cast(dict[str, Any], json.loads(line))
        if (
            row.get("agent") == "director"
            and row.get("turn_number") in (28, 29)
            and row.get("error") is None
        ):
            response = json.loads(cast(str, row["response"]))
            if not isinstance(response, dict):
                raise ValueError("Director response is not an object")
            selected[int(row["turn_number"])] = (line_number, row)
    if set(selected) != {28, 29}:
        raise RuntimeError("accepted Director responses for T28 and T29 are required")
    return selected


def public_projection(response_text: str) -> dict[str, Any]:
    response = cast(dict[str, Any], json.loads(response_text))
    projection = {
        "scene_blocking": {
            "spatial_constraints": response["scene_blocking"]["spatial_constraints"]
        },
        "perception_events": [
            {"content": event["content"]} for event in response["perception_events"]
        ],
        "scene_update": response["scene_update"],
    }
    serialized = json.dumps(projection, ensure_ascii=False)
    if ID_PATTERN.search(serialized):
        raise AssertionError("projected request contains an internal character ID")
    return projection


def prompt(turn: int, projection: dict[str, Any]) -> list[dict[str, str]]:
    current = {
        "pillar": "damaged" if turn == 28 else "destroyed",
        "gap": "ajar",
    }
    catalogue = {
        "pillar": {
            "label": "cracked hall pillar",
            "property": "integrity",
            "current_state": current["pillar"],
            "candidate_new_state": "destroyed",
        },
        "gap": {
            "label": "rubble gap to inner corridor",
            "property": "aperture",
            "current_state": current["gap"],
            "candidate_new_state": "closed",
        },
    }
    system = (
        "You are a fail-closed reader of an accepted Director physical proposal. "
        "Judge only the supplied proposal fields and the fixed current-state catalogue. "
        "scene_blocking is a spatial draft of the situation BEFORE the event list, "
        "not a post-event result. Read the event list in order, then scene_update. "
        "For each property return exactly one of change, no_change, uncertain. "
        "change is authorized only when the proposal explicitly warrants the fixed "
        "candidate new state AND it differs from that property's current state. "
        "Judge only the named integrity or aperture property, not all physical "
        "movement of the object. no_change means the proposal supports retaining the "
        "current state. uncertain means the transition is unresolved; it authorizes no "
        "transition. Do not infer from later narration or unstated world facts. Return "
        "only one JSON object matching this schema: "
        + json.dumps(SCHEMA, ensure_ascii=False, separators=(",", ":"))
    )
    user = json.dumps(
        {
            "turn": f"T{turn}",
            "public_catalogue": catalogue,
            "proposal": projection,
        },
        ensure_ascii=False,
        indent=2,
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def expected_cases(provider: dict[str, Any]) -> list[dict[str, Any]]:
    model = cast(str, provider["model"])
    max_tokens = int(provider["max_tokens_narrator"])
    cases: list[dict[str, Any]] = []
    for turn, (line, row) in sorted(source_rows().items()):
        projection = public_projection(cast(str, row["response"]))
        cases.append(
            {
                "turn": turn,
                "source_line": line,
                "request": {
                    "model": model,
                    "messages": prompt(turn, projection),
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                    "thinking": {"type": "disabled"},
                },
            }
        )
    return cases


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve the existing manifest")
    config = cast(
        dict[str, Any],
        json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8")),
    )
    provider = cast(dict[str, Any], config["providers"]["deepseek"])
    cases = expected_cases(provider)
    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "script": str(Path(__file__).relative_to(ROOT)),
        "script_sha256": sha256(Path(__file__)),
        "preregistration": str(PREREG.relative_to(ROOT)),
        "preregistration_sha256": sha256(PREREG),
        "session_id": "8bd4d0f1",
        "runs_per_turn": 4,
        "schema": SCHEMA,
        "cases": cases,
    }
    write_json(MANIFEST, manifest)
    print("Prepared two prompt-safe public proposal payloads")


def curl_config(api_key: str) -> bytes:
    if any(char in api_key for char in '\r\n"\\'):
        raise ValueError("API key contains a character unsafe for curl config stdin")
    return f'header = "Authorization: Bearer {api_key}"\n'.encode()


async def call_one(case: dict[str, Any], repeat: int, cfg: dict[str, Any]) -> None:
    turn = int(case["turn"])
    label = f"T{turn}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    result_path = RUNS / f"{label}.result.json"
    write_json(request_path, case["request"])
    result: dict[str, Any] = {
        "session_id": "8bd4d0f1",
        "turn": turn,
        "agent": "audit:proposal_extraction",
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
        f"{cfg['api_base'].rstrip('/')}/chat/completions",
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
        write_json(RUNS / f"{label}.envelope.json", envelope)
        result["envelope_file"] = f"{label}.envelope.json"
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
    if not MANIFEST.exists():
        raise RuntimeError("Run prepare first")
    if RUNS.exists():
        raise RuntimeError("Preserve existing run directory")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = cast(
        dict[str, Any],
        json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
            "deepseek"
        ],
    )
    for key, path in (
        ("source_sha256", SOURCE),
        ("script_sha256", Path(__file__)),
        ("preregistration_sha256", PREREG),
    ):
        if manifest[key] != sha256(path):
            raise RuntimeError(f"Frozen {key} changed after prepare")
    if [case["turn"] for case in manifest["cases"]] != [28, 29]:
        raise RuntimeError("Expected exactly the frozen T28 and T29 cases")
    if manifest["cases"] != expected_cases(cfg) or manifest["schema"] != SCHEMA:
        raise RuntimeError("Frozen request or schema changed after prepare")
    if manifest["runs_per_turn"] != 4 or manifest["session_id"] != "8bd4d0f1":
        raise RuntimeError("Frozen run scope changed after prepare")
    for case in manifest["cases"]:
        if ID_PATTERN.search(json.dumps(case["request"], ensure_ascii=False)):
            raise RuntimeError("Frozen request contains an internal character ID")
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
        },
    )
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration is incomplete")
    semaphore = asyncio.Semaphore(4)

    async def limited_call(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await call_one(case, repeat, cfg)

    jobs = [limited_call(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    await asyncio.gather(*jobs)
    print("Completed exactly four fresh calls for each turn")


def grade() -> None:
    if not RUNS.exists():
        raise RuntimeError("Run the screen first")
    results = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(RUNS.glob("T*-*.result.json"))
    ]
    valid = [row for row in results if row.get("valid")]
    t28 = [row["parsed"] for row in valid if row["turn"] == 28]
    t29 = [row["parsed"] for row in valid if row["turn"] == 29]
    technical = len(results) == 8 and len(valid) == 8
    content = (
        len(t28) == 4
        and all(row["pillar"] == "change" and row["gap"] != "change" for row in t28)
        and len(t29) == 4
        and all(row["pillar"] != "change" for row in t29)
    )
    outcome = {
        "technical_gate": technical,
        "content_gate": content,
        "pass": technical and content,
        "valid_count": len(valid),
        "t28": t28,
        "t29": t29,
    }
    write_json(RUNS / "grade.json", outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    args = parser.parse_args()
    if args.command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[args.command])()
