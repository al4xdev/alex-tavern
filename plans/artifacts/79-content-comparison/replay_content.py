import asyncio
import copy
import hashlib
import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "plans/artifacts/79-content-comparison"
CASES = [("pedra", "base-P1-r2", "bb72dc94", 9), ("cedro", "base-P1-r1", "ea6620fb", 12)]


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def prepare():
    OUT.mkdir(exist_ok=True)
    if (OUT / "manifest.json").exists():
        raise RuntimeError("Preserve the existing manifest")
    cases = []
    for label, cell, sid, turn in CASES:
        source = ROOT / f"plans/artifacts/repetition-battery/{cell}/sessions/{sid}/debug.jsonl"
        rows = [
            (index, json.loads(line))
            for index, line in enumerate(source.read_text().splitlines(), 1)
        ]
        selected = [
            (index, row)
            for index, row in rows
            if row.get("agent") == "prose"
            and row.get("turn_number") == turn
            and not row.get("error")
        ]
        index, row = selected[-1]
        req = row["request"]
        assert req["provider_options"]["thinking_enabled"] is False
        body = {
            "model": row["model"],
            "messages": req["messages"],
            "max_tokens": req["max_tokens"],
            "response_format": req["response_format"],
            "thinking": {"type": "disabled"},
        }
        without = copy.deepcopy(body)
        count = 0
        for message in without["messages"]:
            text = message["content"]
            if "BLOCKING (where each person" not in text:
                continue
            start = text.index("BLOCKING (where each person")
            end = text.index("READER TRANSCRIPT", start)
            message["content"] = text[:start] + text[end:]
            count += 1
        assert count == 1
        cases.append(
            {
                "label": label,
                "session_id": sid,
                "turn_number": turn,
                "source": str(source.relative_to(ROOT)),
                "line": index,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "arms": {"with": body, "without": without},
            }
        )
    write(OUT / "manifest.json", cases)
    print("Prepared two archived prose requests")


async def run():
    cases = json.loads((OUT / "manifest.json").read_text())
    cfg = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    assert "\n" not in cfg["api_key"] and "\r" not in cfg["api_key"]
    runs = OUT / "runs"
    runs.mkdir(exist_ok=False)
    source = Path(__file__).read_bytes()
    (runs / "executed-script.py").write_bytes(source)
    write(
        runs / "run.json",
        {
            "started_unix": time.time(),
            "script_sha256": hashlib.sha256(source).hexdigest(),
            "preregistration_sha256": hashlib.sha256(
                (OUT / "PREREGISTRATION.md").read_bytes()
            ).hexdigest(),
            "manifest_sha256": hashlib.sha256((OUT / "manifest.json").read_bytes()).hexdigest(),
        },
    )
    jobs = [
        (case, arm, repeat) for case in cases for arm in ("with", "without") for repeat in range(3)
    ]
    random.Random(790906).shuffle(jobs)
    write(runs / "schedule.json", [(case["label"], arm, repeat) for case, arm, repeat in jobs])
    sem = asyncio.Semaphore(6)

    async def call(case, arm, repeat):
        label = f"{case['label']}-{arm}-{repeat}"
        reqpath = runs / f"{label}.request.json"
        respath = runs / f"{label}.response.json"
        write(reqpath, case["arms"][arm])
        result = {
            "session_id": case["session_id"],
            "turn_number": case["turn_number"],
            "agent": "audit:content_comparison",
            "arm": arm,
            "repeat": repeat,
            "request": case["arms"][arm],
        }
        async with sem:
            start = time.monotonic()
            proc = await asyncio.create_subprocess_exec(
                "curl",
                "-q",
                "--config",
                "-",
                "--silent",
                "--show-error",
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
                str(respath),
                "--write-out",
                "%{http_code}",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, error = await proc.communicate(
                (
                    "header = " + json.dumps("Authorization: Bearer " + cfg["api_key"]) + "\n"
                ).encode()
            )
            result.update(
                http_status=out.decode().strip(),
                curl_exit=proc.returncode,
                duration_ms=round((time.monotonic() - start) * 1000),
                curl_error=error.decode().replace(cfg["api_key"], "[REDACTED]"),
            )
            try:
                response = json.loads(respath.read_text())
                result["response"] = response
                assert result["http_status"] == "200" and not proc.returncode
                parsed = json.loads(response["choices"][0]["message"]["content"])
                assert isinstance(parsed["narration"], str) and parsed["narration"].strip()
                result["parsed"] = parsed
            except (OSError, ValueError, KeyError, IndexError, TypeError, AssertionError) as exc:
                result["error"] = type(exc).__name__
        write(runs / f"{label}.result.json", result)
        print(label, result.get("error", "ok"), flush=True)

    await asyncio.gather(*(call(*job) for job in jobs))


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "prepare":
        prepare()
    elif sys.argv[1] == "run":
        asyncio.run(run())
