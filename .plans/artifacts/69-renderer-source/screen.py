"""Review retained prose using the actual renderer boundary and admitted counterfactual."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT = HERE.parent / "69-reference-full-screen"
spec = importlib.util.spec_from_file_location("full_boundary", PARENT / "screen.py")
assert spec and spec.loader
full = importlib.util.module_from_spec(spec)
spec.loader.exec_module(full)
base = full.base
OLD_HASHES = full.hashes
OLD_SCHEMA = base.schema
OLD_SENTENCE = (
    "Current inputs provide original source context; their world resolution "
    "belongs to upstream admission. "
)
NEW_SENTENCE = (
    "Source contains reader-entitled renderer context; "
    "confirmed events have already been admitted upstream. "
)
assert base.SYSTEM.count(OLD_SENTENCE) == 1
base.SYSTEM = base.SYSTEM.replace(OLD_SENTENCE, NEW_SENTENCE)
DETAIL = (
    "Explain 'kind' using facts at 'source_refs'. Check depiction of 'confirmed_events' "
    "against 'renderer_context', not whether upstream admission was physically feasible."
)
EXTINCTION = "Uma corrente fraca de ar apaga a lanterna de Iara, e seu facho desaparece."

from src.agents.prose import build_prose_messages, build_prose_schema  # noqa: E402
from src.models import dict_to_game_state  # noqa: E402
from src.runner import Runner  # noqa: E402


def schema(source):
    value = OLD_SCHEMA(source)
    value["schema"]["properties"]["issues"]["items"]["properties"]["detail"]["description"] = DETAIL
    return value


def hashes():
    value = OLD_HASHES()
    for path in [
        PARENT / "screen.py",
        PARENT / "manifest.json",
        ROOT / "src/runner.py",
        ROOT / "src/agents/prose.py",
        ROOT / "src/perception.py",
        ROOT / "src/models.py",
        HERE.parent / "69-runner-authority/candidate.py",
    ]:
        value[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return value


base.HERE = HERE
base.MANIFEST = HERE / "manifest.json"
base.schema = schema
base.hashes = hashes


async def renderer_source(fixture, text, admit):
    prose_probe = base.reviewer.prose
    game = dict_to_game_state(fixture["game"])
    raw = copy.deepcopy(fixture["director"])
    if admit:
        raw["scene_update"]["lanterna"] = "apagada"
        event = copy.deepcopy(raw["perception_events"][0])
        event["event_kind"] = "physical_outcome"
        event["content"] = EXTINCTION
        raw["perception_events"].append(event)
    cfg = prose_probe.CONFIG
    captured = []

    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps({"narration": text})}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        authority = prose_probe.prior.candidate.AuthorityRunner(
            client, cfg, prose_probe.prior.clean_review
        )
        authority._apply_canon(game, raw, 2)
        runner = Runner(client, cfg)
        assert runner._narration_clusters(game, raw["perception_events"]) == [None]
        messages = build_prose_messages(
            game.scene,
            game.characters,
            game.player.controlled_character_id,
            game.history,
            raw["perception_events"],
            context_max=cfg.get("context_max"),
            max_tokens=cfg["max_tokens_narrator"],
            min_words=cfg["narrator_min_words"],
            blocking=raw["blocking"],
        )
        await runner._render_narration(game, raw["perception_events"], 2, blocking=raw["blocking"])
    assert len(captured) == 1
    if not admit:
        assert captured[0] == fixture["requests"][0], "Actual retained renderer body drift"
    # Verify pre-adapter context against independently adapted shared-client capture.
    expected = copy.deepcopy(messages)
    # Match the shared client's language/text policy before vendor schema adaptation.
    policy = (
        f"\n- Always respond and write in {cfg['language']}."
        "\n- Do not use Unicode em dash (U+2014) or en dash (U+2013) anywhere in your writing; "
        "use commas, periods, or parentheses instead."
    )
    expected[0]["content"] = expected[0]["content"].rstrip() + policy
    adapter = prose_probe.prior.DeepSeekAdapter()
    adapted = adapter.prepare_request(expected, None, build_prose_schema(), cfg["thinking_enabled"])
    assert adapted.messages == captured[0]["messages"]
    events = [
        {"event_kind": e["event_kind"], "content": e["content"]}
        for e in raw["perception_events"]
        if e["event_kind"] != "audible_speech"
    ]
    return {"renderer_context": expected, "confirmed_events": events}, captured[0]


async def prepare():
    assert not base.MANIFEST.exists()
    protocol = (HERE / "PREREGISTRATION.md").read_text().replace("\n", " ")
    assert DETAIL in protocol and NEW_SENTENCE.strip() in protocol
    retained = base.prior.read(PARENT / "manifest.json")
    old = {c["id"]: c for c in retained["cases"]}
    fixture = base.prior.read(HERE.parent / "69-prose-compensation/manifest.json")["cases"][1]
    source, capture = await renderer_source(fixture, old["r1"]["candidate"], False)
    admitted, admitted_capture = await renderer_source(fixture, old["r6"]["candidate"], True)
    assert old["r6"]["candidate"] == old["r1"]["candidate"] + "\n\n" + EXTINCTION
    cases = []
    for cid, text, context, reject in [
        ("r1", old["r1"]["candidate"], source, False),
        ("r6", old["r6"]["candidate"], source, True),
        ("r9", old["r6"]["candidate"], admitted, False),
        ("r8", old["r8"]["candidate"], source, True),
    ]:
        case = {"id": cid, "candidate": text, "source": context, "expected_reject": reject}
        case["request"] = await base.capture(case)
        prompt = str(case["request"]["messages"])
        assert not base.reviewer.base.operator_ontology_hits(prompt)
        assert all(
            token not in prompt
            for token in ["private-blue", "private-green", '"C1"', '"C2"', '"C3"']
        )
        cases.append(case)
    jobs = [[c["id"], n] for n in range(1, 5) for c in cases]
    random.Random(457).shuffle(jobs)
    base.reviewer.write(
        base.MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "jobs": jobs,
            "renderer_requests": [capture, admitted_capture],
        },
    )
    print(
        "Frozen 16 reviews; actual renderer parity and coherent admission counterfactual",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "run"])
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else base.run())
