"""Automatic compaction, reversible checkpoints, and measured progress contracts."""

from __future__ import annotations

import asyncio
import copy
import json
import shutil
from dataclasses import asdict
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from src.agents import summarizer as summarizer_mod
from src.compaction import CompactionDraft, CompactionProgress, invert_plugin_delta
from src.models import Character, CharacterBody, CharacterMind, GameState, Player, Scene, TurnRecord
from src.plugins.hooks import HookRegistry
from src.runner import Runner
from src.store.sessions import (
    SESSIONS_DIR,
    compaction_checkpoint_path,
    delete_session,
    fork_session,
    generate_session_id,
    load_game,
    save_game,
    session_backups_dir,
    session_debug_path,
    session_state_path,
)


@pytest.fixture(autouse=True)
def _remove_created_sessions():  # noqa: ANN202
    before = {path.name for path in SESSIONS_DIR.iterdir()} if SESSIONS_DIR.exists() else set()
    yield
    if SESSIONS_DIR.exists():
        for path in SESSIONS_DIR.iterdir():
            if path.name not in before and path.is_dir():
                shutil.rmtree(path)


def _characters() -> dict[str, Character]:
    return {
        "C1": Character(
            mind=CharacterMind("Thorn", "steady", [], "calm"),
            body=CharacterBody("Thorn", "scarred", "coat"),
        ),
        "C2": Character(
            mind=CharacterMind("Lyra", "curious", [], "alert"),
            body=CharacterBody("Lyra", "silver hair", "robe"),
        ),
    }


def _seed(turns: int, *, plugin_state: dict[str, Any] | None = None) -> str:
    session_id = generate_session_id()
    scene = Scene("Crossroads", "night", ["C1", "C2"], {})
    game = GameState(
        session_id=session_id,
        characters=_characters(),
        player=Player("C1"),
        scene=scene,
        plugin_state=copy.deepcopy(plugin_state or {}),
    )
    for turn_number in range(1, turns + 1):
        game.history.append(
            TurnRecord(
                turn_number=turn_number,
                speaker="Narrator",
                content=f"Thorn and Lyra cross marker {turn_number}.",
                content_type="narration",
                scene_snapshot=copy.deepcopy(scene),
            )
        )
    save_game(game)
    return session_id


def _runner_config(**overrides: Any) -> dict[str, Any]:
    return {
        "compaction_keep_recent_turns": 2,
        "automatic_compaction_enabled": True,
        "automatic_compaction_threshold_percent": 80,
        "context_max": 100,
        "max_tokens_narrator": 10,
        **overrides,
    }


def _narrator_result() -> dict[str, Any]:
    return {
        "narration": "The road answers.",
        "next_speaker": "C1",
        "context_for_character": "",
        "scene_update": None,
        "mood_updates": None,
    }


async def _successful_summary(**kwargs: Any) -> tuple[str, dict[str, str]]:
    callback = kwargs.get("on_model_completed")
    if callback is not None:
        callback("summarizer:world")
        callback("summarizer:Thorn")
        callback("summarizer:Lyra")
    return "Durable summary.", {"C1": "Thorn remembers.", "C2": "Lyra remembers."}


