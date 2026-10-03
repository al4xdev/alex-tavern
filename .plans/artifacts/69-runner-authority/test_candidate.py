"""Real Runner transactions with deterministic model/reviewer doubles."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from typing import Any

# This file can run independently of tests/conftest.py. Isolation precedes all
# application imports and does not reuse a caller's real runtime data directory.
os.environ["ROLEPLAY_DATA_DIR"] = tempfile.mkdtemp(prefix="69-runner-authority-")

import httpx  # noqa: E402
import pytest  # noqa: E402

from src.durable_state import bootstrap_physical_entities  # noqa: E402
from src.models import Roteiro, RoteiroBeat, game_state_to_dict  # noqa: E402
from src.prompt_contract import operator_ontology_hits  # noqa: E402
from src.runner import Runner  # noqa: E402
from src.store.locks import session_lock  # noqa: E402
from src.store.sessions import save_game  # noqa: E402
from tests.factories import director_beat, make_cast, make_scene  # noqa: E402

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("authority_candidate", HERE / "candidate.py")
assert spec is not None and spec.loader is not None
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

GOALS = [
    {"anchor": "azul aberto", "kind": "aperture", "target": "portal azul", "state": "open"},
    {
        "anchor": "Téo no túnel",
        "kind": "crossing",
        "actor": "Téo",
        "target": "portal azul",
        "destination": "túnel",
    },
]
ORIGINAL_FALSE_TEXT = "O portal azul está aberto. Téo está no túnel. Iara ajusta a lanterna."
FALSE_TEXT = "O portal azul aberto deixa Téo no túnel, do outro lado. Iara ajusta a lanterna."
CONFIG = {
    "api_base": "https://fixture.invalid/v1",
    "provider": "llama_cpp",
    "roteiro_enabled": False,
    "autonomous_burst_max_beats": 1,
}


def event(text: str, witnesses: list[str] | None = None) -> dict[str, Any]:
    return {
        "event_kind": "physical_outcome",
        "subject_id": "Narrator",
        "content": text,
        "witness_ids": ["C1", "C2", "C3"] if witnesses is None else witnesses,
    }


def operation(kind: str, target: str = "portal azul", **fields: str) -> dict[str, str]:
    return {
        "kind": kind,
        "target": target,
        "actor": "",
        "from_state": "",
        "to_state": "",
        "result": "",
        "cause": "",
        **fields,
    }


def opening(from_state: str = "closed", to_state: str = "open", **fields: str) -> dict:
    return operation(
        "aperture_change",
        from_state=from_state,
        to_state=to_state,
        cause="Bento retira a barra do portal azul e puxa sua folha.",
        **fields,
    )


def crossing(result: str = "crossed") -> dict:
    return operation("attempt_result", actor="Téo", result=result)


def output(steps: list[dict] | None = None, text: str = FALSE_TEXT, **fields: Any) -> dict:
    result = director_beat(next_speakers=[], perception_events=[event(text)], **fields)
    result.pop("narration")
    result["physical_steps"] = copy.deepcopy(steps or [])
    return result


def attempts(*turns: int) -> dict[str, list[dict[str, str]]]:
    return {
        str(turn): [
            {"actor": "Téo", "target": "portal azul", "origin": "salão", "destination": "túnel"}
        ]
        for turn in turns
    }


class Models:
    """Requests pass through the actual Director builder and shared LLM client."""

    def __init__(self, *outputs: dict) -> None:
        self.outputs = list(outputs)
        self.requests: list[dict] = []
        self.replan_requests: list[dict] = []
        self.reviews: list[tuple[str, dict]] = []
        self.refuse: str = ""
        self.prose_override: str | None = None

    def transport(self, request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if payload["response_format"]["json_schema"]["name"] == "roteiro_next_beat":
            self.replan_requests.append(payload)
            response = {
                "act_completed": False,
                "beat": {
                    "beat_id": "continuation",
                    "intent": "Abrir o portal azul e permitir a passagem de Téo.",
                    "expected_actors": ["C2"],
                    "expected_anchors": ["azul aberto", "Téo no túnel", "lanterna"],
                    "exit_condition": "Bento decide como prosseguir.",
                },
            }
            return httpx.Response(
                200, json={"choices": [{"message": {"content": json.dumps(response)}}]}
            )
        self.requests.append(payload)
        assert self.outputs, "Unexpected model retry or extra call"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(self.outputs.pop(0))}}]}
        )

    async def review(self, stage: str, payload: dict) -> bool:
        self.reviews.append((stage, copy.deepcopy(payload)))
        return stage != self.refuse

    async def prose(self, game, events, turn_number, viewers=None, **kwargs) -> str:
        if self.prose_override is not None:
            return self.prose_override
        scope = set(game.characters) if viewers is None else set(viewers)
        return " ".join(
            item["content"]
            for item in events
            if scope.intersection(item["witness_ids"]) or item["subject_id"] in scope
        )


async def seed(runner: Runner, *, aperture: str = "closed", declared: dict | None = None) -> str:
    cast = make_cast("Iara", "Bento", "Téo")
    scene = make_scene(
        characters=cast,
        present=[*cast, "Player"],
        location="observatório",
        zones={"salão": ["túnel", "pátio"], "túnel": ["salão"], "pátio": ["salão"]},
        positions=dict.fromkeys(cast, "salão"),
        physical_facts={"portal azul": aperture, "portal verde": "closed", "lanterna": "acesa"},
    )
    sid = await runner.start_session(
        {"characters": cast, "scene": scene, "controlled_character_id": "C1"}
    )
    async with session_lock(sid):
        game = await_load_without_lock(sid)
        game.durable_state = bootstrap_physical_entities(
            [
                {
                    "entity_id": "private-blue-entity",
                    "key": "portal azul",
                    "kind": "passage",
                    "scene_key": "observatório",
                    "dimensions": {"aperture": aperture},
                },
                {
                    "entity_id": "private-green-entity",
                    "key": "portal verde",
                    "kind": "passage",
                    "scene_key": "observatório",
                    "dimensions": {"aperture": "closed"},
                },
            ],
            character_ids=set(cast),
        )
        game.roteiro = Roteiro(
            premise="Encontrar uma saída sem perder a lanterna.",
            beat=RoteiroBeat(
                beat_id="fixture",
                intent="Abrir o portal azul e permitir a passagem de Téo.",
                expected_actors=["C2"],
                budget_turns=12,
                expected_anchors=["azul aberto", "Téo no túnel", "lanterna"],
            ),
        )
        game.plugin_state["authority_fixture"] = {
            "routes": {
                "portal azul": {"origin": "salão", "destination": "túnel"},
                "portal verde": {"origin": "salão", "destination": "pátio"},
            },
            "attempts_by_turn": declared or {},
            "goals": copy.deepcopy(GOALS),
        }
        save_game(game)
    return sid


def await_load_without_lock(sid):
    from src.store.sessions import load_game

    game = load_game(sid)
    assert game is not None
    return game


async def snapshot(runner: Runner, sid: str) -> dict:
    game = await runner.get_state(sid)
    assert game is not None
    return game_state_to_dict(game)


@pytest.mark.asyncio
@pytest.mark.parametrize("text,covered", [(ORIGINAL_FALSE_TEXT, False), (FALSE_TEXT, True)])
async def test_baseline_text_covers_anchor_without_physical_commit(text, covered) -> None:
    baseline = output(text=text)
    baseline.pop("physical_steps")
    models = Models(baseline)
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = Runner(client, CONFIG)
        runner._render_narration = models.prose
        sid = await seed(runner)
        await runner.player_turn(sid, action="Observo o portal azul.")
        game = await runner.get_state(sid)
        assert game is not None and game.roteiro is not None
        assert (
            game.durable_state.physical_entities["private-blue-entity"].dimensions["aperture"].state
            == "closed"
        )
        assert game.scene.positions["C3"] == "salão"
        assert ("azul aberto" in game.roteiro.anchors_seen) is covered
        assert ("Téo no túnel" in game.roteiro.anchors_seen) is covered


@pytest.mark.asyncio
async def test_event_and_final_prose_cannot_complete_physical_goals() -> None:
    models = Models(output())
    models.prose_override = FALSE_TEXT
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner)
        await runner.player_turn(sid, action="Observo o portal azul.")
        game = await runner.get_state(sid)
        assert game is not None and game.roteiro is not None
        assert candidate.project(game, 0)["apertures"]["portal azul"] == "closed"
        assert game.scene.positions["C3"] == "salão"
        assert game.roteiro.anchors_seen == ["lanterna"]
        decision = runner._evaluate_roteiro(game, 2)
        assert decision.progress.anchors_missing == ("azul aberto", "Téo no túnel")
        # This is an exposed narrative failure, not a successful semantic gate.
        assert any(record.content == FALSE_TEXT for record in game.history)
        assert {stage for stage, _ in models.reviews} == {"director", "prose"}


@pytest.mark.asyncio
async def test_hidden_claims_in_cause_have_no_state_authority() -> None:
    close = operation(
        "aperture_change",
        from_state="open",
        to_state="closed",
        cause="O vento fecha o portal azul; logo o portal azul abre e Téo atravessa.",
    )
    models = Models(output([close], text="Iara ajusta a lanterna."))
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner, aperture="open")
        await runner.player_turn(sid, action="Observo o portal azul.")
        game = await runner.get_state(sid)
        assert game is not None and game.roteiro is not None
        assert candidate.project(game, 0)["apertures"]["portal azul"] == "closed"
        assert game.scene.positions["C3"] == "salão"
        assert game.roteiro.anchors_seen == ["lanterna"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parallel",
    [
        {"scene_update": {"portal azul": "open"}},
        {"zone_moves": {"C3": "túnel"}},
        {"scene_update": {"location": "cidade"}},
        {"scene_update": {"present_characters": ["C1", "C2"]}},
        {"scene_update": {"zones": {"salão": []}}},
    ],
)
async def test_parallel_bypasses_abort_the_whole_turn(parallel: dict) -> None:
    models = Models(output([], **parallel))
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner)
        before = await snapshot(runner, sid)
        with pytest.raises(candidate.TurnRejectedError):
            await runner.player_turn(sid, action="Observo o portal azul.")
        assert await snapshot(runner, sid) == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "steps,parallel,declared",
    [
        ([opening()], {"zone_moves": {"C3": "túnel"}}, {}),
        ([crossing()], {}, attempts(1)),
        ([opening(), crossing()], {}, {}),
        (
            [operation("aperture_change", from_state="closed", to_state="closed", cause="Vento.")],
            {},
            {},
        ),
    ],
)
async def test_invalid_typed_transactions_leave_no_partial_commit(
    steps, parallel, declared
) -> None:
    models = Models(output(steps, **parallel))
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner, declared=declared)
        before = await snapshot(runner, sid)
        with pytest.raises(ValueError):
            await runner.player_turn(sid, action="Observo o portal azul.")
        assert await snapshot(runner, sid) == before


@pytest.mark.asyncio
async def test_empty_steps_cannot_omit_a_declared_attempt() -> None:
    models = Models(output([]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner, declared=attempts(1))
        before = await snapshot(runner, sid)
        with pytest.raises(candidate.TurnRejectedError, match="Not every declared attempt"):
            await runner.player_turn(sid, action="Observo o portal azul.")
        assert await snapshot(runner, sid) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("malformation", ["missing_steps", "wrong_type", "unknown_target"])
async def test_schema_failures_exhaust_existing_retries_without_a_commit(malformation: str) -> None:
    response = output([opening()])
    if malformation == "missing_steps":
        response.pop("physical_steps")
    elif malformation == "wrong_type":
        response["physical_steps"] = {}
    else:
        response["physical_steps"][0]["target"] = "portal inventado"
    models = Models(*(copy.deepcopy(response) for _ in range(3)))
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner)
        before = await snapshot(runner, sid)
        with pytest.raises(ValueError, match="3 attempts"):
            await runner.player_turn(sid, action="Observo o portal azul.")
        assert len(models.requests) == 3
        assert models.reviews == []
        assert await snapshot(runner, sid) == before


@pytest.mark.asyncio
async def test_consecutive_reload_projection_and_undo() -> None:
    models = Models(
        output(
            [
                operation(
                    "aperture_change",
                    from_state="open",
                    to_state="closed",
                    cause="O vento fecha o portal azul.",
                ),
                crossing("blocked"),
            ],
            text="O vento fecha o portal azul e impede Téo de passar. Iara ajusta a lanterna.",
        ),
        output([crossing("blocked")], text="A barra resiste a Téo. Iara levanta a lanterna."),
        output(
            [opening(), crossing()],
            text="Bento abre o portal azul; Téo passa para o túnel. Iara baixa a lanterna.",
            zone_moves={"C3": "túnel"},
            scene_update={"portal azul": "open", "lanterna": "baixa"},
        ),
        output([], text="Téo ajusta a mochila no túnel. Iara mantém a lanterna baixa."),
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner, aperture="open", declared=attempts(1, 2, 3))
        reloaded = []
        for _ in range(4):
            await runner.player_turn(sid, action="Observo o portal azul.")
            game = await runner.get_state(sid)
            assert game is not None
            reloaded.append(game)
        assert [candidate.project(game, 0)["apertures"]["portal azul"] for game in reloaded] == [
            "closed",
            "closed",
            "open",
            "open",
        ]
        assert [game.scene.positions["C3"] for game in reloaded] == [
            "salão",
            "salão",
            "túnel",
            "túnel",
        ]
        assert [game.roteiro.anchors_seen for game in reloaded] == [
            ["lanterna"],
            ["lanterna"],
            ["lanterna", "azul aberto", "Téo no túnel"],
            ["lanterna", "azul aberto", "Téo no túnel"],
        ]
        assert reloaded[-1].scene.physical_facts["lanterna"] == "baixa"
        assert len(models.replan_requests) == 1
        for index, request in enumerate(models.requests):
            user = request["messages"][1]["content"]
            projected = json.loads(user.split("committed_physical: ")[1].split("\n")[0])
            if index:
                expected = candidate.project(reloaded[index - 1], index + 1)
                if index == 2:
                    # Real hard-cap replanning resets current-beat coverage before
                    # the third Director call. It never replaces physical state.
                    expected["covered_goals"] = []
                assert projected == expected
            joined = json.dumps(request["messages"], ensure_ascii=False)
            assert "private-blue-entity" not in joined and "private-green-entity" not in joined
            assert not operator_ontology_hits(joined)
        assert (
            "Beat elements awaiting coverage: azul aberto, Téo no túnel"
            in models.requests[2]["messages"][1]["content"]
        )
        assert (
            "Beat elements awaiting coverage:" not in models.requests[3]["messages"][1]["content"]
        )
        await runner.undo_turn(sid)
        await runner.undo_turn(sid)
        restored = await runner.get_state(sid)
        assert restored is not None
        assert candidate.project(restored, 3) == candidate.project(reloaded[1], 3)


@pytest.mark.asyncio
@pytest.mark.parametrize("refused_stage", ["director", "prose"])
async def test_semantic_refusal_keeps_the_entire_persisted_state(refused_stage: str) -> None:
    models = Models(output([opening(), crossing()]))
    models.refuse = refused_stage
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner, declared=attempts(1))
        before = await snapshot(runner, sid)
        with pytest.raises(candidate.TurnRejectedError):
            await runner.player_turn(sid, action="Observo o portal azul.")
        assert await snapshot(runner, sid) == before


@pytest.mark.asyncio
async def test_restricted_events_keep_their_viewer_audiences() -> None:
    response = output([], text="Iara nota um brilho reservado na lanterna.")
    response["perception_events"] = [event("Iara nota um brilho reservado na lanterna.", ["C1"])]
    models = Models(response)
    async with httpx.AsyncClient(transport=httpx.MockTransport(models.transport)) as client:
        runner = candidate.AuthorityRunner(client, CONFIG, models.review)
        runner._generate_prose = models.prose
        sid = await seed(runner)
        await runner.player_turn(sid, action="Observo o portal azul.")
        game = await runner.get_state(sid)
        assert game is not None
        rendered = [record for record in game.history if record.content_type == "narration"]
        assert len(rendered) == 1
        assert rendered[0].audience == ["C1"]
        prose_reviews = [payload for stage, payload in models.reviews if stage == "prose"]
        assert prose_reviews and all(payload["viewers"] == ["C1"] for payload in prose_reviews)
