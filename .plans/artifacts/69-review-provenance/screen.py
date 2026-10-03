"""Repeat-draw contrast of explicit current-turn provenance in reviewer source."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "69-admission-screen"
MANIFEST = HERE / "manifest.json"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA != ROOT / ".data" and ROOT / ".data" not in DATA.parents
spec = importlib.util.spec_from_file_location("admission_baseline", BASE / "screen.py")
assert spec is not None and spec.loader is not None
base: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE / "manifest.json",
        BASE / "screen.py",
    ]
    result = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result.update(base.hashes())
    return result


def revised(source: dict) -> dict:
    result = copy.deepcopy(source)
    records = result.pop("public_history")
    prior_records = [record for record in records if record["turn"] < 2]
    inputs = [record for record in records if record["turn"] == 2]
    assert prior_records + inputs == records and inputs
    attempts = result["committed_before_beat"].pop("declared_attempts")
    if "accepted_after_beat" in result:
        assert result["accepted_after_beat"].pop("declared_attempts") == attempts
    result["resolved_history"] = {
        "description": "Records before 'current_beat.turn_number'; "
        "their outcomes are already resolved.",
        "value": prior_records,
    }
    result["current_beat"] = {
        "turn_number": 2,
        "inputs": {
            "description": "Inputs submitted in 'turn_number'; actions await an outcome "
            "or supported obstruction in 'candidate'.",
            "value": inputs,
        },
        "attempts": {
            "description": "Crossing attempts for 'turn_number'; resolve them in 'candidate' "
            "subject to the committed world and supported causes.",
            "value": attempts,
        },
    }
    return result


async def prepare() -> None:
    assert not MANIFEST.exists(), "Preserve executed manifest"
    parent = read(BASE / "manifest.json")
    assert parent["hashes"] == base.hashes(), "Prior screen source drift"
    cases = []
    for original in parent["cases"][:4]:
        for variant in ("original", "explicit"):
            case = {
                "id": f"q{len(cases) + 1}",
                "stage": original["stage"],
                "source": copy.deepcopy(original["source"])
                if variant == "original"
                else revised(original["source"]),
                "candidate": copy.deepcopy(original["candidate"]),
                "expected": original["expected"],
                "label": original["label"],
                "source_case": original["id"],
                "variant": variant,
            }
            prompt = json.dumps(
                {"source": case["source"], "candidate": case["candidate"]}, ensure_ascii=False
            )
            assert not base.operator_ontology_hits(prompt)
            assert "private-blue" not in prompt and "private-green" not in prompt
            captured = []

            def capture(request: httpx.Request, captured: list = captured) -> httpx.Response:
                captured.append(json.loads(request.content))
                return httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": '{"issues":[],"reject":false}'}}]},
                )

            async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
                await base.review(client, base.CONFIG, case, str(uuid4()))
            assert len(captured) == 1
            case["request"] = captured[0]
            if variant == "original":
                assert case["request"] == original["request"], "Baseline request changed"
            else:
                assert case["request"]["messages"][0] == original["request"]["messages"][0]
                assert {k: v for k, v in case["request"].items() if k != "messages"} == {
                    k: v for k, v in original["request"].items() if k != "messages"
                }
            cases.append(case)
    jobs = []
    rng = random.Random(72)
    for repeat in range(1, 5):
        block = [(case["id"], repeat) for case in cases]
        rng.shuffle(block)
        jobs.extend(block)
    base.prior.write(MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print("Frozen eight conditions and32 jobs; original requests exactly match prior screen")


async def run() -> None:
    manifest = read(MANIFEST)
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    runs = HERE / "runs"
    runs.mkdir()
    provider = read(ROOT / ".data/config.json")["providers"]["deepseek"]
    base.prior.DeepSeekAdapter().validate_api_base(provider["api_base"])
    cfg = {**base.CONFIG, "api_base": provider["api_base"], "api_key": provider["api_key"]}
    semaphore = asyncio.Semaphore(4)
    cases = {case["id"]: case for case in manifest["cases"]}

    async def logical(case: dict, repeat: int) -> None:
        async with semaphore:
            stem = f"{case['id']}-{repeat}"
            attempts = 0
            sid = str(uuid4())

            async def network(request: httpx.Request) -> httpx.Response:
                nonlocal attempts
                attempts += 1
                body = json.loads(request.content)
                assert body == case["request"], "Frozen request drift"
                name = f"{stem}-attempt{attempts}"
                path = runs / f"{name}.request.json"
                base.prior.write(path, body)
                lines = [
                    "silent",
                    "show-error",
                    "request = POST",
                    "max-time = 180",
                    "url = " + json.dumps(str(request.url)),
                    "header = " + json.dumps("Content-Type: application/json"),
                    "header = " + json.dumps("Authorization: " + request.headers["Authorization"]),
                    "data-binary = " + json.dumps("@" + str(path)),
                    'write-out = "\\n%{http_code}"',
                ]
                process = await asyncio.create_subprocess_exec(
                    "curl",
                    "--config",
                    "-",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate(("\n".join(lines) + "\n").encode())
                raw, _, status = stdout.rpartition(b"\n")
                (runs / f"{name}.raw.json").write_bytes(raw)
                base.prior.write(
                    runs / f"{name}.transport.json",
                    {
                        "exit_code": process.returncode,
                        "http_status": status.decode(),
                        "stderr": stderr.decode(),
                    },
                )
                if process.returncode or not status.isdigit() or int(status) == 0:
                    raise httpx.RequestError("curl failed; evidence retained", request=request)
                return httpx.Response(int(status), content=raw, request=request)

            result = {
                "case": case["id"],
                "repeat": repeat,
                "session_id": sid,
                "terminal_success": False,
            }
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                try:
                    value = await base.review(client, cfg, case, sid)
                    result.update(
                        terminal_success=True,
                        output=value,
                        consistent=value["reject"] == bool(value["issues"]),
                    )
                except Exception as exc:
                    result["error"] = repr(exc)
            result["attempts"] = attempts
            base.prior.write(runs / f"{stem}.result.json", result)
            print(f"{stem}: success={result['terminal_success']} attempts={attempts}", flush=True)

    await asyncio.gather(*(logical(cases[cid], repeat) for cid, repeat in manifest["jobs"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else run())
