"""Frozen real-payload A/B for one stale T38 scene fact."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base

HERE = Path(__file__).resolve().parent
PREREG = HERE / "T38-STALE-FACT-AB-PREREGISTRATION.md"
MANIFEST = HERE / "t38-stale-fact-ab-manifest.json"
RUNS = HERE / "t38-stale-fact-ab-runs"
SOURCE = base.ROOT / "plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl"
ORIGINAL = '"dungeon_gates": "todos os quatro portões abertos, revelando túneis escuros"'
REPLACEMENT = '"dungeon_gates": "todos os quatro portões selados"'


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "source_debug": base.digest(SOURCE),
        "base_script": base.digest(Path(base.__file__)),
    }


def requests(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    row = json.loads(SOURCE.read_text(encoding="utf-8").splitlines()[349])
    if row["agent"] != "director" or row["turn_number"] != 38:
        raise RuntimeError("Archived T38 Director row changed")
    original = cast(list[dict[str, str]], row["request"]["messages"])
    if len(original) != 2 or original[1]["content"].count(ORIGINAL) != 1:
        raise RuntimeError("Expected one stale fact in two-message request")
    candidate = [dict(message) for message in original]
    candidate[1]["content"] = candidate[1]["content"].replace(ORIGINAL, REPLACEMENT)
    settings = {
        "model": cfg["model"],
        "max_tokens": row["request"]["max_tokens"],
        "response_format": row["request"]["response_format"],
        "thinking": {"type": "disabled"},
    }
    a = {**settings, "messages": original}
    b = {**settings, "messages": candidate}
    if original[1]["content"].replace(ORIGINAL, REPLACEMENT) != candidate[1]["content"]:
        raise RuntimeError("A/B requests differ beyond the single fact value")
    return {"A": a, "B": b}


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    base.write_json(
        MANIFEST,
        {"hashes": hashes(), "runs_per_arm": 4, "requests": requests(base.config())},
    )
    print("Frozen one-variable T38 A/B requests")


async def call_one(arm: str, repeat: int, request: dict[str, Any], cfg: dict[str, Any]) -> None:
    label = f"{arm}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    base.write_json(request_path, request)
    result: dict[str, Any] = {
        "arm": arm,
        "repeat": repeat,
        "valid": False,
        "request_sha256": base.digest(request_path),
        "raw_file": raw_path.name,
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
        if not isinstance(parsed, dict) or not isinstance(parsed.get("perception_events"), list):
            raise ValueError("No parseable perception_events list")
        result.update(
            valid=True,
            output={
                key: parsed.get(key)
                for key in ("scene_blocking", "perception_events", "zone_moves", "scene_update")
            },
        )
    except Exception as exc:  # Preserve every failed call without replacement.
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    if manifest != {"hashes": hashes(), "runs_per_arm": 4, "requests": requests(cfg)}:
        raise RuntimeError("Frozen source, script, protocol or request changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(arm: str, repeat: int, request: dict[str, Any]) -> None:
        async with semaphore:
            await call_one(arm, repeat, request, cfg)

    await asyncio.gather(
        *(
            limited(arm, repeat, request)
            for arm, request in manifest["requests"].items()
            for repeat in range(1, 5)
        )
    )
    print("Completed exactly eight frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
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
            {"arm": row["arm"], "repeat": row["repeat"], "error": row.get("error")}
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
