"""Controlled producer screen with an isolated reasoning ablation."""

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
BASE = ROOT / ".plans/artifacts/69-coverage-client-boundary/screen.py"
spec = importlib.util.spec_from_file_location("transaction_client_transport", BASE)
assert spec is not None and spec.loader is not None
transport: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)

import httpx  # noqa: E402

from src.durable_state import (  # noqa: E402
    DurableState,
    PhysicalEntity,
    PhysicalTransition,
    PhysicalTransitionRejectionError,
    PhysicalValue,
    apply_physical_transition,
    register_physical_entity,
)
from src.llm.client import chat_completion  # noqa: E402

NAMES = ["Iara", "Bento", "Téo"]
TARGETS = ["portal azul", "portal verde"]
FIELDS: dict[str, Any] = {
    "kind": {
        "type": "string",
        "enum": ["aperture_change", "attempt_result", "other"],
        "description": "Use 'aperture_change' for a tracked portal aperture change, "
        "'attempt_result' for a tracked character's declared crossing attempt, "
        "and 'other' for remaining events. No tracked change/crossing may occur in 'other'.",
    },
    "target": {
        "type": "string",
        "enum": ["", *TARGETS],
        "description": "Portal addressed by 'aperture_change' or 'attempt_result'; "
        "use '' for 'other'.",
    },
    "actor": {
        "type": "string",
        "enum": ["", *NAMES],
        "description": "Character resolving a declared attempt in 'attempt_result'; otherwise ''.",
    },
    "from_state": {
        "type": "string",
        "enum": ["", "closed", "ajar", "open"],
        "description": "For 'aperture_change', the current state of 'target' before this step; "
        "otherwise ''.",
    },
    "to_state": {
        "type": "string",
        "enum": ["", "closed", "ajar", "open"],
        "description": "For 'aperture_change', the new state of 'target', different from "
        "'from_state'; otherwise ''.",
    },
    "result": {
        "type": "string",
        "enum": ["", "blocked", "crossed"],
        "description": "For 'attempt_result', 'blocked' keeps 'actor' on their starting side; "
        "'crossed' moves them through 'target' only when open. Otherwise ''.",
    },
    "cause": {
        "type": "string",
        "description": "For 'aperture_change', the witnessed cause supported by "
        "'proposed_beat'; otherwise ''. Do not invent a cause to rescue an illegal draft.",
    },
    "text": {
        "type": "string",
        "description": "For 'other', a remaining witnessed event or reported speech intent "
        "without quoted/authored dialogue. It may include an unregistered guard's entry "
        "after opening, but no tracked aperture change/crossing. Otherwise ''.",
    },
}
SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "description": "The entire corrected beat, in causal order.",
            "items": {
                "type": "object",
                "properties": FIELDS,
                "required": list(FIELDS),
                "additionalProperties": False,
            },
        }
    },
    "required": ["steps"],
    "additionalProperties": False,
}
SYSTEM = (
    "Convert a proposed roleplay beat into one ordered physical transaction. "
    "Resolve against 'committed_start': 'proposed_beat' has not happened yet and "
    "may contradict that start. Correct illegal physical proposals without losing "
    "the remaining consequential events. Preserve character choices and causal order. "
    "A starting ajar gap is too narrow for a person to cross. "
    "Do not repeat a passage already completed, invent new choices/causes "
    "or omit a declared attempt."
)


