from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import random
import statistics
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "plans/artifacts/79-positional-audit"
LABELS = {"MUDOU_DE_LUGAR", "REPOSICIONOU_NO_MESMO_LUGAR", "NAO_DA_PARA_SABER"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare() -> None:
    manifest_path = OUT / "manifest.json"
    if manifest_path.exists():
        raise RuntimeError("Manifest already exists; preserve this run")
    script = SOURCE / "blind_read_judge.py"
    tree = ast.parse(script.read_text())
    prompt = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "PROMPT" for target in node.targets)
    )
    original_path = SOURCE / "blind_read/results.json"
    original = json.loads(original_path.read_text())
    paths = {}
    for path in sorted((ROOT / "plans/artifacts").rglob("state.json")):
        paths.setdefault(path.parent.name, path)
    cases = []
    sessions = []
    for sid in sorted({row["session"] for row in original}):
        path = paths[sid]
        raw = path.read_bytes()
        state = json.loads(raw)
        sessions.append(
            {"session_id": sid, "path": str(path.relative_to(ROOT)), "sha256": digest(raw)}
        )
        for index, row in enumerate(original):
            if row["session"] != sid:
                continue
            name = state["characters"][row["cid"]]["mind"]["name"]
            assert name and name != row["cid"]
            assert row["character"] == row["cid"]
            narration = "\n\n".join(
                record["content"]
                for record in state["history"]
                if record["content_type"] == "narration" and record["turn_number"] == row["turn"]
            )
            assert len(narration) >= 200
            prompts = {
                arm: prompt.replace("{character}", who).replace("{narration}", narration[:4000])
                for arm, who in (("id", row["character"]), ("name", name))
            }
            assert (
                prompts["id"].replace(
                    "PERSONAGEM: " + row["character"] + "\n", "PERSONAGEM: " + name + "\n", 1
                )
                == prompts["name"]
            )
            cases.append(
                {
                    "case": index,
                    "session_id": sid,
                    "turn_number": row["turn"],
                    "cid": row["cid"],
                    "name": name,
                    "old_verdict": row["verdict"],
                    "narration": narration[:4000],
                    "full_narration_chars": len(narration),
                    "prompts": prompts,
                }
            )
    cases.sort(key=lambda row: row["case"])
    assert len(cases) == 40 and len(sessions) == 20
    write_json(
        manifest_path,
        {
            "original_results_sha256": digest(original_path.read_bytes()),
            "original_script_sha256": digest(script.read_bytes()),
            "prompt_sha256": digest(prompt.encode()),
            "sessions": sessions,
            "cases": cases,
            "seed": 790905,
            "repeats": 3,
        },
    )
    print(
        f"Prepared {len(cases)} cases across {len(sessions)} sessions; "
        "all 40 archived targets are IDs"
    )


