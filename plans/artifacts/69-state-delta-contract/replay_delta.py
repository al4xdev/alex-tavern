from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


NEW_DELTA = (
    '- "scene_update": object with changes to the current scene (e.g.,\n'
    '  {"location": "Old Watchtower", "door": "open"}). "location" and\n'
    '  "time_of_day" are reserved Scene fields. Every other key is a physical\n'
    "  fact for the current location. Reuse the existing snake_case key for the\n"
    "  same fact; do not add a synonym alongside it. Use null if nothing changed.\n"
    "  After resolving this turn's events, update every existing fact they make\n"
    "  false. If a value combines several assertions, rewrite it to preserve the\n"
    "  still-true parts while replacing the changed part. Set a key to null only\n"
    "  when none of that fact remains current. A new key does not retire an old\n"
    "  assertion. Orders, plans and attempted actions are not completed events.\n"
)


def prepare() -> None:
    sys.path.insert(0, str(ROOT))
    from src.agents.narrator import _build_system_prompt

    path = OUT / "manifest.json"
    if path.exists():
        raise RuntimeError("Preserve existing manifest")
    source = ROOT / "plans/artifacts/77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl"
    state_path = source.with_name("state.json")
    raw = source.read_bytes()
    row = json.loads(raw.decode().splitlines()[41])
    assert row["agent"] == "director" and row["turn_number"] == 4 and not row["error"]
    state = json.loads(state_path.read_text())
    before = [r["scene_snapshot"] for r in state["history"] if r["turn_number"] == 3][-1]
    req = row["request"]
    assert req["provider_options"]["thinking_enabled"] is False
    original = {
        "model": row["model"],
        "messages": req["messages"],
        "max_tokens": req["max_tokens"],
        "response_format": req["response_format"],
        "thinking": {"type": "disabled"},
    }
    candidate = copy.deepcopy(original)
    system = candidate["messages"][0]["content"]
    start = system.index('- "scene_update":')
    end = system.index('- "mood_updates":', start)
    old = system[start:end]
    assert old in _build_system_prompt(list(state["characters"]))
    candidate["messages"][0]["content"] = system[:start] + NEW_DELTA + system[end:]
    assert (
        candidate["messages"][0]["content"].replace(NEW_DELTA, old)
        == original["messages"][0]["content"]
    )
    write(OUT / "prior-scene.json", before)
    (OUT / "candidate.txt").write_text(NEW_DELTA)
    write(
        path,
        {
            "seed": 694204,
            "state_sha256": digest(state_path.read_bytes()),
            "candidate_sha256": digest(NEW_DELTA.encode()),
            "old_clause": old,
            "cases": [
                {
                    "label": "delta",
                    "session_id": "fb62cc2f",
                    "turn_number": 4,
                    "line": 42,
                    "source": str(source.relative_to(ROOT)),
                    "source_sha256": digest(raw),
                    "arms": {"A": original, "B": candidate},
                }
            ],
        },
    )
    print("Prepared exact Director request and state-delta candidate")