def fixtures() -> list[dict[str, Any]]:
    hall = dict.fromkeys(NAMES, "salão")
    base = {"portal azul": "closed", "portal verde": "closed"}
    return [
        {
            "id": 1,
            "title": "ineffective_push",
            "apertures": base,
            "positions": hall,
            "declared_attempts": [{"actor": "Téo", "target": "portal azul"}],
            "facts": "A pesada barra azul não cede à força de Téo. Não há nova causa de abertura.",
            "proposed_beat": "O portal azul se fecha novamente. Téo passa ao túnel. "
            "Bento pede que Téo pare de forçar a folha. Iara segura a lanterna acesa.",
            "obligations": "Nenhuma mudança de abertura; Téo bloqueado no salão; "
            "preservar aviso de Bento e suporte da lanterna de Iara.",
        },
        {
            "id": 2,
            "title": "legal_external_opening",
            "apertures": {**base, "portal azul": "ajar"},
            "positions": hall,
            "declared_attempts": [],
            "facts": "Um impacto externo é suficiente para abrir a folha azul.",
            "proposed_beat": "O impacto abre o portal azul. Um guarda ferido entra pela abertura "
            "e cai de joelhos, desfalecendo. Bento pede que mantenham a entrada livre. "
            "Iara apoia o escudo para proteger o guarda dos destroços.",
            "obligations": "Azul ajar->open antes da entrada/desmaio do guarda; "
            "reter ordem de Bento e apoio do escudo de Iara.",
        },
        {
            "id": 3,
            "title": "already_beyond",
            "apertures": base,
            "positions": {"Iara": "túnel", "Bento": "túnel", "Téo": "salão"},
            "declared_attempts": [{"actor": "Téo", "target": "portal azul"}],
            "facts": "Iara e Bento já atravessaram antes; a barra azul não cede ao empurrão "
            "de Téo. Não há nova causa de abertura.",
            "proposed_beat": "Iara, Bento e Téo passam pelo portal azul, que se fecha de novo. "
            "Iara reacomoda a mochila no túnel.",
            "obligations": "Téo bloqueado no salão; Iara/Bento continuam no túnel sem nova "
            "travessia; azul permanece fechado; preservar ajuste da mochila.",
        },
        {
            "id": 4,
            "title": "different_portal",
            "apertures": {**base, "portal verde": "ajar"},
            "positions": hall,
            "declared_attempts": [{"actor": "Téo", "target": "portal azul"}],
            "facts": "O vento tem força suficiente para abrir a folha verde; a barra azul "
            "não cede ao empurrão de Téo.",
            "proposed_beat": "Uma rajada abre o portal verde. Téo atravessa o portal azul, "
            "que se fecha novamente. Bento afasta a lanterna da água que pinga do teto.",
            "obligations": "Verde ajar->open, azul continua closed; tentativa azul de Téo "
            "bloqueada; preservar afastamento da lanterna de Bento.",
        },
        {
            "id": 5,
            "title": "new_reopening",
            "apertures": base,
            "positions": {"Iara": "túnel", "Bento": "salão", "Téo": "salão"},
            "declared_attempts": [{"actor": "Téo", "target": "portal azul"}],
            "facts": "O azul foi fechado em um turno anterior. Agora Bento retira a barra "
            "e puxa a folha: intervenção nova suficiente para abrir a passagem.",
            "proposed_beat": "Bento retira a barra e puxa a folha, abrindo o portal azul. "
            "Téo atravessa para o túnel. Iara mantém a lanterna acesa no túnel.",
            "obligations": "Azul closed->open após intervenção nova de Bento; "
            "travessia declarada de Téo após abertura; preservar lanterna de Iara, já no túnel.",
        },
    ]


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        ROOT / "src/durable_state.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/llm/schema.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def options(case: dict[str, Any]) -> dict[str, Any]:
    body = case["request"]
    return {
        "provider": "deepseek",
        "api_base": "https://api.deepseek.com",
        "model": body["model"],
        "language": "pt-BR",
        "thinking_enabled": body["thinking"]["type"] == "enabled",
        "max_tokens": 8192,
        "timeout": 180,
        "json_schema": {"name": "physical_transaction", "schema": SCHEMA},
    }


