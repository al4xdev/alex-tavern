"""Curl-validate the WT-09 fix on the REAL Dorothy T24 payload.

The fix persists the Director's T20 audible_speech reveal as a spoken record,
so by T24 it appears in Dorothy's RECENT EVENTS (she witnessed it). This replays
her REAL T24 character call two ways and measures whether she now recalls the
name.

PRE-REGISTERED DECISION RULE (frozen before running):
  - BEFORE (real payload, reveal absent — as shipped in the failing run): expect
    ~0/4 replies naming "Glinda" (reproduces the failure).
  - AFTER (same payload with the persisted reveal line inserted into RECENT
    EVENTS, as the fix now produces): the fix RESOLVES WT-09 iff >= 3/4 replies
    name "Glinda".
"""

from __future__ import annotations

import asyncio
import copy
import json
import re
from pathlib import Path

import httpx

from src.llm.client import chat_completion_json

DEBUG = "plans/artifacts/xfailed3-post-39-41/full-ce87167b/debug.jsonl"
RUNS = 4

# The reveal exactly as the Director emitted it at T20 (second perception event),
# rendered as the speech record the fix now writes into history.
REVEAL_LINE = (
    "Turn 20 | TYPE=SPEECH | SPEAKER=Mulher adulta de postura diplomática, olhar "
    "atento e gestos medidos: Lê em voz alta: 'Pela presente, confirmo que Holmes "
    "é meu agente, e a Dama do Norte é Glinda, que planeja a conquista das cinco "
    "cidades. Assinado, Moriarty.'"
)
ANCHOR = (
    "Turn 20 | TYPE=SPEECH | SPEAKER=Mulher adulta de postura diplomática, olhar "
    "atento e gestos medidos: A cifra decifrada nomeia o patrono secreto"
)


def real_t24_messages() -> list[dict]:
    for line in open(DEBUG):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("turn_number") == 24 and r.get("agent") == "character:Dorothy":
            return r["request"]["messages"]
    raise SystemExit("T24 Dorothy call not found")


def with_reveal(messages: list[dict]) -> list[dict]:
    out = copy.deepcopy(messages)
    for m in out:
        if ANCHOR.split(":")[0] in m["content"] and "cifra decifrada nomeia" in m["content"]:
            # insert the reveal line right after the T20 preamble line
            m["content"] = m["content"].replace(
                ANCHOR, ANCHOR + "\n" + REVEAL_LINE, 1
            )
    return out


def config() -> dict:
    cfg = json.loads(Path(".data/config.json").read_text())
    p = cfg["providers"]["deepseek"]
    return {"model": p.get("model", ""), "api_base": p.get("api_base", ""),
            "api_key": p.get("api_key", ""), "provider": "deepseek"}


SCHEMA = {
    "name": "character_reply",
    "schema": {
        "type": "object",
        "properties": {
            "speech": {"type": ["string", "null"]},
            "thought": {"type": ["string", "null"]},
            "action_intent": {"type": ["string", "null"]},
        },
        "required": ["speech", "thought", "action_intent"],
        "additionalProperties": False,
    },
}


async def run_arm(client: httpx.AsyncClient, cfg: dict, messages: list[dict], label: str) -> int:
    hits = 0
    print(f"\n===== {label} =====")
    for i in range(RUNS):
        r = await chat_completion_json(
            client, messages, model=cfg["model"], max_tokens=256, json_schema=SCHEMA,
            provider=cfg["provider"], api_base=cfg["api_base"], api_key=cfg["api_key"],
            agent="exp:wt09",
        )
        speech = str(r.get("speech") or "")
        hit = bool(re.search(r"(?i)glinda", speech))
        hits += int(hit)
        print(f"  run {i}: glinda={hit} | {speech[:110]}")
    return hits


async def main() -> None:
    cfg = config()
    base = real_t24_messages()
    fixed = with_reveal(base)
    assert any("Glinda" in m["content"] for m in fixed), "reveal not injected"
    assert not any("Glinda" in m["content"] for m in base), "base already had Glinda"
    async with httpx.AsyncClient() as client:
        before = await run_arm(client, cfg, base, "BEFORE (reveal absent)")
        after = await run_arm(client, cfg, fixed, "AFTER (reveal persisted)")
    print("\n===== VERDICT =====")
    print(f"BEFORE glinda: {before}/{RUNS}")
    print(f"AFTER  glinda: {after}/{RUNS}  (fix resolves iff >= 3/4)")
    print(f"\nFIX RESOLVES WT-09: {after >= 3 and after > before}")


if __name__ == "__main__":
    asyncio.run(main())
