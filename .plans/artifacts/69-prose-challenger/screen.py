"""Replay retained prose-review pairs with only a different model identifier."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path
from uuid import uuid4

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT = HERE.parent / "69-prose-admission"
MANIFEST = HERE / "manifest.json"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA != ROOT / ".data" and ROOT / ".data" not in DATA.parents
spec = importlib.util.spec_from_file_location("confirmed_prose_probe", PARENT / "screen.py")
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
CONFIG = {**probe.CONFIG, "model": "deepseek-v4-pro"}


def read(path: Path):
    return json.loads(path.read_text())


def write(path: Path, value) -> None:
    probe.write(path, value)


def hashes() -> dict[str, str]:
    paths = [
        HERE / "screen.py",
        HERE / "PREREGISTRATION.md",
        PARENT / "screen.py",
        PARENT / "manifest.json",
    ]
    paths.extend((PARENT / "runs").glob("fresh*.result.json"))
    paths.extend((PARENT / "runs").glob("fresh*-review-frozen.json"))
    paths.extend((ROOT / "src/llm").rglob("*.py"))
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)
    }


async def capture(source: dict, prose: str) -> dict:
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"issues":[],"reject":false}'}}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        await probe.review(client, CONFIG, source, prose, "")
    assert len(requests) == 1
    return requests[0]


async def prepare() -> None:
    assert not MANIFEST.exists(), "Preserve frozen execution"
    parent = read(PARENT / "manifest.json")
    cases = []
    for original in parent["cases"]:
        request = await capture(original["source"], original["candidate"])
        assert request == {**original["request"], "model": CONFIG["model"]}
        cases.append({**original, "request": request, "repeats": 4})
    for index in range(1, 5):
        result = read(PARENT / "runs" / f"fresh{index}.result.json")
        assert result["render_success"] and result["review_success"]
        frozen = read(PARENT / "runs" / f"fresh{index}-review-frozen.json")
        payload = json.loads(frozen["messages"][1]["content"])
        assert payload["candidate"] == result["narration"]
        request = await capture(payload["source"], payload["candidate"])
        assert request == {**frozen, "model": CONFIG["model"]}
        cases.append(
            {
                "id": f"fresh{index}",
                "source": payload["source"],
                "candidate": payload["candidate"],
                "request": request,
                "repeats": 1,
            }
        )
    jobs = [[case["id"], repeat] for case in cases for repeat in range(1, case["repeats"] + 1)]
    random.Random(75).shuffle(jobs)
    write(MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print(
        "Frozen20 reviewer calls; each request differs from retained Flash request only by model",
        flush=True,
    )


async def run() -> None:
    manifest = read(MANIFEST)
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    runs = HERE / "runs"
    runs.mkdir()
    provider = read(ROOT / ".data/config.json")["providers"]["deepseek"]
    probe.base.prior.DeepSeekAdapter().validate_api_base(provider["api_base"])
    cfg = {**CONFIG, "api_base": provider["api_base"], "api_key": provider["api_key"]}
    semaphore = asyncio.Semaphore(4)
    cases = {case["id"]: case for case in manifest["cases"]}

    async def job(case_id: str, repeat: int) -> None:
        async with semaphore:
            case = cases[case_id]
            stem = f"{case_id}-{repeat}"
            network = probe.CurlTransport(runs, stem, [case["request"]])
            result = {"case": case_id, "repeat": repeat, "terminal_success": False}
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                try:
                    value = await probe.review(
                        client, cfg, case["source"], case["candidate"], str(uuid4())
                    )
                    result.update(
                        terminal_success=True,
                        output=value,
                        consistent=value["reject"] == bool(value["issues"]),
                    )
                except Exception as exc:
                    result["error"] = repr(exc)
            result["attempts"] = network.attempts
            write(runs / f"{stem}.result.json", result)
            print(
                f"{stem}: success={result['terminal_success']} attempts={network.attempts}",
                flush=True,
            )

    await asyncio.gather(*(job(case_id, repeat) for case_id, repeat in manifest["jobs"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else run())
