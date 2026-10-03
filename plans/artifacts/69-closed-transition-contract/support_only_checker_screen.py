"""Ablate complete-source access from the closure admission checker."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base

HERE = Path(__file__).resolve().parent
PREREG = HERE / "SUPPORT-ONLY-CHECKER-PREREGISTRATION.md"
MANIFEST = HERE / "support-only-checker-manifest.json"
RUNS = HERE / "support-only-checker-runs"
SOURCE_MANIFEST = HERE / "closure-admission-manifest.json"
SOURCE_RUNS = HERE / "closure-admission-runs"
SOURCE_RESULT_NAMES = (
    "t37_blue-extractor-1.result.json",
    "t37_blue-extractor-3.result.json",
    "t38_blue-extractor-1.result.json",
)


def source_result(name: str) -> dict[str, Any]:
    result = cast(dict[str, Any], json.loads((SOURCE_RUNS / name).read_text(encoding="utf-8")))
    if not result["valid"]:
        raise RuntimeError(f"Frozen source result is invalid: {name}")
    return result


def source_cases() -> list[dict[str, Any]]:
    prior = cast(dict[str, Any], json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")))
    old = {case["id"]: case for case in prior["cases"]}
    t37_1 = source_result(SOURCE_RESULT_NAMES[0])["parsed"]["support"]
    t37_3 = source_result(SOURCE_RESULT_NAMES[1])["parsed"]["support"]
    t38 = source_result(SOURCE_RESULT_NAMES[2])["parsed"]["support"]
    specs = (
        ("t37_generic_1", base.BLUE, t37_1, "not_entailed", "archived_output"),
        ("t37_generic_3", base.BLUE, t37_3, "not_entailed", "archived_output"),
        ("t38_explicit", base.BLUE, t38, "entailed", "archived_output"),
        (
            "t38_weak",
            base.BLUE,
            [old["t38_weak_support"]["seed_support"]],
            "not_entailed",
            "archived_seed",
        ),
        ("wrong_target", base.GREEN, t38, "not_entailed", "archived_output"),
        (
            "minimal_future",
            base.BLUE,
            [old["minimal_future"]["seed_support"]],
            "not_entailed",
            "synthetic",
        ),
        (
            "minimal_complete",
            base.BLUE,
            [old["minimal_complete"]["seed_support"]],
            "entailed",
            "synthetic",
        ),
    )
    return [
        {
            "id": case_id,
            "subject": subject,
            "source": {"perception_events": offered, "time_skip_summary": ""},
            "expected_checker": expected,
            "origin": origin,
        }
        for case_id, subject, offered, expected, origin in specs
    ]


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Você lê somente as passagens OFERECIDAS como prova de uma alegação. "
        "Decida se elas, sozinhas, estabelecem que o portão nomeado TERMINOU DE FECHAR "
        "neste intervalo. 'entailed' exige identidade do portão e ação concluída. "
        "Um 'o portão' genérico sem contexto identificador, aviso futuro, estado já selado "
        "ou outro portão é insuficiente. Não invente contexto ausente. "
        "Responda verdict: entailed|contradicted|insufficient e support: lista de "
        "trechos literais das passagens oferecidas; [] é permitido quando não há suporte. "
        "Retorne só JSON conforme: " + json.dumps(base.SCHEMAS["checker"], ensure_ascii=False)
    )
    user = {
        "subject": case["subject"],
        "claim": "Esta proposta afirma que o portão nomeado terminou de fechar neste intervalo.",
        "offered_support": case["source"]["perception_events"],
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
    return [{**case, "requests": {"checker": request(case, cfg)}} for case in source_cases()]


def hashes() -> dict[str, str]:
    paths = {
        "script": Path(__file__),
        "prereg": PREREG,
        "base_script": Path(base.__file__),
        "source_manifest": SOURCE_MANIFEST,
        **{name: SOURCE_RUNS / name for name in SOURCE_RESULT_NAMES},
    }
    return {name: base.digest(path) for name, path in paths.items()}


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    cases = frozen(base.config())
    for case in cases:
        if base.ID_PATTERN.search(json.dumps(case["requests"], ensure_ascii=False)):
            raise RuntimeError("Internal ID leaked to support-only request")
    base.write_json(
        MANIFEST,
        {"hashes": hashes(), "runs_per_case": 4, "cases": cases},
    )
    print("Frozen seven support bundles, four checker calls each")


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    if manifest["hashes"] != hashes() or manifest["cases"] != frozen(cfg):
        raise RuntimeError("Frozen source, code or requests changed")
    if manifest["runs_per_case"] != 4 or not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("Frozen scope or provider configuration invalid")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json",
        {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()},
    )
    base.RUNS = RUNS
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await base.call_one(case, "checker", repeat, cfg, case["requests"]["checker"])

    await asyncio.gather(
        *(limited(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )
    print("Completed exactly 28 frozen checker calls")


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
    cases: dict[str, Any] = {}
    semantic = True
    for case in manifest["cases"]:
        values = [
            row.get("parsed", {}).get("verdict") for row in results if row["case"] == case["id"]
        ]
        expected = case["expected_checker"]
        matched = len(values) == 4 and all(
            value == "entailed"
            if expected == "entailed"
            else value in ("contradicted", "insufficient")
            for value in values
        )
        semantic &= matched
        cases[case["id"]] = {"expected": expected, "verdicts": values, "local_match": matched}
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
        "cases": cases,
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
