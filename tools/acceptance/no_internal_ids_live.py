"""End-to-end proof that no internal character id reaches player-facing text.

Task 36's criterion ("no IDs in the prose request, assertable from debug.jsonl")
was verified by scanning 17 archived sessions on 2026-07-27, which found 4968
raw ids and 11 corrupted story summaries. The fix is unit-tested in
`tests/test_internal_ids_in_prompts.py`, but those tests call prompt builders.
This drives the real HTTP API against the real provider, because the failure
that started all of this was a summary the builders never see.

Checks, all deterministic:

  1. Every prompt the server actually sent, read back from `debug.jsonl`: no
     raw id in prose or summarizer requests.
  2. The Director still receives ids AND the roster that resolves them - the
     fix must not have flattened the one prompt that needs them.
  3. After a real compaction, `story_summary` carries no raw id.
  4. No narration or speech the player can read carries one.

Usage: python -m tools.acceptance.no_internal_ids_live [base_url]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8903"
TURNS = 8
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{' | ' + detail if detail else ''}")
    if not ok:
        failures.append(f"{label} — {detail}")


with httpx.Client(base_url=BASE, timeout=600) as client:
    token = client.get("/bootstrap").json()["access_token"]
    client.headers["x-tavern-token"] = token
    client.headers["Origin"] = BASE

    config = client.get("/config").json()
    print(f"provider={config['active_provider']} language={config.get('language')}")

    # Saved and restored below. Leaving the server on a 2-turn retention window
    # would compact almost every later turn - a side effect that outlives this
    # script and quietly changes any measurement taken afterwards.
    original_config = json.loads(json.dumps(config))

    # The summarizer only runs at a compaction, and a compaction only evicts what
    # falls outside the retained window. With the default 200 the run below plays
    # 8 turns, nothing is evicted, and the story_summary check passes on an empty
    # summary - which is exactly the vacuous green this script exists to avoid.
    config["compaction_keep_recent_turns"] = 2
    saved = client.put("/config", json=config)
    check("retention window narrowed so a compaction can happen", saved.status_code == 200)

    scenario = client.get("/scenario-defaults?name=thorn-lyra").json()["scenario"]
    started = client.post(
        "/session/start",
        json={
            "characters": scenario["characters"],
            "scene": scenario["scene"],
            "controlled_character_id": scenario["controlled_character_id"],
            "narrator_directives": scenario["narrator_directives"],
        },
    ).json()
    sid = started["session_id"]
    ids = list(scenario["characters"])
    id_re = re.compile(r"\b(" + "|".join(re.escape(i) for i in ids) + r")\b")
    print(f"session {sid} | cast {ids}")

    prompts = [
        "Who runs this inn?",
        "I look around for anyone watching us.",
        "Tell me what you know about the medallion.",
        "I move toward the back door.",
    ]
    for turn in range(TURNS):
        body = {"speech": prompts[turn % len(prompts)]} if turn % 2 == 0 else {"skip": True}
        posted = client.post(f"/session/{sid}/turn", json=body)
        if posted.status_code != 200:
            check(f"turn {turn + 1} was accepted", False, str(posted.status_code))

    compacted = client.post(f"/session/{sid}/compact").json()
    check(
        "a real compaction ran",
        compacted.get("compacted") is True and (compacted.get("evicted_records") or 0) > 0,
        str(compacted.get("reason") or compacted.get("evicted_records")),
    )

    state = client.get(f"/session/{sid}/state").json()
    restored = client.put("/config", json=original_config)
    check("the server config was restored", restored.status_code == 200, str(restored.status_code))

    # 3. the durable memory, which every later prompt reads
    summary = state.get("story_summary") or ""
    found = id_re.search(summary)
    check(
        "story_summary carries no raw id",
        not found,
        f"...{summary[max(0, found.start() - 90) : found.start() + 90]}..." if found else "",
    )

    # 4. what the player can actually read
    visible = [
        record
        for record in state["history"]
        if record["content_type"] in ("narration", "speech")
    ]
    bad = [r for r in visible if id_re.search(r["content"])]
    check(
        "no player-visible text carries a raw id",
        not bad,
        f"{len(bad)} of {len(visible)} records" if bad else f"{len(visible)} records clean",
    )

# 1 + 2. what the server actually sent
debug_path = Path(".data/sessions") / sid / "debug.jsonl"
if not debug_path.exists():
    check("debug.jsonl found", False, str(debug_path))
else:
    counts = {"prose": 0, "summarizer": 0, "director": 0}
    dirty: list[str] = []
    director_with_roster = 0
    for line in debug_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        agent = (record.get("agent") or "").split(":")[0]
        request = record.get("request")
        if agent not in counts or not isinstance(request, dict) or "messages" not in request:
            continue
        counts[agent] += 1
        text = "\n".join(message["content"] for message in request["messages"])
        if agent == "director":
            if all(f"ID={cid} | NAME=" in text for cid in ids):
                director_with_roster += 1
            continue
        hit = id_re.search(text)
        if hit:
            dirty.append(f"{agent} t{record.get('turn_number')}: {hit.group(0)}")

    check(
        "no raw id in prose/summarizer requests",
        not dirty,
        f"{len(dirty)} dirty of {counts['prose'] + counts['summarizer']} calls"
        if dirty
        else f"{counts['prose']} prose + {counts['summarizer']} summarizer calls clean",
    )
    for item in dirty[:5]:
        print(f"       {item}")
    check(
        "the Director still gets the roster that resolves its ids",
        counts["director"] > 0 and director_with_roster == counts["director"],
        f"{director_with_roster}/{counts['director']}",
    )

print()
if failures:
    print(f"{len(failures)} FALHA(S):")
    for item in failures:
        print("  -", item)
    raise SystemExit(1)
print("nenhum id interno em texto de jogador nem em prompt sem roster: tudo verde")
