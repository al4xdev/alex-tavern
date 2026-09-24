from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "plans/artifacts/repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl"
HEADERS = (
    "Current beat:",
    "Not in play yet — introduce as concrete perception events:",
    "The beat ends when:",
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare() -> None:
    path = OUT / "manifest.json"
    if path.exists():
        raise RuntimeError("Preserve the existing manifest")
    selected = {}
    raw = SOURCE.read_bytes()
    for line, text in enumerate(raw.decode().splitlines(), 1):
        row = json.loads(text)
        if (
            row.get("agent") == "director"
            and row.get("turn_number") in (34, 35)
            and not row.get("error")
        ):
            json.loads(row["response"])
            selected[row["turn_number"]] = (line, row)
    assert set(selected) == {34, 35}
    cases = []
    for turn, (line, row) in sorted(selected.items()):
        request = row["request"]
        assert request["provider_options"]["thinking_enabled"] is False
        body = {
            "model": row["model"],
            "messages": request["messages"],
            "max_tokens": request["max_tokens"],
            "response_format": request["response_format"],
            "thinking": {"type": "disabled"},
        }
        modified = copy.deepcopy(body)
        removed = []
        for message in modified["messages"]:
            lines = message["content"].splitlines(keepends=True)
            retained = []
            for value in lines:
                if any(value.lstrip().startswith(header) for header in HEADERS):
                    removed.append(value)
                else:
                    retained.append(value)
            message["content"] = "".join(retained)
        assert len(removed) == 3
        assert all(
            sum(value.lstrip().startswith(header) for value in removed) == 1 for header in HEADERS
        )
        cases.append(
            {
                "turn_number": turn,
                "line": line,
                "arms": {"A": body, "B": modified},
                "removed": removed,
                "original_response": row["response"],
            }
        )
    write(
        path,
        {
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": digest(raw),
            "session_id": "8bd4d0f1",
            "seed": 690905,
            "cases": cases,
        },
    )
    print("Prepared two real payloads; B removes exactly three lines each")


async def run() -> None:
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    cfg = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    assert "\n" not in cfg["api_key"] and "\r" not in cfg["api_key"]
    runs = OUT / "runs"
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
        for arm in ("A", "B")
        for repeat in range(4)
    ]
    random.Random(manifest["seed"]).shuffle(jobs)
    sem = asyncio.Semaphore(4)
    stopped = asyncio.Event()

    async def call(case: dict, arm: str, repeat: int) -> None:
        label = f"{case['turn_number']}-{arm}-{repeat}"
        request = case["arms"][arm]
        reqpath = runs / f"{label}.request.json"
        responsepath = runs / f"{label}.response.json"
        write(reqpath, request)
        result = {
            "session_id": manifest["session_id"],
            "turn_number": case["turn_number"],
            "agent": "audit:roof_input",
            "arm": arm,
            "repeat": repeat,
            "request": request,
            "request_sha256": digest(reqpath.read_bytes()),
        }
        async with sem:
            if stopped.is_set():
                result["error"] = "not_dispatched_after_account_error"
            else:
                start = time.monotonic()
                proc = await asyncio.create_subprocess_exec(
                    "curl",
                    "-q",
                    "--config",
                    "-",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    "240",
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
                        "header = " + json.dumps("Authorization: Bearer " + cfg["api_key"]) + "\n"
                    ).encode()
                )
                status = stdout.decode().strip()
                result.update(
                    http_status=status,
                    curl_exit=proc.returncode,
                    duration_ms=round((time.monotonic() - start) * 1000),
                    curl_error=stderr.decode().replace(cfg["api_key"], "[REDACTED]"),
                )
                if status in ("401", "402", "403"):
                    stopped.set()
                try:
                    response = json.loads(responsepath.read_text())
                    result["response"] = response
                    if status != "200" or proc.returncode:
                        result["error"] = "provider_or_transport_error"
                    else:
                        parsed = json.loads(response["choices"][0]["message"]["content"])
                        assert isinstance(parsed["perception_events"], list)
                        result["parsed"] = parsed
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
        print(f"Finished {label}: {result.get('error', 'ok')}", flush=True)

    await asyncio.gather(*(call(*job) for job in jobs))


def blind() -> None:
    path = OUT / "read-order.json"
    if path.exists():
        raise RuntimeError("Preserve existing read order")
    paths = sorted((OUT / "runs").glob("*.result.json"))
    assert len(paths) == 16
    random.Random(690906).shuffle(paths)
    write(path, {f"R{index:02d}": str(file.relative_to(OUT)) for index, file in enumerate(paths)})
    with (OUT / "blind-read.txt").open("w") as stream:
        for index, file in enumerate(paths):
            row = json.loads(file.read_text())
            stream.write(f"\nR{index:02d}\n")
            stream.write(
                json.dumps(
                    row.get("parsed", {"error": row.get("error")}), ensure_ascii=False, indent=2
                )
                + "\n"
            )
    print("Prepared opaque read dossier; do not open read-order until judgments are saved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "blind"))
    args = parser.parse_args()
    if args.command == "run":
        asyncio.run(run())
    else:
        globals()[args.command]()
