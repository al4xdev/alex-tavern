"""Frozen offline screen for manually bound gate-closure admission."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl"
PREREG = HERE / "CLOSURE-ADMISSION-PREREGISTRATION.md"
MANIFEST = HERE / "closure-admission-manifest.json"
RUNS = HERE / "closure-admission-runs"
BLUE = "O portão azul que dá acesso ao túnel da equipe azul"
GREEN = "O portão verde que dá acesso ao túnel da equipe verde"
TURNS = {36: 334, 37: 344, 38: 350, 39: 352}
ID_PATTERN = re.compile(r"\bC\d+\b")
SCHEMAS: dict[str, dict[str, Any]] = {
    "extractor": {
        "type": "object",
        "properties": {
            "completed_closure": {"type": "string", "enum": ["yes", "no", "ambiguous"]},
            "support": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["completed_closure", "support"],
        "additionalProperties": False,
    },
    "checker": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["entailed", "contradicted", "insufficient"],
            },
            "support": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["verdict", "support"],
        "additionalProperties": False,
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_events() -> dict[int, dict[str, Any]]:
    selected: dict[int, dict[str, Any]] = {}
    for line_number, line in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(), 1):
        row = cast(dict[str, Any], json.loads(line))
        if line_number not in TURNS.values():
            continue
        turn = int(row["turn_number"])
        if (
            TURNS.get(turn) != line_number
            or row["agent"] != "director"
            or row["attempt_number"] != 1
            or row["error"] is not None
        ):
            raise RuntimeError(f"Source line {line_number} is not the frozen Director row")
        response = cast(dict[str, Any], json.loads(cast(str, row["response"])))
        selected[turn] = {
            "perception_events": [event["content"] for event in response["perception_events"]],
            "time_skip_summary": response["time_skip_summary"],
        }
    if set(selected) != set(TURNS):
        raise RuntimeError("Missing frozen source turns")
    return selected


def cases() -> list[dict[str, Any]]:
    src = source_events()
    swap = json.loads(
        json.dumps(src[38], ensure_ascii=False)
        .replace("azul", "__TEMP__")
        .replace("verde", "azul")
        .replace("__TEMP__", "verde")
    )
    future = {
        "perception_events": ["Restam cinco segundos para o portão azul se fechar de vez."],
        "time_skip_summary": "",
    }
    complete = {
        "perception_events": ["O portão azul se fechou de vez com um baque."],
        "time_skip_summary": "",
    }
    ambiguous = {
        "perception_events": [
            "O portão azul e o portão verde estavam abertos lado a lado.",
            "Um dos portões se fechou com um baque, mas ninguém viu qual deles.",
        ],
        "time_skip_summary": "",
    }
    specs = [
        (
            "t36_blue",
            "archived",
            BLUE,
            src[36],
            "no",
            "not_entailed",
            src[36]["perception_events"][0],
        ),
        ("t37_blue", "archived", BLUE, src[37], "yes", "entailed", src[37]["time_skip_summary"]),
        ("t38_blue", "archived", BLUE, src[38], "yes", "entailed", src[38]["perception_events"][1]),
        (
            "t39_blue",
            "archived",
            BLUE,
            src[39],
            "no",
            "not_entailed",
            src[39]["perception_events"][0],
        ),
        (
            "t38_green",
            "archived_other_subject",
            GREEN,
            src[38],
            "no",
            "not_entailed",
            src[38]["perception_events"][1],
        ),
        (
            "swap_t38_green",
            "synthetic",
            GREEN,
            swap,
            "yes",
            "entailed",
            swap["perception_events"][1],
        ),
        (
            "swap_t38_blue",
            "synthetic",
            BLUE,
            swap,
            "no",
            "not_entailed",
            swap["perception_events"][1],
        ),
        (
            "minimal_future",
            "synthetic",
            BLUE,
            future,
            "no",
            "not_entailed",
            future["perception_events"][0],
        ),
        (
            "minimal_complete",
            "synthetic",
            BLUE,
            complete,
            "yes",
            "entailed",
            complete["perception_events"][0],
        ),
        (
            "ambiguous_two_gates",
            "synthetic",
            BLUE,
            ambiguous,
            "ambiguous",
            "insufficient",
            ambiguous["perception_events"][1],
        ),
    ]
    return [
        {
            "id": case_id,
            "origin": origin,
            "subject": subject,
            "source": source,
            "expected_extractor": expected_extractor,
            "expected_checker": expected_checker,
            "seed_support": seed_support,
        }
        for case_id, origin, subject, source, expected_extractor, expected_checker, seed_support in specs
    ]


def request(case: dict[str, Any], role: str, model: str, max_tokens: int) -> dict[str, Any]:
    source = case["source"]
    common = {
        "subject": case["subject"],
        "perception_events": source["perception_events"],
        "time_skip_summary": source["time_skip_summary"],
    }
    if role == "extractor":
        system = (
            "Leia todos os eventos de um intervalo na ordem dada, depois o resumo de passagem de tempo. "
            "Decida se O PORTÃO NOMEADO terminou de fechar neste intervalo. 'yes' exige fechamento "
            "concluído do mesmo portão; 'no' para estreitamento, aviso de fechamento futuro ou "
            "observação de portão já fechado; 'ambiguous' se houve fechamento mas não é possível "
            "resolver qual portão. Não julgue se a ação é fisicamente repetida. "
            "Em support, copie trechos literais dos eventos que sustentem o veredito; pode ser [] "
            "para no ou ambiguous. Responda só um objeto JSON conforme: "
        )
        common["question"] = "Este portão terminou de fechar neste intervalo?"
    else:
        system = (
            "Você é um leitor independente. Verifique se a alegação positiva é implicada pelos "
            "eventos COMPLETOS, não apenas pela citação oferecida. 'entailed' só se o portão "
            "nomeado terminou de fechar neste intervalo; 'contradicted' se os eventos negam "
            "isso; 'insufficient' se falta prova ou o referente é indeterminado. Futuro, "
            "estreitamento, estado já fechado e fechamento de outro portão não bastam. "
            "Em support copie trechos literais, ou [] se nenhum sustenta seu veredito. "
            "Responda só um objeto JSON conforme: "
        )
        common["claim"] = "O portão nomeado terminou de fechar neste intervalo."
        common["offered_support"] = case["seed_support"]
    messages = [
        {"role": "system", "content": system + json.dumps(SCHEMAS[role], ensure_ascii=False)},
        {"role": "user", "content": json.dumps(common, ensure_ascii=False, indent=2)},
    ]
    return {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def config() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
            "deepseek"
        ],
    )


def frozen(configured: dict[str, Any]) -> list[dict[str, Any]]:
    model, max_tokens = str(configured["model"]), int(configured["max_tokens_narrator"])
    return [
        {**case, "requests": {role: request(case, role, model, max_tokens) for role in SCHEMAS}}
        for case in cases()
    ]


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    selected = frozen(config())
    for case in selected:
        for req in case["requests"].values():
            if ID_PATTERN.search(json.dumps(req, ensure_ascii=False)):
                raise RuntimeError("Internal ID leaked into a request")
    write_json(
        MANIFEST,
        {
            "source_sha256": digest(SOURCE),
            "script_sha256": digest(Path(__file__)),
            "preregistration_sha256": digest(PREREG),
            "runs_per_case_role": 4,
            "schemas": SCHEMAS,
            "cases": selected,
        },
    )
    print(f"Frozen {len(selected)} cases, two roles, four repetitions")


def curl_config(api_key: str) -> bytes:
    if any(char in api_key for char in '\r\n\\"'):
        raise ValueError("API key contains unsafe curl-config character")
    return f'header = "Authorization: Bearer {api_key}"\n'.encode()


async def call_one(case: dict[str, Any], role: str, repeat: int, cfg: dict[str, Any]) -> None:
    label = f"{case['id']}-{role}-{repeat}"
    request_path = RUNS / f"{label}.request.json"
    raw_path = RUNS / f"{label}.raw.json"
    write_json(request_path, case["requests"][role])
    result: dict[str, Any] = {
        "case": case["id"],
        "role": role,
        "repeat": repeat,
        "valid": False,
        "request_sha256": digest(request_path),
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
    stdout, stderr = await proc.communicate(curl_config(cast(str, cfg["api_key"])))
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
        content = cast(str, envelope["choices"][0]["message"]["content"])
        parsed = cast(dict[str, Any], json.loads(content))
        sys.path.insert(0, str(ROOT))
        from src.llm.schema import validate_json_schema

        validate_json_schema(parsed, SCHEMAS[role])
        passages = case["source"]["perception_events"] + (
            [case["source"]["time_skip_summary"]] if case["source"]["time_skip_summary"] else []
        )
        support = parsed["support"]
        if any(not quote or not any(quote in passage for passage in passages) for quote in support):
            raise ValueError("Nonliteral or empty support")
        positive = (
            parsed["completed_closure"] == "yes"
            if role == "extractor"
            else parsed["verdict"] == "entailed"
        )
        if positive and not support:
            raise ValueError("Positive verdict without literal support")
        result.update(parsed=parsed, valid=True)
    except Exception as exc:  # Every failed call remains in the frozen sample.
        result["error"] = f"{type(exc).__name__}: {exc}"
    write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once, preserve existing run directory")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    for key, path in (
        ("source_sha256", SOURCE),
        ("script_sha256", Path(__file__)),
        ("preregistration_sha256", PREREG),
    ):
        if manifest[key] != digest(path):
            raise RuntimeError(f"Frozen {key} changed")
    cfg = config()
    if (
        manifest["cases"] != frozen(cfg)
        or manifest["schemas"] != SCHEMAS
        or manifest["runs_per_case_role"] != 4
    ):
        raise RuntimeError("Frozen requests changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    write_json(
        RUNS / "run.json",
        {
            "manifest_sha256": digest(MANIFEST),
            "started_unix": time.time(),
            "model": cfg["model"],
            "api_base": cfg["api_base"],
        },
    )
    semaphore = asyncio.Semaphore(6)

    async def limited(case: dict[str, Any], role: str, repeat: int) -> None:
        async with semaphore:
            await call_one(case, role, repeat, cfg)

    await asyncio.gather(
        *(
            limited(case, role, repeat)
            for case in manifest["cases"]
            for role in SCHEMAS
            for repeat in range(1, 5)
        )
    )
    print("Completed exactly 80 frozen calls")


def grade() -> None:
    if not MANIFEST.exists() or not RUNS.exists():
        raise RuntimeError("Run frozen screen first")
    manifest = cast(dict[str, Any], json.loads(MANIFEST.read_text(encoding="utf-8")))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("response_id") for row in results]
    technical = (
        len(results) == 80
        and all(row.get("valid") for row in results)
        and len(set(ids)) == 80
        and all(ids)
    )
    by_case: dict[str, Any] = {}
    semantic = True
    for case in manifest["cases"]:
        rows = [row for row in results if row["case"] == case["id"]]
        extractor = [
            row.get("parsed", {}).get("completed_closure")
            for row in rows
            if row["role"] == "extractor"
        ]
        checker = [row.get("parsed", {}).get("verdict") for row in rows if row["role"] == "checker"]
        checked = [
            value == "entailed"
            if case["expected_checker"] == "entailed"
            else value in ("contradicted", "insufficient")
            for value in checker
        ]
        if case["expected_checker"] == "insufficient":
            checked = [value == "insufficient" for value in checker]
        case_ok = (
            len(extractor) == len(checker) == 4
            and all(value == case["expected_extractor"] for value in extractor)
            and all(checked)
        )
        semantic &= case_ok
        by_case[case["id"]] = {
            "expected_extractor": case["expected_extractor"],
            "extractor": extractor,
            "expected_checker": case["expected_checker"],
            "checker": checker,
            "local_match": case_ok,
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
        "unique_ids": len(set(ids)),
        "cases": by_case,
    }
    write_json(RUNS / "grade.json", outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
