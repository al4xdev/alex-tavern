"""Task 26, acceptance criterion 2: a fresh blind continuity review.

"A fresh blind continuity review reports no staging jump of the door/table kind
and no verbatim-duplicated thoughts."

Blind means blind: the reviewer is told it is reading a transcript and what to
look for structurally, and is told NOTHING about which arm produced it, what we
expect to find, or that a previous review found anything. It never sees this
project's vocabulary (roteiro, beat, Director) either.

Reported per session, never aggregated into a verdict here - the numbers go in
the task and the judgement is made there.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

D = Path(sys.argv[1])
ARMS = sys.argv[2].split(",")

SYSTEM = """\
You review a transcript of a scene for CONTINUITY defects only. You are not
judging style, pacing or quality.

Report exactly two kinds of defect:

1. STAGING: something physically impossible given what came before. A person
   acting in a place they had left; an object described as being in two places;
   a door or a seat described as open/closed or occupied/empty inconsistently;
   someone reacting to something they could not have perceived.
2. REPEAT: two passages that are word-for-word identical or nearly so, where
   the repetition is not an intentional refrain.

For each defect give the two line numbers involved and one short sentence. If
there are none of a kind, return an empty list for it. Do not invent defects to
fill the output; an empty report is a valid answer.
"""

SCHEMA = {
    "name": "continuity_review",
    "schema": {
        "type": "object",
        "properties": {
            "staging": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "lines": {"type": "array", "items": {"type": "integer"}},
                        "why": {"type": "string"},
                    },
                    "required": ["lines", "why"],
                    "additionalProperties": False,
                },
            },
            "repeats": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "lines": {"type": "array", "items": {"type": "integer"}},
                        "why": {"type": "string"},
                    },
                    "required": ["lines", "why"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["staging", "repeats"],
        "additionalProperties": False,
    },
}


def transcript_of(state: dict) -> str:
    """What a reader sees: narration and public speech, numbered."""
    lines = []
    for record in state.get("history", []):
        if record["content_type"] not in ("narration", "speech"):
            continue
        if record.get("audience"):
            continue  # private to a subset; a reader never saw it
        who = "NARRATION" if record["content_type"] == "narration" else record["speaker"]
        lines.append(f"{len(lines) + 1}. [{who}] {record['content']}")
    return "\n".join(lines)


async def main() -> None:
    config = json.loads((D / "cfg_off.json").read_text(encoding="utf-8"))
    provider = config["providers"][config["active_provider"]]

    sessions = []
    for arm in ARMS:
        for session_dir in sorted((D / arm / "sessions").iterdir()):
            state_path = session_dir / "state.json"
            if state_path.exists():
                sessions.append((arm, session_dir.name, json.loads(state_path.read_text())))

    results = []
    async with httpx.AsyncClient(
        base_url=provider["api_base"],
        headers={"Authorization": f"Bearer {provider['api_key']}"},
    ) as client:
        for arm, sid, state in sessions:
            text = transcript_of(state)
            if text.count("\n") < 5:
                continue
            payload = {
                "model": provider["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            "Transcript:\n\n" + text + "\n\nReturn only one JSON object "
                            "matching this schema:\n" + json.dumps(SCHEMA["schema"])
                        ),
                    },
                ],
                "max_tokens": 4096,
                "stream": False,
                "response_format": {"type": "json_object"},
            }
            report = None
            for _ in range(3):
                response = await client.post("/chat/completions", json=payload, timeout=240)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"] or ""
                start, end = raw.find("{"), raw.rfind("}")
                if start < 0 or end <= start:
                    continue
                try:
                    report = json.loads(raw[start : end + 1], strict=False)
                    break
                except json.JSONDecodeError:
                    continue
            if report is None:
                finish = response.json()["choices"][0].get("finish_reason")
                print(
                    f"  {arm:12} {sid}  (unreadable) finish={finish} "
                    f"len={len(raw)} tail={raw[-90:]!r}",
                    flush=True,
                )
                continue
            staging = len(report.get("staging") or [])
            repeats = len(report.get("repeats") or [])
            results.append((arm, sid, staging, repeats, report))
            print(f"  {arm:12} {sid}  staging={staging}  repeats={repeats}", flush=True)
            for kind in ("staging", "repeats"):
                for item in (report.get(kind) or [])[:2]:
                    print(f"       {kind}: lines {item['lines']} — {item['why'][:90]}")

    print("\n=== resumo ===")
    print(f"sessoes revisadas: {len(results)}")
    print(f"com staging jump:  {sum(1 for r in results if r[2])}/{len(results)}")
    print(f"com repeticao:     {sum(1 for r in results if r[3])}/{len(results)}")
    staging_total = sum(r[2] for r in results)
    repeat_total = sum(r[3] for r in results)
    print(f"total staging: {staging_total}  total repeats: {repeat_total}")
    (D / "blind_continuity_report.json").write_text(
        json.dumps(
            [{"arm": a, "session": s, "staging": st, "repeats": rp, "report": rep}
             for a, s, st, rp, rep in results],
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )


asyncio.run(main())
