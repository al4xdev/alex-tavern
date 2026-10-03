"""Frozen counterfactual gate-transaction and production prose-builder screen."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base

HERE = Path(__file__).resolve().parent
PREREG = HERE / "AUTHORITATIVE-TRANSACTION-PREREGISTRATION.md"
CASES = HERE / "AUTHORITATIVE-TRANSACTION-CASES.json"
MANIFEST = HERE / "authoritative-transaction-manifest.json"
RUNS = HERE / "authoritative-transaction-runs"

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ordered_events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["open", "close", "cross", "observation"],
                    },
                    "gate_name": {"type": "string", "enum": ["portão azul"]},
                    "subject_name": {"type": "string", "enum": ["", "Liora Celestria"]},
                    "content": {"type": "string"},
                },
                "required": ["kind", "gate_name", "subject_name", "content"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ordered_events"],
    "additionalProperties": False,
}

SYSTEM = (
    "Você é o Diretor físico de uma cena de ficção. Decida a sequência de "
    "acontecimentos deste beat sem escrever prosa final. A resposta JSON tem "
    "ordered_events em ordem temporal. open e close movem a ABERTURA do "
    "portão; cross significa que Liora Celestria cruzou inteiramente do salão "
    "para o túnel. Um portão fechado impede cross até um open anterior. "
    "Gelo que já sela o portão é uma propriedade separada da abertura; "
    "verificar ou manter esse gelo não é close. Uma tentativa bloqueada não "
    "é cross. Para open, close e cross, content deve ser string vazia: o "
    "programa escreverá o evento físico a partir do tipo. Para observation, "
    "content deve descrever apenas sensação, reação ou tentativa sem mudança "
    "da abertura ou do lado do portão; nunca esconda outra abertura, fechamento ou "
    "travessia nesse campo. gate_name é sempre 'portão azul'. subject_name é "
    "'Liora Celestria' apenas para cross e vazio nos demais. Use somente nomes "
    "públicos. Responda só JSON conforme: "
    + json.dumps(SCHEMA, ensure_ascii=False, separators=(",", ":"))
)


def cases() -> list[dict[str, Any]]:
    selected = cast(list[dict[str, Any]], json.loads(CASES.read_text(encoding="utf-8")))
    if [case["id"] for case in selected] != [
        "closed_blocked",
        "open_cross",
        "reopen_cross",
        "seal_maintenance",
    ]:
        raise RuntimeError("Case order or names changed")
    return selected


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    user = {
        "place": "Salão dos Quatro Arcos e túnel da equipe azul",
        "gate": "portão azul",
        "initial_aperture": case["initial_aperture"],
        "initial_positions": case["initial_positions"],
        "initial_ice_seal": case["initial_ice_seal"],
        "beat_request": case["beat_request"],
    }
    return {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def hashes() -> dict[str, str]:
    sys.path.insert(0, str(base.ROOT))
    from src.agents import prose

    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "cases": base.digest(CASES),
        "base_script": base.digest(Path(base.__file__)),
        "prose_builder": base.digest(Path(prose.__file__)),
    }


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "hashes": hashes(),
        "schema": SCHEMA,
        "runs_per_case": 4,
        "cases": cases(),
        "requests": {case["id"]: request(case, cfg) for case in cases()},
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen four counterfactual cases and 16 Director requests")


async def curl_json(
    label: str, stage: str, request_body: dict[str, Any], cfg: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    request_path = RUNS / f"{label}.{stage}.request.json"
    raw_path = RUNS / f"{label}.{stage}.raw.json"
    base.write_json(request_path, request_body)
    result: dict[str, Any] = {
        "request_sha256": base.digest(request_path),
        "raw_file": raw_path.name,
    }
    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-q",
        "--silent",
        "--show-error",
        "--max-time",
        str(cfg["llm_timeout_seconds"]),
        "--config",
        "-",
        "--request",
        "POST",
        "--header",
        "Content-Type: application/json",
        "--data-binary",
        f"@{request_path}",
        "--output",
        str(raw_path),
        "--write-out",
        "%{http_code}",
        f"{cfg['api_base'].rstrip('/')}/chat/completions",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    started = time.monotonic()
    stdout, stderr = await proc.communicate(base.curl_config(cast(str, cfg["api_key"])))
    result.update(
        http_status=stdout.decode().strip(),
        curl_returncode=proc.returncode,
        duration_ms=round((time.monotonic() - started) * 1000),
        stderr=stderr.decode().replace(cast(str, cfg["api_key"]), "[REDACTED]").strip(),
    )
    if result["http_status"] != "200" or proc.returncode != 0:
        raise ValueError(f"HTTP/transport failure: {result}")
    envelope = cast(dict[str, Any], json.loads(raw_path.read_text(encoding="utf-8")))
    result["response_id"] = envelope.get("id")
    output = cast(dict[str, Any], json.loads(envelope["choices"][0]["message"]["content"]))
    return result, output


def derive(case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(base.ROOT))
    from src.llm.schema import validate_json_schema

    validate_json_schema(output, SCHEMA)
    aperture = cast(str, case["initial_aperture"])
    side = cast(str, case["initial_positions"]["Liora Celestria"])
    operations: list[dict[str, str]] = []
    observations = 0
    events: list[dict[str, Any]] = []
    for item in output["ordered_events"]:
        kind = item["kind"]
        subject = item["subject_name"]
        content = item["content"]
        if kind == "observation":
            if subject or not content.strip():
                raise ValueError("Observation subject must be empty and content nonempty")
            observations += 1
            event_text = content
            event_kind = "observation"
            subject_id = ""
        else:
            if content or subject != ("Liora Celestria" if kind == "cross" else ""):
                raise ValueError("Physical item has content or wrong crossing subject")
            operations.append(
                {"kind": kind, "gate_name": item["gate_name"], "subject_name": subject}
            )
            event_kind = "physical_outcome"
            subject_id = "C2" if kind == "cross" else ""
            if kind == "open":
                if aperture != "closed":
                    raise ValueError("Open on non-closed aperture")
                aperture = "open"
                event_text = "O portão azul se abre, liberando a passagem entre salão e túnel."
            elif kind == "close":
                if aperture != "open":
                    raise ValueError("Close on non-open aperture")
                aperture = "closed"
                event_text = "O portão azul se fecha, bloqueando a passagem entre salão e túnel."
            else:
                if aperture != "open" or side != "salon":
                    raise ValueError("Crossing blocked or duplicate")
                side = "tunnel"
                event_text = "Liora Celestria atravessa o portão azul e entra no túnel."
        events.append(
            {
                "event_kind": event_kind,
                "subject_id": subject_id,
                "content": event_text,
                "witness_ids": ["C1", "C2", "C3", "C4"],
            }
        )
    if operations != case["expected_operations"]:
        raise ValueError(f"Operation sequence {operations} != {case['expected_operations']}")
    if observations < case["min_observations"]:
        raise ValueError("Required observation missing")
    return {
        "aperture": aperture,
        "liora_side": side,
        "ice_seal": case["initial_ice_seal"],
        "operations": operations,
        "events": events,
    }


def prose_request(derived: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(base.ROOT))
    from src.agents.prose import build_prose_messages
    from src.models import Character, CharacterBody, CharacterMind, Scene

    names = {"C1": "Link", "C2": "Liora Celestria", "C3": "Garran Holt", "C4": "Mirella Valecourt"}
    characters = {
        cid: Character(
            mind=CharacterMind(name=name, personality="", knowledge=[], current_mood="alerta"),
            body=CharacterBody(
                name=name, physical_description="pessoa na cena", outfit="roupas comuns"
            ),
        )
        for cid, name in names.items()
    }
    positions = {"C1": "salon", "C2": derived["liora_side"], "C3": "salon", "C4": "salon"}
    scene = Scene(
        location="Salão dos Quatro Arcos, junto ao portão azul",
        time_of_day="manhã",
        present_characters=list(names),
        physical_facts={
            "portão azul": derived["aperture"],
            "selo de gelo": derived["ice_seal"],
        },
        zones={"salon": ["tunnel"], "tunnel": ["salon"]},
        positions=positions,
    )
    viewers = {cid for cid, zone in positions.items() if zone == "salon"}
    messages = build_prose_messages(
        scene, characters, "C1", [], derived["events"], viewers=viewers, max_tokens=1024
    )
    return {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


async def run_one(
    case: dict[str, Any], repeat: int, director_request: dict[str, Any], cfg: dict[str, Any]
) -> None:
    label = f"{case['id']}-{repeat}"
    result: dict[str, Any] = {"case": case["id"], "repeat": repeat, "valid": False}
    try:
        director_meta, director_output = await curl_json(label, "director", director_request, cfg)
        result["director"] = {**director_meta, "output": director_output}
        derived = derive(case, director_output)
        result["derived"] = derived
        request_body = prose_request(derived, cfg)
        prose_meta, prose_output = await curl_json(label, "prose", request_body, cfg)
        sys.path.insert(0, str(base.ROOT))
        from src.agents.prose import build_prose_schema
        from src.llm.schema import validate_json_schema

        validate_json_schema(prose_output, build_prose_schema()["schema"])
        result["prose"] = {**prose_meta, "output": prose_output}
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    cfg = base.config()
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen inputs changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    sem = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with sem:
            await run_one(case, repeat, manifest["requests"][case["id"]], cfg)

    await asyncio.gather(*(limited(case, repeat) for case in cases() for repeat in range(1, 5)))
    print("Completed 16 frozen Director calls and any eligible prose calls")


def grade() -> None:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    director_ids = [row.get("director", {}).get("response_id") for row in results]
    prose_ids = [row.get("prose", {}).get("response_id") for row in results]
    technical = (
        len(results) == 16
        and all(row.get("valid") for row in results)
        and all(director_ids)
        and all(prose_ids)
        and len(set(director_ids + prose_ids)) == 32
    )
    outcome = {
        "technical_gate": bool(technical),
        "director_valid_count": sum(bool(row.get("director")) for row in results),
        "prose_valid_count": sum(bool(row.get("prose")) for row in results),
        "full_valid_count": sum(bool(row.get("valid")) for row in results),
        "status": "content_read_pending" if technical else "incomplete",
        "errors": [
            {"case": row["case"], "repeat": row["repeat"], "error": row.get("error")}
            for row in results
            if not row.get("valid")
        ],
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