async def run(run_name: str = "runs") -> None:
    sys.path.insert(0, str(ROOT))
    from src.llm.schema import validate_json_schema

    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    cfg = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    assert "\n" not in cfg["api_key"] and "\r" not in cfg["api_key"]
    if Path(run_name).name != run_name or run_name in (".", ".."):
        raise ValueError("Run name must be a single directory name")
    runs = OUT / run_name
    runs.mkdir(exist_ok=False)
    raw_script = Path(__file__).read_bytes()
    (runs / "executed-script.py").write_bytes(raw_script)
    write(
        runs / "run.json",
        {
            "script_sha256": digest(raw_script),
            "manifest_sha256": digest(manifest_path.read_bytes()),
            "preregistration_sha256": digest((OUT / "PREREGISTRATION.md").read_bytes()),
            "started_unix": time.time(),
            "api_base": cfg["api_base"],
        },
    )
    jobs = [
        (case, arm, repeat)
        for case in manifest["cases"]
        for arm in case["arms"]
        for repeat in range(4)
    ]
    random.Random(manifest["seed"]).shuffle(jobs)
    sem = asyncio.Semaphore(4)
    stopped = asyncio.Event()

    async def call(case: dict, arm: str, repeat: int) -> None:
        label = f"{case['label']}-{arm}-{repeat}"
        request = case["arms"][arm]
        reqpath = runs / f"{label}.request.json"
        responsepath = runs / f"{label}.response.json"
        write(reqpath, request)
        result = {
            "session_id": case["session_id"],
            "turn_number": case["turn_number"],
            "agent": "audit:state_delta_contract",
            "arm": arm,
            "repeat": repeat,
            "request": request,
            "request_sha256": digest(reqpath.read_bytes()),
        }
        async with sem:
            if stopped.is_set():
                result["error"] = "not_dispatched_after_account_error"
            else:
                result["attempts"] = []
                for attempt in range(2):
                    responsepath = runs / f"{label}.attempt-{attempt}.response.json"
                    start = time.monotonic()
                    proc = await asyncio.create_subprocess_exec(
                        "curl",
                        "-q",
                        "--config",
                        "-",
                        "--silent",
                        "--show-error",
                        "--connect-timeout",
                        "30",
                        "--max-time",
                        "180",
                        "--request",
                        "POST",
                        cfg["api_base"].rstrip("/") + "/chat/completions",
                        "--header",
                        "Content-Type: application/json",
                        "--data-binary",
                        "@" + str(reqpath),
                        "--output",
                        str(responsepath),
                        "--write-out",
                        "%{http_code}",
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate(
                        (
                            "header = "
                            + json.dumps("Authorization: Bearer " + cfg["api_key"])
                            + "\n"
                        ).encode()
                    )
                    status = stdout.decode().strip()
                    result.update(
                        http_status=status,
                        curl_exit=proc.returncode,
                        duration_ms=round((time.monotonic() - start) * 1000),
                        curl_error=stderr.decode().replace(cfg["api_key"], "[REDACTED]"),
                    )
                    attempt_result = {
                        key: result[key]
                        for key in ("http_status", "curl_exit", "duration_ms", "curl_error")
                    }
                    attempt_result["response_file"] = responsepath.name
                    result["attempts"].append(attempt_result)
                    write(runs / f"{label}.attempt-{attempt}.json", attempt_result)
                    connection_failure = status == "000" and any(
                        value in stderr.decode()
                        for value in (
                            "Failed to connect",
                            "Could not connect",
                            "Could not resolve host",
                            "Connection timed out",
                        )
                    )
                    no_response = not responsepath.exists() or not responsepath.stat().st_size
                    if attempt == 0 and connection_failure and no_response:
                        continue
                    break
                result["total_duration_ms"] = sum(
                    item["duration_ms"] for item in result["attempts"]
                )
                if status in ("401", "402", "403"):
                    stopped.set()
                try:
                    if not responsepath.exists():
                        result["error"] = "transport_without_response"
                        write(runs / f"{label}.result.json", result)
                        print("Finished replay: transport_without_response", flush=True)
                        return
                    response = json.loads(responsepath.read_text())
                    result["response"] = response
                    if status != "200" or proc.returncode:
                        result["error"] = "provider_or_transport_error"
                    else:
                        parsed = json.loads(response["choices"][0]["message"]["content"])
                        assert isinstance(parsed, dict)
                        result["parsed"] = parsed
                        system = request["messages"][0]["content"]
                        schema_text = system.split("JSON Schema", 1)[1]
                        schema = json.loads(schema_text[schema_text.index("{") :])
                        validate_json_schema(parsed, schema)
                        result["schema_valid"] = True
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    IndexError,
                    TypeError,
                    AssertionError,
                ) as exc:
                    result["error"] = type(exc).__name__
        write(runs / f"{label}.result.json", result)
        print("Finished replay: " + result.get("error", "ok"), flush=True)

    await asyncio.gather(*(call(*job) for job in jobs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--run-name", default="runs")
    args = parser.parse_args()
    if args.command == "run":
        asyncio.run(run(args.run_name))
    else:
        prepare()
