"""Retained effort labels, flags, raw metadata and blinded source-bound plans."""

import hashlib
import json
import random
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
assert len(rows) == 48
requests = [json.loads(p.read_text()) for p in (HERE / "runs").glob("*.request.json")]
assert all(
    r["model"] == "deepseek-v4-flash"
    and r["thinking"] == {"type": "enabled"}
    and r["reasoning_effort"] in ("minimal", "low", "medium", "high")
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
    "edits, messages, clipboard or delegation. Audience: roleplay developer selecting "
    "working reasoning effort on ambiguous act-completion inputs. Outputs are shuffled, "
    "opaque labeled, no effort labels/expected verdicts/provider reasoning supplied. "
    "Assess source and actual plan, not narrator prose. Identify current objective "
    "contradictions, denial of confirmed closure/location, unestablished PRIOR "
    "possessions/actions and scripted cognitive or voluntary decisions. NEW external "
    "pressures/arrivals/discoveries/reversals and prospective exit targets are allowed. "
    "A new reversal does not erase historical act completion. Physical force is not "
    "automatically voluntary choice. Quote source and output with case/opaque ID; "
    "separate certain contradictions, ambiguities and stylistic impressions. "
    "Return compact concrete findings, at most 1200 words; no invented percentage "
    "or hidden-cognition diagnosis. No inferred arm identities."
]
transcript = ["# Flash effort-label plans", ""]
for case in manifest["cases"]:
    selected = [r for r in rows if r["case"] == case["case"] and r["effort"] == case["effort"]]
    cell = {
        "case": case["case"],
        "effort": case["effort"],
        "expected": case["expected"],
        "valid": sum(r["valid"] for r in selected),
        "correct": sum(r["correct"] for r in selected),
        "flags": [r.get("output", {}).get("act_completed") for r in selected],
    }
    summary["cells"].append(cell)
    transcript.extend(["## " + case["case"] + " / " + case["effort"], ""])
    for r in selected:
        output = json.dumps(r.get("output", r.get("error")), ensure_ascii=False, indent=2)
        transcript.extend([f"### Draw {r['repeat']}", "", "```json", output, "```", ""])

mapping = {}
for name in ("portal_attempt", "portal_closed", "portal_left"):
    source = next(c for c in manifest["cases"] if c["case"] == name)
    packet.extend(["SOURCE " + name, json.dumps(source["request"]["messages"], ensure_ascii=False)])
    selected = [r for r in rows if r["case"] == name]
    random.Random(691008 + len(mapping)).shuffle(selected)
    for r in selected:
        key = "O" + str(len(mapping) + 1).zfill(2)
        mapping[key] = {k: r[k] for k in ("case", "effort", "repeat", "valid")}
        packet.append(key + " " + json.dumps(r.get("output", r.get("error")), ensure_ascii=False))

envelopes = []
for path in (HERE / "runs").glob("*.raw.json"):
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError:
        continue
    if "choices" in raw:
        raw["requested_effort"] = json.loads(
            path.with_name(path.name.replace(".raw.json", ".request.json")).read_text()
        )["reasoning_effort"]
        envelopes.append(raw)
summary["response_models"] = dict(Counter(r.get("model") for r in envelopes))
summary["all_attempt_prompt_tokens"] = sum(
    r.get("usage", {}).get("prompt_tokens", 0) for r in envelopes
)
summary["all_attempt_completion_tokens"] = sum(
    r.get("usage", {}).get("completion_tokens", 0) for r in envelopes
)
summary["labels"] = []
for effort in ("minimal", "low", "medium", "high"):
    subset = [r for r in rows if r["effort"] == effort]
    received = [r for r in envelopes if r["requested_effort"] == effort]
    reason_tokens = [
        r.get("usage", {}).get("completion_tokens_details", {}).get("reasoning_tokens")
        for r in received
    ]
    reason_tokens = [n for n in reason_tokens if n is not None]
    summary["labels"].append(
        {
            "effort": effort,
            "http_envelopes": len(received),
            "reasoning_tokens_median": statistics.median(reason_tokens) if reason_tokens else None,
            "all_completion_tokens": sum(
                r.get("usage", {}).get("completion_tokens", 0) for r in received
            ),
            "valid": sum(r["valid"] for r in subset),
            "correct": sum(r["correct"] for r in subset),
            "wall_median": statistics.median(
                r["wall_seconds"] for r in subset if "wall_seconds" in r
            ),
            "completion_tokens_median": statistics.median(
                r["usage"]["completion_tokens"] for r in subset if r["valid"]
            ),
            "missing_reasoning": [
                r["repeat"] for r in subset if r["valid"] and not r["reasoning_chars"]
            ],
        }
    )
(HERE / "runs/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(HERE / "runs/reader-mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
(HERE / "runs/reader-packet.txt").write_text("\n\n".join(packet))
(HERE / "TRANSCRIPTS.md").write_text("\n".join(transcript))
print(json.dumps(summary, indent=2))
