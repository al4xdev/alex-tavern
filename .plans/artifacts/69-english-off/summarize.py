"""Retained paired-language flags, metadata and source-bound output packet."""

import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "manifest.json").read_text())
assert all(
    hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    for name, digest in manifest["hashes"].items()
)
rows = [json.loads(p.read_text()) for p in sorted((HERE / "runs").glob("*.result.json"))]
assert len(rows) == 24
requests = [json.loads(p.read_text()) for p in (HERE / "runs").glob("*.request.json")]
assert all(
    r["model"] == "deepseek-v4-flash"
    and r["thinking"] == {"type": "disabled"}
    and "reasoning_effort" not in r
    for r in requests
)
valid = [r for r in rows if r["valid"]]
summary = {
    "logical": len(rows),
    "attempts": len(requests),
    "valid": len(valid),
    "correct": sum(r["correct"] for r in rows),
    "distinct_ids": len({r["response_id"] for r in valid}),
    "reasoning_chars": sum(r["reasoning_chars"] for r in valid),
    "finish_reasons": dict(Counter(r["finish_reason"] for r in valid)),
    "prompt_tokens": sum(r["usage"]["prompt_tokens"] for r in valid),
    "completion_tokens": sum(r["usage"]["completion_tokens"] for r in valid),
    "wall_seconds": {
        "min": min(r["wall_seconds"] for r in rows if "wall_seconds" in r),
        "median": statistics.median(r["wall_seconds"] for r in rows if "wall_seconds" in r),
        "max": max(r["wall_seconds"] for r in rows if "wall_seconds" in r),
    },
    "cells": [],
}
packet = [
    "Independent text reader. Read only supplied text. No tools, filesystem, shell, MCP, "
    "edits, messages, clipboard or delegation. Audience: developer considering English "
    "without reasoning on ambiguous act-completion inputs. Assess actual plan and source, "
    "not reader-facing prose (none was generated). Check continued pursuit of already "
    "completed goal, canonical closure/location, agency, unestablished historical premises, "
    "and naturalness vs technical diction. Prospective external escalation is allowed; "
    "distinguish a genuinely NEW pressure from treating confirmed closure as never completed. "
    "Quotes/case/language/repeat required. Return compact observations/uncertainties, "
    "not percentages or word/similarity metrics. No hidden causal diagnosis."
]
transcript = ["# Paired next-beat plans without reasoning", ""]
for case in manifest["cases"]:
    selected = [r for r in rows if r["case"] == case["case"] and r["language"] == case["language"]]
    cell = {
        "case": case["case"],
        "language": case["language"],
        "expected": case["expected"],
        "valid": sum(r["valid"] for r in selected),
        "correct": sum(r["correct"] for r in selected),
        "flags": [r.get("output", {}).get("act_completed") for r in selected],
    }
    summary["cells"].append(cell)
    label = case["case"] + " / " + case["language"]
    packet.extend(["SOURCE " + label, json.dumps(case["request"]["messages"], ensure_ascii=False)])
    transcript.extend(["## " + label, ""])
    for r in selected:
        output = json.dumps(r.get("output", r.get("error")), ensure_ascii=False, indent=2)
        packet.append(f"DRAW {r['repeat']}\n{output}")
        transcript.extend([f"### Draw {r['repeat']}", "", "```json", output, "```", ""])
(HERE / "runs/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(HERE / "runs/reader-packet.txt").write_text("\n\n".join(packet))
(HERE / "TRANSCRIPTS.md").write_text("\n".join(transcript))
print(json.dumps(summary, indent=2))
