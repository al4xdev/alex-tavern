"""Frozen A/B of optional full-source context in gate-closure support checking."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, cast

import closure_admission_pilot as base
import support_only_checker_screen as support

HERE = Path(__file__).resolve().parent
PREREG = HERE / "CHECKER-CONTEXT-AB-PREREGISTRATION.md"
MANIFEST = HERE / "checker-context-ab-manifest.json"
RUNS = HERE / "checker-context-ab-runs"
SOURCE_MANIFEST = HERE / "closure-admission-manifest.json"
SELECTED = (
    "t38_explicit",
    "t38_weak",
    "t37_generic_3",
    "wrong_target",
    "minimal_future",
    "minimal_complete",
    "synthetic_correction",
)


def cases() -> list[dict[str, Any]]:
    prior = cast(dict[str, Any], json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")))
    original = {case["id"]: case for case in prior["cases"]}
    sources = {case["id"]: case for case in support.source_cases()}
    complete_from = {
        "t38_explicit": "t38_blue",
        "t38_weak": "t38_blue",
        "t37_generic_3": "t37_blue",
        "wrong_target": "t38_blue",
        "minimal_future": "minimal_future",
        "minimal_complete": "minimal_complete",
    }
    selected = []
    for case_id in SELECTED:
        if case_id == "synthetic_correction":
            offered = "O portão azul se fecha com um baque."
            source = {
                "subject": base.BLUE,
                "source": {"perception_events": [offered], "time_skip_summary": ""},
                "expected_checker": "entailed",
                "origin": "synthetic_correction",
            }
            complete = {
                "perception_events": [
                    offered,
                    "Correção do narrador: o baque veio da dobradiça, e o portão azul "
                    "permaneceu aberto durante todo este intervalo; não chegou a se fechar.",
                ],
                "time_skip_summary": "",
            }
        else:
            source = sources[case_id]
            complete = original[complete_from[case_id]]["source"]
        for arm in ("offered_only", "full_source"):
            selected.append(
                {
                    "id": f"{case_id}__{arm}",
                    "base_case": case_id,
                    "arm": arm,
                    "subject": source["subject"],
                    "source": source["source"],
                    "complete_events": complete,
                    "expected_checker": (
                        "not_entailed"
                        if case_id == "synthetic_correction" and arm == "full_source"
                        else source["expected_checker"]
                    ),
                    "origin": source["origin"],
                }
            )
    return selected


def request(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Leia a alegação e as passagens OFERECIDAS como prova. 'entailed' somente se "
        "essas passagens, por si, identificam o portão nomeado e afirmam que ele "
        "terminou de fechar neste intervalo. Um 'o portão' genérico sem contexto "
        "identificador, um aviso futuro, estado já selado ou outro portão é "
        "insuficiente. Se complete_events estiver presente, use-o para detectar "
        "contradições; nunca substitua suporte ausente por outra frase dele. "
        "Em support, cite somente trechos literais de offered_support; [] se "
        "não houver suporte. Responda só JSON conforme: "
        + json.dumps(base.SCHEMAS["checker"], ensure_ascii=False)
    )
    user: dict[str, Any] = {
        "subject": case["subject"],
        "claim": "Esta proposta afirma que o portão nomeado terminou de fechar neste intervalo.",
        "offered_support": case["source"]["perception_events"],
    }
    if case["arm"] == "full_source":
        user["complete_events"] = case["complete_events"]
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
    return [{**case, "requests": {"checker": request(case, cfg)}} for case in cases()]


def hashes() -> dict[str, str]:
    return {
        "script": base.digest(Path(__file__)),
        "prereg": base.digest(PREREG),
        "base_script": base.digest(Path(base.__file__)),
        "support_script": base.digest(Path(support.__file__)),
        "source_manifest": base.digest(SOURCE_MANIFEST),
        **{name: base.digest(support.SOURCE_RUNS / name) for name in support.SOURCE_RESULT_NAMES},
    }


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    prepared = frozen(base.config())
    for case in prepared:
        if base.ID_PATTERN.search(json.dumps(case["requests"], ensure_ascii=False)):
            raise RuntimeError("Internal ID leaked to checker request")
        user = json.loads(case["requests"]["checker"]["messages"][1]["content"])
        assert ("complete_events" in user) == (case["arm"] == "full_source")
    by_base = {case["id"]: case for case in prepared}
    for case_id in SELECTED:
        offered = by_base[f"{case_id}__offered_only"]["requests"]["checker"]
        complete = by_base[f"{case_id}__full_source"]["requests"]["checker"]
        if offered["messages"][0] != complete["messages"][0]:
            raise RuntimeError("A/B system messages diverged")
        offered_user = json.loads(offered["messages"][1]["content"])
        complete_user = json.loads(complete["messages"][1]["content"])
        del complete_user["complete_events"]
        if offered_user != complete_user:
            raise RuntimeError("A/B changed more than source availability")
    base.write_json(MANIFEST, {"hashes": hashes(), "runs_per_arm_case": 4, "cases": prepared})
    print("Frozen seven cases in two arms, four calls each")


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing runs")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    cfg = base.config()
    if manifest["hashes"] != hashes() or manifest["cases"] != frozen(cfg):
        raise RuntimeError("Frozen source, code or requests changed")
    if manifest["runs_per_arm_case"] != 4 or not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("Frozen scope or provider configuration invalid")
    RUNS.mkdir()
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    base.RUNS = RUNS
    semaphore = asyncio.Semaphore(6)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await base.call_one(case, "checker", repeat, cfg, case["requests"]["checker"])

    await asyncio.gather(
        *(limited(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )
    print("Completed exactly 56 frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 56
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 56
        and all(ids)
    )
    local: dict[str, Any] = {}
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
        local[case["id"]] = {"expected": expected, "verdicts": values, "local_match": matched}
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
        "cases": local,
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
