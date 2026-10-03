"""Separate claim discovery from authorization on frozen speech fixtures."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import random
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from src.llm.client import chat_completion

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = HERE / "speech-extraction-manifest.json"
OUT = HERE / "speech-extraction-runs"
spec = importlib.util.spec_from_file_location(
    "extraction_audit", HERE / "whole_beat_audit_screen_v2.py"
)
assert spec and spec.loader
old: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
baseline = old.baseline
EXTRACT = """Enumerate atomic speech acts claimed in the supplied candidate, before any
judgment of authorization. Read all fields, including reported speech inside an
observation or narration. A physical pointing gesture alone is not speech.
Extract assertions that someone spoke, asked, answered, read aloud, promised or
verbally described something. A future proposal of an utterance is proposed;
a narration or observation saying it occurred is completed. A completed reply
to another actor's question also presupposes a completed question: enumerate both.
Split a read-aloud source disclosure and an added question into separate acts.
Preserve tense, negation and neighboring context; do not turn declining to explain
into having explained. Copy an exact span and its field_path from the source.
Do not consult or guess actual speech evidence: none is supplied to this step.
Actor names are uniform. Return every act; empty list is permitted only if no
speech act is asserted or proposed in the whole candidate.
"""
JUDGE = """Check each extracted speech act against the supplied evidence.
All actors use identical completed_actor_content records. actual_spoken_words
contains exact words actually spoken in this beat, NOT proposals; an empty list
means NO audible words were produced by that actor. submitted_action_attempts
contains their submitted attempts, not proof of accomplished consequences.
Speech proposals are prospective, not proof of completed speech. A speech act
with status completed needs a realized same-actor utterance supporting it, or the
authorized reading exception below. Evaluate the meaning, not exact phrasing.
A genuinely realized NPC explanation is allowed. Merely proposing to explain
cannot be treated as having explained. A reply uttered now does not establish
someone else's unspoken question; its causal premise needs its own evidence.
Exception: an explicit submitted attempt to read a legible canonical source aloud
can produce that source disclosure as a world-adjudicated result even if no
actual_spoken_words contains its words. Check actor, initiating action, source,
recipient and source content. It authorizes only reading those contents, not
added questions, opinions or demands. There is no restriction to one special actor.
For every act, return its index, support class, evidence_paths and a reason.
Use realized_speech for supported completed utterance, authorized_reading for the
source exception, prospective_only for a future utterance, unsupported otherwise.
Evidence paths must exist; citation presence alone does not make evidence support
an act. If support is unsupported, explain the missing or contradictory basis.
Do not relabel actual_spoken_words as proposals. Do not invent extra speech.
"""


def text_fields(value: Any, prefix: str = "") -> dict[str, str]:
    if isinstance(value, str):
        return {prefix: value}
    if isinstance(value, list):
        return {
            k: v
            for i, item in enumerate(value)
            for k, v in text_fields(item, f"{prefix}/{i}").items()
        }
    if isinstance(value, dict):
        return {
            k: v
            for key, item in value.items()
            for k, v in text_fields(item, f"{prefix}/{key}").items()
        }
    return {}


def definitions() -> list[dict[str, Any]]:
    cases = old.cases()
    base = copy.deepcopy(next(c for c in cases if c["id"] == "observation_without_speech"))
    for name, clause, expected in (
        ("pointing_only", "Bento aponta para as marcas junto ao encaixe.", False),
        ("verbal_description", "Bento descreve verbalmente as marcas junto ao encaixe.", True),
    ):
        item = copy.deepcopy(base)
        item["id"], item["expected_revision"] = name, expected
        item["input"]["candidate"]["events"][0]["text"] = clause
        item["input"]["candidate"]["narration"] = [clause]
        cases.append(item)
    for case in cases:
        acts = []
        candidate = case["input"]["candidate"]

        def add(
            path: str,
            actor: str,
            act: str,
            status: str,
            claimed: str,
            _candidate: dict[str, Any] = candidate,
            _acts: list[dict[str, Any]] = acts,
        ) -> None:
            span = text_fields({"candidate": _candidate})[path]
            _acts.append(
                {
                    "field_path": path,
                    "span": span,
                    "actor": actor,
                    "act": act,
                    "status": status,
                    "claimed_content": claimed,
                }
            )

        name = case["id"]
        if name == "question_reply":
            add(
                "/candidate/speech_proposals/0/text",
                "Iara",
                "question",
                "proposed",
                "onde encaixar o mapa",
            )
            add(
                "/candidate/speech_proposals/1/text",
                "Bento",
                "reply",
                "proposed",
                "responder à pergunta de Iara",
            )
            add(
                "/candidate/narration/0",
                "Bento",
                "reply",
                "completed",
                "respondeu indicando o encaixe",
            )
            add(
                "/candidate/narration/0",
                "Iara",
                "question",
                "completed",
                "pergunta de Iara pressuposta pela resposta",
            )
        elif name in ("observation_without_speech", "verbal_description"):
            for path in ("/candidate/events/0/text", "/candidate/narration/0"):
                add(
                    path,
                    "Bento",
                    "description",
                    "completed",
                    "descreveu verbalmente o encaixe ou as marcas",
                )
        elif name == "npc_owned_positive":
            add(
                "/candidate/speech_proposals/0/text",
                "Bento",
                "description",
                "proposed",
                "localização do encaixe",
            )
            add(
                "/candidate/narration/0",
                "Bento",
                "assertion",
                "completed",
                "o encaixe fica ao lado do arco",
            )
        elif name in ("reading_positive", "reading_appended_question"):
            for path in ("/candidate/events/0/text", "/candidate/narration/0"):
                add(
                    path,
                    "Iara",
                    "reading",
                    "completed",
                    "conteúdo da cifra_legivel lido para Bento",
                )
            if name == "reading_appended_question":
                for path in ("/candidate/events/1/text", "/candidate/narration/1"):
                    add(path, "Iara", "question", "completed", "onde encaixar o mapa")
        elif name == "independent_npc_positive":
            add(
                "/candidate/speech_proposals/0/text",
                "Bento",
                "assertion",
                "proposed",
                "propõe examinar o encaixe",
            )
            add(
                "/candidate/narration/0",
                "Bento",
                "assertion",
                "completed",
                "propôs examinar o encaixe",
            )
        elif name != "pointing_only":
            raise AssertionError(name)
        case["manual_acts"] = acts
        case["session_id"] = str(uuid4())
    return cases


def extraction_schema(case: dict[str, Any]) -> dict[str, Any]:
    fields = text_fields({"candidate": case["input"]["candidate"]})
    schema = {
        "type": "object",
        "properties": {
            "field_path": {"type": "string", "enum": list(fields)},
            "span": {"type": "string"},
            "actor": {"type": "string", "enum": ["Iara", "Bento"]},
            "act": {
                "type": "string",
                "enum": ["assertion", "question", "reply", "description", "reading", "promise"],
            },
            "status": {"type": "string", "enum": ["proposed", "completed"]},
            "claimed_content": {"type": "string"},
        },
        "required": ["field_path", "span", "actor", "act", "status", "claimed_content"],
        "additionalProperties": False,
    }
    return {
        "name": "speech_claim_extraction",
        "schema": {
            "type": "object",
            "properties": {"acts": {"type": "array", "items": schema}},
            "required": ["acts"],
            "additionalProperties": False,
        },
    }


def judgment_schema(count: int) -> dict[str, Any]:
    item = {
        "type": "object",
        "properties": {
            "act_index": {"type": "integer", "minimum": 0, "maximum": max(0, count - 1)},
            "support": {
                "type": "string",
                "enum": [
                    "realized_speech",
                    "authorized_reading",
                    "prospective_only",
                    "unsupported",
                ],
            },
            "evidence_paths": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
        "required": ["act_index", "support", "evidence_paths", "reason"],
        "additionalProperties": False,
    }
    return {
        "name": "speech_claim_authorization",
        "schema": {
            "type": "object",
            "properties": {
                "decisions": {"type": "array", "items": item, "minItems": count, "maxItems": count}
            },
            "required": ["decisions"],
            "additionalProperties": False,
        },
    }


async def request_for(
    system: str, value: dict[str, Any], schema: dict[str, Any], cfg: dict[str, Any]
) -> dict[str, Any]:
    captured = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        await chat_completion(
            client,
            [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(value, ensure_ascii=False)},
            ],
            provider="deepseek",
            model=cfg["model"],
            language=cfg["language"],
            api_base=cfg["api_base"],
            api_key="",
            json_schema=schema,
            max_tokens=2048,
        )
    assert len(captured) == 1
    return captured[0]


async def judge_case(
    case: dict[str, Any], acts: list[dict[str, Any]], arm: str, cfg: dict[str, Any]
) -> dict[str, Any]:
    value = copy.deepcopy(case["input"])
    value["extracted_acts"] = acts
    schema = judgment_schema(len(acts))
    return {
        "fixture": {"id": case["id"] + "_" + arm},
        "schema": schema["schema"],
        "request": await request_for(JUDGE, value, schema, cfg),
        "agent": "speech_authorization_lab",
        "session_id": case["session_id"],
        "turn_number": 4,
    }


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "SPEECH-EXTRACTION-PREREGISTRATION.md",
        HERE / "whole_beat_audit_screen_v2.py",
        HERE / "whole-beat-audit-v2-manifest.json",
        HERE / "speech-basis-runs/npc_basis-2.result.json",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    assert not MANIFEST.exists()
    cfg = baseline.config()
    cases = definitions()
    for case in cases:
        schema = extraction_schema(case)
        case["extraction"] = {
            "fixture": {"id": case["id"] + "_extract"},
            "schema": schema["schema"],
            "request": await request_for(
                EXTRACT, {"candidate": case["input"]["candidate"]}, schema, cfg
            ),
            "agent": "speech_extraction_lab",
            "session_id": case["session_id"],
            "turn_number": 4,
        }
        case["manual"] = await judge_case(case, case["manual_acts"], "manual", cfg)
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "provider": {k: cfg[k] for k in ("model", "language", "api_base")},
        },
    )
    print(
        "Frozen eight cases: extraction and manual authorization, four repetitions; "
        "automatic authorization follows exact extraction"
    )


def verify_acts(case: dict[str, Any], acts: list[dict[str, Any]]) -> bool:
    fields = text_fields({"candidate": case["input"]["candidate"]})
    return all(
        act["span"] and act["field_path"] in fields and act["span"] in fields[act["field_path"]]
        for act in acts
    )


def grade_decisions(
    case: dict[str, Any], acts: list[dict[str, Any]], output: dict[str, Any]
) -> dict[str, Any]:
    decisions = output["decisions"]
    indices = [d["act_index"] for d in decisions]
    ordered = sorted(indices) == list(range(len(acts)))
    evidence_fields = text_fields(case["input"])
    valid_citations = all(
        path in evidence_fields and not path.startswith("/candidate/")
        for d in decisions
        for path in d["evidence_paths"]
    )
    mapping = {d["act_index"]: d for d in decisions}
    revision = any(
        act["status"] == "completed"
        and mapping.get(i, {}).get("support") in ("unsupported", "prospective_only")
        for i, act in enumerate(acts)
    )
    return {
        "unique_complete_indices": ordered,
        "citations_exist": valid_citations,
        "revision": revision,
        "matches_label": ordered and valid_citations and revision == case["expected_revision"],
    }


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes() and not OUT.exists()
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in manifest["provider"].items())
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = [
        (case, arm, repeat)
        for case in manifest["cases"]
        for arm in ("extraction", "manual")
        for repeat in range(1, 5)
    ]
    random.Random(6922).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def call(payload: dict[str, Any], repeat: int) -> dict[str, Any]:
        async with semaphore:
            await baseline.call_one(payload, repeat, cfg)
        label = payload["fixture"]["id"] + "-" + str(repeat)
        result = json.loads((OUT / (label + ".result.json")).read_text())
        baseline.write(
            OUT / (label + ".observability.json"),
            {k: payload[k] for k in ("agent", "session_id", "turn_number")},
        )
        return result

    async def chain(case: dict[str, Any], arm: str, repeat: int) -> dict[str, Any]:
        result = await call(case[arm], repeat)
        row = {"case": case["id"], "arm": arm, "repeat": repeat, "valid": result["valid"]}
        if not result["valid"]:
            return row
        acts = case["manual_acts"] if arm == "manual" else result["output"]["acts"]
        row["source_spans_valid"] = verify_acts(case, acts)
        if arm == "extraction":
            if not row["source_spans_valid"]:
                return row
            automatic = await judge_case(case, acts, "automatic", cfg)
            baseline.write(OUT / f"{case['id']}_automatic-{repeat}.payload.json", automatic)
            result = await call(automatic, repeat)
            row["automatic_valid"] = result["valid"]
            if not result["valid"]:
                return row
        row.update(grade_decisions(case, acts, result["output"]))
        return row

    rows = await asyncio.gather(*(chain(case, arm, repeat) for case, arm, repeat in jobs))
    baseline.write(HERE / "speech-extraction-grade.json", {"rows": rows})
    print(
        json.dumps(
            {
                "chains": len(rows),
                "initial_valid": sum(r["valid"] for r in rows),
                "manual_labels": sum(
                    r.get("matches_label", False) for r in rows if r["arm"] == "manual"
                ),
                "automatic_labels": sum(
                    r.get("matches_label", False) for r in rows if r["arm"] == "extraction"
                ),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