async def prepare() -> None:
    if transport.MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    captured: list[dict[str, Any]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    cases = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        for fixture in fixtures():
            source = {
                "committed_start": {
                    "apertures": fixture["apertures"],
                    "positions": fixture["positions"],
                },
                "facts": fixture["facts"],
                "declared_attempts": fixture["declared_attempts"],
                "proposed_beat": fixture["proposed_beat"],
            }
            for arm in ("disabled", "high"):
                captured.clear()
                await chat_completion(
                    client,
                    [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": json.dumps(source, ensure_ascii=False)},
                    ],
                    provider="deepseek",
                    api_base="https://api.deepseek.com",
                    model="deepseek-v4-flash",
                    language="pt-BR",
                    max_tokens=8192,
                    thinking_enabled=arm == "high",
                    json_schema={"name": "physical_transaction", "schema": SCHEMA},
                )
                cases.append(
                    {
                        "fixture": {**fixture, "id": f"submission{fixture['id']}-{arm}"},
                        "arm": arm,
                        "request": captured[0],
                        "schema": SCHEMA,
                    }
                )
    for index in range(0, len(cases), 2):
        a, b = (cases[index + i]["request"] for i in (0, 1))
        assert a["messages"] == b["messages"] and a["max_tokens"] == b["max_tokens"]
        assert {k: v for k, v in a.items() if k not in {"thinking", "reasoning_effort"}} == {
            k: v for k, v in b.items() if k not in {"thinking", "reasoning_effort"}
        }
    transport.write(transport.MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen five controlled fixtures, two thinking arms, forty logical calls")


def mechanical(fixture: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    state = DurableState()
    for target, value in fixture["apertures"].items():
        register_physical_entity(
            state,
            PhysicalEntity(
                entity_id=f"fixture:{target}",
                key=target,
                kind="passage",
                scene_key="fixture",
                registered_turn_number=0,
                registered_update_id="fixture:register",
                dimensions={"aperture": PhysicalValue(value, 0, "fixture:register", None)},
            ),
        )
    positions = dict(fixture["positions"])
    attempts = {(a["actor"], a["target"]) for a in fixture["declared_attempts"]}
    resolved: set[tuple[str, str]] = set()
    used = {
        "aperture_change": {"target", "from_state", "to_state", "cause"},
        "attempt_result": {"target", "actor", "result"},
        "other": {"text"},
    }
    for index, step in enumerate(output["steps"]):
        kind = step["kind"]
        if any(step[k] for k in FIELDS if k != "kind" and k not in used[kind]):
            raise PhysicalTransitionRejectionError("Irrelevant step fields must be empty")
        if any(not step[k].strip() for k in used[kind]):
            raise PhysicalTransitionRejectionError("Relevant step fields must be nonempty")
        if kind == "aperture_change":
            target = step["target"]
            apply_physical_transition(
                state,
                PhysicalTransition(
                    transition_id=f"fixture:transition:{index}",
                    entity_id=f"fixture:{target}",
                    key=target,
                    dimension="aperture",
                    from_state=step["from_state"],
                    to_state=step["to_state"],
                    turn_number=1,
                    update_id=f"fixture:update:{index}",
                ),
                expected_turn_number=1,
            )
        elif kind == "attempt_result":
            actor, target = step["actor"], step["target"]
            pair = (actor, target)
            if pair not in attempts or pair in resolved or positions[actor] != "salão":
                raise PhysicalTransitionRejectionError(
                    "Unknown, repeated or already-completed attempt"
                )
            aperture = state.physical_entities[f"fixture:{target}"].dimensions["aperture"].state
            if step["result"] == "crossed":
                if aperture != "open":
                    raise PhysicalTransitionRejectionError("Crossing requires an open aperture")
                positions[actor] = "túnel" if target == "portal azul" else "pátio"
            elif aperture == "open":
                raise PhysicalTransitionRejectionError(
                    "Fixture blocking is not supported at open aperture"
                )
            resolved.add(pair)
    if resolved != attempts:
        raise PhysicalTransitionRejectionError("Declared attempts not fully resolved")
    return {
        "apertures": {
            e.key: e.dimensions["aperture"].state for e in state.physical_entities.values()
        },
        "positions": positions,
    }


def validate() -> None:
    manifest = json.loads(transport.MANIFEST.read_text())
    rows = []
    for path in sorted((HERE / "runs").glob("*.result.json")):
        row = json.loads(path.read_text())
        case = next(c for c in manifest["cases"] if c["fixture"]["id"] == row["case"])
        row["mechanical"] = False
        if row["accepted"]:
            try:
                row["final_state"] = mechanical(case["fixture"], row["output"])
                row["mechanical"] = True
            except PhysicalTransitionRejectionError as error:
                row["mechanical_error"] = str(error)
        rows.append(row)
    transport.write(HERE / "mechanical-results.json", rows)
    for case in manifest["cases"]:
        selected = [r for r in rows if r["case"] == case["fixture"]["id"]]
        print(
            case["fixture"]["title"],
            case["arm"],
            "accepted",
            sum(r["accepted"] for r in selected),
            "mechanical",
            sum(r["mechanical"] for r in selected),
            "attempts",
            sum(r["attempts"] for r in selected),
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
