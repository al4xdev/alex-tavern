"""Frozen public-name physical projection screen for a draft contradiction reporter."""

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
PREREG = HERE / "WHOLE-DRAFT-REPORTER-PREREGISTRATION.md"
CASES = HERE / "WHOLE-DRAFT-REPORTER-CASES.json"
MANIFEST = HERE / "whole-draft-reporter-manifest.json"
RUNS = HERE / "whole-draft-reporter-runs"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["contradiction", "consistent", "uncertain"]},
        "conflicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "committed_quote": {"type": "string"},
                    "draft_quote": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["committed_quote", "draft_quote", "reason"],
                "additionalProperties": False,
            },
        },
        "uncertainty_quote": {"type": "string"},
    },
    "required": ["status", "conflicts", "uncertainty_quote"],
    "additionalProperties": False,
}
EXPECTED = {
    "archived_t38_blue": "contradiction",
    "archived_kennel_t34": "contradiction",
    "synthetic_ajar_closure": "consistent",
    "synthetic_reopening": "consistent",
    "synthetic_open_crossing": "consistent",
    "synthetic_ambiguous_gate": "uncertain",
    "synthetic_static_aftermath": "consistent",
}


def cases() -> list[dict[str, Any]]:
    selected = cast(list[dict[str, Any]], json.loads(CASES.read_text(encoding="utf-8")))
    if [row["id"] for row in selected] != list(EXPECTED):
        raise RuntimeError("Case IDs or order changed")
    return selected


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Você é um leitor independente de continuidade física em ficção. "
        "Leia SOMENTE a evidência committed, a tentativa pendente e o rascunho "
        "inteiro (blocking, events, zone_moves, scene_update). Identifique "
        "contradiction somente quando um resultado físico do rascunho é "
        "incompatível com algo já confirmado ou com o próprio rascunho, sem "
        "transição causal que os reconcilie. Uma intenção é tentativa, não "
        "sucesso. Reabertura narrada permite travessia posterior; passagem "
        "aberta e fresta ainda transitável permitem ação antes de fechamento. "
        "'Permanece fechado' e eco de impacto anterior não são novo fechamento. "
        "'Trancado' sozinho não estabelece que a abertura fechou; prosa de "
        "narrador que diz 'se fecha' estabelece. Se 'o portão' puder designar "
        "mais de um portão presente, use uncertain, sem vincular ao alvo por "
        "palpite. Para contradiction, retorne conflitos com trechos literais "
        "da evidência committed e do rascunho, e razão específica. Para "
        "consistent, conflicts=[] e uncertainty_quote=''. Para uncertain, "
        "conflicts=[] e uncertainty_quote literal do rascunho. Não invente "
        "acontecimentos fora das passagens. Só JSON conforme: "
        + json.dumps(SCHEMA, ensure_ascii=False)
    )
    user = {
        "committed": case["committed"],
        "pending_attempt": case["pending_attempt"],
        "draft": case["draft"],
    }
    if base.ID_PATTERN.search(json.dumps(user, ensure_ascii=False)):
        raise RuntimeError("Internal ID leaked into reporter prompt")
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
    return [
        {
            "id": case["id"],
            "origin": case["origin"],
            "expected": EXPECTED[case["id"]],
            "request": request(case, cfg),
        }
        for case in cases()
    ]


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "cases": base.digest(CASES),
        "base_script": base.digest(Path(base.__file__)),
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    base.write_json(
        MANIFEST,
        {
            "hashes": hashes(),
            "runs_per_request": 4,
            "schema": SCHEMA,
            "cases": frozen(base.config()),
        },
    )
    print("Frozen seven reporter requests")


def draft_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in draft_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in draft_strings(item)]
    return []


def literal(quote: str, passages: list[str]) -> bool:
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
        user = json.loads(case["request"]["messages"][1]["content"])
        committed = cast(list[str], user["committed"])
        draft = draft_strings(user["draft"])
        status = parsed["status"]
        conflicts = cast(list[dict[str, str]], parsed["conflicts"])
        uncertain = cast(str, parsed["uncertainty_quote"])
        if status == "contradiction":
            if not conflicts or uncertain:
                raise ValueError("Contradiction requires conflicts and no uncertainty quote")
            for item in conflicts:
                if not literal(item["committed_quote"], committed):
                    raise ValueError("Committed quote not literal source text")
                if not literal(item["draft_quote"], draft):
                    raise ValueError("Draft quote not literal draft text")
                if not item["reason"].strip():
                    raise ValueError("Conflict needs a reason")
        elif status == "consistent":
            if conflicts or uncertain:
                raise ValueError("Consistent must have no conflict or uncertainty quote")
        elif conflicts or not literal(uncertain, draft):
            raise ValueError("Uncertain requires only literal ambiguous draft quote")
        result.update(valid=True, parsed=parsed)
    except Exception as exc:  # Preserve every failed call without replacement.
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
    print("Completed exactly 28 frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 28
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 28
        and all(ids)
    )
    summary: dict[str, Any] = {}
    semantic = True
    for case in manifest["cases"]:
        rows = sorted(
            (row for row in results if row["case"] == case["id"]), key=lambda row: row["repeat"]
        )
        values = [row.get("parsed", {}).get("status") for row in rows]
        matched = len(values) == 4 and all(value == case["expected"] for value in values)
        semantic &= matched
        summary[case["id"]] = {
            "expected": case["expected"],
            "values": values,
            "local_match": matched,
        }
    outcome = {
        "status": "incomplete"
        if not technical
        else ("status_gate_pass_pending_content_read" if semantic else "semantic_status_fail"),
        "technical_gate": bool(technical),
        "status_gate": semantic if technical else None,
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
