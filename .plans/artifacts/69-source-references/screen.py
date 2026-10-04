"""Isolate source-reference provenance and issue classification on retained texts."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path
from uuid import uuid4

import httpx

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/alex/git/my/alex-tavern")
PARENT = ROOT / ".plans/artifacts/69-asserted-change"
MANIFEST = HERE / "manifest.json"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA != ROOT / ".data" and ROOT / ".data" not in DATA.parents
spec = importlib.util.spec_from_file_location("asserted", PARENT / "screen.py")
assert spec and spec.loader
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
reviewer = prior.reviewer
SYSTEM = prior.SYSTEM
CONFIG = prior.CONFIG


def nodes(value, path=""):
    result = {path: value}
    if isinstance(value, dict):
        for key, item in value.items():
            token = key.replace("~", "~0").replace("/", "~1")
            result.update(nodes(item, path + "/" + token))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.update(nodes(item, path + "/" + str(index)))
    return result


def schema(source):
    result = copy.deepcopy(reviewer.base.SCHEMA)
    fields = result["schema"]["properties"]["issues"]["items"]["properties"]
    fields["kind"]["description"] = (
        "'missing_outcome': an admitted 'source.confirmed_events' outcome "
        "is absent from 'candidate'; "
        "'unsupported_transition': 'candidate' asserts a new consequential change "
        "not admitted by 'source'; "
        "'contradiction': claims cannot both hold at their asserted times; "
        "different earlier/later states are not by themselves contradictions; "
        "'dialogue': narration authors withheld speech; 'private_mental_fact': "
        "narration asserts private mental content as objective fact; "
        "'uncertainty': a material grounded ambiguity prevents accepting 'candidate'."
    )
    revised = {}
    for key, field in fields.items():
        if key == "source_evidence":
            revised["source_refs"] = {
                "type": "array",
                "minItems": 1,
                "description": (
                    "JSON pointers relative to 'source' establishing 'kind'; "
                    "values are resolved from 'source', not written here. "
                    "Existing references must support 'detail', not merely exist."
                ),
                "items": {"type": "string", "enum": list(nodes(source))},
            }
        else:
            revised[key] = field
    item = result["schema"]["properties"]["issues"]["items"]
    item["properties"] = revised
    item["required"] = list(revised)
    result["name"] = "source_reference_review"
    return result


async def review(client, cfg, case, sid):
    return await reviewer.call_agent(
        client,
        cfg,
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {"stage": "prose", "source": case["source"], "candidate": case["candidate"]},
                    ensure_ascii=False,
                ),
            },
        ],
        agent="source_reference_screen",
        json_schema=schema(case["source"]),
        max_tokens=16384,
        session_id=sid,
        turn_number=2,
    )


async def capture(case):
    bodies = []

    def respond(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"issues":[],"reject":false}'}}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        await review(client, CONFIG, case, "")
    assert len(bodies) == 1
    return bodies[0]


def hashes():
    paths = [
        HERE / "screen.py",
        HERE / "PREREGISTRATION.md",
        PARENT / "manifest.json",
        PARENT / "screen.py",
    ]
    paths.extend(ROOT.joinpath("src/llm").rglob("*.py"))
    for folder in [
        "69-prose-admission",
        "69-admission-screen",
        "69-review-provenance",
        "69-prose-compensation",
        "69-runner-director-live",
    ]:
        paths.append(PARENT.parent / folder / "screen.py")
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


async def prepare():
    assert not MANIFEST.exists()
    retained = prior.read(PARENT / "manifest.json")
    cases = [copy.deepcopy(c) for c in retained["cases"] if c["id"] in ["r1", "r7", "r8"]]
    for case in cases:
        request = await capture(case)
        assert request["messages"][1] == case["request"]["messages"][1]
        before, after = copy.deepcopy(case["request"]), copy.deepcopy(request)
        before.pop("messages")
        after.pop("messages")
        assert before == after, "Change outside schema-bearing system message"
        assert request["messages"][0]["content"].startswith(SYSTEM)
        case["request"] = request
    jobs = [[case["id"], repeat] for repeat in range(1, 5) for case in cases]
    random.Random(223).shuffle(jobs)
    reviewer.write(MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print("Frozen 12 logical reviews", flush=True)


async def run():
    manifest = prior.read(MANIFEST)
    assert manifest["hashes"] == hashes()
    runs = HERE / "runs"
    runs.mkdir()
    provider = prior.read(ROOT / ".data/config.json")["providers"]["deepseek"]
    reviewer.base.prior.DeepSeekAdapter().validate_api_base(provider["api_base"])
    cfg = {**CONFIG, "api_base": provider["api_base"], "api_key": provider["api_key"]}
    cases = {c["id"]: c for c in manifest["cases"]}
    semaphore = asyncio.Semaphore(4)

    async def job(cid, repeat):
        async with semaphore:
            case = cases[cid]
            stem = f"{cid}-{repeat}"
            network = reviewer.CurlTransport(runs, stem, [case["request"]])
            result = {"case": cid, "repeat": repeat, "terminal_success": False}
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                try:
                    value = await review(client, cfg, case, str(uuid4()))
                    lookup = nodes(case["source"])
                    evidence = [
                        {ref: lookup[ref] for ref in issue["source_refs"]}
                        for issue in value["issues"]
                    ]
                    result.update(
                        terminal_success=True,
                        output=value,
                        resolved_evidence=evidence,
                        consistent=value["reject"] == bool(value["issues"]),
                    )
                except Exception as exc:
                    result["error"] = repr(exc)
            result["attempts"] = network.attempts
            reviewer.write(runs / f"{stem}.result.json", result)
            print(
                f"{stem}: success={result['terminal_success']} attempts={network.attempts}",
                flush=True,
            )

    await asyncio.gather(*(job(cid, repeat) for cid, repeat in manifest["jobs"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "run"])
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else run())