@pytest.mark.asyncio
async def test_automatic_compaction_runs_once_before_narrator(monkeypatch) -> None:  # noqa: ANN001
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config())
    observed: dict[str, Any] = {}

    monkeypatch.setattr(runner_mod, "estimate_prompt_tokens", lambda messages: 1000)
    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)

    async def narrate(game, *_args, **_kwargs):  # noqa: ANN001, ANN202
        observed["summary"] = game.story_summary
        observed["last"] = game.history[-1].content
        observed["revision"] = game.revision
        return _narrator_result()

    monkeypatch.setattr(runner, "_call_narrator", narrate)
    result = await runner.player_turn(session_id, speech="The current effective line.")

    assert result["automatic_compaction"]["status"] == "compacted"
    assert result["automatic_compaction"]["trigger"] == "automatic"
    assert observed == {
        "summary": "Durable summary.",
        "last": "The current effective line.",
        "revision": 1,
    }
    game = load_game(session_id)
    assert game is not None
    assert game.revision == 2
    assert [record.turn_number for record in game.history[:2]] == [3, 4]
    assert len(game.compaction_stack) == 1
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_below_threshold_and_private_thought_do_not_call_historian(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config(context_max=10_000))
    calls = 0

    def estimate(_messages):  # noqa: ANN001, ANN202
        nonlocal calls
        calls += 1
        return 10

    async def forbidden_summary(**_kwargs):  # noqa: ANN003, ANN202
        raise AssertionError("Historian must not be called")

    async def narrate(*_args, **_kwargs):  # noqa: ANN202
        return _narrator_result()

    monkeypatch.setattr(runner_mod, "estimate_prompt_tokens", estimate)
    monkeypatch.setattr(runner_mod, "summarize", forbidden_summary)
    monkeypatch.setattr(runner, "_call_narrator", narrate)

    below = await runner.player_turn(session_id, action="Wait.")
    assert below["automatic_compaction"]["status"] == "not_needed"
    assert calls == 1
    thought = await runner.player_turn(session_id, thought="A private doubt.")
    assert thought["automatic_compaction"] is None
    assert calls == 1
    assert list(session_backups_dir(session_id).glob("compaction.c*.json")) == []
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_retention_block_and_historian_failure_are_non_destructive(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import runner as runner_mod

    async def narrate(*_args, **_kwargs):  # noqa: ANN202
        return _narrator_result()

    monkeypatch.setattr(runner_mod, "estimate_prompt_tokens", lambda messages: 1000)

    blocked_id = _seed(2)
    blocked_runner = Runner(httpx.AsyncClient(), _runner_config(compaction_keep_recent_turns=5))
    monkeypatch.setattr(blocked_runner, "_call_narrator", narrate)
    blocked = await blocked_runner.player_turn(blocked_id, action="Continue.")
    assert blocked["automatic_compaction"]["status"] == "blocked_by_retention_window"
    assert list(session_backups_dir(blocked_id).glob("compaction.c*.json")) == []

    failed_id = _seed(4)
    failed_runner = Runner(httpx.AsyncClient(), _runner_config())

    async def fail_summary(**_kwargs):  # noqa: ANN003, ANN202
        raise RuntimeError("private summary text must not leak")

    monkeypatch.setattr(runner_mod, "summarize", fail_summary)
    monkeypatch.setattr(failed_runner, "_call_narrator", narrate)
    failed = await failed_runner.player_turn(failed_id, action="Continue anyway.")
    assert failed["automatic_compaction"]["status"] == "failed"
    game = load_game(failed_id)
    assert game is not None
    assert game.story_summary == ""
    assert game.revision == 1
    assert len(game.history) == 6
    assert list(session_backups_dir(failed_id).glob("compaction.c*.json")) == []
    entries = [
        json.loads(line)
        for line in session_debug_path(failed_id).read_text(encoding="utf-8").splitlines()
    ]
    marker = next(entry for entry in entries if entry.get("status") == "failed")
    assert marker["error_type"] == "RuntimeError"
    assert "private summary text" not in json.dumps(marker)
    await blocked_runner.client.aclose()
    await failed_runner.client.aclose()


@pytest.mark.asyncio
async def test_effective_plugin_input_drives_probe(monkeypatch) -> None:  # noqa: ANN001
    from src import runner as runner_mod

    session_id = _seed(4)
    hooks = HookRegistry()

    def transform(value, _context):  # noqa: ANN001, ANN202
        value["speech"] = "PLUGIN_EXPANDED_SPEECH"
        return value

    hooks.register("input-expander", "turn.input", "filter", transform)
    plugins = SimpleNamespace(hooks=hooks)
    runner = Runner(httpx.AsyncClient(), _runner_config(), plugins=plugins)
    probes: list[str] = []

    def estimate(messages):  # noqa: ANN001, ANN202
        rendered = "\n".join(str(message["content"]) for message in messages)
        probes.append(rendered)
        return 1000 if "PLUGIN_EXPANDED_SPEECH" in rendered else 0

    async def narrate(*_args, **_kwargs):  # noqa: ANN202
        return _narrator_result()

    monkeypatch.setattr(runner_mod, "estimate_prompt_tokens", estimate)
    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)
    monkeypatch.setattr(runner, "_call_narrator", narrate)
    result = await runner.player_turn(session_id, speech="short")

    assert result["effective_input"]["speech"] == "PLUGIN_EXPANDED_SPEECH"
    assert result["automatic_compaction"]["status"] == "compacted"
    assert probes and "short" not in probes[0]
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_measured_progress_is_monotonic_and_contains_no_story_text(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config())
    events: list[CompactionProgress] = []
    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)

    result = await runner.compact_session(session_id, progress=events.append)

    assert result["compacted"] is True
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert [event.stage for event in events] == [
        "checking",
        "summarizing",
        "model_completed",
        "model_completed",
        "model_completed",
        "before_commit",
        "checkpointing",
        "committing",
        "completed",
    ]
    assert {event.total_units for event in events[1:]} == {3}
    assert events[-1].result == result
    payload = json.dumps([asdict(event) for event in events])
    assert "Thorn remembers" not in payload
    assert "Lyra remembers" not in payload
    assert "marker 1" not in payload
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_failed_progress_leaves_state_and_checkpoint_absent(monkeypatch) -> None:  # noqa: ANN001
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config())
    before = session_state_path(session_id).read_bytes()
    events: list[CompactionProgress] = []

    async def fail(**_kwargs):  # noqa: ANN003, ANN202
        raise ValueError("model failed")

    monkeypatch.setattr(runner_mod, "summarize", fail)
    with pytest.raises(ValueError, match="model failed"):
        await runner.compact_session(session_id, progress=events.append)

    assert [event.stage for event in events] == ["checking", "summarizing", "failed"]
    assert events[-1].error_type == "ValueError"
    assert session_state_path(session_id).read_bytes() == before
    assert list(session_backups_dir(session_id).glob("compaction.c*.json")) == []
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_failed_atomic_state_save_removes_uncommitted_checkpoint(monkeypatch) -> None:  # noqa: ANN001
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config())
    before = session_state_path(session_id).read_bytes()
    real_save = runner_mod.save_game

    def fail_compacted_save(game):  # noqa: ANN001, ANN202
        if game.revision > 0:
            raise OSError("disk full")
        real_save(game)

    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)
    monkeypatch.setattr(runner_mod, "save_game", fail_compacted_save)
    with pytest.raises(OSError, match="disk full"):
        await runner.compact_session(session_id)

    assert session_state_path(session_id).read_bytes() == before
    assert list(session_backups_dir(session_id).glob("compaction.c*.json")) == []
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_cancellation_releases_lock_without_mutation(monkeypatch) -> None:  # noqa: ANN001
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config())
    before = session_state_path(session_id).read_bytes()
    entered = asyncio.Event()
    events: list[CompactionProgress] = []

    async def wait_forever(**_kwargs):  # noqa: ANN003, ANN202
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(runner_mod, "summarize", wait_forever)
    operation = asyncio.create_task(runner.compact_session(session_id, progress=events.append))
    await asyncio.wait_for(entered.wait(), timeout=0.5)
    operation.cancel()
    with pytest.raises(asyncio.CancelledError):
        await operation

    assert events[-1].stage == "failed"
    assert events[-1].error_type == "CancelledError"
    assert session_state_path(session_id).read_bytes() == before
    assert list(session_backups_dir(session_id).glob("compaction.c*.json")) == []
    assert await asyncio.wait_for(runner.get_state(session_id), timeout=0.5) is not None
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_plugin_precommit_failure_discards_draft_and_checkpoint(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import runner as runner_mod

    session_id = _seed(4)
    hooks = HookRegistry()

    def fail(_draft, _context):  # noqa: ANN001, ANN202
        raise RuntimeError("filter failed")

    hooks.register("broken", "compaction.before_commit", "filter", fail)
    runner = Runner(
        httpx.AsyncClient(),
        _runner_config(),
        plugins=SimpleNamespace(hooks=hooks),
    )
    before = session_state_path(session_id).read_bytes()
    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)

    with pytest.raises(RuntimeError, match="filter failed"):
        await runner.compact_session(session_id)

    assert session_state_path(session_id).read_bytes() == before
    assert list(session_backups_dir(session_id).glob("compaction.c*.json")) == []
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_historian_jobs_start_together_and_notes_finish_deterministically(
    monkeypatch,  # noqa: ANN001
) -> None:
    session_id = _seed(1)
    game = load_game(session_id)
    assert game is not None
    started: list[str] = []
    completed: list[str] = []
    all_started = asyncio.Event()
    delays = {"summarizer:Lyra": 0.0, "summarizer:Thorn": 0.01, "summarizer:world": 0.02}

    async def fake_json(*_args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        agent = kwargs["agent"]
        started.append(agent)
        if len(started) == 3:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), timeout=0.5)
        await asyncio.sleep(delays[agent])
        if agent == "summarizer:world":
            return {"story_summary": "World."}
        return {"character_note": f"Note for {agent}."}

    monkeypatch.setattr(summarizer_mod, "chat_completion_json", fake_json)
    async with httpx.AsyncClient() as client:
        summary, notes = await asyncio.wait_for(
            summarizer_mod.summarize(
                client=client,
                characters=game.characters,
                controlled_id="C1",
                story_summary="",
                character_notes={},
                evicted_turns=game.history,
                config={},
                on_model_completed=completed.append,
            ),
            timeout=1,
        )

    assert set(started) == {"summarizer:world", "summarizer:Thorn", "summarizer:Lyra"}
    assert completed == ["summarizer:Lyra", "summarizer:Thorn", "summarizer:world"]
    assert summary == "World."
    assert list(notes) == ["C1", "C2"]


