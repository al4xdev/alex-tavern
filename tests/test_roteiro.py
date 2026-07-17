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

    def test_budget_exhaustion_stalls(self) -> None:
        history = [_record(turn, "C3", "Conversa fiada.") for turn in range(1, 5)]
        decision = evaluate_roteiro(_roteiro(), history, "C1", 5)
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
                "beat": {"beat_id": "act1-beat2", "intent": "novo rumo",
                         "expected_actors": ["C3"], "expected_anchors": ["adaga"],
                         "exit_condition": "adaga aparece", "budget_turns": 4},
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
                "beat": {"beat_id": "act2-beat1", "intent": "confronto",
                         "expected_actors": [], "expected_anchors": [],
                         "exit_condition": "", "budget_turns": 5},
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
                "acts": [{"act_id": "act2r", "summary": "novo acto 2",
                          "exit_condition": "novo fim"}],
                "beat": {"beat_id": "act1-beat9", "intent": "retomada",
                         "expected_actors": ["C2"], "expected_anchors": [],
                         "exit_condition": "", "budget_turns": 3},
            }

        monkeypatch.setattr(roteiro_mod, "chat_completion_json", fake_llm)
        game = _game(roteiro=_roteiro(beat_replans_in_act=ACT_REPLAN_THRESHOLD))
        decision = ReplanDecision(action="replan_act", reason="stalled")
        async with httpx.AsyncClient() as client:
            updated = await replan_roteiro(client, game, decision, {}, 11)
        assert [act.act_id for act in updated.acts] == ["act1", "act2r"]
        assert updated.beat_replans_in_act == 0


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

    def test_prose_and_character_builders_have_no_roteiro_surface(self) -> None:
        """Confidentiality is structural: the other prompt builders cannot even
        receive a roteiro — the parameter does not exist on their signatures."""
        import inspect

        from src.agents.character import act
        from src.agents.character import _build_user_prompt as character_user_prompt
        from src.agents.prose import build_prose_messages, render_narration

        for builder in (act, character_user_prompt, build_prose_messages, render_narration):
            assert "roteiro" not in str(inspect.signature(builder)).lower()


class TestRunnerWiring:
    async def _turn(self, monkeypatch, config, game_roteiro=None, seed_history=None):  # noqa: ANN001, ANN202
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

        async def fake_replan(client, game, decision, config, turn_number):  # noqa: ANN001, ANN202, ARG001
            calls["replan"] += 1
            return compiled

        monkeypatch.setattr(runner_mod, "generate_roteiro", fake_generate)
        monkeypatch.setattr(runner_mod, "replan_roteiro", fake_replan)

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
                "return_control": False,
            }

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
            try:
                if game_roteiro is not None or seed_history:
                    game = await runner.get_state(sid)
                    assert game is not None
                    game.roteiro = game_roteiro
                    game.history.extend(seed_history or [])
                    runner_mod.save_game(game)
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
        )
        seed_history = [
            _record(1, "C2", "Falando do tempo."),
            _record(2, "C3", "E da colheita."),
        ]
        calls, game = await self._turn(
            monkeypatch, config, game_roteiro=stalled, seed_history=seed_history
        )
        # 2 seeded chatter turns + the player's own = budget exceeded without
        # anchor coverage -> the deterministic engine ordered one beat replan.
        assert calls["replan"] == 1
        assert game is not None and game.roteiro is not None
