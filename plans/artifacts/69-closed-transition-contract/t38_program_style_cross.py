"""Frozen T38 event-program × archived-style curl screen; no runtime imports."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transport
import closure_admission_pilot as base

sys.path.insert(0, str(base.ROOT))

from src.agents.prose import build_prose_schema  # noqa: E402
from src.llm.schema import validate_json_schema  # noqa: E402

HERE = Path(__file__).resolve().parent
PREREG = HERE / "T38-PROGRAM-STYLE-CROSS-PREREGISTRATION.md"
MANIFEST = HERE / "t38-program-style-cross-manifest.json"
RUNS = HERE / "t38-program-style-cross-runs"
SOURCE = base.ROOT / "plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a"
DEBUG_HASH = "03aef5776ce1565352f1c526ee4c7b17909b3f873ac57cda06704c2f68f1f187"
STATE_HASH = "c66b438dfb62452153ea9b9c0c841baae366424245b07c7d85eb513caab06302"
CASES = ("S38", "S39", "L38", "L39")

SCENE = {
    "place": "Salão dos Quatro Arcos, Academia Real do Primeiro Sino",
    "observer": "pessoas no salão, diante do portão azul",
    "static_objects": [
        "piso de pedra branca",
        "lâmpadas de mana sem chama",
        "arquibancadas",
        "portão azul de folhas metálicas",
        "portão verde selado, separado do azul",
        "túnel da equipe azul atrás do portão azul",
    ],
    "known_prior": [
        "a equipe azul entrou no túnel antes deste beat",
        "Téo Ventobravo estava no salão antes deste beat",
    ],
    "present_actor": "Téo Ventobravo",
    "tracked_gate": "portão azul",
}

PROGRAMS = {
    "S": {
        "initial": {"blue_aperture": "closed", "teo_zone": "hall", "blue_team_zone": "tunnel"},
        "ordered_events": [
            {
                "op": "attempt_cross",
                "actor": "Téo Ventobravo",
                "gate": "portão azul",
                "outcome": "blocked",
                "gate_delta": "none",
                "actor_zone_after": "hall",
            },
        ],
        "final": {"blue_aperture": "closed", "teo_zone": "hall", "blue_team_zone": "tunnel"},
        "forbidden": ["new gate closure", "gate opening", "Téo crossing", "blue team re-crossing"],
    },
    "L": {
        "initial": {"blue_aperture": "ajar", "teo_zone": "hall", "blue_team_zone": "tunnel"},
        "ordered_events": [
            {
                "op": "cross",
                "actor": "Téo Ventobravo",
                "gate": "portão azul",
                "actor_zone_before": "hall",
                "actor_zone_after": "tunnel",
            },
            {
                "op": "close_gate",
                "gate": "portão azul",
                "mechanism": "automatic",
                "aperture_before": "ajar",
                "aperture_after": "closed",
            },
        ],
        "final": {"blue_aperture": "closed", "teo_zone": "tunnel", "blue_team_zone": "tunnel"},
        "forbidden": [
            "gate closes before Téo crosses",
            "Téo stays in hall",
            "blue team re-crossing",
        ],
    },
}

SCHEMA = build_prose_schema()["schema"]
SYSTEM = (
    "Você realiza um programa fechado de eventos em prosa narrativa para RPG. "
    "O campo PROGRAMA é a única autoridade sobre acontecimentos físicos, "
    "ordem, resultado e lugares neste beat. A REFERÊNCIA mostra apenas ritmo e "
    "dicção: não copie dela fatos, sons de ações, movimentos, personagens ou "
    "causas que não constem do PROGRAMA. Fatos prévios podem ser lembrados como "
    "passado, nunca executados novamente. Estado imóvel não produz som de nova "
    "mudança. Uma tentativa bloqueada não é travessia. Fatos de pessoas fora "
    "da visão podem ser lembrados, mas suas ações presentes não são visíveis. "
    "Escreva prosa brasileira acabada e fluente, com cadência e detalhes "
    "sensoriais apenas dos fatos estáticos ou eventos autorizados; não transforme "
    "a lista em relatório. Não invente ação, estado, efeito, diálogo ou causa. "
    "Não use travessão nem meia-risca. Responda apenas JSON com narration "
    "conforme este esquema: " + json.dumps(SCHEMA, ensure_ascii=False, separators=(",", ":"))
)


def source_references() -> dict[str, str]:
    if base.digest(SOURCE / "debug.jsonl") != DEBUG_HASH:
        raise RuntimeError("Archived T38 debug source changed")
    if base.digest(SOURCE / "state.json") != STATE_HASH:
        raise RuntimeError("Archived T38 state source changed")
    state = json.loads((SOURCE / "state.json").read_text(encoding="utf-8"))
    return {
        str(turn): next(
            record["content"]
            for record in state["history"]
            if record["turn_number"] == turn
            and record["speaker"] == "Narrator"
            and record["content_type"] == "narration"
        )
        for turn in (38, 39)
    }


def request(case: str, refs: dict[str, str], cfg: dict[str, Any]) -> dict[str, Any]:
    program = PROGRAMS[case[0]]
    reference = refs[case[1:]]
    user = (
        "REFERÊNCIA DE ESTILO, SEM AUTORIDADE FACTUAL:\n"
        + reference
        + "\n\nPROGRAMA AUTORITATIVO DESTE BEAT:\n"
        + json.dumps({"scene": SCENE, "program": program}, ensure_ascii=False)
    )
    return {
        "model": cfg["model"],
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    refs = source_references()
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "debug": base.digest(SOURCE / "debug.jsonl"),
            "state": base.digest(SOURCE / "state.json"),
        },
        "schema": SCHEMA,
        "runs_per_case": 4,
        "cases": list(CASES),
        "requests": {case: request(case, refs, cfg) for case in CASES},
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen 2×2 realizer screen: 16 requests")


async def one(case: str, repeat: int, request_body: dict[str, Any], cfg: dict[str, Any]) -> None:
    label = f"program-style-{case}-{repeat}"
    result: dict[str, Any] = {"case": case, "repeat": repeat, "valid": False}
    try:
        meta, output = await transport.curl_json(label, "prose", request_body, cfg)
        result.update(meta=meta, output=output)
        validate_json_schema(output, SCHEMA)
        if not output["narration"].strip():
            raise ValueError("Empty narration")
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing calls")
    cfg = base.config()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen source, script, prereg or requests changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    transport.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(case: str, repeat: int) -> None:
        async with semaphore:
            await one(case, repeat, manifest["requests"][case], cfg)

    await asyncio.gather(*(limited(case, repeat) for case in CASES for repeat in range(1, 5)))
    print("Completed 16 frozen event-program × style curls")


def grade() -> None:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    outcome = {
        "calls": len(rows),
        "technical_gate": (
            len(rows) == 16
            and all(row.get("valid") for row in rows)
            and all(ids)
            and len(set(ids)) == len(ids)
        ),
        "by_case": {
            case: {
                "valid": sum(bool(row.get("valid")) for row in rows if row["case"] == case),
                "errors": [
                    {"repeat": row["repeat"], "error": row.get("error")}
                    for row in rows
                    if row["case"] == case and not row.get("valid")
                ],
            }
            for case in CASES
        },
    }
    base.write_json(RUNS / "grade.json", outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
