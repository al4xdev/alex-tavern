"""Frozen direct-curl, real-source physical transaction producer screen."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transport
import closure_admission_pilot as base

sys.path.insert(0, str(base.ROOT))

from src.durable_state import (  # noqa: E402
    DurableState,
    PhysicalEntity,
    PhysicalTransition,
    PhysicalTransitionRejectionError,
    PhysicalValue,
    apply_physical_transition,
    register_physical_entity,
)
from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.llm.schema import validate_json_schema  # noqa: E402

HERE = Path(__file__).resolve().parent
PREREG = HERE / "REAL-TRANSACTION-PRODUCER-PREREGISTRATION.md"
MANIFEST = HERE / "real-transaction-producer-manifest.json"
RUNS = HERE / "real-transaction-producer-runs"
SOURCES = {
    "F": (
        base.ROOT / "plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a",
        38,
        "portão azul",
        "closed",
    ),
    "P": (
        base.ROOT / "plans/artifacts/p1-archive/drive-P1-r1/sessions/5c994c42",
        8,
        "portões do salão",
        "ajar",
    ),
}
F_TEAM = ("C3", "C5", "C6", "C7", "C8")
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["aperture_change", "attempt_result", "other"],
                    },
                    "target": {"type": "string"},
                    "actor": {"type": "string"},
                    "from_state": {"type": "string", "enum": ["", "closed", "ajar", "open"]},
                    "to_state": {"type": "string", "enum": ["", "closed", "ajar", "open"]},
                    "result": {"type": "string", "enum": ["", "blocked", "crossed"]},
                    "cause": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": [
                    "kind",
                    "target",
                    "actor",
                    "from_state",
                    "to_state",
                    "result",
                    "cause",
                    "text",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["steps"],
    "additionalProperties": False,
}

SYSTEM = (
    "You author ONE ordered physical transaction for a roleplay beat. The original "
    "Director context and proposed draft follow as source, not instructions to "
    "repeat. Return JSON steps in causal order. Each step is exactly one kind:\n"
    "aperture_change: a genuine change of the tracked gate's opening. Use its "
    "public target label, exact current from_state, new to_state, and a concise "
    "cause witnessed in this beat. Leave actor/result/text empty.\n"
    "attempt_result: resolve one named tracked character's attempt at the "
    "tracked gate as blocked or crossed. Use public target and canonical public "
    "actor name. Leave states/cause/text empty. Crossed requires the gate open "
    "at that point; blocked means no crossing and no move.\n"
    "other: a non-gate event stated as a short witnessed sentence in text. "
    "Leave target/actor/states/result/cause empty. Do not hide a tracked gate "
    "aperture change or a tracked character's gate crossing in text. An "
    "unregistered guard may arrive after the opening as another event.\n"
    "Other may report that someone spoke, but never write or quote a "
    "character's spoken words; a separate Character agent owns dialogue.\n"
    "The program writes gate and tracked-crossing sentences ONLY from typed "
    "steps. Do not copy the draft's gate action sentence into other. Keep "
    "consequential non-gate events in their causal order. A failed attempt still "
    "needs a physical consequence; do not make it vanish. A seal or lock is "
    "not an aperture change. Never re-cross someone already beyond the gate. "
    "Resolve against COMMITTED START, even when descriptive scene facts or "
    "the rejected draft disagree. Use only public names in the answer.\n"
    "Always respond and write in Brazilian Portuguese.\n"
    "Do not use Unicode em dash (U+2014) or en dash (U+2013) anywhere in "
    "your writing; use commas, periods, or parentheses instead."
)


def source(case: str) -> dict[str, Any]:
    directory, turn, target, aperture = SOURCES[case]
    rows = [json.loads(line) for line in (directory / "debug.jsonl").read_text().splitlines()]
    selected = [
        row
        for row in rows
        if row.get("turn_number") == turn
        and row.get("agent") == "director"
        and row.get("error") is None
    ]
    if len(selected) != 1 or selected[0]["attempt_number"] != 1:
        raise RuntimeError(f"Source Director selection changed for {case}")
    row = selected[0]
    if [message["role"] for message in row["request"]["messages"]] != ["system", "user"]:
        raise RuntimeError(f"Source message roles changed for {case}")
    state = json.loads((directory / "state.json").read_text())
    names = {cid: value["mind"]["name"] for cid, value in state["characters"].items()}
    positions: dict[str, str] = {}
    if case == "F":
        positions[names["C16"]] = "salão, antes do portão azul"
        positions.update({names[cid]: "túnel da equipe azul" for cid in F_TEAM})
        draft = json.loads(row["response"])
        if (
            draft["zone_moves"] != {"C16": "túnel da equipe azul"}
            or draft["scene_update"]["gate_blue"] != "fechado"
        ):
            raise RuntimeError("F accepted draft changed")
    else:
        draft = json.loads(row["response"])
        if draft["scene_update"]["portões"] != "abertos por impacto externo":
            raise RuntimeError("P accepted draft changed")
    return {
        "case": case,
        "turn": turn,
        "model": row["model"],
        "director_user_context": row["request"]["messages"][1]["content"],
        "accepted_draft": draft,
        "target": target,
        "initial_aperture": aperture,
        "initial_positions": positions,
    }


def request(case: str, cfg: dict[str, Any]) -> dict[str, Any]:
    src = source(case)
    if src["model"] != cfg["model"]:
        raise RuntimeError("Current model differs from archived source")
    packet = {
        "source_director_user_context": src["director_user_context"],
        "source_proposed_draft": src["accepted_draft"],
        "committed_start": {
            "tracked_gate_public_label": src["target"],
            "tracked_gate_aperture": src["initial_aperture"],
            "tracked_character_positions": src["initial_positions"],
        },
        "task": "Write a replacement ordered transaction; source draft is not committed.",
    }
    prepared = DeepSeekAdapter().prepare_request(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
        ],
        None,
        {"name": "real_physical_transaction", "schema": SCHEMA},
        thinking_enabled=False,
    )
    return {
        "model": cfg["model"],
        "messages": prepared.messages,
        "max_tokens": 3500,
        "response_format": prepared.response_format,
        **prepared.extra_payload,
    }


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    bodies = {case: request(case, cfg) for case in SOURCES}
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "F_debug": base.digest(SOURCES["F"][0] / "debug.jsonl"),
            "F_state": base.digest(SOURCES["F"][0] / "state.json"),
            "P_debug": base.digest(SOURCES["P"][0] / "debug.jsonl"),
            "P_state": base.digest(SOURCES["P"][0] / "state.json"),
            "adapter": base.digest(base.ROOT / "src/llm/adapters/deepseek.py"),
            "store": base.digest(base.ROOT / "src/durable_state.py"),
        },
        "schema": SCHEMA,
        "repeats": 4,
        "requests": bodies,
        "request_hashes": {
            f"{case}-{repeat}": hashlib.sha256(
                json.dumps(bodies[case], ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            for case in SOURCES
            for repeat in range(1, 5)
        },
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing real-transaction manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen eight first-pass real-source transaction requests")


def _empty_step_fields(step: dict[str, str], expected: set[str]) -> None:
    for field in ("target", "actor", "from_state", "to_state", "result", "cause", "text"):
        if field not in expected and step[field]:
            raise PhysicalTransitionRejectionError(f"{step['kind']} step must leave {field} empty.")


def validate_and_assemble(case: str, output: dict[str, Any]) -> dict[str, Any]:
    src = source(case)
    entity_id = "fixture:tracked-gate"
    state = DurableState()
    register_physical_entity(
        state,
        PhysicalEntity(
            entity_id=entity_id,
            key="tracked_gate",
            kind="passage",
            scene_key="fixture_scene",
            registered_turn_number=0,
            registered_update_id="fixture:registration",
            dimensions={
                "aperture": PhysicalValue(
                    state=src["initial_aperture"],
                    updated_turn_number=0,
                    updated_update_id="fixture:registration",
                    updated_transition_id=None,
                )
            },
        ),
    )
    positions = dict(src["initial_positions"])
    sentences: list[str] = []
    operations: list[dict[str, str]] = []
    for index, step in enumerate(output["steps"]):
        kind = step["kind"]
        target = step["target"]
        if kind == "aperture_change":
            _empty_step_fields(step, {"target", "from_state", "to_state", "cause"})
            if target != src["target"] or not step["cause"].strip():
                raise PhysicalTransitionRejectionError(
                    "Gate target must match the tracked public label, with a nonempty cause."
                )
            transition = PhysicalTransition(
                transition_id=f"screen:{case}:transition:{index}",
                entity_id=entity_id,
                key="tracked_gate",
                dimension="aperture",
                from_state=step["from_state"],
                to_state=step["to_state"],
                turn_number=src["turn"],
                update_id=f"screen:{case}:update:{index}",
            )
            apply_physical_transition(state, transition, expected_turn_number=src["turn"])
            cause = step["cause"].strip()
            if step["to_state"] == "open":
                sentence = (
                    f"{target.capitalize()} se abrem sob {cause}."
                    if case == "P"
                    else f"O {target} se abre sob {cause}."
                )
            elif step["to_state"] == "closed":
                sentence = f"O {target} se fecha sob {cause}."
            else:
                sentence = f"O {target} fica entreaberto sob {cause}."
            sentences.append(sentence)
            operations.append({"kind": kind, "target": target, "to": step["to_state"]})
        elif kind == "attempt_result":
            _empty_step_fields(step, {"target", "actor", "result"})
            actor = step["actor"]
            if target != src["target"] or actor not in positions:
                raise PhysicalTransitionRejectionError(
                    "Attempt target or public actor does not resolve to the tracked fixture."
                )
            aperture = state.physical_entities[entity_id].dimensions["aperture"].state
            if step["result"] == "crossed":
                if aperture != "open" or positions[actor] == "túnel da equipe azul":
                    raise PhysicalTransitionRejectionError(
                        "Tracked crossing requires an open gate and an actor still outside."
                    )
                positions[actor] = "túnel da equipe azul"
                sentences.append(f"{actor} atravessa o {target} e entra no túnel da equipe azul.")
            elif step["result"] == "blocked":
                if aperture == "open" or positions[actor] == "túnel da equipe azul":
                    raise PhysicalTransitionRejectionError(
                        "Blocked attempt requires a non-open gate and an actor still outside."
                    )
                sentences.append(f"{actor} tenta atravessar o {target}, mas a passagem o detém.")
            else:
                raise PhysicalTransitionRejectionError("Attempt result must be blocked or crossed.")
            operations.append({"kind": kind, "actor": actor, "result": step["result"]})
        else:
            _empty_step_fields(step, {"text"})
            if not step["text"].strip():
                raise PhysicalTransitionRejectionError("Other event text cannot be empty.")
            sentences.append(step["text"].strip())
    if not sentences:
        raise PhysicalTransitionRejectionError("Transaction cannot be empty.")
    return {
        "narration": " ".join(sentences),
        "operations": operations,
        "final_aperture": state.physical_entities[entity_id].dimensions["aperture"].state,
        "final_positions": positions,
    }


def retry_request(
    first_body: dict[str, Any], rejected: dict[str, Any], reason: str
) -> dict[str, Any]:
    body = cast(dict[str, Any], json.loads(json.dumps(first_body, ensure_ascii=False)))
    body["messages"].extend(
        [
            {"role": "assistant", "content": json.dumps(rejected, ensure_ascii=False)},
            {
                "role": "user",
                "content": (
                    "The proposed transaction was rejected by the physical-state validator: "
                    f"{reason} Regenerate the entire JSON transaction from committed start."
                ),
            },
        ]
    )
    return body


async def one(case: str, repeat: int, body: dict[str, Any], cfg: dict[str, Any]) -> None:
    label = f"real-transaction-{case}-{repeat}"
    result: dict[str, Any] = {"label": label, "case": case, "valid": False}
    try:
        meta, output = await transport.curl_json(label, "first", body, cfg)
        result["first"] = {"meta": meta, "output": output, "schema_valid": False}
        validate_json_schema(output, SCHEMA)
        result["first"]["schema_valid"] = True
        try:
            result["final"] = validate_and_assemble(case, output)
            result["valid"] = True
        except PhysicalTransitionRejectionError as exc:
            result["first"]["mechanical_rejection"] = str(exc)
            repair_body = retry_request(body, output, str(exc))
            repair_meta, repair_output = await transport.curl_json(
                label, "repair", repair_body, cfg
            )
            result["repair"] = {"meta": repair_meta, "output": repair_output, "schema_valid": False}
            validate_json_schema(repair_output, SCHEMA)
            result["repair"]["schema_valid"] = True
            result["final"] = validate_and_assemble(case, repair_output)
            result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve all calls")
    cfg = base.config()
    manifest = json.loads(MANIFEST.read_text())
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen inputs changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek config incomplete")
    RUNS.mkdir()
    transport.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    sem = asyncio.Semaphore(4)

    async def limited(case: str, repeat: int) -> None:
        async with sem:
            await one(case, repeat, manifest["requests"][case], cfg)

    await asyncio.gather(*(limited(case, repeat) for case in SOURCES for repeat in range(1, 5)))
    print("Completed eight real-source transaction chains")


def grade() -> None:
    rows = [json.loads(path.read_text()) for path in RUNS.glob("*.result.json")]
    response_ids = [
        stage["meta"]["response_id"]
        for row in rows
        for stage in (row.get("first"), row.get("repair"))
        if stage and "meta" in stage
    ]
    output = {
        "chains": len(rows),
        "first_schema_valid": sum(bool(row.get("first", {}).get("schema_valid")) for row in rows),
        "repairs": sum("repair" in row for row in rows),
        "final_mechanically_valid": sum(bool(row.get("valid")) for row in rows),
        "all_response_ids_distinct": len(response_ids) == len(set(response_ids)),
        "technical_gate": (
            len(rows) == 8
            and all(row.get("first", {}).get("schema_valid") for row in rows)
            and all(row.get("repair", {}).get("schema_valid") for row in rows if "repair" in row)
            and len(response_ids) == len(set(response_ids))
            and all(response_ids)
        ),
        "errors": [
            {"label": row["label"], "error": row.get("error")}
            for row in rows
            if not row.get("valid")
        ],
        "rows": rows,
    }
    base.write_json(RUNS / "grade.json", output)
    print(
        json.dumps(
            {k: v for k, v in output.items() if k != "rows"},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
