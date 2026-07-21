"""Task 38: roteiro with typed beat contracts and algorithmic replanning."""

from __future__ import annotations

import httpx
import pytest

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    GameState,
    Player,
    Roteiro,
    RoteiroAct,
    RoteiroBeat,
    Scene,
    TurnRecord,
    deepcopy_scene,
    dict_to_game_state,
    game_state_to_dict,
)
from src.roteiro import (
    ACT_REPLAN_THRESHOLD,
    COOLDOWN_TURNS,
    ReplanDecision,
    _validate_acts,
    _validate_beat,
    anchor_matched,
    describe_roteiro_for_director,
    evaluate_roteiro,
    measure_beat_progress,
    replan_roteiro,
)
from src.store.sessions import delete_session


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta"), "C3": _char("Bento")}
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _record(turn: int, speaker: str, content: str, content_type: str = "speech") -> TurnRecord:
    return TurnRecord(
        turn_number=turn,
        speaker=speaker,
        content=content,
        content_type=content_type,
        scene_snapshot=deepcopy_scene(SCENE),
    )


def _beat(**overrides) -> RoteiroBeat:  # noqa: ANN003
    fields = {
        "beat_id": "act1-beat1",
        "intent": "A carta some do balcao",
        "expected_actors": ["C2"],
        "expected_anchors": ["carta lacrada"],
        "exit_condition": "alguem percebe o sumico",
        "budget_turns": 4,
    }
    fields.update(overrides)
    return RoteiroBeat(**fields)


def _roteiro(**overrides) -> Roteiro:  # noqa: ANN003
    fields = {
        "premise": "Uma heranca disputada chega a estalagem.",
        "acts": [
            RoteiroAct(act_id="act1", summary="A carta chega", exit_condition="carta aberta"),
            RoteiroAct(act_id="act2", summary="O confronto", exit_condition="segredo dito"),
        ],
        "act_index": 0,
        "beat": _beat(),
        "beat_started_turn": 1,
    }
    fields.update(overrides)
    return Roteiro(**fields)


def _game(**overrides) -> GameState:  # noqa: ANN003
    fields = {
        "session_id": "test-roteiro",
        "characters": dict(CHARACTERS),
        "player": Player(controlled_character_id="C1"),
        "scene": deepcopy_scene(SCENE),
    }
    fields.update(overrides)
    return GameState(**fields)


class TestAnchorMatching:
    def test_exact_substring(self) -> None:
        assert anchor_matched("carta lacrada", "Ele nota a carta lacrada no balcao.")

    def test_accent_and_case_insensitive(self) -> None:
        assert anchor_matched("estábulo", "Um barulho vem do ESTABULO agora.")

    def test_fuzzy_inflection(self) -> None:
        assert anchor_matched("venezianas", "Ela fecha as venezianas do salao.")
        assert anchor_matched("corredor solar", "abriram o corredor solares ontem")

    def test_no_match(self) -> None:
        assert not anchor_matched("carta lacrada", "Nada de novo acontece na cozinha.")
        assert not anchor_matched("", "qualquer texto")


class TestBeatProgress:
    def test_actor_counts_only_own_speech_or_action(self) -> None:
        roteiro = _roteiro()
        history = [
            _record(1, "C3", "A Marta parece nervosa hoje."),
            _record(2, "Narrator", "Marta observa o salao.", "narration"),
        ]
        progress = measure_beat_progress(roteiro, history, "C1")
        assert progress.actors_missing == ("C2",)

    def test_anchor_counts_in_any_record_type(self) -> None:
        roteiro = _roteiro()
        history = [_record(2, "Narrator", "A carta lacrada repousa no balcao.", "narration")]
        progress = measure_beat_progress(roteiro, history, "C1")
        assert progress.anchors_hit == ("carta lacrada",)

    def test_player_speaker_maps_to_controlled_id(self) -> None:
        roteiro = _roteiro(beat=_beat(expected_actors=["C1"]))
        history = [_record(1, "Player", "Eu abro a porta.")]
        progress = measure_beat_progress(roteiro, history, "C1")
        assert progress.actors_hit == ("C1",)

    def test_disengaged_streak_counts_trailing_untouched_turns(self) -> None:
        roteiro = _roteiro()
        history = [
            _record(1, "C2", "Vi a carta lacrada."),
            _record(2, "C3", "O tempo fecha la fora."),
            _record(3, "C3", "Vou dormir cedo."),
        ]
        progress = measure_beat_progress(roteiro, history, "C1")
        assert progress.disengaged_streak == 2
        assert progress.turns_elapsed == 3

    def test_anchor_seen_via_evidence_counts_without_history_mention(self) -> None:
        """The regression that stalled every beat: an anchor staged only as an
        audible_speech event never reaches the prose/history, yet must count."""
        roteiro = _roteiro(anchors_seen=["carta lacrada"])
        # History says nothing about the anchor — it lived only in the event.
        history = [_record(1, "C3", "Que noite comprida.")]
        progress = measure_beat_progress(roteiro, history, "C1")
        assert progress.anchors_hit == ("carta lacrada",)
        assert progress.anchors_missing == ()


