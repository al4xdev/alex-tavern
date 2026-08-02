"""The beat's two clocks, driven end to end through a real autonomous burst.

This is a manipulation check, not evidence about repetition: it proves the
ceiling is wired and fires, so that a null result in the live battery means "the
fix does not help" rather than "the fix never ran".

The defect it pins (docs/cases/20-repetition-baseline-2026-08-01.md): a bare
skip commits up to ``autonomous_burst_max_beats`` turns while
``beat_actions_elapsed`` advances once, so a cap counted in ACTIONS could not
fire inside a burst. Measured over sessions 20d4cdb3 and 15d40dfa, 17 turns
produced two beat exits — both from the act clock — and single beats occupied
five consecutive narrated turns.

Nothing here is stubbed except the model. ``replan_roteiro`` runs for real, so
the cooldown, the counter reset and ``beat_started_turn`` are the production
state transitions; only ``call_agent`` is scripted, and it returns a DISTINCT
beat every time. That last part matters: the sibling harness in
``test_roteiro.py`` hands back one shared roteiro object, which would make every
assertion about beat identity vacuous.
"""

from __future__ import annotations

import httpx
import pytest

from src.models import CharacterPerspective, Roteiro, RoteiroAct, RoteiroBeat, Scene, deepcopy_scene
from src.roteiro import HARD_BEAT_ACTION_CAP, HARD_BEAT_TURN_CAP
from src.store.sessions import delete_session
from tests.factories import director_beat, make_cast

CHARACTERS = make_cast("Rui", "Marta", "Bento")
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)
BURST_BEATS = 6  # the production default

# Genuinely unrelated stimuli, one per beat. They must not merely differ by an
# index: the burst's own dedup filter (repeats_event_text, threshold 0.8) drops
# near-identical events, so a templated fixture would measure that filter
# instead of the beat clock and every turn after the first would go silent.
DISTINCT_EVENTS = [
    "Uma tabua do assoalho cede sob o peso de alguem.",
    "O lampiao pendurado na viga se apaga sozinho.",
    "Chega um cheiro forte de fumaca vindo da cozinha.",
    "Batidas rapidas soam contra a porta dos fundos.",
    "Um cavalo relincha alto no patio e puxa a corda.",
    "A janela do sotao bate com o vento e estilhaca.",
    "Moedas rolam do balcao e se espalham pelo chao.",
    "Um estranho encapuzado para na soleira e observa.",
    "O relogio de parede comeca a bater fora de hora.",
    "Agua comeca a pingar do teto sobre a mesa grande.",
    "Alguem derruba uma bandeja de canecas de estanho.",
    "O fogo da lareira cresce de repente e chia alto.",
]


def _unreachable_beat(index: int) -> RoteiroBeat:
    """A beat whose coverage can never complete, so only a clock can end it."""
    return RoteiroBeat(
        beat_id=f"B{index}",
        intent=f"Situacao numero {index} pressiona a sala",
        expected_actors=["C2"],
        expected_anchors=[f"objeto inatingivel {index}"],
        exit_condition="alguem reage",
        budget_turns=10,  # far above both caps: the caps must be what fires
    )


def _seed_roteiro() -> Roteiro:
    return Roteiro(
        premise="Uma heranca disputada chega a estalagem.",
        acts=[
            RoteiroAct(act_id="act1", summary="A carta chega", exit_condition="carta aberta"),
            RoteiroAct(act_id="act2", summary="O confronto", exit_condition="segredo dito"),
        ],
        act_index=0,
        beat=_unreachable_beat(0),
        beat_started_turn=1,
    )


