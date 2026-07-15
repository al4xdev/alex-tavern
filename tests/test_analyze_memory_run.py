"""Testes do localizador camada-a-camada de perdas de memória."""

from __future__ import annotations

from tools.analyze_memory_run import localize_loss


def _analysis(**overrides) -> dict:
    analysis = {
        "state": [{"turn_number": 1, "speaker": "Player", "content_type": "speech"}],
        "selection": {"C1": True, "C2": True},
        "prompt": [{"turn_number": 2, "agent": "character:Vela", "present": True}],
        "response": [{"turn_number": 2, "agent": "character:Vela", "present": True}],
    }
    analysis.update(overrides)
    return analysis


def test_no_loss_when_marker_survives_all_layers() -> None:
    assert localize_loss(_analysis()).startswith("sem perda")


def test_layer1_when_marker_never_persisted() -> None:
    assert "CAMADA 1" in localize_loss(_analysis(state=[]))


def test_layer2_when_marker_only_exists_as_narration() -> None:
    analysis = _analysis(
        state=[{"turn_number": 1, "speaker": "Narrator", "content_type": "narration"}],
        selection={"C1": False, "C2": False},
        prompt=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
        response=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
    )
    localization = localize_loss(analysis)
    assert "CAMADA 2" in localization and "content_type" in localization


def test_layer2_when_trim_removes_marker_from_selection() -> None:
    analysis = _analysis(
        selection={"C1": False, "C2": False},
        prompt=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
        response=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
    )
    assert "CAMADA 2" in localize_loss(analysis)


def test_layer3_when_marker_missing_from_all_requests() -> None:
    analysis = _analysis(
        prompt=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
        response=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
    )
    assert "CAMADA 3" in localize_loss(analysis)


def test_layer4_when_marker_reaches_prompt_but_never_a_reply() -> None:
    analysis = _analysis(
        response=[{"turn_number": 2, "agent": "character:Vela", "present": False}],
    )
    assert "CAMADA 4" in localize_loss(analysis)