class TestCollectBeatEvidence:
    def test_collects_only_new_anchors(self) -> None:
        from src.roteiro import collect_beat_evidence

        roteiro = _roteiro(
            beat=_beat(expected_anchors=["carta lacrada", "adaga"]),
            anchors_seen=["carta lacrada"],
        )
        found = collect_beat_evidence(roteiro, ["Ele saca a adaga do cinto."])
        assert found == ["adaga"]

    def test_matches_across_accents_and_inflection(self) -> None:
        from src.roteiro import collect_beat_evidence

        roteiro = _roteiro(beat=_beat(expected_anchors=["murmurio"]))
        found = collect_beat_evidence(roteiro, ["Um murmúrio rouco escapa do ferido."])
        assert found == ["murmurio"]

    def test_no_beat_returns_empty(self) -> None:
        from src.roteiro import collect_beat_evidence

        assert collect_beat_evidence(_roteiro(beat=None), ["qualquer coisa"]) == []


class TestEvaluateRoteiro:
    def test_in_progress_returns_no_action(self) -> None:
        decision = evaluate_roteiro(_roteiro(), [_record(1, "C3", "Nada.")], "C1", 2)
        assert decision.action is None
        assert decision.reason == "in_progress"

    def test_full_coverage_advances(self) -> None:
        history = [_record(1, "C2", "Cadê a carta lacrada que estava aqui?")]
        decision = evaluate_roteiro(_roteiro(), history, "C1", 2)
        assert decision.action == "advance"
        assert decision.reason == "coverage_complete"

    def test_contract_without_measurables_never_advances(self) -> None:
        roteiro = _roteiro(beat=_beat(expected_actors=[], expected_anchors=[]))
        decision = evaluate_roteiro(roteiro, [_record(1, "C3", "Oi.")], "C1", 2)
        assert decision.action is None

    def test_partial_coverage_advances_after_patience(self) -> None:
        # Actors covered, one anchor landed, one stubborn holdout: after the
        # patience window the beat advances instead of grinding to a stall
        # (the round-1 pinned-beat regression).
        roteiro = _roteiro(beat=_beat(expected_anchors=["carta lacrada", "adaga"], budget_turns=10))
        history = [_record(1, "C2", "Vi a carta lacrada."), _record(2, "C3", "Nada demais.")]
        decision = evaluate_roteiro(roteiro, history, "C1", 3)
        assert decision.action == "advance"
        assert decision.reason == "coverage_sufficient"

    def test_partial_coverage_waits_for_patience(self) -> None:
        roteiro = _roteiro(beat=_beat(expected_anchors=["carta lacrada", "adaga"], budget_turns=10))
        history = [_record(1, "C2", "Vi a carta lacrada.")]
        decision = evaluate_roteiro(roteiro, history, "C1", 2)
        assert decision.action is None
        assert decision.reason == "in_progress"

    def test_two_missing_anchors_is_not_substantial(self) -> None:
        roteiro = _roteiro(
            beat=_beat(expected_anchors=["carta lacrada", "adaga", "selo"], budget_turns=10)
        )
        # Under the hard turn cap (2 turns), so not yet stalled: two anchors
        # still missing => not substantial => keep going.
        history = [_record(1, "C2", "Vi a carta lacrada."), _record(2, "C2", "Nada mais.")]
        decision = evaluate_roteiro(roteiro, history, "C1", 3)
        assert decision.action is None

    def test_hard_cap_stalls_engaged_beat_before_budget(self) -> None:
        # An ENGAGED beat (its actor speaks every turn) that never lands its
        # anchor stalls at the hard turn cap, not at its far-larger budget -
        # the fix for the portais pin (a beat held 5 turns restaged the scene).
        roteiro = _roteiro(beat=_beat(expected_anchors=["selo real"], budget_turns=10))
        history = [_record(turn, "C2", "Preciso agir logo.") for turn in range(1, 4)]
        decision = evaluate_roteiro(roteiro, history, "C1", 4)
        assert decision.action == "replan_beat"
        assert decision.reason == "stalled"

    def test_drift_window_triggers_before_budget(self) -> None:
        roteiro = _roteiro(beat=_beat(budget_turns=10))
        history = [_record(turn, "C3", "Assunto alheio.") for turn in range(1, 4)]
        decision = evaluate_roteiro(roteiro, history, "C1", 4)
        assert decision.action == "replan_beat"
        assert decision.reason == "drifted"

    def test_cooldown_blocks_stall_and_drift_replans(self) -> None:
        roteiro = _roteiro(cooldown_until_turn=6)
        history = [_record(turn, "C3", "Conversa fiada.") for turn in range(1, 5)]
        decision = evaluate_roteiro(roteiro, history, "C1", 5)
        assert decision.action is None
        assert decision.reason == "cooldown"

    def test_cooldown_never_blocks_advance(self) -> None:
        roteiro = _roteiro(cooldown_until_turn=10)
        history = [_record(1, "C2", "A carta lacrada sumiu!")]
        decision = evaluate_roteiro(roteiro, history, "C1", 2)
        assert decision.action == "advance"

    def test_burst_turns_do_not_stall_a_beat(self) -> None:
        """One continuation costs the beat ONE action, not one per beat.

        Regression (observed 2026-07-20 in sessions 29caff75 and 503bb018): a
        6-beat continuation committed 6 turns from a single click, blowing past
        the 3-turn cap inside one player action, so the screenplay replanned as
        "stalled" after every continuation.
        """
        roteiro = _roteiro(
            beat=_beat(expected_anchors=["selo real"], budget_turns=10),
            beat_actions_elapsed=1,
        )
        history = [_record(turn, "C2", "Preciso agir logo.") for turn in range(1, 7)]
        decision = evaluate_roteiro(roteiro, history, "C1", 7)
        assert decision.action is None
        assert decision.reason == "in_progress"
        # Three real actions still stall it — the cap itself is untouched.
        roteiro = _roteiro(
            beat=_beat(expected_anchors=["selo real"], budget_turns=10),
            beat_actions_elapsed=3,
        )
        decision = evaluate_roteiro(roteiro, history, "C1", 7)
        assert decision.action == "replan_beat"
        assert decision.reason == "stalled"

    def test_repeated_replans_escalate_to_act_rewrite(self) -> None:
        roteiro = _roteiro(beat_replans_in_act=ACT_REPLAN_THRESHOLD)
        history = [_record(turn, "C3", "Conversa fiada.") for turn in range(1, 5)]
        decision = evaluate_roteiro(roteiro, history, "C1", 5)
        assert decision.action == "replan_act"


