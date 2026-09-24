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
SOURCE = ROOT / "plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl"
PREREG = HERE / "BLUE-GATE-EXTRACTION-PREREGISTRATION.md"
MANIFEST = HERE / "blue-gate-extraction-manifest.json"
RUNS = HERE / "blue-gate-extraction-runs"
ID_PATTERN = re.compile(r"\bC\d+\b")
TURNS = (36, 37, 38, 39)
LABELS = ("change", "no_change", "uncertain")

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "aperture": {"type": "string", "enum": list(LABELS)},
        "repeated_closure": {"type": "boolean"},
    },
    "required": ["aperture", "repeated_closure"],
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
            and row.get("turn_number") in TURNS
            and row.get("attempt_number") == 1
            and row.get("error") is None
        ):
            turn = int(row["turn_number"])
            if turn in selected:
                raise RuntimeError(f"multiple accepted first-attempt Director rows for T{turn}")
            response = json.loads(cast(str, row["response"]))
            if not isinstance(response, dict):
                raise ValueError("Director response is not an object")
            selected[turn] = (line_number, row)
    if set(selected) != set(TURNS):
        raise RuntimeError(
            "exactly one accepted first-attempt Director response per T36-T39 is required"
        )
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
        "time_skip_ticks": response["time_skip_ticks"],
        "time_skip_summary": response["time_skip_summary"],
        "scene_update": response["scene_update"],
    }
    if ID_PATTERN.search(json.dumps(projection, ensure_ascii=False)):
        raise AssertionError("projected request contains an internal character ID")
    return projection


def prompt(turn: int, projection: dict[str, Any]) -> list[dict[str, str]]:
    current = "ajar" if turn in (36, 37) else "closed"
    candidate = "closed"
    catalogue = {
        "blue_dungeon_gate": {
            "label": "blue dungeon gate",
            "property": "aperture",
            "current_state": current,
            "candidate_new_state": candidate,
        }
    }
    system = (
        "You are a fail-closed reader of an accepted Director physical proposal. "
        "Judge only the supplied proposal fields and the fixed current-state catalogue. "
        "scene_blocking is a spatial draft of the situation BEFORE the event list, "
        "not a post-event result. Read the event list in order, then the time_skip_summary "
        "as a final confirmed event when time_skip_ticks is positive, then scene_update. "
        "The aperture property is discrete: ajar includes a narrowing but still usable gap. "
        "Return change, no_change, or uncertain for aperture and a boolean repeated_closure. "
        "change is authorized only when the proposal explicitly warrants the fixed "
        "candidate new state AND it differs from the aperture property's current state. "
        "repeated_closure is true only when the proposal explicitly asserts a new "
        "closing action although the current aperture is already closed; merely "
        "observing a sealed gate is false. "
        "Judge only the named aperture property, not all physical movement around the gates. "
        "no_change means the proposal supports retaining the current state. uncertain "
        "means the transition is unresolved; it authorizes no transition. Do not infer "
        "from later narration or unstated world facts. Return only one JSON object "
        "matching this schema: " + json.dumps(SCHEMA, ensure_ascii=False, separators=(",", ":"))
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
        dict[str, Any], json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))
    )
    provider = cast(dict[str, Any], config["providers"]["deepseek"])
    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "script": str(Path(__file__).relative_to(ROOT)),
        "script_sha256": sha256(Path(__file__)),
        "preregistration": str(PREREG.relative_to(ROOT)),
        "preregistration_sha256": sha256(PREREG),
        "session_id": "7fd84e9a",
        "turns": list(TURNS),
        "runs_per_turn": 4,
        "schema": SCHEMA,
        "cases": expected_cases(provider),
    }
    write_json(MANIFEST, manifest)
    print("Prepared four prompt-safe blue-gate payloads")


def curl_config(api_key: str) -> bytes:
    if any(char in api_key for char in '\r\n\\"'):
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
        "session_id": "7fd84e9a",
        "turn": turn,
        "agent": "audit:blue_gate_extraction",
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
    if (
        manifest["turns"] != list(TURNS)
        or manifest["runs_per_turn"] != 4
        or manifest["session_id"] != "7fd84e9a"
    ):
        raise RuntimeError("Frozen run scope changed after prepare")
    if manifest["cases"] != expected_cases(cfg) or manifest["schema"] != SCHEMA:
        raise RuntimeError("Frozen request or schema changed after prepare")
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

    await asyncio.gather(
        *(limited_call(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )
    print("Completed exactly four fresh calls for each turn")


def grade() -> None:
    if not RUNS.exists():
        raise RuntimeError("Run the screen first")
    results = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(RUNS.glob("T*-*.result.json"))
    ]
    valid = [row for row in results if row.get("valid")]
    per_turn = {turn: [row["parsed"] for row in valid if row["turn"] == turn] for turn in TURNS}
    technical = len(results) == 16 and len(valid) == 16
    content = all(
        len(per_turn[turn]) == 4
        and all(
            row["aperture"] == aperture and row["repeated_closure"] == repeated
            for row in per_turn[turn]
        )
        for turn, aperture, repeated in (
            (36, "no_change", False),
            (37, "change", False),
            (38, "no_change", True),
            (39, "no_change", False),
        )
    )
    status = "incomplete" if not technical else ("pass" if content else "semantic_fail")
    outcome = {
        "technical_gate": technical,
        "content_gate": content,
        "pass": technical and content,
        "status": status,
        "semantic_fail": technical and not content,
        "valid_count": len(valid),
        "results": per_turn,
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
