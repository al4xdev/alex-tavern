"""Tests for the queued, repeatable live-playtest harness."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tools.playtest_harness import (
    PlaytestConfigurationError,
    ScenarioQueue,
    aggregate_runs,
    analyze_debug_records,
    assert_safe_output_dir,
    build_markdown_report,
    build_session_config,
    evaluate_recall_check,
    load_scenario,
    prepare_output_dir,
    session_invariants,
)


def _write_scenario(path: Path, events: list[dict] | None = None) -> Path:
    value = {
        "name": "test-scenario",
        "description": "A test scenario.",
        "narrator_directives": "",
        "events": events
        or [
            {
                "type": "turn",
                "speech": "Hello",
                "action": "",
                "force_speaker": "C2",
            }
        ],
    }
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_scenario_load_round_trip_and_supported_operations(tmp_path: Path) -> None:
    path = _write_scenario(
        tmp_path / "scenario.json",
        [
            {"type": "turn", "speech": "Speak", "action": "Act", "force_speaker": None},
            {"type": "suggest"},
            {"type": "compact"},
            {"type": "restore_compaction"},
            {"type": "undo"},
        ],
    )

    scenario = load_scenario(path)

    assert scenario.name == "test-scenario"
    assert [event["type"] for event in scenario.events] == [
        "turn",
        "suggest",
        "compact",
        "restore_compaction",
        "undo",
    ]
    assert scenario.events[0]["force_speaker"] is None


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"name": "x", "description": "x", "events": []},
        {"name": "x", "description": "x", "events": [{"type": "unknown"}]},
        {
            "name": "x",
            "description": "x",
            "events": [{"type": "turn", "speech": "", "action": ""}],
        },
    ],
)
def test_scenario_validation_rejects_invalid_inputs(tmp_path: Path, value: dict) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(PlaytestConfigurationError):
        load_scenario(path)


def test_output_directory_is_fresh_and_isolated(tmp_path: Path) -> None:
    output = tmp_path / "run"

    prepared = prepare_output_dir(output)

    assert prepared == output
    with pytest.raises(PlaytestConfigurationError, match="already exists"):
        prepare_output_dir(output)


def test_output_directory_rejects_real_data_and_descendants() -> None:
    from tools.playtest_harness import REAL_DATA_DIR

    for path in (REAL_DATA_DIR, REAL_DATA_DIR / "playtests"):
        with pytest.raises(PlaytestConfigurationError, match="real data"):
            assert_safe_output_dir(path)


@pytest.mark.asyncio
async def test_scenario_queue_serializes_jobs() -> None:
    queue = ScenarioQueue(1)
    active = 0
    maximum_active = 0

    async def operation(label: str) -> dict:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        await asyncio.sleep(0.02)
        active -= 1
        return {"label": label}

    first, second = await asyncio.gather(
        queue.run(lambda: operation("first")),
        queue.run(lambda: operation("second")),
    )

    assert maximum_active == 1
    assert {first["label"], second["label"]} == {"first", "second"}
    assert max(first["queue"]["wait_ms"], second["queue"]["wait_ms"]) >= 10


def test_analysis_detects_observable_signals() -> None:
    narrator_response = json.dumps(
        {
            "narration": "You feel the air change.",
            "next_speaker": "C2",
            "context_for_character": "Context",
            "scene_update": {"physical_facts": '{"door": "open"}'},
            "mood_updates": {"C2": "calm"},
        }
    )
    records = [
        {
            "agent": "narrator",
            "turn_number": 1,
            "request": {"messages": [{"role": "user", "content": "SPEAKER=Thorn"}]},
            "response": narrator_response,
            "error": None,
            "duration_ms": 12.5,
            "attempt_number": 1,
            "prompt_chars": 100,
        },
        {
            "agent": "character:Lyra",
            "turn_number": 1,
            "request": {"messages": []},
            "response": '{"speech":null,"thought":"Arrumo o cabelo atrás da orelha."}',
            "error": None,
            "duration_ms": 5.0,
            "attempt_number": 2,
            "prompt_chars": 50,
        },
    ]
    event_results = [
        {
            "type": "turn",
            "before": {"moods": {"C2": "calm"}},
            "result": {"turn_number": 1},
        }
    ]

    analysis = analyze_debug_records(records, event_results)

    assert analysis["llm_calls"] == 2
    assert analysis["retry_attempts"] == 1
    assert analysis["nested_physical_facts_outputs"] == 1
    assert analysis["second_person_narrations"] == 1
    assert analysis["character_action_heuristic_hits"] == 1
    assert analysis["redundant_mood_updates"] == 1
    assert analysis["player_prompt_occurrences"] == 0


def _character_payload(name: str) -> dict:
    return {
        "mind": {"name": name, "personality": "p", "knowledge": [], "current_mood": "calm"},
        "body": {"name": name, "physical_description": "d", "outfit": "o"},
    }


def test_recall_check_event_loads_and_normalizes(tmp_path: Path) -> None:
    path = _write_scenario(
        tmp_path / "recall.json",
        [
            {
                "type": "recall_check",
                "speech": "What was the password?",
                "force_speaker": "C2",
                "prompt_patterns": ["ORQU[ÍI]DEA-741"],
                "reply_patterns": ["ORQU[ÍI]DEA-741"],
                "reply_forbidden_patterns": ["GIRASSOL"],
            }
        ],
    )

    scenario = load_scenario(path)

    event = scenario.events[0]
    assert event["type"] == "recall_check"
    assert event["required"] is True
    assert event["thought"] == "" and event["action"] == ""
    assert event["prompt_patterns"] == ["ORQU[ÍI]DEA-741"]
    assert event["prompt_forbidden_patterns"] == []


@pytest.mark.parametrize(
    "event",
    [
        {"type": "recall_check", "speech": "q", "force_speaker": "C2"},
        {"type": "recall_check", "speech": "q", "prompt_patterns": ["x"]},
        {
            "type": "recall_check",
            "speech": "q",
            "force_speaker": "C2",
            "prompt_patterns": ["(unclosed"],
        },
        {
            "type": "recall_check",
            "speech": "q",
            "force_speaker": "C2",
            "prompt_patterns": ["x"],
            "required": "yes",
        },
    ],
)
def test_recall_check_validation_rejects_invalid_inputs(tmp_path: Path, event: dict) -> None:
    path = _write_scenario(tmp_path / "invalid-recall.json", [event])

    with pytest.raises(PlaytestConfigurationError):
        load_scenario(path)


def test_turn_and_recall_events_accept_audience(tmp_path: Path) -> None:
    path = _write_scenario(
        tmp_path / "audience.json",
        [
            {
                "type": "turn",
                "speech": "segredo",
                "action": "",
                "force_speaker": "C2",
                "audience": ["C1", "C2"],
            },
            {
                "type": "recall_check",
                "speech": "qual era?",
                "force_speaker": "C2",
                "audience": ["C1", "C2"],
                "reply_patterns": ["(?i)x"],
            },
        ],
    )

    scenario = load_scenario(path)

    assert scenario.events[0]["audience"] == ["C1", "C2"]
    assert scenario.events[1]["audience"] == ["C1", "C2"]


@pytest.mark.parametrize("audience", [[], ["C1", 2], "C2"])
def test_audience_validation_rejects_invalid_values(tmp_path: Path, audience: object) -> None:
    path = _write_scenario(
        tmp_path / "bad-audience.json",
        [{"type": "turn", "speech": "x", "action": "", "audience": audience}],
    )

    with pytest.raises(PlaytestConfigurationError, match="audience"):
        load_scenario(path)


def test_session_config_must_be_an_object(tmp_path: Path) -> None:
    path = tmp_path / "bad-session-config.json"
    path.write_text(
        json.dumps(
            {
                "name": "x",
                "description": "x",
                "session_config": ["not", "an", "object"],
                "events": [{"type": "suggest"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PlaytestConfigurationError, match="session_config"):
        load_scenario(path)


def test_build_session_config_converts_characters_and_scene(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    path.write_text(
        json.dumps(
            {
                "name": "x",
                "description": "x",
                "narrator_directives": "Stay calm.",
                "session_config": {
                    "controlled_character_id": "C1",
                    "characters": {
                        "C1": _character_payload("Dario"),
                        "C2": _character_payload("Vela"),
                        "C3": _character_payload("Rook"),
                    },
                    "scene": {
                        "location": "Tavern",
                        "time_of_day": "night",
                        "present_characters": ["C1", "C2", "C3", "Player"],
                    },
                },
                "events": [{"type": "suggest"}],
            }
        ),
        encoding="utf-8",
    )
    from src.models import Character, Scene

    session_config = build_session_config(load_scenario(path))

    assert session_config is not None
    assert session_config["controlled_character_id"] == "C1"
    assert session_config["narrator_directives"] == "Stay calm."
    assert set(session_config["characters"]) == {"C1", "C2", "C3"}
    assert all(
        isinstance(character, Character) for character in session_config["characters"].values()
    )
    assert isinstance(session_config["scene"], Scene)
    assert session_config["scene"].present_characters == ["C1", "C2", "C3", "Player"]


def test_build_session_config_without_custom_session_keeps_legacy_shape(tmp_path: Path) -> None:
    scenario = load_scenario(_write_scenario(tmp_path / "plain.json"))

    assert build_session_config(scenario) is None


def _recall_event(**overrides) -> dict:
    event = {
        "type": "recall_check",
        "speech": "What was the password?",
        "force_speaker": "C2",
        "prompt_patterns": ["ORQU[ÍI]DEA-741"],
        "prompt_forbidden_patterns": [],
        "reply_patterns": ["ORQU[ÍI]DEA-741"],
        "reply_forbidden_patterns": ["GIRASSOL"],
        "required": True,
    }
    event.update(overrides)
    return event


def _character_debug_record(turn_number: int, prompt: str, speech: str) -> dict:
    return {
        "agent": "character:Vela",
        "turn_number": turn_number,
        "request": {"messages": [{"role": "user", "content": prompt}]},
        "response": json.dumps({"speech": speech, "thought": None}),
        "error": None,
    }


def test_evaluate_recall_check_passes_when_prompt_and_reply_match() -> None:
    records = [
        {"agent": "narrator", "turn_number": 7, "request": {"messages": []}, "response": "{}"},
        _character_debug_record(7, "RECENT EVENTS:\n... ORQUÍDEA-741 ...", "Era ORQUÍDEA-741."),
    ]

    recall = evaluate_recall_check(_recall_event(), 7, records)

    assert recall["passed"] is True
    assert recall["character_calls"] == 1
    assert recall["prompt_passed"] is True and recall["reply_passed"] is True


def test_evaluate_recall_check_localizes_prompt_versus_reply_failures() -> None:
    prompt_loss = evaluate_recall_check(
        _recall_event(),
        3,
        [_character_debug_record(3, "RECENT EVENTS:\n(nothing relevant)", "Era ORQUÍDEA-741.")],
    )
    reply_loss = evaluate_recall_check(
        _recall_event(),
        3,
        [_character_debug_record(3, "RECENT EVENTS:\n... ORQUÍDEA-741 ...", "Não me lembro.")],
    )
    forbidden_leak = evaluate_recall_check(
        _recall_event(),
        3,
        [_character_debug_record(3, "... ORQUÍDEA-741 ...", "Era ORQUÍDEA-741, ou GIRASSOL?")],
    )

    assert prompt_loss["prompt_passed"] is False and prompt_loss["reply_passed"] is True
    assert reply_loss["prompt_passed"] is True and reply_loss["reply_passed"] is False
    assert forbidden_leak["reply_forbidden_hits"]["GIRASSOL"] is True
    assert all(not result["passed"] for result in (prompt_loss, reply_loss, forbidden_leak))


def test_evaluate_recall_check_fails_without_character_calls() -> None:
    records = [
        {"agent": "narrator", "turn_number": 5, "request": {"messages": []}, "response": "{}"}
    ]

    recall = evaluate_recall_check(_recall_event(), 5, records)

    assert recall["passed"] is False
    assert recall["character_calls"] == 0


def _game_with_history(presences: list[list[str]], final_presence: list[str]):
    from src.models import (
        Character,
        CharacterBody,
        CharacterMind,
        GameState,
        Player,
        Scene,
        TurnRecord,
    )

    def scene(present: list[str]) -> Scene:
        return Scene("Tavern", "night", list(present), {})

    characters = {
        "C1": Character(
            mind=CharacterMind("Dario", "p", [], "calm"),
            body=CharacterBody("Dario", "d", "o"),
        )
    }
    history = [
        TurnRecord(index + 1, "Player", "hello", "speech", scene(present))
        for index, present in enumerate(presences)
    ]
    return GameState(
        session_id="s",
        characters=characters,
        player=Player(controlled_character_id="C1"),
        scene=scene(final_presence),
        history=history,
    )


def test_session_invariants_accept_a_stable_session() -> None:
    game = _game_with_history([["C1", "Player"], ["C1", "Player"]], ["C1", "Player"])

    assert session_invariants(game) == []


def test_session_invariants_flag_presence_changes_and_compaction() -> None:
    changed = _game_with_history([["C1", "Player"], ["C1", "C2", "Player"]], ["C1", "Player"])
    compacted = _game_with_history([["C1", "Player"]], ["C1", "Player"])
    compacted.story_summary = "Summary."

    changed_violations = session_invariants(changed)
    compacted_violations = session_invariants(compacted)

    assert any("present_characters changed" in violation for violation in changed_violations)
    assert any("story_summary" in violation for violation in compacted_violations)


def test_whisper_leak_records_flags_character_leak_only() -> None:
    from src.models import TurnRecord
    from tools.playtest_harness import whisper_leak_records

    game = _game_with_history([], ["C1", "Player"])
    from src.models import Character, CharacterBody, CharacterMind, Scene

    def _char(name: str) -> Character:
        return Character(
            mind=CharacterMind(name, "p", [], "calm"), body=CharacterBody(name, "d", "o")
        )

    game.characters["C2"] = _char("Vela")
    game.characters["C3"] = _char("Rook")  # o outsider presente que não pode ouvir
    scene = Scene("Tavern", "night", ["C1", "C2", "C3", "Player"], {})
    whispered = TurnRecord(1, "Player", "O código é GIRASSOL-222.", "speech", scene)
    whispered.audience = ["C1", "C2"]
    player_public = TurnRecord(2, "Player", "Digo eu mesmo: GIRASSOL-222!", "speech", scene)
    character_leak = TurnRecord(3, "C2", "Claro, GIRASSOL-222, todos ouviram.", "speech", scene)

    # Vazamento do personagem é violação; o jogador gastar o próprio segredo, não.
    game.history = [whispered, character_leak]
    leaks = whisper_leak_records(game)
    assert len(leaks) == 1 and leaks[0]["speaker"] == "C2"
    assert "girassol" in leaks[0]["leaked_tokens"]

    game.history = [whispered, player_public, character_leak]
    assert whisper_leak_records(game) == []  # público antes → conhecimento ganho


def test_analysis_counts_whisper_guard_events() -> None:
    records = [
        {"agent": "whisper_output_guard", "outcome": "retried", "turn_number": 3},
        {"agent": "whisper_output_guard", "outcome": "redacted", "turn_number": 3},
        {"agent": "narrator", "turn_number": 3, "request": {"messages": []}, "response": "{}"},
    ]

    analysis = analyze_debug_records(records, [])

    assert analysis["whisper_guard_retries"] == 1
    assert analysis["whisper_guard_redactions"] == 1


def test_analysis_counts_recall_results() -> None:
    event_results = [
        {"type": "turn", "result": {"turn_number": 1}, "before": {}},
        {
            "type": "recall_check",
            "result": {"turn_number": 2},
            "before": {},
            "recall": {"passed": True, "prompt_passed": True, "reply_passed": True},
        },
        {
            "type": "recall_check",
            "result": {"turn_number": 3},
            "before": {},
            "recall": {"passed": False, "prompt_passed": True, "reply_passed": False},
        },
    ]

    analysis = analyze_debug_records([], event_results)

    assert analysis["recall_checks"] == 2
    assert analysis["recall_failures"] == 1
    assert analysis["recall_prompt_failures"] == 0
    assert analysis["recall_reply_failures"] == 1


def test_memory_focus_scenario_asset_is_valid() -> None:
    scenario_path = (
        Path(__file__).resolve().parents[1] / "tools" / "playtests" / "memory_focus_xyz.json"
    )

    scenario = load_scenario(scenario_path)

    recall_events = [event for event in scenario.events if event["type"] == "recall_check"]
    assert len(recall_events) == 3
    assert scenario.session_config is not None
    session_config = build_session_config(scenario)
    assert session_config is not None
    assert set(session_config["characters"]) == {"C1", "C2", "C3"}
    presence = session_config["scene"].present_characters
    assert presence == ["C1", "C2", "C3", "Player"]
    turn_events = [event for event in scenario.events if event["type"] == "turn"]
    assert all(event["force_speaker"] in {"C2", "C3"} for event in turn_events)


def test_aggregation_and_markdown_are_repeatable() -> None:
    runs = [
        {
            "scenario": "same",
            "repetition": 1,
            "session_id": "one",
            "queue": {"wait_ms": 0.0},
            "analysis": {"llm_calls": 2, "llm_errors": 0},
        },
        {
            "scenario": "same",
            "repetition": 2,
            "session_id": "two",
            "queue": {"wait_ms": 1.0},
            "analysis": {"llm_calls": 4, "llm_errors": 0},
        },
    ]
    aggregates = aggregate_runs(runs)
    manifest = {
        "started_at": "now",
        "model_label": "model",
        "llm_host": "local",
        "repeat": 2,
        "max_in_flight": 1,
        "data_dir": "/tmp/run",
        "runs": runs,
    }

    assert aggregates == [
        {
            "scenario": "same",
            "runs": 2,
            "metrics": {
                "llm_calls": {"min": 2.0, "mean": 3.0, "max": 4.0},
                "llm_errors": {"min": 0.0, "mean": 0.0, "max": 0.0},
            },
        }
    ]
    report = build_markdown_report(manifest)
    assert "same" in report
    assert "model" in report
