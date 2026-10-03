"""Fresh production validation/retry boundary over frozen Runner requests."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / ".plans/artifacts/69-runner-anchor-coverage/manifest.json"
MANIFEST = HERE / "manifest.json"
task_data = os.environ.get("ROLEPLAY_DATA_DIR")
if not task_data:
    raise RuntimeError("Set isolated ROLEPLAY_DATA_DIR before importing storage")
task_root = Path(task_data).resolve()
real_root = (ROOT / ".data").resolve()
if task_root == real_root or real_root in task_root.parents:
    raise RuntimeError("Refuse real data root")

from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.llm.client import chat_completion, chat_completion_json  # noqa: E402


def write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        PRIOR,
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/roteiro.py",
        ROOT / "src/agents/narrator.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def options(case: dict[str, Any]) -> dict[str, Any]:
    body = case["request"]
    return {
        "provider": "deepseek",
        "api_base": "https://api.deepseek.com",
        "model": body["model"],
        "language": "pt-BR",
        "thinking_enabled": True,
        "max_tokens": body["max_tokens"],
        "timeout": 180,
        "json_schema": {"name": "narrator", "schema": case["schema"]},
    }


def messages(case: dict[str, Any]) -> list[dict[str, Any]]:
    result = copy.deepcopy(case["request"]["messages"])
    marker = "\n\nReturn only one JSON object that conforms exactly to this JSON Schema. "
    content, separator, _ = result[0]["content"].rpartition(marker)
    assert separator
    result[0]["content"] = content
    return result


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    prior = json.loads(PRIOR.read_text())
    cases = prior["cases"]
    for case in cases:
        captured: list[dict[str, Any]] = []

        def capture(
            request: httpx.Request, captured: list[dict[str, Any]] = captured
        ) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
            await chat_completion(client, messages(case), **options(case))
        assert captured == [case["request"]], case["fixture"]["id"]
    write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Production adapter parity verified for all four frozen requests")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes()
    runs = HERE / "runs"
    runs.mkdir()
    canonical = json.loads((ROOT / ".data/config.json").read_text())
    cfg = canonical["providers"]["deepseek"]
    DeepSeekAdapter().validate_api_base(cfg["api_base"])
    semaphore = asyncio.Semaphore(4)

    async def logical(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            stem = f"{case['fixture']['id']}-{repeat}"
            session_id = str(uuid4())
            attempts = 0
            response_ids: list[str] = []
            reasoning: list[bool] = []

            async def transport(request: httpx.Request) -> httpx.Response:
                nonlocal attempts
                attempts += 1
                name = f"{stem}-attempt{attempts}"
                body = json.loads(request.content)
                assert body == case["request"], "Production request drift"
                request_path = runs / f"{name}.request.json"
                write(request_path, body)
                curl_config = (
                    "\n".join(
                        [
                            "silent",
                            "show-error",
                            "request = POST",
                            "max-time = 180",
                            "url = " + json.dumps(str(request.url)),
                            "header = " + json.dumps("Content-Type: application/json"),
                            "header = "
                            + json.dumps("Authorization: " + request.headers["Authorization"]),
                            "data-binary = " + json.dumps("@" + str(request_path)),
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
                write(
                    runs / f"{name}.transport.json",
                    {
                        "exit_code": process.returncode,
                        "http_status": status.decode(),
                        "stderr": stderr.decode(),
                    },
                )
                (runs / f"{name}.raw.json").write_bytes(raw)
                if process.returncode or not status.isdigit() or int(status) == 0:
                    raise httpx.RequestError(
                        "curl transport failed; see retained attempt", request=request
                    )
                if int(status) == 200:
                    envelope = json.loads(raw)
                    response_ids.append(envelope.get("id", ""))
                    reasoning.append(
                        bool(envelope["choices"][0]["message"].get("reasoning_content"))
                    )
                return httpx.Response(int(status), content=raw, request=request)

            result: dict[str, Any] = {
                "case": case["fixture"]["id"],
                "repeat": repeat,
                "session_id": session_id,
                "data_root": str(task_root),
                "accepted": False,
            }
            async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
                try:
                    result["output"] = await chat_completion_json(
                        client,
                        messages(case),
                        **{**options(case), "api_base": cfg["api_base"]},
                        api_key=cfg["api_key"],
                        session_id=session_id,
                        turn_number=int(case["fixture"]["id"][10]),
                        agent="narrator",
                    )
                    result["accepted"] = True
                except Exception as error:
                    result["error"] = f"{type(error).__name__}: {error}"
            result.update(attempts=attempts, response_ids=response_ids, reasoning=reasoning)
            write(runs / f"{stem}.result.json", result)
            print(stem, "accepted", result["accepted"], "attempts", attempts, flush=True)

    await asyncio.gather(*(logical(c, r) for r in range(1, 5) for c in manifest["cases"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
