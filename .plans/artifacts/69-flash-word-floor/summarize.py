"""Summarize retained Flash attempts without making additional model calls."""

import json
import statistics
from collections import Counter
from contextlib import suppress
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


manifest = read(HERE / "manifest.json")
results = [read(p) for p in sorted((HERE / "runs").glob("*.result.json"))]
assert len(results) == 27
raw_paths = sorted((HERE / "runs").glob("*.raw.json"))
raws = []
for path in raw_paths:
    # Failed transport evidence remains on disk and in the attempt count.
    with suppress(json.JSONDecodeError):
        raws.append(read(path))
requests = [read(p) for p in sorted((HERE / "runs").glob("*.request.json"))]
assert all(r["model"] == "deepseek-v4-flash" for r in requests)
assert all(r["thinking"] == {"type": "disabled"} for r in requests)
assert all("reasoning_effort" not in r for r in requests)
words = [r["words"] for r in results if r["valid"]]
summary = {
    "planned": 27,
    "valid": sum(r["valid"] for r in results),
    "floor_pass": sum(r["floor_pass"] for r in results),
    "attempts": len(raw_paths),
    "response_envelopes": len(raws),
    "skipped": sum("skipped" in r for r in results),
    "words": {"min": min(words), "median": statistics.median(words), "max": max(words)},
    "finish_reasons": dict(
        Counter(c.get("finish_reason") for r in raws for c in r.get("choices", []))
    ),
    "response_models": dict(Counter(r.get("model") for r in raws)),
    "reasoning_characters": sum(
        len(c["message"].get("reasoning_content") or "") for r in raws for c in r.get("choices", [])
    ),
    "prompt_tokens": sum(r.get("usage", {}).get("prompt_tokens", 0) for r in raws),
    "completion_tokens": sum(r.get("usage", {}).get("completion_tokens", 0) for r in raws),
    "max_prompt_tokens": max(r.get("usage", {}).get("prompt_tokens", 0) for r in raws),
    "max_completion_tokens": max(r.get("usage", {}).get("completion_tokens", 0) for r in raws),
    "wall_seconds": {
        "min": min(r["wall_seconds"] for r in results if "wall_seconds" in r),
        "median": statistics.median(r["wall_seconds"] for r in results if "wall_seconds" in r),
        "max": max(r["wall_seconds"] for r in results if "wall_seconds" in r),
    },
    "cases": [
        {
            "id": c["id"],
            "local": c["local_words"],
            "flash": [
                r.get("words")
                for r in sorted(results, key=lambda r: r["repeat"])
                if r["case"] == c["id"]
            ],
        }
        for c in manifest["cases"]
    ],
}
(HERE / "runs/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))

transcript = [
    "# Flash prose replays",
    "",
    "All three draws per retained source case. Source requests and raw responses remain "
    "in ignored local runs/; scope and fixture context are in the protocol "
    "and prior English report.",
    "",
]
packet = [
    "Objective: independently assess source fidelity and narrative readability of prose replays. "
    "Audience: roleplay developer choosing whether the word floor provides useful prose. "
    "Judge actual supplied messages and outputs, not imagined engine context. "
    "Dialogue is separate, so do not require spoken lines. Sources may omit an actor's name; "
    "report ambiguity instead of presuming it was explicit. Distinguish verified contradictions "
    "from expansions. Do not infer that a word floor causes padding. Return compact evidence "
    "quotes/case/repeat for actor swaps, restaged historical actions, "
    "unsupported physical changes, "
    "technical diction, filler and grammar; state uncertainties. NO tools, filesystem, shell, "
    "MCP, clipboard, edits, messages or delegation. Read only supplied text."
]
for case in manifest["cases"]:
    transcript.extend([f"## {case['id']}", "", f"Local baseline: {case['local_words']} words.", ""])
    packet.extend(
        [
            "SOURCE " + case["id"],
            json.dumps(case["source_request"]["messages"], ensure_ascii=False),
            "SCOPE " + json.dumps(case["scope"]),
            "LOCAL BASELINE " + case["local_prose"],
        ]
    )
    for r in sorted(results, key=lambda r: r["repeat"]):
        if r["case"] != case["id"]:
            continue
        prose = r.get("output", {}).get("narration", r.get("error", r.get("skipped", "No output")))
        transcript.extend([f"### Flash draw {r['repeat']}: {r.get('words')} words", "", prose, ""])
        packet.append(f"FLASH DRAW {r['repeat']}\n" + prose)
(HERE / "TRANSCRIPTS.md").write_text("\n".join(transcript))
(HERE / "runs/reader-packet.txt").write_text("\n\n".join(packet))
