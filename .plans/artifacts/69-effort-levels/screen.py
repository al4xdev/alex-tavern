"""Four requested effort labels on the historical act-completion inputs."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import random
import time
from pathlib import Path
from uuid import uuid4

from src.llm.adapters.deepseek import DeepSeekAdapter
from src.llm.schema import validate_json_schema

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / ".plans/artifacts/69-english-off/manifest.json"
EFFORTS = ("minimal", "low", "medium", "high")


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def hashes():
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        PRIOR,
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/llm/schema.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def guard(body):
    assert body["model"] == "deepseek-v4-flash", "Pro and model substitution forbidden"
    assert body["thinking"] == {"type": "enabled"}
    assert body["reasoning_effort"] in EFFORTS
    assert body["max_tokens"] == 8192


def prepare():
    assert not (HERE / "manifest.json").exists(), "Preserve frozen requests"
    prior = json.loads(PRIOR.read_text())
    cases = []
    for old in prior["cases"]:
        if old["language"] != "pt":
            continue
        source = copy.deepcopy(old["request"])
        for effort in EFFORTS:
            request = copy.deepcopy(source)
            request.update(thinking={"type": "enabled"}, reasoning_effort=effort)
            guard(request)
            cases.append(
                {
                    "case": old["case"],
                    "effort": effort,
                    "effective_effort": "low" if effort in ("minimal", "low") else "high",
                    "request": request,
                    "schema": old["schema"],
                    "expected": old["expected"],
                }
            )
    assert len(cases) == 12
    for offset in range(0, 12, 4):
        normalized = []
        for c in cases[offset : offset + 4]:
            body = copy.deepcopy(c["request"])
            body.pop("reasoning_effort")
            normalized.append(body)
        assert all(body == normalized[0] for body in normalized)
    write(HERE / "manifest.json", {"hashes": hashes(), "cases": cases, "repeats": 4})
    print("Frozen 48 Flash-only calls: three cases × four labels × four draws")


async def run():
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert manifest["hashes"] == hashes()
    stored = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    adapter = DeepSeekAdapter()
    adapter.validate_api_base(stored["api_base"])
    assert stored["api_key"]
    endpoint = stored["api_base"].rstrip("/") + "/chat/completions"
    runs = HERE / "runs"
    runs.mkdir()
    jobs = [(c, r) for c in manifest["cases"] for r in range(1, 5)]
    random.Random(691007).shuffle(jobs)
    first = [(next(c for c in manifest["cases"] if c["effort"] == e), 1) for e in EFFORTS]
    jobs = first + [(c, r) for c, r in jobs if (c, r) not in first]
    semaphore = asyncio.Semaphore(4)
    blocked = asyncio.Event()

    async def call(case, repeat):
        async with semaphore:
            stem = f"{case['case']}-{case['effort']}-{repeat}"
            result = {
                "case": case["case"],
                "effort": case["effort"],
                "repeat": repeat,
                "valid": False,
                "correct": False,
                "session_id": str(uuid4()),
                "agent": "next_beat_effort_replay",
                "turn_number": 3,
            }
            if blocked.is_set():
                result["skipped"] = "Unsent after credential/balance rejection"
                write(runs / f"{stem}.result.json", result)
                return
            body = case["request"]
            guard(body)
            path = runs / f"{stem}.request.json"
            write(path, body)
            config = (
                "\n".join(
                    [
                        "silent",
                        "show-error",
                        "request = POST",
                        "max-time = 180",
                        "url = " + json.dumps(endpoint),
                        "header = " + json.dumps("Content-Type: application/json"),
                        "header = " + json.dumps("Authorization: Bearer " + stored["api_key"]),
                        "data-binary = " + json.dumps("@" + str(path)),
                        'write-out = "\\n%{http_code}"',
                    ]
                )
                + "\n"
            )
            start = time.monotonic()
            process = await asyncio.create_subprocess_exec(
                "curl",
                "--config",
                "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate(config.encode())
            raw, _, status = stdout.rpartition(b"\n")
            (runs / f"{stem}.raw.json").write_bytes(raw)
            write(
                runs / f"{stem}.transport.json",
                {
                    "exit_code": process.returncode,
                    "http_status": status.decode(),
                    "stderr": stderr.decode(),
                },
            )
            if status in (b"401", b"402"):
                blocked.set()
            try:
                assert process.returncode == 0 and status == b"200", "HTTP/transport failure"
                envelope = json.loads(raw)
                message = envelope["choices"][0]["message"]
                output = json.loads(message["content"])
                validate_json_schema(output, case["schema"])
                result.update(
                    valid=True,
                    output=output,
                    correct=output["act_completed"] is case["expected"],
                    response_id=envelope.get("id"),
                    usage=envelope.get("usage"),
                    finish_reason=envelope["choices"][0].get("finish_reason"),
                    reasoning_chars=len(message.get("reasoning_content") or ""),
                )
            except Exception as error:
                result["error"] = f"{type(error).__name__}: {error}"
            result["wall_seconds"] = round(time.monotonic() - start, 3)
            write(runs / f"{stem}.result.json", result)
            (runs / f"{stem}.debug.jsonl").write_text(
                json.dumps({**result, "request": body}, ensure_ascii=False) + "\n"
            )
            print(
                stem,
                "valid",
                result["valid"],
                "correct",
                result["correct"],
                "flag",
                result.get("output", {}).get("act_completed"),
                flush=True,
            )

    await asyncio.gather(*(call(c, r) for c, r in jobs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    if parser.parse_args().command == "prepare":
        prepare()
    else:
        asyncio.run(run())
