"""Frozen source-grounded screen for closure aspect and target identity."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base
import two_stage_closure_screen as previous

HERE = Path(__file__).resolve().parent
PREREG = HERE / "IDENTITY-ASPECT-PREREGISTRATION.md"
MANIFEST = HERE / "identity-aspect-manifest.json"
RUNS = HERE / "identity-aspect-runs"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "completed_closure": {"type": "boolean"},
        "identity": {
            "type": "string",
            "enum": ["named", "resolved", "ambiguous", "other", "absent"],
        },
        "action_quote": {"type": "string"},
        "identity_quote": {"type": "string"},
    },
    "required": ["completed_closure", "identity", "action_quote", "identity_quote"],
    "additionalProperties": False,
}


def cases() -> list[dict[str, Any]]:
    src = base.source_events()
    bare_result = json.loads(previous.BARE_RESULT.read_text(encoding="utf-8"))
    bare = cast(list[str], bare_result["parsed"]["support"])
    if not bare_result["valid"] or bare != ["o portão se fecha com um baque surdo"]:
        raise RuntimeError("Archived bare T37 quote changed")
    rows = [
        ("t38_explicit", base.BLUE, [src[38]["perception_events"][1]], True, "named", "archived"),
        ("t37_bare", base.BLUE, bare, True, "ambiguous", "archived_output"),
        (
            "t37_context",
            base.BLUE,
            [src[37]["perception_events"][1], src[37]["time_skip_summary"]],
            True,
            "ambiguous",
            "archived",
        ),
        ("t36_future", base.BLUE, [src[36]["perception_events"][0]], False, "named", "archived"),
        (
            "t38_static_green",
            base.BLUE,
            [src[38]["perception_events"][2]],
            False,
            "absent",
            "archived",
        ),
        ("wrong_target", base.GREEN, [src[38]["perception_events"][1]], True, "other", "archived"),
        (
            "synthetic_resolved",
            base.BLUE,
            [
                "O salão tem um único portão, pintado de azul. O grupo atravessa sua abertura. "
                "Atrás deles, o portão se fecha com um baque."
            ],
            True,
            "resolved",
            "synthetic",
        ),
        (
            "synthetic_competitors",
            base.BLUE,
            ["O portão azul range. O portão verde estremece. O portão se fecha com um baque."],
            True,
            "ambiguous",
            "synthetic",
        ),
        (
            "synthetic_aborted",
            base.BLUE,
            ["O portão azul começa a se fechar, mas para antes de completar o movimento."],
            False,
            "named",
            "synthetic",
        ),
    ]
    return [
        {
            "id": case_id,
            "subject": subject,
            "offered_support": offered,
            "expected": {"completed_closure": completed, "identity": identity},
            "origin": origin,
        }
        for case_id, subject, offered, completed, identity, origin in rows
    ]


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Leia SOMENTE as passagens oferecidas, como ficção. Julgue duas coisas "
        "separadamente: (1) se a ação de fechar um portão foi CONCLUÍDA neste "
        "intervalo; (2) a identidade do portão dessa ação em relação ao subject. "
        "No presente narrativo, 'se fecha com um baque' conclui o fechamento; "
        "aviso futuro, começo interrompido e estado já selado não concluem "
        "uma nova ação. identity=named se a frase da ação nomeia o subject; "
        "resolved se usa 'o portão' mas o texto oferecido estabelece um referente "
        "único; ambiguous se há dúvida real; other se a ação nomeia outro portão; "
        "absent se nenhuma ação de fechamento é mencionada. Um aviso futuro pode "
        "ter identity=named e completed_closure=false; absent exige false. "
        "action_quote: trecho literal da ação de fechamento, mesmo futura ou "
        "interrompida, ou string vazia se nenhuma ação; identity_quote: trecho "
        "literal que nomeia o portão ou estabelece seu antecedente único quando "
        "identity é named, resolved ou other; string vazia quando ambiguous ou "
        "absent. Não use informações fora das passagens. Só JSON conforme: "
        + json.dumps(SCHEMA, ensure_ascii=False)
    )
    user = {
        "subject": case["subject"],
        "offered_support": case["offered_support"],
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
        "base_script": base.digest(Path(base.__file__)),
        "previous_script": base.digest(Path(previous.__file__)),
        "source_debug": base.digest(base.SOURCE),
        "t37_bare_result": base.digest(previous.BARE_RESULT),
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    selected = frozen(base.config())
    if len(selected) != 9:
        raise RuntimeError("Expected nine fixed packets")
    for case in selected:
        if base.ID_PATTERN.search(json.dumps(case["request"], ensure_ascii=False)):
            raise RuntimeError("Internal ID leaked into request")
    base.write_json(
        MANIFEST,
        {"hashes": hashes(), "runs_per_request": 4, "schema": SCHEMA, "cases": selected},
    )
    print("Frozen nine requests")


def literal(quote: str, offered: list[str]) -> bool:
    return bool(quote) and any(quote in passage for passage in offered)


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
        action_quote = cast(str, parsed["action_quote"])
        identity_quote = cast(str, parsed["identity_quote"])
        offered = cast(list[str], case["offered_support"])
        if action_quote and not literal(action_quote, offered):
            raise ValueError("Action quote not literal offered text")
        if identity_quote and not literal(identity_quote, offered):
            raise ValueError("Identity quote not literal offered text")
        if parsed["identity"] == "absent":
            if parsed["completed_closure"] or action_quote or identity_quote:
                raise ValueError("Absent action must have false and empty quotes")
        elif not action_quote:
            raise ValueError("Mentioned closing action needs a quote")
        if parsed["identity"] in ("named", "resolved", "other") and not identity_quote:
            raise ValueError("Bound identity needs a quote")
        if parsed["identity"] == "ambiguous" and identity_quote:
            raise ValueError("Ambiguous identity must not assert a binding quote")
        result.update(parsed=parsed, valid=True)
    except Exception as exc:  # Preserve failed calls without replacement.
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    if manifest != {
        "hashes": hashes(),
        "runs_per_request": 4,
        "schema": SCHEMA,
        "cases": frozen(cfg),
    }:
        raise RuntimeError("Frozen source, code, protocol or requests changed")
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
    print("Completed exactly 36 frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 36
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 36
        and all(ids)
    )
    summary: dict[str, Any] = {}
    semantic = True
    for case in manifest["cases"]:
        rows = sorted(
            (row for row in results if row["case"] == case["id"]), key=lambda row: row["repeat"]
        )
        values = [
            {
                "completed_closure": row.get("parsed", {}).get("completed_closure"),
                "identity": row.get("parsed", {}).get("identity"),
            }
            for row in rows
        ]
        matched = len(values) == 4 and all(value == case["expected"] for value in values)
        semantic &= matched
        summary[case["id"]] = {
            "expected": case["expected"],
            "values": values,
            "local_match": matched,
        }
    outcome = {
        "status": (
            "incomplete"
            if not technical
            else ("local_pass_pending_content_read" if semantic else "semantic_fail")
        ),
        "technical_gate": bool(technical),
        "semantic_gate": semantic if technical else None,
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
