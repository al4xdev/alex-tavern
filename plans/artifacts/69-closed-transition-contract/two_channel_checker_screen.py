"""Frozen source-aware checker with separate positive and correction evidence."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import checker_context_ab_screen as context
import closure_admission_pilot as base
import support_only_checker_screen as support

HERE = Path(__file__).resolve().parent
PREREG = HERE / "TWO-CHANNEL-CHECKER-PREREGISTRATION.md"
MANIFEST = HERE / "two-channel-checker-manifest.json"
RUNS = HERE / "two-channel-checker-runs"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "offer_verdict": {
            "type": "string",
            "enum": ["entailed", "insufficient", "contradicted"],
        },
        "offer_quote": {"type": "string"},
        "source_conflict": {"type": "boolean"},
        "conflict_quote": {"type": "string"},
    },
    "required": ["offer_verdict", "offer_quote", "source_conflict", "conflict_quote"],
    "additionalProperties": False,
}


def cases() -> list[dict[str, Any]]:
    selected = [
        {
            "id": row["base_case"],
            "subject": row["subject"],
            "offered_support": row["source"]["perception_events"],
            "complete_events": row["complete_events"],
            "origin": row["origin"],
            "expected_offer": row["expected_checker"]
            if row["base_case"] != "synthetic_correction"
            else "entailed",
            "expected_conflict": row["base_case"] == "synthetic_correction",
        }
        for row in context.cases()
        if row["arm"] == "full_source"
    ]
    closure = "O portão azul se fecha com um baque."
    selected.append(
        {
            "id": "synthetic_reopen",
            "subject": base.BLUE,
            "offered_support": [closure],
            "complete_events": {
                "perception_events": [
                    closure,
                    "Logo depois, Mirella reabre o portão azul, "
                    "que fica aberto ao fim do intervalo.",
                ],
                "time_skip_summary": "",
            },
            "origin": "synthetic_reopen",
            "expected_offer": "entailed",
            "expected_conflict": False,
        }
    )
    return selected


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Avalie separadamente duas fontes de evidência. (1) offered_support, SOZINHO, "
        "prova que o portão nomeado terminou de fechar neste intervalo? Responda "
        "offer_verdict='entailed' somente se as passagens OFERECIDAS identificam o "
        "portão e narram fechamento concluído; caso contrário insufficient ou "
        "contradicted. Em offer_quote, copie somente trecho literal de "
        "offered_support que prova o positivo; deixe vazio se não houver prova. "
        "(2) complete_events contém uma correção explícita que DESMENTE que o "
        "fechamento oferecido tenha ocorrido? Uma reabertura posterior é outro "
        "evento e NÃO desmente que antes fechou. Responda source_conflict=true SOMENTE "
        "nesse caso, com conflict_quote literal da correção em complete_events; "
        "caso contrário false e conflict_quote vazio. O texto completo não pode "
        "suprir prova faltante em offered_support. Um aviso futuro, portão já "
        "selado ou fechamento de outro portão não prova a alegação. Julgue o que "
        "a proposta AFIRMA, sem estado anterior do mundo. Retorne só JSON conforme: "
        + json.dumps(SCHEMA, ensure_ascii=False)
    )
    user = {
        "subject": case["subject"],
        "claim": "Esta proposta afirma que o portão nomeado terminou de fechar neste intervalo.",
        "offered_support": case["offered_support"],
        "complete_events": case["complete_events"],
    }
    return {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False, indent=2)},
        ],
        "max_tokens": int(cfg["max_tokens_narrator"]),
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def frozen(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**case, "request": request(case, cfg)} for case in cases()]


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "context_script": base.digest(Path(context.__file__)),
        "support_script": base.digest(Path(support.__file__)),
        "base_script": base.digest(Path(base.__file__)),
        "source_manifest": base.digest(context.SOURCE_MANIFEST),
        **{name: base.digest(support.SOURCE_RUNS / name) for name in support.SOURCE_RESULT_NAMES},
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    prepared = frozen(base.config())
    if len(prepared) != 8:
        raise RuntimeError("Expected eight frozen cases")
    for case in prepared:
        if base.ID_PATTERN.search(json.dumps(case["request"], ensure_ascii=False)):
            raise RuntimeError("Internal ID leaked to checker request")
    base.write_json(
        MANIFEST,
        {"hashes": hashes(), "runs_per_case": 4, "schema": SCHEMA, "cases": prepared},
    )
    print("Frozen eight two-channel cases, four calls each")


def literal_in(quote: str, passages: list[str]) -> bool:
    return bool(quote) and any(quote in passage for passage in passages)


async def call_one(case: dict[str, Any], repeat: int, cfg: dict[str, Any]) -> None:
    label = f"{case['id']}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    base.write_json(request_path, case["request"])
    result: dict[str, Any] = {
        "case": case["id"],
        "repeat": repeat,
        "valid": False,
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
    try:
        envelope = cast(dict[str, Any], json.loads(raw_path.read_text(encoding="utf-8")))
        result["response_id"] = envelope.get("id")
        if result["http_status"] != "200" or proc.returncode != 0:
            raise ValueError("HTTP or transport failure")
        parsed = cast(dict[str, Any], json.loads(envelope["choices"][0]["message"]["content"]))
        sys.path.insert(0, str(base.ROOT))
        from src.llm.schema import validate_json_schema

        validate_json_schema(parsed, SCHEMA)
        offer_quote = cast(str, parsed["offer_quote"])
        conflict_quote = cast(str, parsed["conflict_quote"])
        if offer_quote and not literal_in(offer_quote, case["offered_support"]):
            raise ValueError("offer_quote is outside offered_support")
        if parsed["offer_verdict"] == "entailed" and not offer_quote:
            raise ValueError("Positive offer verdict lacks offer_quote")
        if parsed["offer_verdict"] != "entailed" and offer_quote:
            raise ValueError("Negative offer verdict has an offer_quote")
        complete = case["complete_events"]["perception_events"] + (
            [case["complete_events"]["time_skip_summary"]]
            if case["complete_events"]["time_skip_summary"]
            else []
        )
        if parsed["source_conflict"]:
            if not literal_in(conflict_quote, complete):
                raise ValueError("Conflict lacks literal quote from complete source")
        elif conflict_quote:
            raise ValueError("No conflict verdict has a conflict quote")
        result.update(parsed=parsed, valid=True)
    except Exception as exc:  # Preserve every invalid call.
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    if manifest["hashes"] != hashes() or manifest["cases"] != frozen(cfg):
        raise RuntimeError("Frozen source, code or requests changed")
    if manifest["schema"] != SCHEMA or manifest["runs_per_case"] != 4:
        raise RuntimeError("Frozen schema or scope changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await call_one(case, repeat, cfg)

    await asyncio.gather(
        *(limited(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )
    print("Completed exactly 32 frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 32
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 32
        and all(ids)
    )
    by_case: dict[str, Any] = {}
    semantic = True
    for case in manifest["cases"]:
        rows = [row for row in results if row["case"] == case["id"]]
        pairs = [
            [
                row.get("parsed", {}).get("offer_verdict"),
                row.get("parsed", {}).get("source_conflict"),
            ]
            for row in rows
        ]
        matched = len(pairs) == 4 and all(
            (
                pair[0] == "entailed"
                if case["expected_offer"] == "entailed"
                else pair[0] in ("insufficient", "contradicted")
            )
            and pair[1] is case["expected_conflict"]
            for pair in pairs
        )
        semantic &= matched
        by_case[case["id"]] = {
            "expected_offer": case["expected_offer"],
            "expected_conflict": case["expected_conflict"],
            "pairs": pairs,
            "local_match": matched,
        }
    status = (
        "incomplete"
        if not technical
        else ("local_pass_pending_content_read" if semantic else "semantic_fail")
    )
    outcome = {
        "status": status,
        "technical_gate": bool(technical),
        "local_semantic_gate": bool(semantic),
        "valid_count": sum(bool(row.get("valid")) for row in results),
        "cases": by_case,
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
