"""Real semantic-gate falsification using uniform actor-owned content."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import random
from pathlib import Path
from typing import Any

import httpx

from src.llm.client import chat_completion

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = HERE / "whole-beat-audit-v2-manifest.json"
OUT = HERE / "whole-beat-audit-v2-runs"
spec = importlib.util.spec_from_file_location("audit_basis", HERE / "speech_basis_screen.py")
assert spec and spec.loader
screen: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
baseline = screen.baseline
SCHEMA = {
    "name": "beat_consistency_audit",
    "schema": {
        "type": "object",
        "properties": {
            "requires_revision": {"type": "boolean"},
            "reasons": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["requires_revision", "reasons"],
        "additionalProperties": False,
    },
}
SYSTEM = """You audit a proposed roleplay beat against confirmed world and authored content.
All actors have identical ownership rules. completed_actor_content is a trusted
record assembled from already completed submissions and generation, not a
proposal. actual_spoken_words contains the exact words actually spoken this beat;
an empty list means that actor produced NO audible words in this beat. Only
candidate.speech_proposals are prospective. Do not relabel actual_spoken_words as
proposals or ignore a completed quote because the same intent was also proposed.
Each actor's submitted_action_attempts is an already submitted attempt, not proof
of completed consequences. A source-reading outcome can be adjudicated under the
exception below. If no issue is found, requires_revision MUST be false and reasons
empty; a reason saying no revision is needed cannot accompany true.
Authored speech establishes what was
said, not whether its claim is world truth. Authored action is an attempt whose
physical consequence the world authority may adjudicate. A speech proposal is
prospective until actual authored speech realizes it. Never infer completed speech
or a response to an unspoken question from a proposal alone, regardless of event
kind or narrator/character attribution. Examine the whole candidate: observations,
world changes, narration and replies, including premises that replies depend on.
A reply genuinely authored now does not prove someone else asked its implied
question. Prior ignorance can change from newly visible clues. Independent NPC
speech and physical consequences remain allowed.
Exception: explicitly attempting to read an established legible source aloud can
produce a world-adjudicated disclosure of that exact content, even if no authored
speech contains the source words. This authorizes only that source's contents, not
added questions, opinions, demands or arbitrary extra facts. Check exact initiating
action, source, recipient and disclosed content. Lack of a new spoken transcript
alone is not a reason to reject an authorized reading operation.
Return requires_revision true only for a concrete contradiction, unsupported
completed speech act or causal premise, or source disclosure beyond the initiating
action. State exact offending claim and evidence. Do not forbid an NPC's ordinary
speech, mistake physical force for voluntary choice, or require a specific wording.
"""


def cases() -> list[dict[str, Any]]:
    base = {
        "world": {
            "portal": "aberto",
            "mapa": "seguro nas mãos de Iara",
            "marcas": "marcas do encaixe visíveis a Bento",
            "cifra_legivel": "A Dama do Norte é Glinda, que planeja conquistar as cinco cidades.",
        },
        "confirmed_history": [
            {"actor": "Iara", "kind": "speech", "text": "Continuo segurando o mapa."},
            {"actor": "Bento", "kind": "speech", "text": "Ainda não sei fechar o portal."},
        ],
        "completed_actor_content": [
            {
                "actor": "Iara",
                "actual_spoken_words": [],
                "submitted_action_attempts": ["Seguro o mapa em silêncio."],
            },
            {
                "actor": "Bento",
                "actual_spoken_words": ["O encaixe fica ao lado do arco."],
                "submitted_action_attempts": [],
            },
        ],
        "candidate": {"speech_proposals": [], "events": [], "narration": [], "scene_update": {}},
    }
    definitions = []

    def add(name: str, expected: bool, value: dict[str, Any]) -> None:
        definitions.append({"id": name, "expected_revision": expected, "input": value})

    v = copy.deepcopy(base)
    v["candidate"]["speech_proposals"] = [
        {"actor": "Iara", "text": "Iara pergunta onde encaixar o mapa."},
        {"actor": "Bento", "text": "Bento responde à pergunta de Iara."},
    ]
    v["candidate"]["narration"] = ["Bento respondeu à pergunta de Iara indicando o encaixe."]
    add("question_reply", True, v)

    v = copy.deepcopy(base)
    v["completed_actor_content"][1]["actual_spoken_words"] = []
    real = json.loads((HERE / "speech-basis-runs/npc_basis-2.result.json").read_text())["output"]
    clause = next(e["content"] for e in real["perception_events"] if e["subject_id"] == "C2")
    v["candidate"]["events"] = [{"kind": "observation", "actor": "Bento", "text": clause}]
    v["candidate"]["narration"] = [clause]
    add("observation_without_speech", True, v)

    v = copy.deepcopy(base)
    v["candidate"]["speech_proposals"] = [
        {"actor": "Bento", "text": "Bento explica onde fica o encaixe."}
    ]
    v["candidate"]["narration"] = ["Bento indicou em voz alta que o encaixe fica ao lado do arco."]
    add("npc_owned_positive", False, v)

    v = copy.deepcopy(base)
    v["completed_actor_content"][0]["submitted_action_attempts"] = [
        "Leio a cifra já decifrada em voz alta para Bento."
    ]
    v["completed_actor_content"][1]["actual_spoken_words"] = []
    v["candidate"]["events"] = [
        {
            "kind": "source_disclosure",
            "actor": "Iara",
            "recipient": "Bento",
            "source": "cifra_legivel",
            "text": base["world"]["cifra_legivel"],
        }
    ]
    v["candidate"]["narration"] = ["A leitura da cifra torna seu conteúdo audível a Bento."]
    add("reading_positive", False, v)

    v = copy.deepcopy(v)
    v["candidate"]["events"].append(
        {
            "kind": "observation",
            "actor": "Iara",
            "text": "Iara pergunta a Bento onde encaixar o mapa.",
        }
    )
    v["candidate"]["narration"].append("Após ler a cifra, Iara pergunta onde encaixar o mapa.")
    add("reading_appended_question", True, v)

    v = copy.deepcopy(base)
    v["completed_actor_content"][1]["actual_spoken_words"] = [
        "Podemos examinar o encaixe antes de decidir."
    ]
    v["candidate"]["speech_proposals"] = [
        {"actor": "Bento", "text": "Bento propõe examinar o encaixe."}
    ]
    v["candidate"]["narration"] = [
        "Bento propõe em voz alta examinar o encaixe, sem atribuir outra fala a Iara."
    ]
    add("independent_npc_positive", False, v)
    return definitions


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "WHOLE-BEAT-AUDIT-V2-PREREGISTRATION.md",
        HERE / "speech_basis_screen.py",
        HERE / "speech-basis-runs/npc_basis-2.result.json",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    assert not MANIFEST.exists()
    cfg = baseline.config()
    prepared = []
    for definition in cases():
        captured: list[dict[str, Any]] = []

        def capture(
            request: httpx.Request, sink: list[dict[str, Any]] = captured
        ) -> httpx.Response:
            sink.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
            await chat_completion(
                client,
                [
                    {"role": "system", "content": SYSTEM},
                    {
                        "role": "user",
                        "content": json.dumps(definition["input"], ensure_ascii=False),
                    },
                ],
                provider="deepseek",
                model=cfg["model"],
                language=cfg["language"],
                api_base=cfg["api_base"],
                api_key="",
                json_schema=SCHEMA,
                max_tokens=1024,
            )
        assert len(captured) == 1
        prepared.append(
            {
                "fixture": {"id": definition["id"]},
                "expected_revision": definition["expected_revision"],
                "input": definition["input"],
                "schema": SCHEMA["schema"],
                "request": captured[0],
                "agent": "beat_audit_lab",
                "turn_number": 4,
            }
        )
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": prepared,
            "provider": {k: cfg[k] for k in ("model", "language", "api_base")},
        },
    )
    print("Frozen six whole-beat semantic fixtures, four calls each")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes() and not OUT.exists()
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in manifest["provider"].items())
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = [(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    random.Random(6921).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    grade = []
    for case, repeat in jobs:
        path = OUT / f"{case['fixture']['id']}-{repeat}.result.json"
        row = json.loads(path.read_text())
        grade.append(
            {
                "case": case["fixture"]["id"],
                "repeat": repeat,
                "valid": row["valid"],
                "matches_label": row["valid"]
                and row["output"]["requires_revision"] == case["expected_revision"],
            }
        )
    baseline.write(
        HERE / "whole-beat-audit-v2-grade.json",
        {
            "rows": grade,
            "all_valid": all(r["valid"] for r in grade),
            "all_labels_match": all(r["matches_label"] for r in grade),
        },
    )
    print(
        json.dumps(
            {
                "valid": sum(r["valid"] for r in grade),
                "labels_match": sum(r["matches_label"] for r in grade),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
