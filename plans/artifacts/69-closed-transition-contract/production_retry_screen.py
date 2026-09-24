from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS = 4
SCHEMA_MARKER = (
    "Return only one JSON object that conforms exactly to this JSON Schema. "
    "Do not add markdown or keys outside the schema:\n"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def execute(run_name: str) -> None:
    out = HERE / run_name
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-v2r-") as temporary_data:
        os.environ["ROLEPLAY_DATA_DIR"] = temporary_data
        sys.path.insert(0, str(ROOT))

        from replay_contract import (  # noqa: PLC0415
            SOURCE,
            candidate_request_v2,
            source_request,
            transition_errors_v2,
        )

        from src.llm.client import call_agent  # noqa: PLC0415

        request = candidate_request_v2(source_request())
        messages = copy.deepcopy(request["messages"])
        before_schema, raw_schema = messages[0]["content"].split(SCHEMA_MARKER, 1)
        messages[0]["content"] = before_schema.rstrip()
        schema = json.loads(raw_schema)
        json_schema = {"name": "narrator_turn", "schema": schema}

        stored = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))
        provider = stored["providers"]["deepseek"]
        config = {
            **provider,
            "provider": "deepseek",
            "language": stored["language"],
        }
        write_json(
            out / "run.json",
            {
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "script_sha256": digest(Path(__file__)),
                "preregistration_sha256": digest(HERE / "PREREGISTRATION-V2R.md"),
                "v2_request_sha256": hashlib.sha256(
                    json.dumps(request, ensure_ascii=False, sort_keys=True).encode()
                ).hexdigest(),
                "started_unix": time.time(),
            },
        )

        async with httpx.AsyncClient() as client:

            async def one(repeat: int) -> dict[str, Any]:
                session_id = f"v2r-{repeat}"
                result: dict[str, Any] = {"repeat": repeat}
                try:
                    parsed = await call_agent(
                        client,
                        config,
                        copy.deepcopy(messages),
                        agent="director",
                        json_schema=json_schema,
                        max_tokens=int(config["max_tokens_narrator"]),
                        session_id=session_id,
                        turn_number=5,
                    )
                    result["client_valid"] = True
                    result["parsed"] = parsed
                    result["transition_errors"] = transition_errors_v2(parsed)
                except ValueError as exc:
                    result["client_valid"] = False
                    result["error"] = str(exc)

                debug_path = Path(temporary_data) / "sessions" / session_id / "debug.jsonl"
                if debug_path.exists():
                    archived = out / f"V2R-{repeat}.debug.jsonl"
                    archived.write_bytes(debug_path.read_bytes())
                    result["attempts"] = len(debug_path.read_text(encoding="utf-8").splitlines())
                else:
                    result["attempts"] = 0
                write_json(out / f"V2R-{repeat}.result.json", result)
                return result

            results = await asyncio.gather(*(one(repeat) for repeat in range(RUNS)))
        write_json(out / "summary.json", results)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: production_retry_screen.py RUN_NAME")
    asyncio.run(execute(sys.argv[1]))
