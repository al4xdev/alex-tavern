"""Controlled complete-transaction audit with isolated causal-target naming."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-audit-source-roles/screen.py"
spec = importlib.util.spec_from_file_location("described_source_audit", BASE)
assert spec is not None and spec.loader is not None
prior: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
transport = prior.transport

import httpx  # noqa: E402

from src.llm.client import chat_completion  # noqa: E402


def cases() -> list[dict[str, Any]]:
    selected = json.loads((HERE / "fixtures.json").read_text())
    for case in selected:
        output_schema = prior.prior.schema(len(case["packet"]["transaction"]["steps"]))
        fields = output_schema["properties"]
        fields["issues"]["description"] = (
            "Every established physical/source-fidelity problem; [] when none is supported."
        )
        fields["issues"]["items"]["properties"]["category"]["description"] = (
            "Extra untyped tracked change/crossing, source/state contradiction, "
            "or lost consequential supported source outcome."
        )
        fields["uncertainties"]["description"] = (
            "Every unresolved identity or claim that affects a physical decision; "
            "[] when no material gap remains."
        )
        case["schema"] = output_schema
    return selected


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        HERE / "fixtures.json",
        HERE / "system.txt",
        BASE,
        prior.BASE,
        prior.prior.BASE,
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def options(case: dict[str, Any]) -> dict[str, Any]:
    result = prior.options(case)
    result["json_schema"]["name"] = "described_source_transaction_audit"
    return result


async def prepare() -> None:
    if transport.MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    captured: list[dict[str, Any]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    selected = cases()
    system = (HERE / "system.txt").read_text().strip()
    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        for case in selected:
            captured.clear()
            await chat_completion(
                client,
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(case["packet"], ensure_ascii=False)},
                ],
                **options(case),
            )
            case["request"] = captured[0]
    original = json.loads((prior.HERE / "manifest.json").read_text())["cases"][0]
    assert selected[0]["request"] == original["request"], "Generic arm request drift"
    changed = json.loads(selected[1]["request"]["messages"][1]["content"])
    changed["source"]["new_causes"]["value"] = selected[0]["packet"]["source"]["new_causes"][
        "value"
    ]
    normalized = json.loads(json.dumps(selected[1]["request"]))
    normalized["messages"][1]["content"] = json.dumps(changed, ensure_ascii=False)
    assert normalized == selected[0]["request"], "More than the registered cause changed"
    transport.write(transport.MANIFEST, {"hashes": hashes(), "cases": selected})
    print("Frozen two causal-target arms; expected labels excluded from requests")


def validate() -> None:
    manifest = json.loads(transport.MANIFEST.read_text())
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    rows = []
    for path in sorted((HERE / "runs").glob("*.result.json")):
        row = json.loads(path.read_text())
        case = next(c for c in manifest["cases"] if c["fixture"]["id"] == row["case"])
        row["provenance_valid"] = False
        if row["accepted"]:
            try:
                prior.prior.provenance(case, row["output"])
                row["provenance_valid"] = True
            except AssertionError:
                row["provenance_error"] = "Decision/evidence quote conditions failed"
            output = row["output"]
            row["status"] = (
                "reject"
                if output["issues"]
                else ("uncertain" if output["uncertainties"] else "accept")
            )
            row["status_match"] = row["status"] in case["fixture"]["expected"]
        rows.append(row)
    transport.write(HERE / "graded-results.json", rows)
    for case in manifest["cases"]:
        selected = [r for r in rows if r["case"] == case["fixture"]["id"]]
        print(
            case["fixture"]["title"],
            "received",
            len(selected),
            "first",
            sum(r["accepted"] and r["attempts"] == 1 for r in selected),
            "terminal",
            sum(r["accepted"] for r in selected),
            "provenance",
            sum(r["provenance_valid"] for r in selected),
            "status",
            sum(r.get("status_match", False) for r in selected),
        )


transport.HERE = HERE
transport.MANIFEST = HERE / "manifest.json"
transport.hashes = hashes
transport.options = options

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "validate"))
    command = parser.parse_args().command
    if command == "validate":
        validate()
    else:
        asyncio.run(prepare() if command == "prepare" else transport.run())
