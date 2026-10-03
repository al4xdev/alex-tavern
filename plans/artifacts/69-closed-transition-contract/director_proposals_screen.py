"""Frozen real-payload Director-authored gate proposal screen."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base

HERE = Path(__file__).resolve().parent
PREREG = HERE / "DIRECTOR-PROPOSALS-PREREGISTRATION.md"
MANIFEST = HERE / "director-proposals-manifest.json"
RUNS = HERE / "director-proposals-runs"
SOURCES = {
    "blue_t38": (
        base.ROOT / "plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl",
        350,
        38,
        "portão azul",
    ),
    "kennel_t34": (
        base.ROOT / "plans/artifacts/p1-archive/oldcode-P1-r2/sessions/a3e1ceda/debug.jsonl",
        398,
        34,
        "portão do canil",
    ),
}
SCHEMA_PREFIX = (
    "Return only one JSON object that conforms exactly to this JSON Schema. "
    "Do not add markdown or keys outside the schema:\n"
)
INSTRUCTION = (
    "PHYSICAL PROPOSALS: For every newly completed opening, closing, or passage "
    "through the tracked gate that you narrate in perception_events or "
    "time_skip_summary, add one ordered physical_proposals item. Quote the "
    "exact event text. Do not annotate attempts, static observations, or old "
    "events. Use the public gate name, never an internal identifier. An empty "
    "array means you narrated no such action. Keep the proposal aligned with "
    "your event, blocking, moves, and scene update.\n\n"
)


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "base_script": base.digest(Path(base.__file__)),
        **{name: base.digest(source) for name, (source, _, _, _) in SOURCES.items()},
    }


def request_and_schema(name: str, cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source, line, turn, gate = SOURCES[name]
    row = json.loads(source.read_text(encoding="utf-8").splitlines()[line - 1])
    if row["agent"] != "director" or row["turn_number"] != turn:
        raise RuntimeError(f"Archived row changed: {name}")
    original = cast(list[dict[str, str]], row["request"]["messages"])
    system = original[0]["content"]
    if system.count(SCHEMA_PREFIX) != 1:
        raise RuntimeError("Expected one embedded schema")
    before, schema_text = system.split(SCHEMA_PREFIX)
    schema = cast(dict[str, Any], json.loads(schema_text))
    if "physical_proposals" in schema["properties"]:
        raise RuntimeError("Archived schema already contains proposals")
    schema["properties"]["physical_proposals"] = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "gate_name": {"type": "string", "enum": [gate]},
                "operation": {"type": "string", "enum": ["close", "open", "cross"]},
                "actor": {"type": "string"},
                "event_quote": {"type": "string"},
            },
            "required": ["gate_name", "operation", "actor", "event_quote"],
            "additionalProperties": False,
        },
    }
    schema["required"].append("physical_proposals")
    messages = [dict(message) for message in original]
    messages[0]["content"] = (
        before
        + INSTRUCTION
        + SCHEMA_PREFIX
        + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    )
    messages.append(
        {
            "role": "user",
            "content": (
                f"Tracked public gate: {gate}. Its committed aperture is closed. "
                "Narrate naturally and complete physical_proposals for only new "
                "completed actions of this gate; a pending attempt is not a "
                "completed passage."
            ),
        }
    )
    return {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": row["request"]["max_tokens"],
        "response_format": row["request"]["response_format"],
        "thinking": {"type": "disabled"},
    }, schema


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    pairs = {name: request_and_schema(name, cfg) for name in SOURCES}
    return {
        "hashes": hashes(),
        "runs_per_case": 4,
        "requests": {name: pair[0] for name, pair in pairs.items()},
        "schemas": {name: pair[1] for name, pair in pairs.items()},
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen two archived requests and amended schemas")


async def call_one(
    name: str, repeat: int, request: dict[str, Any], schema: dict[str, Any], cfg: dict[str, Any]
) -> None:
    label = f"{name}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    base.write_json(request_path, request)
    result: dict[str, Any] = {
        "case": name,
        "repeat": repeat,
        "valid": False,
        "request_sha256": base.digest(request_path),
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
    stdout, stderr = await proc.communicate(base.curl_config(cast(str, cfg["api_key"])))
    result.update(
        http_status=stdout.decode().strip(),
        curl_returncode=proc.returncode,
        duration_ms=round((time.monotonic() - started) * 1000),
        stderr=stderr.decode().replace(cast(str, cfg["api_key"]), "[REDACTED]").strip(),
    )
    try:
        envelope = cast(dict[str, Any], json.loads(raw_path.read_text(encoding="utf-8")))
        result["response_id"] = envelope.get("id")
        if result["http_status"] != "200" or proc.returncode != 0:
            raise ValueError("HTTP or transport failure")
        parsed = cast(dict[str, Any], json.loads(envelope["choices"][0]["message"]["content"]))
        sys.path.insert(0, str(base.ROOT))
        from src.llm.schema import validate_json_schema

        validate_json_schema(parsed, schema)
        event_texts = [e["content"] for e in parsed["perception_events"]]
        event_texts.append(parsed["time_skip_summary"])
        for proposal in parsed["physical_proposals"]:
            quote = proposal["event_quote"]
            if not quote or not any(quote in event for event in event_texts):
                raise ValueError("Nonliteral or empty proposal quote")
        result.update(valid=True, output=parsed)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    cfg = base.config()
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen inputs changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    sem = asyncio.Semaphore(4)

    async def limited(name: str, repeat: int) -> None:
        async with sem:
            await call_one(name, repeat, manifest["requests"][name], manifest["schemas"][name], cfg)

    await asyncio.gather(*(limited(name, repeat) for name in SOURCES for repeat in range(1, 5)))
    print("Completed exactly eight frozen calls")


def grade() -> None:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 8
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 8
        and all(ids)
    )
    outcome = {
        "technical_gate": bool(technical),
        "valid_count": sum(bool(row.get("valid")) for row in results),
        "status": "content_read_pending" if technical else "incomplete",
        "errors": [
            {"case": row["case"], "repeat": row["repeat"], "error": row.get("error")}
            for row in results
            if not row.get("valid")
        ],
    }
    base.write_json(RUNS / "grade.json", outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