async def _drive(monkeypatch, actions: int, max_beats: int = BURST_BEATS):  # noqa: ANN001, ANN202
    """Run ``actions`` bare skips; return every roteiro evaluation that happened.

    Each entry is what the deterministic engine saw and decided, captured by
    wrapping the real ``evaluate_roteiro`` rather than re-deriving it.
    """
    import src.roteiro as roteiro_mod
    import src.runner as runner_mod
    from src.runner import Runner

    async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return CharacterPerspective(
            initialized_turn=kwargs.get("turn_number", 0),
            processed_through_turn=kwargs.get("turn_number", 0),
        )

    monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

    # The only stub: the architect. Every replan yields a NEW beat.
    minted = {"count": 0}

    async def fake_call_agent(client, config, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        minted["count"] += 1
        beat = _unreachable_beat(minted["count"])
        payload = {
            "beat_id": beat.beat_id,
            "intent": beat.intent,
            "expected_actors": list(beat.expected_actors),
            "expected_anchors": list(beat.expected_anchors),
            "exit_condition": beat.exit_condition,
            "budget_turns": beat.budget_turns,
        }
        result: dict = {"act_completed": False, "beat": payload}
        # An act-scope replan also rewrites the remaining acts.
        if "acts" in kwargs.get("json_schema", {}).get("schema", {}).get("properties", {}):
            result["acts"] = [
                {
                    "act_id": f"act{minted['count']}",
                    "summary": f"Ato reescrito {minted['count']}",
                    "exit_condition": "algo muda",
                    "duration_ticks": 6,
                    "world_event": "o sino toca",
                }
            ]
        return result

    monkeypatch.setattr(roteiro_mod, "call_agent", fake_call_agent)

    evaluations: list[dict] = []
    real_evaluate = runner_mod.evaluate_roteiro

    def spy_evaluate(roteiro, history, controlled_id, next_turn):  # noqa: ANN001, ANN202
        decision = real_evaluate(roteiro, history, controlled_id, next_turn)
        progress = decision.progress
        evaluations.append(
            {
                "next_turn": next_turn,
                "beat_id": roteiro.beat.beat_id if roteiro.beat else None,
                "actions_elapsed": progress.actions_elapsed if progress else None,
                "turns_elapsed": progress.turns_elapsed if progress else None,
                "action": decision.action,
                "reason": decision.reason,
            }
        )
        return decision

    monkeypatch.setattr(runner_mod, "evaluate_roteiro", spy_evaluate)

    speakers = iter(["C2", "C3"] * (max_beats * actions + 4))
    # What the DIRECTOR was actually handed, recorded after _maintain_roteiro has
    # had its say. The evaluation list alone cannot answer this: the evaluation
    # that stalls a beat still sees the OLD beat, while the turn it belongs to is
    # narrated under the new one.
    staged: list[tuple[int, str]] = []

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        assert game.roteiro is not None and game.roteiro.beat is not None
        staged.append((turn_number, game.roteiro.beat.beat_id))
        # A burst beat with no novel perception event narrates nothing by
        # design (runner.py, "atmospheric beat" suppression), so a fixture
        # without events would measure silence instead of the clock.
        return director_beat(
            next_speakers=[next(speakers)],
            perception_events=[
                {
                    "event_kind": "observation",
                    "subject_id": "Narrator",
                    "content": DISTINCT_EVENTS[(turn_number - 1) % len(DISTINCT_EVENTS)],
                    "witness_ids": ["C2", "C3"],
                }
            ],
        )

    async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return {"speech": "Digo alguma coisa nova.", "thought": None, "action_intent": None}

    config = {
        "auto_event_enabled": False,
        "roteiro_enabled": True,
        "autonomous_burst_max_beats": max_beats,
    }
    async with httpx.AsyncClient() as client:
        runner = Runner(client, dict(config))
        sid = await runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(runner, "_call_character", fake_character)
        monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: _prose())
        try:
            game = await runner.get_state(sid)
            assert game is not None
            game.roteiro = _seed_roteiro()
            runner_mod.save_game(game)
            for _ in range(actions):
                await runner.player_turn(sid, skip=True)
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)
    return evaluations, staged, game


async def _prose() -> str:
    return "Prosa."


def _occupancy(staged: list[tuple[int, str]]) -> dict[str, int]:
    """How many narrated turns each beat was handed to the Director for."""
    counts: dict[str, int] = {}
    for _, beat_id in staged:
        counts[beat_id] = counts.get(beat_id, 0) + 1
    return counts


