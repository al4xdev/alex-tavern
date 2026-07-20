"""WT-09 mode 2: does the Director actually READ THE NAMES aloud at T20?

The scripted action is "Ler em voz alta a cifra decifrada de Moriarty diante de
toda a delegacao". The Director is omniscient (its prompt holds Glinda +
Moriarty) but inconsistently resolves the action into a PUBLIC audible_speech
that actually names them. This replays the real T20 Director call and measures
the public-naming rate, BEFORE vs a prompt nudge.

PRE-REGISTERED RULE: the nudge SHIPS iff it raises "public audible_speech that
names Glinda AND Moriarty" to >= 4/5 (from the BEFORE baseline) without the
name appearing in a NON-public (scoped) event (no new leak surface).
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from src.llm.client import chat_completion_json

MSGS = json.load(open("scratchpad/t20_director_msgs.json"))
RUNS = 5
PRESENT = {"C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"}  # non-subject present cast

# The nudge: appended to the Director system prompt. When an action voices named
# content aloud to the room, the resulting audible_speech MUST contain the words
# actually spoken (the names), addressed to everyone who can hear — never a
# deferral or a preamble that withholds them.
NUDGE = (
    "\n\nREADING/ANNOUNCING ALOUD: when a character's action reads out, announces, "
    "or reveals NAMED content to those present (a decoded message, a verdict, a "
    "list of names), you MUST emit an `audible_speech` event whose `content` "
    "quotes the ACTUAL words spoken - including the specific names or facts - "
    "witnessed by everyone who can hear. Never substitute a preamble that defers "
    "or withholds the names ('before I read them...'); the action already reads "
    "them, so the words are now public. Only withhold when the action itself is "
    "private/whispered."
)


def config() -> dict:
    c = json.loads(Path(".data/config.json").read_text())["providers"]["deepseek"]
    return {"model": c.get("model", ""), "api_base": c.get("api_base", ""),
            "api_key": c.get("api_key", ""), "provider": "deepseek"}


def analyze(resp: dict) -> tuple[bool, bool]:
    """(public_named, scoped_named): did Glinda+Moriarty appear in a PUBLIC
    audible_speech, and did either name appear in a NON-public event (leak)?"""
    public_named = False
    scoped_named = False
    for e in resp.get("perception_events") or []:
        if e.get("event_kind") != "audible_speech":
            continue
        c = e.get("content", "").lower()
        named = ("glinda" in c) and ("moriarty" in c)
        if not ("glinda" in c or "moriarty" in c):
            continue
        witnesses = {w for w in e.get("witness_ids", []) if w.startswith("C")}
        public = witnesses >= PRESENT
        if public and named:
            public_named = True
        if not public:
            scoped_named = True
    return public_named, scoped_named


async def arm(client: httpx.AsyncClient, cfg: dict, msgs: list[dict], label: str) -> None:
    pub = 0
    leak = 0
    print(f"\n===== {label} =====")
    for i in range(RUNS):
        r = await chat_completion_json(
            client, msgs, model=cfg["model"], max_tokens=1200,
            provider=cfg["provider"], api_base=cfg["api_base"], api_key=cfg["api_key"],
            agent="exp:wt09_mode2",
        )
        p, s = analyze(r)
        pub += int(p)
        leak += int(s)
        # find the reveal content for display
        rev = ""
        for e in r.get("perception_events") or []:
            if e.get("event_kind") == "audible_speech" and re.search(r"(?i)glinda|moriarty", e.get("content", "")):
                rev = e["content"][:80]
        print(f"  run {i}: public_named={p} scoped_leak={s} | {rev}")
    print(f"  -> public-named {pub}/{RUNS} | scoped-leak {leak}/{RUNS}")


async def main() -> None:
    cfg = config()
    nudged = [dict(m) for m in MSGS]
    nudged[0] = {**nudged[0], "content": nudged[0]["content"] + NUDGE}
    async with httpx.AsyncClient() as client:
        await arm(client, cfg, MSGS, "BEFORE (real prompt)")
        await arm(client, cfg, nudged, "AFTER (reading-aloud nudge)")


if __name__ == "__main__":
    asyncio.run(main())
