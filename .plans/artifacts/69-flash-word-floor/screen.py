"""Flash-only no-reasoning replay of all nine retained English prose inputs."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "69-local-english"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA.is_relative_to(Path("/tmp")), "Isolated /tmp data only"

from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.llm.client import call_agent  # noqa: E402

FLASH = "deepseek-v4-flash"
CONFIG = {
    "provider": "deepseek",
    "api_base": "https://api.deepseek.com",
    "model": FLASH,
    "thinking_enabled": False,
    "language": "en-US",
    "llm_timeout_seconds": 240,
}


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        PRIOR / "manifest.json",
        PRIOR / "RESULT.md",
        *sorted((ROOT / "src/llm").rglob("*.py")),
    ]
    paths.extend(sorted((PRIOR / "runs").glob("chain*/*.request.json")))
    paths.extend(sorted((PRIOR / "runs").glob("chain*/*.raw.json")))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def assert_flash(body: dict) -> None:
    assert body["model"] == FLASH, "Only explicitly authorized Flash is permitted"
    assert body["thinking"] == {"type": "disabled"}, "Reasoning must be disabled"
    assert "reasoning_effort" not in body, "No high-effort default may leak into this test"
    assert body["max_tokens"] == 4096


async def call(client: httpx.AsyncClient, case: dict, config: dict, sid: str) -> dict:
    return await call_agent(
        client,
        config,
        case["source_request"]["messages"],
        agent="prose",
        json_schema=case["source_request"]["response_format"]["json_schema"],
        max_tokens=case["source_request"]["max_tokens"],
        session_id=sid,
        turn_number=case["turn"],
        retries=2,
    )


async def prepare() -> None:
    assert not (HERE / "manifest.json").exists(), "Preserve frozen manifest"
    cases = []
    for directory in sorted((PRIOR / "runs").glob("chain*")):
        for path in sorted(directory.glob("*.raw.json")):
            raw = read(path)
            output = json.loads(raw["choices"][0]["message"]["content"])
            if "narration" not in output:
                continue
            request_path = path.with_name(path.name.replace(".raw.json", ".request.json"))
            scope_path = path.with_name(path.name.replace(".raw.json", ".scope.json"))
            source_request = read(request_path)
            case = {
                "id": directory.name + "-" + path.name.removesuffix(".raw.json"),
                "turn": int(path.name.split("-")[0][1:]),
                "source_path": str(request_path.relative_to(ROOT)),
                "scope": read(scope_path),
                "source_request": source_request,
                "local_prose": output["narration"],
                "local_words": len(output["narration"].split()),
            }
            captured = []

            def capture(request: httpx.Request, captured: list = captured) -> httpx.Response:
                body = json.loads(request.content)
                assert_flash(body)
                captured.append(body)
                return httpx.Response(
                    200,
                    json={
                        "choices": [
                            {"message": {"content": '{"narration":"Fixture capture only."}'}}
                        ]
                    },
                )

            async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
                await call(client, case, CONFIG, str(uuid4()))
            assert len(captured) == 1
            case["request"] = captured[0]
            assert "Narrate at least 600 words" in json.dumps(captured[0]["messages"])
            cases.append(case)
    assert len(cases) == 9
    write(
        HERE / "manifest.json",
        {
            "hashes": hashes(),
            "config": CONFIG,
            "cases": cases,
            "repeats": 3,
            "logical_calls": 27,
            "local_compliant": 0,
        },
    )
    print("Frozen nine actual prose inputs × three Flash draws; reasoning disabled; no paid calls")


async def run() -> None:
    manifest = read(HERE / "manifest.json")
    assert manifest["hashes"] == hashes(), "Frozen dependency drift"
    stored = read(ROOT / ".data/config.json")["providers"]["deepseek"]
    config = {**CONFIG, "api_base": stored["api_base"], "api_key": stored["api_key"]}
    DeepSeekAdapter().validate_api_base(config["api_base"])
    assert config["api_key"], "DeepSeek credential unavailable; never substitute another provider"
    runs = HERE / "runs"
    runs.mkdir()
    semaphore = asyncio.Semaphore(3)
    blocked = asyncio.Event()

    async def logical(case: dict, repeat: int) -> None:
        async with semaphore:
            stem = f"{case['id']}-r{repeat}"
            sid = str(uuid4())
            result: dict[str, Any] = {
                "case": case["id"],
                "repeat": repeat,
                "valid": False,
                "floor_pass": False,
                "session_id": sid,
                "attempts": 0,
            }
            if blocked.is_set():
                result["skipped"] = (
                    "Remaining unsent draw stopped after credential/balance rejection"
                )
                write(runs / f"{stem}.result.json", result)
                return

            async def network(request: httpx.Request) -> httpx.Response:
                result["attempts"] += 1
                name = f"{stem}-attempt{result['attempts']}"
                body = json.loads(request.content)
                assert_flash(body)
                assert body == case["request"], "Prepared production request drift"
                path = runs / f"{name}.request.json"
                write(path, body)
                curl_config = (
                    "\n".join(
                        [
                            "silent",
                            "show-error",
                            "request = POST",
                            "max-time = 240",
                            "url = " + json.dumps(str(request.url)),
                            "header = " + json.dumps("Content-Type: application/json"),
                            "header = "
                            + json.dumps("Authorization: " + request.headers["Authorization"]),
                            "data-binary = " + json.dumps("@" + str(path)),
                            'write-out = "\\n%{http_code}"',
                        ]
                    )
                    + "\n"
                )
                process = await asyncio.create_subprocess_exec(
                    "curl",
                    "--config",
                    "-",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate(curl_config.encode())
                raw, _, status = stdout.rpartition(b"\n")
                (runs / f"{name}.raw.json").write_bytes(raw)
                write(
                    runs / f"{name}.transport.json",
                    {
                        "exit_code": process.returncode,
                        "http_status": status.decode(),
                        "stderr": stderr.decode(),
                    },
                )
                if status in (b"401", b"402"):
                    blocked.set()
                if process.returncode or not status.isdigit() or int(status) == 0:
                    raise httpx.RequestError("curl failed; see retained transport", request=request)
                return httpx.Response(int(status), content=raw, request=request)

            start = time.monotonic()
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                try:
                    output = await call(client, case, config, sid)
                    result.update(valid=True, output=output, words=len(output["narration"].split()))
                    result["floor_pass"] = result["words"] >= 600
                except Exception as error:
                    result["error"] = f"{type(error).__name__}: {error}"
            result["wall_seconds"] = round(time.monotonic() - start, 3)
            write(runs / f"{stem}.result.json", result)
            log = DATA / "sessions" / sid / "debug.jsonl"
            if log.exists():
                (runs / f"{stem}.debug.jsonl").write_bytes(log.read_bytes())
            print(
                stem,
                "valid",
                result["valid"],
                "words",
                result.get("words"),
                "floor",
                result["floor_pass"],
                "error",
                result.get("error"),
                flush=True,
            )

    await asyncio.gather(
        *(logical(case, repeat) for case in manifest["cases"] for repeat in range(1, 4))
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
