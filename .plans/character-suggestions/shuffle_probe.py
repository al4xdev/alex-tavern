"""Replay a recorded Character request with reproducible whole-context permutations."""

# ruff: noqa: E402 — set isolated runtime paths before application imports
from __future__ import annotations

import asyncio
import json
import random
import re
import runpy
from pathlib import Path

transport = runpy.run_path(str(Path(__file__).with_name("compare.py")))["CurlTransport"]

import httpx

from src.agents.character import build_character_json_schema
from src.config import load_config, resolve_active_config
from src.llm.client import call_agent

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "alex-tavern"
OUT = Path(__file__).parent / "private" / "shuffle"
OUT.mkdir(exist_ok=True)


async def main():
    path = SOURCE / ".data/sessions/274679ed/debug.jsonl"
    raw = path.read_bytes()
    records = [json.loads(line) for line in raw.splitlines()]
    record = next(r for r in reversed(records) if r.get("agent", "").startswith("character:"))
    config = resolve_active_config(load_config(SOURCE / ".data/config.json"))
    original = record["request"]["messages"]
    content = original[-1]["content"]
    prefix, final = content.rsplit("Return your audible speech", 1)
    blocks = re.split(
        r"(?=^(?:RECENT EVENTS:|WHO IS HERE WITH YOU:|CURRENT PRIVATE STATE:|SCENE CONTEXT))",
        prefix,
        flags=re.M,
    )
    blocks = [block for block in blocks if block.strip()]
    assert len(blocks) == 4
    (OUT / "source.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
    outputs = []
    async with httpx.AsyncClient(transport=transport()) as client:
        for seed in (None, 11, 22, 33):
            order = list(range(len(blocks)))
            if seed is not None:
                random.Random(seed).shuffle(order)
            messages = [dict(message) for message in original]
            messages[-1]["content"] = (
                "".join(blocks[i] for i in order) + "Return your audible speech" + final
            )
            for repetition in range(3):
                result = await call_agent(
                    client,
                    config,
                    messages,
                    agent="character:Asword:order-probe",
                    json_schema=build_character_json_schema(),
                    max_tokens=record["request"]["max_tokens"],
                    session_id=f"shuffle-{seed}-{repetition}",
                    turn_number=record["turn_number"],
                )
                outputs.append(
                    {"seed": seed, "order": order, "repetition": repetition, "response": result}
                )
                (OUT / "results.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2))
                print(f"order {order}, run {repetition}: completed", flush=True)
    assert path.read_bytes() == raw
    print("Source log unchanged", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
