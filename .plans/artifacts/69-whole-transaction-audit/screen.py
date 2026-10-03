"""Whole transaction diagnosis over controlled sources and injected bypasses."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-coverage-client-boundary/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-controlled-transaction-reasoning"
spec = importlib.util.spec_from_file_location("whole_transaction_transport", BASE)
assert spec is not None and spec.loader is not None
transport: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)

import httpx  # noqa: E402

from src.llm.client import chat_completion  # noqa: E402

SYSTEM = (
    "Audit an entire proposed physical transaction before it reaches narrative consumers. "
    "Resolve against 'source.committed_start' and supported new causes in 'source'. "
    "The source's proposed_beat is uncommitted and may contain impossible outcomes: "
    "do not demand their preservation. Check every claim in all step fields, not only "
    "the typed operations. Tracked portal changes/cast crossings must agree with typed "
    "steps and source; other/cause cannot add extra tracked changes/crossings. "
    "A continuing state observation is not a new transition, and a supporting reference "
    "to the SAME typed event is not an extra event. Unregistered guard entry is allowed "
    "only after the typed opening. Preserve consequential supported events and reported "
    "speech intent without authoring dialogue. Causally independent events can be "
    "reordered unless the source explicitly imposes chronology. Do not bind an "
    "unidentified door to a known portal without evidence. Diagnose all independent "
    "problems, rather than stopping after the first. Return evidence, not a repaired draft."
)


def schema(length: int) -> dict[str, Any]:
    issue_fields = {
        "step_number": {
            "type": "integer",
            "minimum": 0,
            "maximum": length,
            "description": "Position in 'transaction.steps', counted from 1; "
            "0 only when a source event is wholly absent from the transaction.",
        },
        "category": {
            "type": "string",
            "enum": ["untyped_change", "untyped_crossing", "state_conflict", "source_loss"],
            "description": "Kind of supported problem: extra untyped change/crossing, "
            "source/state contradiction, or lost consequential source event.",
        },
        "source_quote": {
            "type": "string",
            "description": "Exact supporting text or field value from 'source'; no paraphrase.",
        },
        "transaction_quote": {
            "type": "string",
            "description": "Exact problematic text or field value in the step addressed by "
            "'step_number'; use '' only when 'step_number' is 0 for a wholly absent event.",
        },
        "reason": {
            "type": "string",
            "description": "Explain how these quotes and the addressed step establish the issue.",
        },
    }
    uncertainty_fields = {
        "step_number": {
            "type": "integer",
            "minimum": 1,
            "maximum": length,
            "description": "Position of the unresolved step in 'transaction.steps', "
            "counted from 1.",
        },
        "quote": {
            "type": "string",
            "description": "Exact ambiguous text in the addressed step.",
        },
        "reason": {
            "type": "string",
            "description": "Explain what missing evidence prevents a decision.",
        },
    }
    fields = {
        "issues": {
            "type": "array",
            "description": "Every supported problem; [] if none is established.",
            "items": {
                "type": "object",
                "properties": issue_fields,
                "required": list(issue_fields),
                "additionalProperties": False,
            },
        },
        "uncertainties": {
            "type": "array",
            "description": "Every unresolved identity/claim; [] if none remains.",
            "items": {
                "type": "object",
                "properties": uncertainty_fields,
                "required": list(uncertainty_fields),
                "additionalProperties": False,
            },
        },
        "can_render": {
            "type": "boolean",
            "description": "true permits this transaction to proceed when 'issues' and "
            "'uncertainties' are both []; false stops it when either field has entries.",
        },
    }
    return {
        "type": "object",
        "properties": fields,
        "required": list(fields),
        "additionalProperties": False,
    }


def cases() -> list[dict[str, Any]]:
    manifest = json.loads((PRIOR / "manifest.json").read_text())

    def pair(case_id: int, output_name: str) -> dict[str, Any]:
        case = next(
            c for c in manifest["cases"] if c["fixture"]["id"] == f"submission{case_id}-high"
        )
        source = json.loads(case["request"]["messages"][1]["content"])
        output = json.loads((PRIOR / "runs" / f"{output_name}.result.json").read_text())["output"]
        return {"source": source, "transaction": output}

    blocked = pair(1, "submission1-high-4")
    hidden = copy.deepcopy(blocked)
    prototype = copy.deepcopy(blocked["transaction"]["steps"][0])
    hidden["transaction"]["steps"].append(
        {**prototype, "text": "O portal azul se abre e Téo atravessa para o túnel."}
    )
    closure = copy.deepcopy(blocked)
    closure["transaction"]["steps"].append(
        {**prototype, "text": "O portal azul se fecha com um baque."}
    )
    opening = pair(2, "submission2-high-2")
    reopening = pair(5, "submission5-high-2")
    hidden_cause = copy.deepcopy(reopening)
    hidden_cause["transaction"]["steps"][0]["cause"] += "; nesse movimento o portal verde se abre"
    independent = pair(4, "submission4-disabled-2")
    source_loss = pair(5, "submission5-disabled-2")
    ambiguous = copy.deepcopy(blocked)
    ambiguous["source"]["facts"] += (
        " Há uma porta sem identificação ao fim do corredor. Não é possível saber "
        "se essa folha pertence a algum dos portais conhecidos ou a outra passagem."
    )
    ambiguous["source"]["proposed_beat"] = (
        "Bento pede que Téo pare de forçar a folha. Iara segura a lanterna acesa. "
        "A porta sem identificação ao fim do corredor se fecha."
    )
    ambiguous["transaction"]["steps"].append(
        {**prototype, "text": "A porta sem identificação ao fim do corredor se fecha."}
    )
    packets = [
        ("blocked_observation", blocked, "accept", "No fresh transition or invented movement."),
        (
            "hidden_open_cross",
            hidden,
            "reject",
            "Diagnose BOTH hidden blue opening and Téo crossing.",
        ),
        ("hidden_reclosure", closure, "reject", "Fresh untyped closure of already closed blue."),
        ("legal_opening", opening, "accept", "Keep legal opening, guard, order and shield."),
        ("new_reopening", reopening, "accept", "Keep new opening then supported Téo crossing."),
        ("hidden_cause", hidden_cause, "reject", "Extra green opening hidden in blue cause."),
        ("independent_order", independent, "accept", "No causal dependency between portals."),
        (
            "source_loss",
            source_loss,
            "reject",
            "Diagnose lost supported passable opening/crossing.",
        ),
        ("ambiguous_door", ambiguous, "uncertain", "No invented portal identity binding."),
    ]
    return [
        {
            "fixture": {
                "id": f"submission{i}-{title}",
                "title": title,
                "expected": expected,
                "obligations": obligations,
            },
            "packet": packet,
        }
        for i, (title, packet, expected, obligations) in enumerate(packets, 1)
    ]


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        PRIOR / "manifest.json",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    names = [
        "submission1-high-4",
        "submission2-high-2",
        "submission5-high-2",
        "submission4-disabled-2",
        "submission5-disabled-2",
    ]
    paths += [PRIOR / "runs" / f"{name}.result.json" for name in names]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def options(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": "deepseek",
        "api_base": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "language": "pt-BR",
        "thinking_enabled": True,
        "max_tokens": 8192,
        "timeout": 180,
        "json_schema": {"name": "whole_transaction_audit", "schema": case["schema"]},
    }


async def prepare() -> None:
    if transport.MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    captured: list[dict[str, Any]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    selected = cases()
    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        for case in selected:
            case["schema"] = schema(len(case["packet"]["transaction"]["steps"]))
            captured.clear()
            await chat_completion(
                client,
                [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(case["packet"], ensure_ascii=False)},
                ],
                **options(case),
            )
            case["request"] = captured[0]
    transport.write(transport.MANIFEST, {"hashes": hashes(), "cases": selected})
    print("Frozen nine complete audit packets; expected labels stay out of requests")


def strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for child in value for s in strings(child)]
    if isinstance(value, dict):
        return list(value) + [s for child in value.values() for s in strings(child)]
    return []


def literal(quote: str, value: Any) -> bool:
    return bool(quote) and (
        quote in json.dumps(value, ensure_ascii=False)
        or any(quote in s for s in strings(value))
    )


def provenance(case: dict[str, Any], output: dict[str, Any]) -> None:
    assert output["can_render"] == (not output["issues"] and not output["uncertainties"])
    steps = case["packet"]["transaction"]["steps"]
    for issue in output["issues"]:
        assert literal(issue["source_quote"], case["packet"]["source"])
        number = issue["step_number"]
        if number == 0:
            assert issue["category"] == "source_loss" and issue["transaction_quote"] == ""
        else:
            assert literal(issue["transaction_quote"], steps[number - 1])
        assert issue["reason"].strip()
    for uncertain in output["uncertainties"]:
        assert literal(uncertain["quote"], steps[uncertain["step_number"] - 1])
        assert uncertain["reason"].strip()


def validate() -> None:
    manifest = json.loads(transport.MANIFEST.read_text())
    rows = []
    for path in sorted((HERE / "runs").glob("*.result.json")):
        row = json.loads(path.read_text())
        case = next(c for c in manifest["cases"] if c["fixture"]["id"] == row["case"])
        row["provenance_valid"] = False
        if row["accepted"]:
            try:
                provenance(case, row["output"])
                row["provenance_valid"] = True
            except AssertionError:
                row["provenance_error"] = "Decision/evidence quote conditions failed"
            output = row["output"]
            row["status"] = (
                "reject"
                if output["issues"]
                else ("uncertain" if output["uncertainties"] else "accept")
            )
            row["status_match"] = row["status"] == case["fixture"]["expected"]
        rows.append(row)
    transport.write(HERE / "graded-results.json", rows)
    for case in manifest["cases"]:
        selected = [r for r in rows if r["case"] == case["fixture"]["id"]]
        print(
            case["fixture"]["title"],
            "accepted",
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