async def run() -> None:
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    cfg = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    assert "\n" not in cfg["api_key"] and "\r" not in cfg["api_key"]
    runs = OUT / "runs"
    runs.mkdir(exist_ok=False)
    write_json(
        runs / "run.json",
        {
            "manifest_sha256": digest(manifest_path.read_bytes()),
            "script_sha256": digest(Path(__file__).read_bytes()),
            "model": cfg["model"],
            "api_base": cfg["api_base"],
            "seed": manifest["seed"],
        },
    )
    jobs = [
        (case, arm, rep) for case in manifest["cases"] for arm in ("id", "name") for rep in range(3)
    ]
    random.Random(manifest["seed"]).shuffle(jobs)
    write_json(
        runs / "schedule.json",
        [{"case": case["case"], "arm": arm, "repeat": rep} for case, arm, rep in jobs],
    )
    semaphore = asyncio.Semaphore(6)
    stop = asyncio.Event()
    completed = 0

    async def call(case: dict, arm: str, rep: int) -> None:
        nonlocal completed
        label = f"{case['case']:02d}-{arm}-{rep}"
        request = {
            "model": cfg["model"],
            "messages": [{"role": "user", "content": case["prompts"][arm]}],
            "max_tokens": 800,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
        }
        request_path = runs / f"{label}.request.json"
        response_path = runs / f"{label}.response.json"
        write_json(request_path, request)
        record = {
            "case": case["case"],
            "session_id": case["session_id"],
            "turn_number": case["turn_number"],
            "agent": "audit:reader_identity",
            "arm": arm,
            "repeat": rep,
            "model": cfg["model"],
            "request": request,
            "request_sha256": digest(request_path.read_bytes()),
        }
        async with semaphore:
            if stop.is_set():
                record["error"] = "not_dispatched_after_account_error"
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
                    "180",
                    "--request",
                    "POST",
                    cfg["api_base"].rstrip("/") + "/chat/completions",
                    "--header",
                    "Content-Type: application/json",
                    "--data-binary",
                    "@" + str(request_path),
                    "--output",
                    str(response_path),
                    "--write-out",
                    "%{http_code}",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                auth = "header = " + json.dumps("Authorization: Bearer " + cfg["api_key"]) + "\n"
                stdout, stderr = await proc.communicate(auth.encode())
                record["duration_ms"] = round((time.monotonic() - start) * 1000)
                status = stdout.decode().strip()
                record["http_status"] = status
                record["curl_exit"] = proc.returncode
                record["curl_error"] = stderr.decode().replace(cfg["api_key"], "[REDACTED]")
                if status in ("401", "402", "403"):
                    stop.set()
                try:
                    envelope = json.loads(response_path.read_text())
                    record["response"] = envelope
                    if status != "200" or proc.returncode:
                        record["error"] = "provider_or_transport_error"
                    else:
                        parsed = json.loads(envelope["choices"][0]["message"]["content"])
                        if parsed["verdict"] not in LABELS:
                            raise ValueError("Unknown verdict")
                        if not isinstance(parsed["evidence"], str):
                            raise ValueError("Evidence is not text")
                        record["parsed"] = parsed
                        record["evidence_verbatim"] = (
                            bool(parsed["evidence"]) and parsed["evidence"] in case["narration"]
                        )
                except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                    record["error"] = type(exc).__name__
        write_json(runs / f"{label}.result.json", record)
        completed += 1
        if completed % 12 == 0 or stop.is_set():
            print(f"Finished {completed}/{len(jobs)}; account_stop={stop.is_set()}", flush=True)

    await asyncio.gather(*(call(*job) for job in jobs))


def analyze() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    results = [
        json.loads(path.read_text()) for path in sorted((OUT / "runs").glob("*.result.json"))
    ]
    complete = len(results) == 240 and all("parsed" in row for row in results)
    output = {
        "complete": complete,
        "planned": 240,
        "recorded": len(results),
        "valid": sum("parsed" in row for row in results),
        "errors": dict(Counter(row["error"] for row in results if "error" in row)),
        "arms": {},
        "sessions": [],
    }
    for arm in ("id", "name"):
        valid = [row for row in results if row["arm"] == arm and "parsed" in row]
        output["arms"][arm] = {
            "valid": len(valid),
            "verdicts": dict(Counter(row["parsed"]["verdict"] for row in valid)),
            "determinate_evidence_nonverbatim_or_empty": sum(
                row["parsed"]["verdict"] != "NAO_DA_PARA_SABER" and not row["evidence_verbatim"]
                for row in valid
            ),
        }
    if complete:
        for source in manifest["sessions"]:
            sid = source["session_id"]
            cases = [case for case in manifest["cases"] if case["session_id"] == sid]
            row = {"session_id": sid, "cases": len(cases)}
            for arm in ("id", "name"):
                row[arm] = statistics.mean(
                    statistics.mean(
                        result["parsed"]["verdict"] == "NAO_DA_PARA_SABER"
                        for result in results
                        if result["case"] == case["case"] and result["arm"] == arm
                    )
                    for case in cases
                )
            row["difference"] = row["name"] - row["id"]
            output["sessions"].append(row)
        diffs = [row["difference"] for row in output["sessions"]]
        output["session_difference"] = {
            "mean": statistics.mean(diffs),
            "median": statistics.median(diffs),
            "population_sd": statistics.pstdev(diffs),
            "min": min(diffs),
            "max": max(diffs),
            "negative": sum(x < 0 for x in diffs),
            "positive": sum(x > 0 for x in diffs),
            "ties": sum(x == 0 for x in diffs),
        }
    write_json(OUT / "summary.json", output)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "run", "analyze"))
    mode = parser.parse_args().mode
    if mode == "run":
        asyncio.run(run())
    elif mode == "prepare":
        prepare()
    else:
        analyze()