def test_plugin_delta_reports_only_divergent_owned_paths() -> None:
    current, conflicts = invert_plugin_delta(
        {"weather": {"count": 3, "later": True}},
        [
            {
                "path": "/weather/count",
                "before_exists": True,
                "before": 1,
                "after_exists": True,
                "after": 2,
            }
        ],
    )

    assert current == {"weather": {"count": 3, "later": True}}
    assert conflicts == {"weather": ["/weather/count"]}


@pytest.mark.asyncio
async def test_plugin_resolver_can_merge_later_state_during_checkpoint_undo(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import runner as runner_mod

    session_id = _seed(4, plugin_state={"weather": {"count": 1}})
    hooks = HookRegistry()

    def compact_filter(draft: CompactionDraft, _context):  # noqa: ANN001, ANN202
        draft.plugin_state["weather"]["count"] = 2
        return draft

    hooks.register("weather", "compaction.before_commit", "filter", compact_filter)
    runner = Runner(
        httpx.AsyncClient(),
        _runner_config(),
        plugins=SimpleNamespace(hooks=hooks),
    )
    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)
    await runner.compact_session(session_id)
    game = load_game(session_id)
    assert game is not None
    game.plugin_state["weather"] = {"count": 3, "later": True}
    save_game(game)

    blocked = await runner.restore_last_compaction(session_id)
    assert blocked["restored"] is False
    assert blocked["plugin_conflicts"] == ["weather"]

    def resolve(namespace, context):  # noqa: ANN001, ANN202
        assert context["paths"] == ["/weather/count"]
        return {**namespace, "resolved": True}

    hooks.register("weather", "compaction.undo_conflict", "filter", resolve)
    restored = await runner.restore_last_compaction(session_id)
    assert restored["restored"] is True
    game = load_game(session_id)
    assert game is not None
    assert game.plugin_state["weather"] == {"count": 3, "later": True, "resolved": True}
    await runner.client.aclose()


@pytest.mark.asyncio
async def test_fork_copies_active_checkpoint_stack_and_delete_removes_it(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import runner as runner_mod

    session_id = _seed(4)
    runner = Runner(httpx.AsyncClient(), _runner_config())
    monkeypatch.setattr(runner_mod, "summarize", _successful_summary)
    await runner.compact_session(session_id)

    forked_id = await fork_session(session_id)
    assert forked_id is not None
    forked = load_game(forked_id)
    assert forked is not None
    assert [entry.checkpoint_id for entry in forked.compaction_stack] == ["c000001"]
    assert compaction_checkpoint_path(forked_id, "c000001").exists()

    assert await delete_session(forked_id) is True
    assert not compaction_checkpoint_path(forked_id, "c000001").exists()
    await runner.client.aclose()
