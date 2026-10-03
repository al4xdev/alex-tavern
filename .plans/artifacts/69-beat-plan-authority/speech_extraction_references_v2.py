"""New authorization run with explicit node citations; frozen extraction reused."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import random
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = HERE / "speech-extraction-v2-manifest.json"
OUT = HERE / "speech-extraction-v2-runs"
spec = importlib.util.spec_from_file_location(
    "extraction_refs", HERE / "speech_extraction_diagnostic.py"
)
assert spec and spec.loader
old: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
baseline = old.baseline
SYSTEM = (
    old.JUDGE
    + """
Citation format: evidence_paths is a list of EXACT JSON Pointer paths from the
schema enum, with initial slash and numeric list indices. A whole list path is
valid evidence: an empty actual_spoken_words list directly establishes absence
of current audible words. Candidate paths can locate an unsupported claim or
establish that a proposal is prospective, but never establish completed speech.
Support realized_speech or authorized_reading for a completed act must be grounded
in the actual completed actor content/history/source outside candidate, not just
the candidate asserting it. An empty evidence list is acceptable for unsupported
when there is no supporting record; state the specific missing evidence in reason.
"""
)


def nodes(value: Any, prefix: str = "") -> dict[str, Any]:
    result = {prefix: value} if prefix else {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(nodes(item, f"{prefix}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.update(nodes(item, f"{prefix}/{index}"))
    return result


async def payload_for(
    case: dict[str, Any], acts: list[dict[str, Any]], arm: str, cfg: dict[str, Any]
) -> dict[str, Any]:
    value = copy.deepcopy(case["input"])
    value["extracted_acts"] = acts
    schema = old.judgment_schema(len(acts))
    schema["schema"]["properties"]["decisions"]["items"]["properties"]["evidence_paths"]["items"][
        "enum"
    ] = list(nodes(case["input"]))
    return {
        "fixture": {"id": case["id"] + "_" + arm},
        "schema": schema["schema"],
        "request": await old.request_for(SYSTEM, value, schema, cfg),
        "agent": "speech_authorization_lab_v2",
        "session_id": case["session_id"],
        "turn_number": 4,
    }


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "SPEECH-EXTRACTION-V2-PREREGISTRATION.md",
        HERE / "speech_extraction_diagnostic.py",
        HERE / "speech-extraction-manifest.json",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    paths.extend(sorted((HERE / "speech-extraction-runs").glob("*_extract-*.result.json")))
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    assert not MANIFEST.exists()
    source = json.loads((HERE / "speech-extraction-manifest.json").read_text())
    cfg = baseline.config()
    calls = []
    for case in source["cases"]:
        for repeat in range(1, 5):
            extracted = json.loads(
                (
                    HERE / "speech-extraction-runs" / f"{case['id']}_extract-{repeat}.result.json"
                ).read_text()
            )
            assert extracted["valid"] and old.verify_acts(case, extracted["output"]["acts"])
            for arm, acts in (
                ("manual", case["manual_acts"]),
                ("automatic", extracted["output"]["acts"]),
            ):
                calls.append(
                    {
                        "case": case["id"],
                        "arm": arm,
                        "repeat": repeat,
                        "input": case["input"],
                        "expected_revision": case["expected_revision"],
                        "acts": acts,
                        "payload": await payload_for(case, acts, arm, cfg),
                    }
                )
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "calls": calls,
            "timeout_seconds": 180,
            "provider": {k: cfg[k] for k in ("model", "language", "api_base")},
        },
    )
    print("Frozen 64 new authorization calls; every original extraction retained, none rerun")


def grade(call: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    row = {
        "case": call["case"],
        "arm": call["arm"],
        "repeat": call["repeat"],
        "valid": result["valid"],
    }
    if not result["valid"]:
        return row
    decisions = result["output"]["decisions"]
    complete = sorted(d["act_index"] for d in decisions) == list(range(len(call["acts"])))
    source_nodes = nodes(call["input"])
    citations_exist = all(path in source_nodes for d in decisions for path in d["evidence_paths"])
    mapping = {d["act_index"]: d for d in decisions}
    revision = any(
        act["status"] == "completed"
        and mapping.get(i, {}).get("support") in ("unsupported", "prospective_only")
        for i, act in enumerate(call["acts"])
    )
    grounded_references = all(
        act["status"] != "completed"
        or mapping.get(i, {}).get("support") not in ("realized_speech", "authorized_reading")
        or any(
            path != "/candidate" and not path.startswith("/candidate/")
            for path in mapping[i]["evidence_paths"]
        )
        for i, act in enumerate(call["acts"])
    )
    row.update(
        {
            "complete_indices": complete,
            "citations_exist": citations_exist,
            "positive_reference_outside_claim": grounded_references,
            "revision": revision,
            "matches_label": complete
            and citations_exist
            and grounded_references
            and revision == call["expected_revision"],
        }
    )
    return row


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes() and not OUT.exists()
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in manifest["provider"].items())
    cfg["llm_timeout_seconds"] = manifest["timeout_seconds"]
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = manifest["calls"][:]
    random.Random(6923).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(call: dict[str, Any]) -> dict[str, Any]:
        async with semaphore:
            payload = call["payload"]
            await baseline.call_one(payload, call["repeat"], cfg)
            label = payload["fixture"]["id"] + "-" + str(call["repeat"])
            result = json.loads((OUT / (label + ".result.json")).read_text())
            baseline.write(
                OUT / (label + ".observability.json"),
                {k: payload[k] for k in ("agent", "session_id", "turn_number")},
            )
        return grade(call, result)

    rows = await asyncio.gather(*(limited(call) for call in jobs))
    baseline.write(HERE / "speech-extraction-v2-grade.json", {"rows": rows})
    print(
        json.dumps(
            {
                "valid": sum(r["valid"] for r in rows),
                "manual_labels": sum(
                    r.get("matches_label", False) for r in rows if r["arm"] == "manual"
                ),
                "automatic_labels": sum(
                    r.get("matches_label", False) for r in rows if r["arm"] == "automatic"
                ),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
