"""Contrast original and clarified weather constraints on retained prose pairs."""

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
ROOT = HERE.parents[2]
PARENT = HERE.parent / "69-prose-challenger"
MANIFEST = HERE / "manifest.json"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA != ROOT / ".data" and ROOT / ".data" not in DATA.parents
spec = importlib.util.spec_from_file_location("model_only_probe", PARENT / "screen.py")
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
CONFIG = probe.CONFIG
SOURCE_VALUE = (
    "Bento retira a barra do portal azul e puxa a folha azul até abrir completamente a passagem. "
    "Sua intervenção é suficiente. Não há nova ventania neste turno: nenhuma rajada forte que "
    "empurre pessoas, objetos ou folhas de portal. O ar pode circular fracamente, "
    "sem essa força nem "
    "mudança de abertura ou deslocamento. "
    "Não há outra causa de mudança de abertura de qualquer portal."
)
STORM = (
    "Uma ventania violenta varre o salão; as rajadas açoitam Iara e Bento, "
    "que precisam se firmar para não cair."
)
LAMP = "Uma corrente fraca de ar apaga a lanterna de Iara, e seu facho desaparece."


def read(path: Path):
    return json.loads(path.read_text())


def write(path: Path, value) -> None:
    probe.write(path, value)


def hashes() -> dict[str, str]:
    paths = [
        HERE / "screen.py",
        HERE / "PREREGISTRATION.md",
        PARENT / "screen.py",
        PARENT / "manifest.json",
    ]
    for folder in [
        "69-prose-admission",
        "69-admission-screen",
        "69-review-provenance",
        "69-prose-compensation",
        "69-runner-director-live",
    ]:
        paths.append(HERE.parent / folder / "screen.py")
    paths.extend((ROOT / "src/llm").rglob("*.py"))
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)
    }


async def capture(source: dict, prose: str) -> dict:
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"issues":[],"reject":false}'}}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        await probe.probe.review(client, CONFIG, source, prose, "")
    assert len(requests) == 1
    return requests[0]


async def prepare() -> None:
    assert not MANIFEST.exists(), "Preserve frozen execution"
    parent = read(PARENT / "manifest.json")
    originals = [copy.deepcopy(case) for case in parent["cases"] if case["id"].startswith("r")]
    assert len(originals) == 4
    complete = originals[0]
    storm = {
        "id": "r5",
        "source": complete["source"],
        "candidate": complete["candidate"] + "\n\n" + STORM,
    }
    storm["request"] = await capture(storm["source"], storm["candidate"])
    originals.append(storm)
    lamp = {
        "id": "r6",
        "source": complete["source"],
        "candidate": complete["candidate"] + "\n\n" + LAMP,
    }
    lamp["request"] = await capture(lamp["source"], lamp["candidate"])
    originals.append(lamp)
    cases = []
    for original in originals:
        for arm in ["original", "clarified"]:
            source = copy.deepcopy(original["source"])
            if arm == "clarified":
                source["supported_this_beat"]["new_causes"]["value"] = SOURCE_VALUE
            request = await capture(source, original["candidate"])
            expected = copy.deepcopy(original["request"])
            payload = json.loads(expected["messages"][1]["content"])
            assert payload["source"] == original["source"]
            if arm == "clarified":
                payload["source"]["supported_this_beat"]["new_causes"]["value"] = SOURCE_VALUE
                expected["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
            assert request == expected, "Unexpected request intervention"
            prompt = json.dumps(request["messages"], ensure_ascii=False)
            assert not probe.probe.base.operator_ontology_hits(prompt)
            assert "private-blue" not in prompt and "private-green" not in prompt
            cases.append(
                {
                    "id": f"{original['id']}-{arm}",
                    "source": source,
                    "candidate": original["candidate"],
                    "request": request,
                    "repeats": 4,
                }
            )
    jobs = []
    rng = random.Random(29142)
    for repeat in range(1, 5):
        block = [[case["id"], repeat] for case in cases]
        rng.shuffle(block)
        jobs.extend(block)
    write(MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print("Frozen48 reviewer calls; only one source field differs between arms", flush=True)


async def run() -> None:
    manifest = read(MANIFEST)
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    runs = HERE / "runs"
    runs.mkdir()
    provider = read(ROOT / ".data/config.json")["providers"]["deepseek"]
    probe.probe.base.prior.DeepSeekAdapter().validate_api_base(provider["api_base"])
    cfg = {**CONFIG, "api_base": provider["api_base"], "api_key": provider["api_key"]}
    semaphore = asyncio.Semaphore(4)
    cases = {case["id"]: case for case in manifest["cases"]}

    async def job(case_id: str, repeat: int) -> None:
        async with semaphore:
            case = cases[case_id]
            stem = f"{case_id}-{repeat}"
            network = probe.probe.CurlTransport(runs, stem, [case["request"]])
            result = {"case": case_id, "repeat": repeat, "terminal_success": False}
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                try:
                    value = await probe.probe.review(
                        client, cfg, case["source"], case["candidate"], str(uuid4())
                    )
                    result.update(
                        terminal_success=True,
                        output=value,
                        consistent=value["reject"] == bool(value["issues"]),
                    )
                except Exception as exc:
                    result["error"] = repr(exc)
            result["attempts"] = network.attempts
            write(runs / f"{stem}.result.json", result)
            print(
                f"{stem}: success={result['terminal_success']} attempts={network.attempts}",
                flush=True,
            )

    await asyncio.gather(*(job(case_id, repeat) for case_id, repeat in manifest["jobs"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else run())
