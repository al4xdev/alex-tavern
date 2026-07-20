"""Task 33b piece 1: the per-turn material-delta auditor."""

from __future__ import annotations

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    deepcopy_scene,
)
from src.watcher import (
    DELTA_CATEGORIES,
    DeltaAudit,
    _normalize_categories,
    build_delta_audit_messages,
    build_delta_audit_schema,
)


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta")}
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "Player"],
    physical_facts={},
)


def _game() -> GameState:
    return GameState(
        session_id="watchertest",
        characters=dict(CHARACTERS),
        player=Player(controlled_character_id="C1"),
        scene=deepcopy_scene(SCENE),
    )


def _record(turn: int, speaker: str, content: str, ctype: str = "speech") -> TurnRecord:
    return TurnRecord(
        turn_number=turn,
        speaker=speaker,
        content=content,
        content_type=ctype,
        scene_snapshot=deepcopy_scene(SCENE),
    )


class TestNormalizeCategories:
    def test_keeps_known_in_taxonomy_order(self) -> None:
        # given out of order, returns in DELTA_CATEGORIES order
        out = _normalize_categories(["threat_advanced", "decision_taken"])
        assert out == ("decision_taken", "threat_advanced")

    def test_drops_none_when_paired_with_material(self) -> None:
        assert _normalize_categories(["none", "information_revealed"]) == ("information_revealed",)

    def test_lone_none_is_preserved(self) -> None:
        assert _normalize_categories(["none"]) == ("none",)

    def test_unknown_and_non_list_are_dropped(self) -> None:
        assert _normalize_categories(["bogus", "decision_taken"]) == ("decision_taken",)
        assert _normalize_categories("decision_taken") == ()
        assert _normalize_categories(None) == ()


class TestDeltaAuditMoved:
    def test_material_category_moves(self) -> None:
        assert DeltaAudit(categories=("information_revealed",)).moved is True

    def test_none_and_empty_do_not_move(self) -> None:
        assert DeltaAudit(categories=("none",)).moved is False
        assert DeltaAudit(categories=()).moved is False


class TestAuditPromptShape:
    def test_prompt_audits_latest_block_with_prior_context(self) -> None:
        game = _game()
        game.history.append(_record(1, "C2", "Chegamos à estalagem.", "narration"))
        game.history.append(
            _record(2, "C1", "A porta se escancara e um mensageiro entra.", "narration")
        )
        game.history.append(_record(2, "C2", "Quem é você?", "speech"))
        joined = "\n".join(m["content"] for m in build_delta_audit_messages(game))
        # location + the taxonomy travel in the prompt
        assert "Estalagem" in joined
        assert "decision_taken" in joined and "information_revealed" in joined
        # the latest turn block (turn 2) is the one under audit; turn 1 is context
        assert "TURN UNDER AUDIT" in joined
        assert "mensageiro" in joined
        assert "Chegamos à estalagem" in joined  # prior context still present for grounding

    def test_empty_history_is_safe(self) -> None:
        joined = "\n".join(m["content"] for m in build_delta_audit_messages(_game()))
        assert "no turn yet" in joined.lower()

    def test_schema_enumerates_the_taxonomy(self) -> None:
        schema = build_delta_audit_schema()
        enum = schema["schema"]["properties"]["categories"]["items"]["enum"]
        assert tuple(enum) == DELTA_CATEGORIES
        assert schema["schema"]["required"] == ["categories", "evidence"]
