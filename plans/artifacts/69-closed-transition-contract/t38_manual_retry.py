"""Frozen complete T38 Director retry with generic versus grounded feedback."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base
import t38_stale_fact_ab as previous

HERE = Path(__file__).resolve().parent
PREREG = HERE / "T38-MANUAL-RETRY-PREREGISTRATION.md"
MANIFEST = HERE / "t38-manual-retry-manifest.json"
RUNS = HERE / "t38-manual-retry-runs"
SOURCE = previous.SOURCE
COMMON = (
    "The prior Director draft was rejected before any event or state effect was "
    "committed. Regenerate a complete new JSON draft from the same committed "
    "scene and the final attempted action. CONSISTENCY REPORT:\n"
)
GENERIC = (
    "The previous draft conflicts with committed scene continuity. Review the "
    "committed state and the final attempted action, then regenerate every "
    "field as a new draft."
)
GROUNDED = (
    "At T37 the blue gate completed closure; gate_blue is fechado. Mirella, Nix, "
    "Doran, Liora and Bruna are already in the blue tunnel; Téo is in the hall. "
    "Téo's final advance through the fresta is an attempt, not a completed "
    "crossing. The rejected draft says destination_reachable_this_beat=false "
    "but moves Téo and the already placed team through that fresta and closes "
    "the blue gate again. Reconcile those statements against the committed "
    "state and regenerate every field. A new causal reopening is possible if "
    "you actually establish it; do not assume this attempt succeeded."
)


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "source_debug": base.digest(SOURCE),
        "base_script": base.digest(Path(base.__file__)),
        "previous_script": base.digest(Path(previous.__file__)),
    }


def schema_and_requests(cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    row = json.loads(SOURCE.read_text(encoding="utf-8").splitlines()[349])
    if row["agent"] != "director" or row["turn_number"] != 38:
        raise RuntimeError("Archived T38 Director row changed")
    original = previous.requests(cfg)["A"]
    rejected = cast(str, row["response"])
    if "O portão azul se fecha com um baque surdo" not in rejected:
        raise RuntimeError("Rejected draft changed")
    present_ids = re.findall(r"(?m)^  ID=(C\d+) \| NAME=", original["messages"][1]["content"])
    if len(present_ids) != 21 or len(set(present_ids)) != 21:
        raise RuntimeError("Expected exactly 21 present character IDs")
    sys.path.insert(0, str(base.ROOT))
    from src.agents.narrator import build_narrator_json_schema

    schema = cast(dict[str, Any], build_narrator_json_schema(present_ids)["schema"])
    outputs: dict[str, dict[str, Any]] = {}
    for arm, report in (("A", GENERIC), ("B", GROUNDED)):
        messages = [*original["messages"], {"role": "assistant", "content": rejected}]
        messages.append({"role": "user", "content": COMMON + report})
        outputs[arm] = {**original, "messages": messages}
    if outputs["A"]["messages"][:-1] != outputs["B"]["messages"][:-1]:
        raise RuntimeError("Retry arms differ before final report")
    if outputs["A"]["messages"][-1]["content"] != COMMON + GENERIC:
        raise RuntimeError("Generic report changed")
    if outputs["B"]["messages"][-1]["content"] != COMMON + GROUNDED:
        raise RuntimeError("Grounded report changed")
    return schema, outputs


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    schema, requests = schema_and_requests(base.config())
    base.write_json(
        MANIFEST,
        {"hashes": hashes(), "runs_per_arm": 4, "schema": schema, "requests": requests},
    )
    print("Frozen T38 complete-draft retry arms")


async def call_one(
    arm: str, repeat: int, request: dict[str, Any], cfg: dict[str, Any], schema: dict[str, Any]
) -> None:
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
        sys.path.insert(0, str(base.ROOT))
        from src.llm.schema import validate_json_schema

        validate_json_schema(parsed, schema)
        result.update(valid=True, output=parsed)
    except Exception as exc:  # Preserve every failed call.
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    schema, requests = schema_and_requests(cfg)
    if manifest != {"hashes": hashes(), "runs_per_arm": 4, "schema": schema, "requests": requests}:
        raise RuntimeError("Frozen source, script, protocol or requests changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(arm: str, repeat: int, request: dict[str, Any]) -> None:
        async with semaphore:
            await call_one(arm, repeat, request, cfg, schema)

    await asyncio.gather(
        *(
            limited(arm, repeat, request)
            for arm, request in requests.items()
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
