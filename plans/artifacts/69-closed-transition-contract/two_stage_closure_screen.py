"""Frozen independent offered-evidence and source-retraction model calls."""

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
PREREG = HERE / "TWO-STAGE-CLOSURE-PREREGISTRATION.md"
MANIFEST = HERE / "two-stage-closure-v2-manifest.json"
RUNS = HERE / "two-stage-closure-v2-runs"
BARE_RESULT = HERE / "closure-admission-runs/t37_blue-extractor-3.result.json"
STAGE_A_SCHEMA = base.SCHEMAS["checker"]
STAGE_B_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "retracted": {"type": "boolean"},
        "evidence_quote": {"type": "string"},
    },
    "required": ["retracted", "evidence_quote"],
    "additionalProperties": False,
}
COMMON = "O portão azul se fecha com um baque."
CORRECTION = (
    "Correção do narrador: o baque veio da dobradiça, e o portão azul "
    "permaneceu aberto durante todo este intervalo; não chegou a se fechar."
)
REOPEN = "Logo depois, Mirella reabre o portão azul, que fica aberto ao fim do intervalo."


def source_cases() -> list[dict[str, Any]]:
    src = base.source_events()
    bare_row = cast(dict[str, Any], json.loads(BARE_RESULT.read_text(encoding="utf-8")))
    if not bare_row["valid"]:
        raise RuntimeError("Frozen bare T37 source output is invalid")
    bare = cast(list[str], bare_row["parsed"]["support"])
    if bare != ["o portão se fecha com um baque surdo"]:
        raise RuntimeError("Bare T37 quote changed")
    stage_a = [
        ("t38_explicit", base.BLUE, [src[38]["perception_events"][1]], "entailed", "archived"),
        ("t37_bare", base.BLUE, bare, "not_entailed", "archived_output"),
        (
            "t37_with_antecedent",
            base.BLUE,
            [src[37]["perception_events"][1], src[37]["time_skip_summary"]],
            "not_entailed",
            "archived",
        ),
        ("t36_future", base.BLUE, [src[36]["perception_events"][0]], "not_entailed", "archived"),
        ("t38_weak", base.BLUE, [src[38]["perception_events"][2]], "not_entailed", "archived"),
        ("wrong_target", base.GREEN, [src[38]["perception_events"][1]], "not_entailed", "archived"),
        ("synthetic_common", base.BLUE, [COMMON], "entailed", "synthetic"),
    ]
    synthetic_plain = {"perception_events": [COMMON], "time_skip_summary": ""}
    synthetic_correction = {"perception_events": [COMMON, CORRECTION], "time_skip_summary": ""}
    synthetic_reopen = {"perception_events": [COMMON, REOPEN], "time_skip_summary": ""}
    stage_b = [
        ("t38_source", base.BLUE, src[38], False, "archived"),
        ("t37_source", base.BLUE, src[37], False, "archived"),
        ("t36_source", base.BLUE, src[36], False, "archived"),
        ("synthetic_plain", base.BLUE, synthetic_plain, False, "synthetic"),
        ("synthetic_correction", base.BLUE, synthetic_correction, True, "synthetic"),
        ("synthetic_reopen", base.BLUE, synthetic_reopen, False, "synthetic"),
    ]
    return [
        {
            "stage": "A",
            "id": case_id,
            "subject": subject,
            "offered_support": offered,
            "expected": expected,
            "origin": origin,
        }
        for case_id, subject, offered, expected, origin in stage_a
    ] + [
        {
            "stage": "B",
            "id": case_id,
            "subject": subject,
            "complete_events": source,
            "expected": expected,
            "origin": origin,
        }
        for case_id, subject, source, expected, origin in stage_b
    ]


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    if case["stage"] == "A":
        system = (
            "Leia SOMENTE a evidência oferecida. Decida se ela afirma que o portão "
            "NOMEADO terminou de fechar neste intervalo. Responda 'entailed' apenas "
            "se a identidade do portão e a ação concluída estão sustentadas nas "
            "passagens. No presente narrativo, 'se fecha com um baque' conta como "
            "conclusão do fechamento, mesmo sem pretérito perfeito. Aviso futuro, "
            "portão já selado, outro portão e 'o portão' genérico sem referente "
            "inequívoco não bastam. Retorne verdict: entailed|insufficient|contradicted "
            "e support: passagens literais da evidência oferecida; entailed "
            "exige pelo menos uma, e outros vereditos podem usar [] ou citar "
            "literalmente a razão da rejeição. Só JSON conforme: "
            + json.dumps(STAGE_A_SCHEMA, ensure_ascii=False)
        )
        user = {
            "subject": case["subject"],
            "claim": "Este portão concluiu um fechamento neste intervalo.",
            "offered_support": case["offered_support"],
        }
    else:
        system = (
            "Leia a sequência COMPLETA de eventos deste intervalo. A pergunta é "
            "somente se o texto desmente explicitamente que o fechamento do portão "
            "nomeado tenha ocorrido. Uma correção do narrador dizendo que ele nunca "
            "se fechou é retraction=true. Uma reabertura DEPOIS de um fechamento "
            "real não é desmentido do evento anterior: retracted=false. Um aviso "
            "de fechamento futuro sem afirmação de fechamento também não é "
            "retração. Responda retracted:boolean e evidence_quote: trecho literal "
            "da correção quando true, string vazia quando false. Não receba nem "
            "infira o julgamento de outra chamada. Só JSON conforme: "
            + json.dumps(STAGE_B_SCHEMA, ensure_ascii=False)
        )
        user = {
            "subject": case["subject"],
            "claim": "Este portão concluiu um fechamento neste intervalo.",
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
    return [{**case, "request": request(case, cfg)} for case in source_cases()]


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "base_script": base.digest(Path(base.__file__)),
        "source_debug": base.digest(base.SOURCE),
        "t37_bare_result": base.digest(BARE_RESULT),
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    selected = frozen(base.config())
    if len(selected) != 13 or sum(case["stage"] == "A" for case in selected) != 7:
        raise RuntimeError("Expected exactly seven Stage A and six Stage B requests")
    for case in selected:
        if base.ID_PATTERN.search(json.dumps(case["request"], ensure_ascii=False)):
            raise RuntimeError("Internal ID leaked into request")
        user = json.loads(case["request"]["messages"][1]["content"])
        if case["stage"] == "A" and "complete_events" in user:
            raise RuntimeError("Stage A received complete events")
        if case["stage"] == "B" and "offered_support" in user:
            raise RuntimeError("Stage B received Stage A evidence")
    base.write_json(
        MANIFEST,
        {
            "hashes": hashes(),
            "runs_per_request": 4,
            "stage_a_schema": STAGE_A_SCHEMA,
            "stage_b_schema": STAGE_B_SCHEMA,
            "cases": selected,
        },
    )
    print("Frozen seven Stage A and six Stage B requests")


def literal_in(quote: str, passages: list[str]) -> bool:
    return bool(quote) and any(quote in passage for passage in passages)


async def call_one(case: dict[str, Any], repeat: int, cfg: dict[str, Any]) -> None:
    label = f"{case['stage']}-{case['id']}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    base.write_json(request_path, case["request"])
    result: dict[str, Any] = {
        "stage": case["stage"],
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

        validate_json_schema(parsed, STAGE_A_SCHEMA if case["stage"] == "A" else STAGE_B_SCHEMA)
        if case["stage"] == "A":
            quotes = cast(list[str], parsed["support"])
            if any(not literal_in(quote, case["offered_support"]) for quote in quotes):
                raise ValueError("Stage A support is not literal offered text")
            if parsed["verdict"] == "entailed" and not quotes:
                raise ValueError("Positive Stage A verdict has no support")
        else:
            quote = cast(str, parsed["evidence_quote"])
            complete = case["complete_events"]["perception_events"] + (
                [case["complete_events"]["time_skip_summary"]]
                if case["complete_events"]["time_skip_summary"]
                else []
            )
            if parsed["retracted"] and not literal_in(quote, complete):
                raise ValueError("Retraction lacks literal complete-source quote")
            if not parsed["retracted"] and quote:
                raise ValueError("No retraction verdict has evidence quote")
        result.update(parsed=parsed, valid=True)
    except Exception as exc:  # Preserve failed calls without replacement.
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    if manifest["hashes"] != hashes() or manifest["cases"] != frozen(cfg):
        raise RuntimeError("Frozen source, code or requests changed")
    if (
        manifest["runs_per_request"] != 4
        or manifest["stage_a_schema"] != STAGE_A_SCHEMA
        or manifest["stage_b_schema"] != STAGE_B_SCHEMA
    ):
        raise RuntimeError("Frozen scope or schema changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(6)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await call_one(case, repeat, cfg)

    await asyncio.gather(
        *(limited(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )
    print("Completed exactly 52 frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 52
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 52
        and all(ids)
    )
    summary: dict[str, Any] = {}
    stage_match = {"A": True, "B": True}
    for case in manifest["cases"]:
        stage = case["stage"]
        rows = [row for row in results if row["stage"] == stage and row["case"] == case["id"]]
        values = [
            row.get("parsed", {}).get("verdict" if stage == "A" else "retracted") for row in rows
        ]
        if stage == "A":
            matched = len(values) == 4 and all(
                value == "entailed"
                if case["expected"] == "entailed"
                else value in ("insufficient", "contradicted")
                for value in values
            )
        else:
            matched = len(values) == 4 and all(value is case["expected"] for value in values)
        stage_match[stage] &= matched
        summary[f"{stage}-{case['id']}"] = {
            "expected": case["expected"],
            "values": values,
            "local_match": matched,
        }
    status = (
        "incomplete"
        if not technical
        else ("local_pass_pending_content_read" if all(stage_match.values()) else "semantic_fail")
    )
    outcome = {
        "status": status,
        "technical_gate": bool(technical),
        "stage_semantic_gate": stage_match,
        "valid_count": sum(bool(row.get("valid")) for row in results),
        "cases": summary,
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