class TestBeatValidation:
    def test_controlled_character_never_an_expected_actor(self) -> None:
        beat = _validate_beat(
            {"intent": "x", "expected_actors": ["C1", "C2", "C9"], "expected_anchors": []},
            _game(),
            fallback_id="fb",
        )
        assert beat.expected_actors == ["C2"]

    def test_budget_clamped_and_anchors_capped(self) -> None:
        beat = _validate_beat(
            {
                "intent": "x",
                "expected_actors": [],
                "expected_anchors": [f"a{i}" for i in range(9)] + ["", "a0"],
                "budget_turns": 99,
            },
            _game(),
            fallback_id="fb",
        )
        assert beat.budget_turns == 10
        assert len(beat.expected_anchors) == 5

    def test_missing_intent_raises(self) -> None:
        with pytest.raises(ValueError):
            _validate_beat({"intent": "  "}, _game(), fallback_id="fb")

    def test_acts_validation_drops_malformed(self) -> None:
        acts = _validate_acts([{"summary": "ok"}, {"act_id": "x"}, "junk"])
        assert len(acts) == 1 and acts[0].act_id == "act1"


class TestReplanBookkeeping:
    @pytest.mark.asyncio
    async def test_stall_replan_counts_and_sets_cooldown(self, monkeypatch) -> None:  # noqa: ANN001
        import src.roteiro as roteiro_mod

        async def fake_llm(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            return {
                "act_completed": False,
                "beat": {
                    "beat_id": "act1-beat2",
                    "intent": "novo rumo",
                    "expected_actors": ["C3"],
                    "expected_anchors": ["adaga"],
                    "exit_condition": "adaga aparece",
                    "budget_turns": 4,
                },
            }

        monkeypatch.setattr(roteiro_mod, "chat_completion_json", fake_llm)
        game = _game(roteiro=_roteiro())
        decision = ReplanDecision(action="replan_beat", reason="stalled")
        async with httpx.AsyncClient() as client:
            updated = await replan_roteiro(client, game, decision, {}, 7)
        assert updated.beat is not None and updated.beat.beat_id == "act1-beat2"
        assert updated.beat_started_turn == 7
        assert updated.cooldown_until_turn == 7 + COOLDOWN_TURNS
        assert updated.beat_replans_in_act == 1
        assert updated.beat_log == ["act1-beat1: stalled"]

    @pytest.mark.asyncio
    async def test_act_completed_advances_act_and_resets_counter(self, monkeypatch) -> None:  # noqa: ANN001
        import src.roteiro as roteiro_mod

        async def fake_llm(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            return {
                "act_completed": True,
                "beat": {
                    "beat_id": "act2-beat1",
                    "intent": "confronto",
                    "expected_actors": [],
                    "expected_anchors": [],
                    "exit_condition": "",
                    "budget_turns": 5,
                },
            }

        monkeypatch.setattr(roteiro_mod, "chat_completion_json", fake_llm)
        game = _game(roteiro=_roteiro(beat_replans_in_act=1))
        decision = ReplanDecision(action="advance", reason="coverage_complete")
        async with httpx.AsyncClient() as client:
            updated = await replan_roteiro(client, game, decision, {}, 9)
        assert updated.act_index == 1
        assert updated.beat_replans_in_act == 0
        assert updated.beat_log == ["act1-beat1: completed"]

    @pytest.mark.asyncio
    async def test_act_rewrite_splices_after_played_acts(self, monkeypatch) -> None:  # noqa: ANN001
        import src.roteiro as roteiro_mod

        async def fake_llm(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            return {
                "act_completed": False,
                "acts": [
                    {"act_id": "act2r", "summary": "novo acto 2", "exit_condition": "novo fim"}
                ],
                "beat": {
                    "beat_id": "act1-beat9",
                    "intent": "retomada",
                    "expected_actors": ["C2"],
                    "expected_anchors": [],
                    "exit_condition": "",
                    "budget_turns": 3,
                },
            }

        monkeypatch.setattr(roteiro_mod, "chat_completion_json", fake_llm)
        game = _game(roteiro=_roteiro(beat_replans_in_act=ACT_REPLAN_THRESHOLD))
        decision = ReplanDecision(action="replan_act", reason="stalled")
        async with httpx.AsyncClient() as client:
            updated = await replan_roteiro(client, game, decision, {}, 11)
        assert [act.act_id for act in updated.acts] == ["act1", "act2r"]
        assert updated.beat_replans_in_act == 0

    @pytest.mark.asyncio
    async def test_act_rewrite_drops_restated_current_act(self, monkeypatch) -> None:  # noqa: ANN001
        """The observed A/B defect: the model restates the current act as its
        first 'new' one, which must not leave two identical acts in the plan."""
        import src.roteiro as roteiro_mod

        async def fake_llm(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            return {
                "act_completed": False,
                "acts": [
                    {
                        "act_id": "dup",
                        "summary": "A carta chega",  # == current act1
                        "exit_condition": "carta aberta",
                    },
                    {
                        "act_id": "act2r",
                        "summary": "O verdadeiro segundo ato",
                        "exit_condition": "fim",
                    },
                ],
                "beat": {
                    "beat_id": "b",
                    "intent": "x",
                    "expected_actors": [],
                    "expected_anchors": [],
                    "exit_condition": "",
                    "budget_turns": 3,
                },
            }

        monkeypatch.setattr(roteiro_mod, "chat_completion_json", fake_llm)
        game = _game(roteiro=_roteiro(beat_replans_in_act=ACT_REPLAN_THRESHOLD))
        decision = ReplanDecision(action="replan_act", reason="stalled")
        async with httpx.AsyncClient() as client:
            updated = await replan_roteiro(client, game, decision, {}, 11)
        summaries = [act.summary for act in updated.acts]
        assert summaries == ["A carta chega", "O verdadeiro segundo ato"]

    @pytest.mark.asyncio
    async def test_replan_resets_anchors_seen(self, monkeypatch) -> None:  # noqa: ANN001
        import src.roteiro as roteiro_mod

        async def fake_llm(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            return {
                "act_completed": False,
                "beat": {
                    "beat_id": "b2",
                    "intent": "x",
                    "expected_actors": [],
                    "expected_anchors": ["novo"],
                    "exit_condition": "",
                    "budget_turns": 3,
                },
            }

        monkeypatch.setattr(roteiro_mod, "chat_completion_json", fake_llm)
        game = _game(roteiro=_roteiro(anchors_seen=["carta lacrada"]))
        decision = ReplanDecision(action="replan_beat", reason="stalled")
        async with httpx.AsyncClient() as client:
            updated = await replan_roteiro(client, game, decision, {}, 7)
        assert updated.anchors_seen == []


class TestPersistence:
    def test_roundtrip_preserves_roteiro(self) -> None:
        game = _game(roteiro=_roteiro(beat_log=["a: completed"]))
        restored = dict_to_game_state(game_state_to_dict(game))
        assert restored.roteiro == game.roteiro

    def test_legacy_session_without_roteiro_loads_none(self) -> None:
        data = game_state_to_dict(_game())
        data.pop("roteiro")
        assert dict_to_game_state(data).roteiro is None


class TestConfidentialityAndConsumption:
    def test_director_prompt_carries_roteiro_block(self) -> None:
        from src.agents.narrator import build_narrator_messages

        lines = describe_roteiro_for_director(_roteiro(), CHARACTERS)
        messages = build_narrator_messages(
            scene=SCENE,
            characters=CHARACTERS,
            player_controlled_id="C1",
            history=[],
            roteiro_lines=lines,
        )
        user_prompt = messages[1]["content"]
        assert "ROTEIRO" in user_prompt
        assert "A carta some do balcao" in user_prompt
        assert "Marta" in user_prompt  # actor rendered by name, not internal ID

    def test_director_block_lists_only_pending_anchors(self) -> None:
        """An anchor already in play is not re-listed — that would invite the
        Director to stage the same prop twice."""
        seen = _roteiro(
            beat=_beat(expected_anchors=["carta lacrada", "adaga"]),
            anchors_seen=["carta lacrada"],
        )
        lines = "\n".join(describe_roteiro_for_director(seen, CHARACTERS))
        assert "adaga" in lines
        assert "carta lacrada" not in lines

    def test_director_block_drops_pending_line_when_all_seen(self) -> None:
        seen = _roteiro(
            beat=_beat(expected_anchors=["carta lacrada"]), anchors_seen=["carta lacrada"]
        )
        lines = "\n".join(describe_roteiro_for_director(seen, CHARACTERS))
        assert "Not in play yet" not in lines

    def test_prose_and_character_builders_have_no_roteiro_surface(self) -> None:
        """Confidentiality is structural: the other prompt builders cannot even
        receive a roteiro — the parameter does not exist on their signatures."""
        import inspect

        from src.agents.character import _build_user_prompt as character_user_prompt
        from src.agents.character import act
        from src.agents.prose import build_prose_messages, render_narration

        for builder in (act, character_user_prompt, build_prose_messages, render_narration):
            assert "roteiro" not in str(inspect.signature(builder)).lower()


class TestRunnerWiring:
    async def _turn(  # noqa: ANN202
        self,
        monkeypatch,
        config,
        game_roteiro=None,
        seed_history=None,
        narrator_events=None,  # noqa: ANN001
        skip=False,
    ):
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)
        compiled = _roteiro()
        calls = {"compile": 0, "replan": 0}

        async def fake_generate(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
            calls["compile"] += 1
            return compiled

        async def fake_replan(client, game, decision, config, turn_number, current_tick=0):  # noqa: ANN001, ANN202, ARG001
            calls["replan"] += 1
            return compiled

        monkeypatch.setattr(runner_mod, "generate_roteiro", fake_generate)
        monkeypatch.setattr(runner_mod, "replan_roteiro", fake_replan)

        speaker_cycle = iter(["C2", "C3"] * 8) if skip else None

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            # On a continuation each beat must actually commit, so a character
            # speaks every beat and the burst runs to its budget.
            queue = [next(speaker_cycle)] if speaker_cycle is not None else ["Narrator"]
            return {
                "next_speakers": queue,
                "perception_events": list(narrator_events or []),
                "scene_update": None,
                "mood_updates": None,
                "return_control": False,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {"speech": "Falo agora.", "thought": None, "action_intent": None}

        async def fake_prose() -> str:
            return "Prosa."

        async with httpx.AsyncClient() as client:
            runner = Runner(client, dict(config))
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: fake_prose())
            if skip:
                monkeypatch.setattr(runner, "_call_character", fake_character)
            try:
                if game_roteiro is not None or seed_history:
                    game = await runner.get_state(sid)
                    assert game is not None
                    game.roteiro = game_roteiro
                    game.history.extend(seed_history or [])
                    runner_mod.save_game(game)
                if skip:
                    await runner.player_turn(sid, skip=True)
                else:
                    await runner.player_turn(sid, speech="Que noite.")
                game = await runner.get_state(sid)
            finally:
                await delete_session(sid)
        return calls, game

    @pytest.mark.asyncio
    async def test_disabled_by_default_never_compiles(self, monkeypatch) -> None:  # noqa: ANN001
        calls, game = await self._turn(monkeypatch, {"auto_event_enabled": False})
        assert calls == {"compile": 0, "replan": 0}
        assert game is not None and game.roteiro is None

    @pytest.mark.asyncio
    async def test_enabled_compiles_once_and_persists(self, monkeypatch) -> None:  # noqa: ANN001
        config = {"auto_event_enabled": False, "roteiro_enabled": True}
        calls, game = await self._turn(monkeypatch, config)
        assert calls["compile"] == 1
        assert game is not None and game.roteiro is not None
        assert game.roteiro.premise.startswith("Uma heranca")

    @pytest.mark.asyncio
    async def test_stalled_beat_triggers_replan_call(self, monkeypatch) -> None:  # noqa: ANN001
        config = {"auto_event_enabled": False, "roteiro_enabled": True}
        stalled = _roteiro(
            beat=_beat(budget_turns=2, expected_anchors=["inatingivel"]),
            beat_started_turn=1,
            beat_actions_elapsed=1,  # one action already spent on this beat
        )
        seed_history = [
            _record(1, "C2", "Falando do tempo."),
            _record(2, "C3", "E da colheita."),
        ]
        calls, game = await self._turn(
            monkeypatch, config, game_roteiro=stalled, seed_history=seed_history
        )
        # 1 spent action + the player's own = budget exceeded without anchor
        # coverage -> the deterministic engine ordered one beat replan.
        assert calls["replan"] == 1
        assert game is not None and game.roteiro is not None

    @pytest.mark.asyncio
    async def test_multi_beat_continuation_spends_one_action(self, monkeypatch) -> None:  # noqa: ANN001
        """A continuation commits several turns but costs the beat ONE action."""
        config = {
            "auto_event_enabled": False,
            "roteiro_enabled": True,
            "autonomous_burst_max_beats": 4,
        }
        _, game = await self._turn(
            monkeypatch,
            config,
            game_roteiro=_roteiro(beat_started_turn=1),
            skip=True,
        )
        assert game is not None and game.roteiro is not None
        assert len(game.history) > 1, "the burst must have committed several turns"
        assert game.roteiro.beat_actions_elapsed == 1

    @pytest.mark.asyncio
    async def test_anchor_from_event_accumulates_into_seen(self, monkeypatch) -> None:  # noqa: ANN001
        """The regression fix, end to end: an anchor the Director stages only as
        a typed audible_speech event (which never surfaces in the prose or any
        history record) is still recorded as covered on the roteiro. The next
        beat's evaluation will therefore see it — the stall that punished the
        obedient Director is gone."""
        config = {"auto_event_enabled": False, "roteiro_enabled": True}
        beat = _beat(budget_turns=4, expected_actors=[], expected_anchors=["murmurio"])
        roteiro = _roteiro(beat=beat, beat_started_turn=1)
        event = {
            "event_kind": "audible_speech",
            "subject_id": "C2",
            "content": "Um murmúrio rouco escapa do ferido.",
            "witness_ids": ["C3"],
        }
        calls, game = await self._turn(
            monkeypatch, config, game_roteiro=roteiro, narrator_events=[event]
        )
        assert game is not None and game.roteiro is not None
        assert "murmurio" in game.roteiro.anchors_seen
        # Budget not exhausted and the anchor is covered -> no replan.
        assert calls["replan"] == 0


class TestNarrativeClock:
    """Task 40: the tick always advances; act deadlines force the world event."""

    def test_tick_and_act_fields_roundtrip(self) -> None:
        acts = [
            RoteiroAct(
                act_id="a1",
                summary="s",
                exit_condition="e",
                duration_ticks=4,
                world_event="O sino toca.",
            )
        ]
        game = _game(roteiro=_roteiro(acts=acts, act_started_tick=3))
        game.narrative_tick = 7
        restored = dict_to_game_state(game_state_to_dict(game))
        assert restored.narrative_tick == 7
        assert restored.roteiro.act_started_tick == 3
        assert restored.roteiro.acts[0].duration_ticks == 4
        assert restored.roteiro.acts[0].world_event == "O sino toca."

    def test_acts_validation_clamps_clock_fields(self) -> None:
        acts = _validate_acts(
            [
                {"summary": "ok", "duration_ticks": 99, "world_event": "x" * 400},
                {"summary": "ok2", "duration_ticks": "junk"},
            ]
        )
        assert acts[0].duration_ticks == 12
        assert len(acts[0].world_event) == 300
        assert acts[1].duration_ticks == 0

    async def _clock_session(self, monkeypatch, roteiro):  # noqa: ANN001, ANN202
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)
        hints: list[str] = []
        replans: list[str] = []

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            hints.append(narrator_hint)
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "return_control": False,
            }

        async def fake_replan(client, game, decision, config, turn_number, current_tick=0):  # noqa: ANN001, ANN202, ARG001
            replans.append(decision.reason)
            updated = _roteiro(acts=list(game.roteiro.acts))
            updated.act_index = game.roteiro.act_index
            updated.act_started_tick = current_tick
            return updated

        monkeypatch.setattr(runner_mod, "replan_roteiro", fake_replan)

        async def fake_prose(game, events, turn_number):  # noqa: ANN001, ANN202
            return ""

        import httpx as _httpx

        client = _httpx.AsyncClient()
        runner = Runner(client, {"auto_event_enabled": False, "roteiro_enabled": True})
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(runner, "_render_narration", fake_prose)
        game = await runner.get_state(sid)
        game.roteiro = roteiro
        runner_mod.save_game(game)
        return runner, sid, client, hints, replans

    @pytest.mark.asyncio
    async def test_tick_advances_per_committed_turn(self, monkeypatch) -> None:  # noqa: ANN001
        from src.store.sessions import delete_session

        acts = [RoteiroAct(act_id="a1", summary="s", exit_condition="e")]  # no deadline
        runner, sid, client, _, _ = await self._clock_session(monkeypatch, _roteiro(acts=acts))
        try:
            await runner.player_turn(sid, speech="Um.")
            await runner.player_turn(sid, speech="Dois.")
            game = await runner.get_state(sid)
            assert game.narrative_tick == 2
        finally:
            await delete_session(sid)
            await client.aclose()

    @pytest.mark.asyncio
    async def test_undo_does_not_regress_the_clock(self, monkeypatch) -> None:  # noqa: ANN001
        from src.store.sessions import delete_session

        acts = [RoteiroAct(act_id="a1", summary="s", exit_condition="e")]  # no deadline
        runner, sid, client, _, _ = await self._clock_session(monkeypatch, _roteiro(acts=acts))
        try:
            await runner.player_turn(sid, speech="Um.")
            await runner.player_turn(sid, speech="Dois.")
            before = await runner.get_state(sid)
            assert before.narrative_tick == 2
            last_turn = before.history[-1].turn_number
            # Time always moves forward: undoing a turn rewinds scene/history but
            # NEVER the clock (an undone turn replays at a later tick).
            await runner.undo_turn(sid)
            game = await runner.get_state(sid)
            assert game.history[-1].turn_number < last_turn  # a turn was undone
            assert game.narrative_tick == 2  # clock held, did not regress to 1
        finally:
            await delete_session(sid)
            await client.aclose()

    @pytest.mark.asyncio
    async def test_act_deadline_stages_world_event_and_advances(self, monkeypatch) -> None:  # noqa: ANN001
        from src.store.sessions import delete_session

        acts = [
            RoteiroAct(
                act_id="a1",
                summary="s",
                exit_condition="e",
                duration_ticks=2,
                world_event="O sino da torre soa e o par e anunciado.",
            ),
            RoteiroAct(act_id="a2", summary="s2", exit_condition="e2"),
        ]
        runner, sid, client, hints, replans = await self._clock_session(
            monkeypatch, _roteiro(acts=acts, act_started_tick=0)
        )
        try:
            await runner.player_turn(sid, speech="Um.")  # tick 0->1
            await runner.player_turn(sid, speech="Dois.")  # tick 1->2
            # Third turn: tick(2) - started(0) >= 2 -> deadline fires BEFORE the
            # narrator: the world_event becomes this beat's UPCOMING EVENT.
            await runner.player_turn(sid, speech="Tres.")
            game = await runner.get_state(sid)
            assert "O sino da torre soa" in hints[2]
            assert replans == ["act_deadline"]
            assert game.roteiro.act_index == 1  # advanced by CODE
            assert game.roteiro.act_started_tick == 2
        finally:
            await delete_session(sid)
            await client.aclose()

    def test_time_skip_fields_are_required_in_narrator_schema(self) -> None:
        from src.agents.narrator import build_narrator_json_schema

        schema = build_narrator_json_schema(["C1"])["schema"]
        assert schema["properties"]["time_skip_ticks"] == {
            "type": "integer",
            "minimum": 0,
            "maximum": 8,
        }
        assert "time_skip_ticks" in schema["required"]
        assert "time_skip_summary" in schema["required"]

    @pytest.mark.asyncio
    async def test_pass_turn_invites_time_compression(self, monkeypatch) -> None:  # noqa: ANN001
        from src.runner import CLOCK_SKIP_INVITE
        from src.store.sessions import delete_session

        acts = [RoteiroAct(act_id="a1", summary="s", exit_condition="e")]
        runner, sid, client, hints, _ = await self._clock_session(monkeypatch, _roteiro(acts=acts))
        try:
            await runner.player_turn(sid, speech="Falo algo.")
            await runner.player_turn(sid, skip=True)
            assert hints == ["", CLOCK_SKIP_INVITE]
        finally:
            await delete_session(sid)
            await client.aclose()

    @pytest.mark.asyncio
    async def test_director_skip_request_is_clamped_and_witnessed(self, monkeypatch) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner
        from src.store.sessions import delete_session

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        requested_ticks = 3
        prose_events: list[list[dict]] = []

        client = httpx.AsyncClient()
        runner = Runner(client, {"auto_event_enabled": False})
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "return_control": False,
                "time_skip_ticks": requested_ticks,
                "time_skip_summary": "As horas passam; o salao esvazia.",
            }

        async def fake_prose(game, events, turn_number):  # noqa: ANN001, ANN202
            prose_events.append(list(events))
            return ""

        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(runner, "_render_narration", fake_prose)
        try:
            await runner.player_turn(sid, skip=True)
            game = await runner.get_state(sid)
            # beat +1 plus the requested compression
            assert game.narrative_tick == 1 + 3
            skip_obs = [
                e for e in prose_events[0] if e["content"] == "As horas passam; o salao esvazia."
            ]
            assert len(skip_obs) == 1
            assert skip_obs[0]["event_kind"] == "observation"
            assert set(skip_obs[0]["witness_ids"]) == {
                cid for cid in game.scene.present_characters if cid in game.characters
            }

            # An absurd request is clamped by CODE, never trusted.
            requested_ticks = 99
            await runner.player_turn(sid, skip=True)
            game = await runner.get_state(sid)
            assert game.narrative_tick == 4 + 1 + 8
        finally:
            await delete_session(sid)
            await client.aclose()
