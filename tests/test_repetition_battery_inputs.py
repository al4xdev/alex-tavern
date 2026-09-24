from unittest.mock import AsyncMock, call

import pytest

from tools.acceptance import repetition_battery


def test_p3_sends_actions_to_runner_instead_of_skipping(monkeypatch, tmp_path):
    from src import config, runner
    from tools.acceptance import roteiro_ab

    instance = AsyncMock()
    instance.start_session.return_value = "test-session"
    monkeypatch.setattr(runner, "Runner", lambda client, settings: instance)
    monkeypatch.setattr(config, "load_config", lambda path: {})
    monkeypatch.setattr(config, "resolve_active_config", lambda stored: {})
    monkeypatch.setattr(roteiro_ab, "_build_session_args", lambda scenario: ({}, []))

    result = repetition_battery.run_one(
        "base", "P3", 1, "unused", config_path=tmp_path / "config.json"
    )

    assert result["inputs"] == 10
    assert instance.player_turn.await_args_list == [
        call("test-session", speech="Eu vou na frente. Abram caminho."),
        call("test-session", skip=True),
        call("test-session", action="atravessar o salão em direção à saída mais próxima"),
        call("test-session", skip=True),
        call("test-session", skip=True),
        call("test-session", speech="Não vou esperar mais. Estou entrando."),
        call("test-session", skip=True),
        call("test-session", skip=True),
        call("test-session", action="seguir em frente sozinho se ninguém acompanhar"),
        call("test-session", skip=True),
    ]


def test_unknown_input_kind_is_rejected(monkeypatch, tmp_path):
    from src import config, runner
    from tools.acceptance import roteiro_ab

    instance = AsyncMock()
    instance.start_session.return_value = "test-session"
    monkeypatch.setattr(runner, "Runner", lambda client, settings: instance)
    monkeypatch.setattr(config, "load_config", lambda path: {})
    monkeypatch.setattr(config, "resolve_active_config", lambda stored: {})
    monkeypatch.setattr(roteiro_ab, "_build_session_args", lambda scenario: ({}, [("typo", "go")]))

    with pytest.raises(ValueError, match="Unknown input kind"):
        repetition_battery.run_one(
            "base", "unknown-profile", 1, "unused", config_path=tmp_path / "config.json"
        )

    instance.player_turn.assert_not_awaited()