class TestBeatTurnCeiling:
    @pytest.mark.asyncio
    async def test_a_single_burst_cannot_hold_one_beat_past_the_ceiling(self, monkeypatch) -> None:  # noqa: ANN001
        """Six beats from ONE skip: no beat may be active for more than 3 of them.

        Before the two clocks this was 6 — the whole burst under one contract,
        with the Director handed the same beat text (and the same pending-anchor
        line) turn after turn.
        """
        evaluations, staged, _ = await _drive(monkeypatch, actions=1)
        assert len(evaluations) == BURST_BEATS, "every beat of the burst must be evaluated"
        occupancy = _occupancy(staged)
        assert max(occupancy.values()) <= HARD_BEAT_TURN_CAP
        # And it genuinely moved on rather than silently doing nothing.
        assert len(occupancy) > 1, "the burst must have advanced to a new beat"
        assert any(e["action"] == "replan_beat" for e in evaluations)

    @pytest.mark.asyncio
    async def test_the_ceiling_fires_on_turns_while_the_action_budget_is_intact(
        self, monkeypatch
    ) -> None:
        """The stall inside a burst is charged to turns, not to the player."""
        evaluations, staged, _ = await _drive(monkeypatch, actions=1)
        stalls = [e for e in evaluations if e["reason"] == "stalled"]
        assert stalls, "the ceiling must fire inside a single action"
        for stall in stalls:
            assert stall["turns_elapsed"] >= HARD_BEAT_TURN_CAP
            assert stall["actions_elapsed"] < HARD_BEAT_ACTION_CAP, (
                "one submission must not consume the action budget"
            )

    @pytest.mark.asyncio
    async def test_a_beat_born_mid_burst_is_capped_too(self, monkeypatch) -> None:
        """The replacement beat starts its own turn clock, and that clock works.

        A beat minted mid-burst has ``beat_actions_elapsed == 0`` and used to be
        measured by the removed fallback, which read committed turns — so it was
        capped only by accident, and the accident reversed at the next action.
        """
        evaluations, staged, _ = await _drive(monkeypatch, actions=2)
        occupancy = _occupancy(staged)
        # Every beat after the seeded one was minted by a replan.
        for beat_id, turns in occupancy.items():
            assert turns <= HARD_BEAT_TURN_CAP, f"{beat_id} held the stage for {turns} turns"

    @pytest.mark.asyncio
    async def test_the_clock_never_regresses_across_an_action_boundary(self, monkeypatch) -> None:
        """Monotonicity, the property the removed ``or`` fallback destroyed.

        With the fallback, a beat born mid-burst read accumulated turns while
        its counter was 0, then dropped to 1 the moment the next submission
        incremented it — measured regressing 2 -> 1 in 20d4cdb3 at turn 7, which
        postponed the cap indefinitely.

        This is an invariant guard, not a reproduction: it holds on the old code
        too under this fixture, because there no replan ever fires and so no
        counter is ever reset to 0. It exists to keep the property once beats
        DO get replaced mid-burst, which is now the normal case.
        """
        evaluations, staged, _ = await _drive(monkeypatch, actions=2)
        by_beat: dict[str, list[dict]] = {}
        for entry in evaluations:
            by_beat.setdefault(entry["beat_id"], []).append(entry)

        for beat_id, entries in by_beat.items():
            actions = [e["actions_elapsed"] for e in entries]
            turns = [e["turns_elapsed"] for e in entries]
            assert actions == sorted(actions), f"{beat_id} action clock regressed: {actions}"
            assert turns == sorted(turns), f"{beat_id} turn clock regressed: {turns}"

    @pytest.mark.asyncio
    async def test_hysteresis_never_swallows_the_ceiling(self, monkeypatch) -> None:
        """Cooldown and ceiling share the turn unit, so they cannot deadlock.

        ``cooldown_until_turn`` is turn-based; if the ceiling were action-based
        the two would race in different units and a beat could be held past its
        ceiling waiting for a cooldown counted in something else.
        """
        evaluations, staged, _ = await _drive(monkeypatch, actions=2)
        assert not [e for e in evaluations if e["reason"] == "cooldown"], (
            "a beat that reached its ceiling was blocked from replanning"
        )

    @pytest.mark.asyncio
    async def test_the_scene_still_produces_turns(self, monkeypatch) -> None:
        """The interlock: cutting repetition must not buy quiet.

        A ceiling that ends beats early could just as well end the scene. Assert
        the burst still commits its turns and every one of them narrates.
        """
        _, staged, game = await _drive(monkeypatch, actions=1)
        assert game is not None
        turns = sorted({record.turn_number for record in game.history})
        assert len(turns) == BURST_BEATS
        narrated = {r.turn_number for r in game.history if r.content_type == "narration"}
        assert narrated == set(turns), "a turn that narrates nothing is silence, not a fix"
