"""Task 43, Phase 1: the disposition substrate (pure code, zero model spend).

The scalar is code-owned; only the projected band ever reaches a model. These
tests exercise the arithmetic half: seeding from the preset set-point, lazy
dyadic materialization, deterministic drift/gravity, clamped integration, and the
scalar->band projection. No model call is involved.
"""

from __future__ import annotations

import pytest

from src.disposition import (
    ALL_AXES,
    AXIS_COMPOSURE,
    AXIS_TRUST,
    AXIS_WARMTH,
    DEFAULT_BASELINE,
    DYADIC_AXES,
    GLOBAL_AXES,
    apply_gravity,
    character_bands,
    dyad_bands,
    ensure_dyad,
    nudge,
    project_band,
    seed_character,
)
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    DispositionState,
    GameState,
    Player,
    Scene,
    deepcopy_scene,
    dict_to_game_state,
    game_state_to_dict,
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
        session_id="disptest",
        characters=dict(CHARACTERS),
        player=Player(controlled_character_id="C1"),
        scene=deepcopy_scene(SCENE),
    )


class TestAxisRegistry:
    def test_global_and_dyadic_partition_all_axes(self) -> None:
        assert set(GLOBAL_AXES) | set(DYADIC_AXES) == set(ALL_AXES)
        assert set(GLOBAL_AXES) & set(DYADIC_AXES) == set()
        assert AXIS_COMPOSURE in GLOBAL_AXES
        assert AXIS_TRUST in DYADIC_AXES and AXIS_WARMTH in DYADIC_AXES


class TestSeeding:
    def test_seed_populates_global_axes_at_baseline(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        axes = state.per_character["C1"]
        assert set(axes) == set(GLOBAL_AXES)
        disp = axes[AXIS_COMPOSURE]
        assert disp.baseline == DEFAULT_BASELINE
        assert disp.value == DEFAULT_BASELINE  # value starts at the set-point

    def test_seed_does_not_create_dyadic_axes(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        assert state.per_dyad == {}  # dyadic is lazy, never seeded at add

    def test_seed_is_idempotent_and_preserves_drifted_value(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        state.per_character["C1"][AXIS_COMPOSURE].value = 0.9  # simulate drift
        seed_character(state, "C1")  # re-seed must not reset a live value
        assert state.per_character["C1"][AXIS_COMPOSURE].value == 0.9

    def test_custom_baselines_override_the_set_point(self) -> None:
        state = DispositionState()
        seed_character(state, "C1", baselines={AXIS_COMPOSURE: 0.2})
        disp = state.per_character["C1"][AXIS_COMPOSURE]
        assert disp.baseline == 0.2 and disp.value == 0.2

    def test_baselines_are_clamped(self) -> None:
        state = DispositionState()
        seed_character(state, "C1", baselines={AXIS_COMPOSURE: 5.0})
        assert state.per_character["C1"][AXIS_COMPOSURE].baseline == 1.0


class TestLazyDyad:
    def test_dyad_absent_until_ensured(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        assert dyad_bands(state, "C1", "C2") == {}  # no cost for an idle pair

    def test_ensure_dyad_materializes_trust_and_warmth_neutral(self) -> None:
        state = DispositionState()
        axes = ensure_dyad(state, "C1", "C2")
        assert set(axes) == set(DYADIC_AXES)
        assert axes[AXIS_TRUST].value == DEFAULT_BASELINE
        assert axes[AXIS_WARMTH].baseline == DEFAULT_BASELINE

    def test_ensure_dyad_is_idempotent(self) -> None:
        state = DispositionState()
        ensure_dyad(state, "C1", "C2")
        state.per_dyad["C1"]["C2"][AXIS_TRUST].value = 0.1
        ensure_dyad(state, "C1", "C2")
        assert state.per_dyad["C1"]["C2"][AXIS_TRUST].value == 0.1

    def test_dyad_is_directional(self) -> None:
        state = DispositionState()
        ensure_dyad(state, "C1", "C2")
        assert "C2" not in state.per_dyad  # C2->C1 is a separate, uncreated entry


class TestProjection:
    def test_poles_and_middle(self) -> None:
        assert project_band(AXIS_TRUST, 0.0) == "desconfiado"
        assert project_band(AXIS_TRUST, 0.5) == "neutro"
        assert project_band(AXIS_TRUST, 1.0) == "devotado"

    def test_edges_round_up_into_the_higher_band(self) -> None:
        # edges at 0.15/0.35/0.65/0.85; value >= edge belongs to the higher band
        assert project_band(AXIS_WARMTH, 0.149) == "hostil"
        assert project_band(AXIS_WARMTH, 0.15) == "frio"
        assert project_band(AXIS_WARMTH, 0.85) == "afetuoso"
        assert project_band(AXIS_WARMTH, 0.849) == "caloroso"

    def test_every_band_is_reachable(self) -> None:
        seen = {project_band(AXIS_COMPOSURE, v / 100) for v in range(0, 101)}
        assert seen == {"em frangalhos", "abalado", "firme", "calmo", "imperturbável"}


class TestGravity:
    def test_relaxes_toward_baseline_monotonically_from_above(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        disp = state.per_character["C1"][AXIS_COMPOSURE]
        disp.value = 1.0  # shock upward
        prev = disp.value
        for _ in range(5):
            apply_gravity(state)
            assert disp.value < prev  # eases down toward 0.5 each tick
            assert disp.value >= disp.baseline
            prev = disp.value

    def test_relaxes_toward_baseline_from_below(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        disp = state.per_character["C1"][AXIS_COMPOSURE]
        disp.value = 0.0
        apply_gravity(state)
        assert disp.value > 0.0 and disp.value <= disp.baseline

    def test_converges_to_baseline(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        disp = state.per_character["C1"][AXIS_COMPOSURE]
        disp.value = 1.0
        for _ in range(60):
            apply_gravity(state)
        assert abs(disp.value - disp.baseline) < 1e-3

    def test_gravity_relaxes_dyadic_axes_too(self) -> None:
        state = DispositionState()
        axes = ensure_dyad(state, "C1", "C2")
        axes[AXIS_TRUST].value = 0.0
        apply_gravity(state)
        assert axes[AXIS_TRUST].value > 0.0

    def test_at_baseline_is_a_fixed_point(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        apply_gravity(state)
        assert state.per_character["C1"][AXIS_COMPOSURE].value == DEFAULT_BASELINE


class TestNudge:
    def test_integrates_and_clamps_high(self) -> None:
        state = DispositionState()
        axes = ensure_dyad(state, "C1", "C2")
        nudge(axes[AXIS_TRUST], 0.9)
        assert axes[AXIS_TRUST].value == 1.0  # clamped, not 1.4

    def test_integrates_and_clamps_low(self) -> None:
        state = DispositionState()
        axes = ensure_dyad(state, "C1", "C2")
        nudge(axes[AXIS_WARMTH], -0.9)
        assert axes[AXIS_WARMTH].value == 0.0

    def test_a_nudge_flips_the_band(self) -> None:
        state = DispositionState()
        axes = ensure_dyad(state, "C1", "C2")  # trust starts neutral
        assert project_band(AXIS_TRUST, axes[AXIS_TRUST].value) == "neutro"
        nudge(axes[AXIS_TRUST], -0.4)  # a betrayal
        assert project_band(AXIS_TRUST, axes[AXIS_TRUST].value) == "desconfiado"


class TestProjectionHelpers:
    def test_character_bands_reads_global_axes(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        state.per_character["C1"][AXIS_COMPOSURE].value = 0.05
        assert character_bands(state, "C1") == {AXIS_COMPOSURE: "em frangalhos"}

    def test_character_bands_empty_for_unseeded(self) -> None:
        assert character_bands(DispositionState(), "C9") == {}


class TestPromptInjection:
    """Phase 2 wiring (pure-code half): the band reaches the prompt, the scalar
    never does, and idle dyads stay silent."""

    def _note(self, state: DispositionState, cid: str) -> str:
        from src.agents.character import _build_disposition_note

        return _build_disposition_note(state, cid, deepcopy_scene(SCENE), dict(CHARACTERS), "C1")

    def test_note_shows_composure_band_not_scalar(self) -> None:
        state = DispositionState()
        seed_character(state, "C1")
        state.per_character["C1"][AXIS_COMPOSURE].value = 0.05
        note = self._note(state, "C1")
        assert "em frangalhos" in note
        # the code-owned number must never appear
        assert "0.05" not in note and "0.0" not in note

    def test_note_includes_materialized_dyad_only(self) -> None:
        state = DispositionState()
        seed_character(state, "C2")
        # no dyad yet -> only composure, no "Toward" line
        assert "Toward" not in self._note(state, "C2")
        axes = ensure_dyad(state, "C2", "C1")
        axes[AXIS_TRUST].value = 0.05
        axes[AXIS_WARMTH].value = 0.95
        note = self._note(state, "C2")
        assert "Toward" in note and "desconfiado" in note and "afetuoso" in note

    def test_empty_state_yields_no_note(self) -> None:
        assert self._note(DispositionState(), "C1") == ""


class TestAppraisalIntegration:
    """Phase 3 pure-code half: parse -> validate -> integrate a directional delta.

    The model half (does the appraisal emit the right DIRECTION under provocation?)
    is the curl gate; here we lock the arithmetic and the guards.
    """

    def _delta(self, **over):  # noqa: ANN003, ANN202
        from src.disposition import RelationshipDelta

        base = {
            "observer": "C1",
            "target": "C2",
            "axis": AXIS_TRUST,
            "direction": "down",
            "intensity": "strong",
        }
        base.update(over)
        return RelationshipDelta(**base)

    def test_validity_guards(self) -> None:
        assert self._delta().valid
        assert not self._delta(observer="C2").valid  # observer == target
        assert not self._delta(axis=AXIS_COMPOSURE).valid  # composure is parked
        assert not self._delta(direction="sideways").valid
        assert not self._delta(intensity="huge").valid

    def test_signed_amount_direction_and_magnitude(self) -> None:
        from src.disposition import INTENSITY_MAGNITUDE

        assert self._delta(direction="up", intensity="slight").signed_amount == pytest.approx(
            INTENSITY_MAGNITUDE["slight"]
        )
        assert self._delta(direction="down", intensity="strong").signed_amount == pytest.approx(
            -INTENSITY_MAGNITUDE["strong"]
        )

    def test_parse_filters_and_scopes_to_present(self) -> None:
        from src.disposition import parse_relationship_deltas

        raw = [
            {
                "observer": "C1",
                "target": "C2",
                "axis": "trust",
                "direction": "down",
                "intensity": "strong",
                "evidence": "betrayed",
            },
            {
                "observer": "C1",
                "target": "CX",
                "axis": "warmth",
                "direction": "up",
                "intensity": "slight",
                "evidence": "absent target",
            },  # CX not present -> drop
            {
                "observer": "C1",
                "target": "C2",
                "axis": "composure",
                "direction": "up",
                "intensity": "slight",
                "evidence": "parked axis",
            },  # composure -> drop
            "garbage",
        ]
        deltas = parse_relationship_deltas(raw, {"C1", "C2"})
        assert len(deltas) == 1
        assert deltas[0].axis == AXIS_TRUST and deltas[0].observer == "C1"

    def test_integrate_materializes_and_nudges(self) -> None:
        from src.disposition import integrate_appraisal

        state = DispositionState()
        integrate_appraisal(state, [self._delta(direction="down", intensity="strong")])
        # dyad was lazily created and trust dropped below neutral
        trust = state.per_dyad["C1"]["C2"][AXIS_TRUST].value
        assert trust < DEFAULT_BASELINE

    def test_repeated_strong_betrayal_flips_the_band(self) -> None:
        from src.disposition import integrate_appraisal

        state = DispositionState()
        d = self._delta(direction="down", intensity="strong")
        assert project_band(AXIS_TRUST, DEFAULT_BASELINE) == "neutro"
        for _ in range(3):
            integrate_appraisal(state, [d])
        value = state.per_dyad["C1"]["C2"][AXIS_TRUST].value
        assert project_band(AXIS_TRUST, value) == "desconfiado"

    def test_gravity_undoes_a_one_off_over_calm_turns(self) -> None:
        from src.disposition import integrate_appraisal

        state = DispositionState()
        integrate_appraisal(state, [self._delta(direction="down", intensity="slight")])
        dropped = state.per_dyad["C1"]["C2"][AXIS_TRUST].value
        assert dropped < DEFAULT_BASELINE
        for _ in range(40):
            apply_gravity(state)
        # a single slight nudge relaxes back toward neutral
        assert abs(state.per_dyad["C1"]["C2"][AXIS_TRUST].value - DEFAULT_BASELINE) < 1e-2


class TestAppraisalPrompt:
    def test_messages_carry_roster_ids_and_latest_block(self) -> None:
        from src.disposition import build_appraisal_messages
        from src.models import TurnRecord

        game = _game()
        game.history.append(
            TurnRecord(
                1,
                "C2",
                "Rasga o contrato na sua cara e cospe no chao.",
                "action",
                deepcopy_scene(SCENE),
            )
        )
        joined = "\n".join(m["content"] for m in build_appraisal_messages(game))
        assert "C1=Rui" in joined and "C2=Marta" in joined  # roster id=name
        assert "trust" in joined and "warmth" in joined
        assert "TURN UNDER APPRAISAL" in joined
        assert "contrato" in joined
        # no scalar surface leaks into the prompt
        assert "0.5" not in joined and "baseline" not in joined

    def test_schema_enumerates_axes_and_requires_fields(self) -> None:
        from src.disposition import APPRAISAL_AXES, build_appraisal_schema

        schema = build_appraisal_schema()
        item = schema["schema"]["properties"]["shifts"]["items"]
        assert tuple(item["properties"]["axis"]["enum"]) == APPRAISAL_AXES
        assert item["properties"]["direction"]["enum"] == ["up", "down"]


class TestSerialization:
    def test_round_trip_preserves_dispositions(self) -> None:
        game = _game()
        seed_character(game.dispositions, "C1")
        seed_character(game.dispositions, "C2")
        game.dispositions.per_character["C1"][AXIS_COMPOSURE].value = 0.12
        axes = ensure_dyad(game.dispositions, "C1", "C2")
        axes[AXIS_TRUST].value = 0.8

        restored = dict_to_game_state(game_state_to_dict(game))

        assert restored.dispositions == game.dispositions
        assert restored.dispositions.per_character["C1"][AXIS_COMPOSURE].value == 0.12
        assert restored.dispositions.per_dyad["C1"]["C2"][AXIS_TRUST].value == 0.8

    def test_absent_dispositions_key_defaults_empty(self) -> None:
        game = _game()
        data = game_state_to_dict(game)
        del data["dispositions"]
        restored = dict_to_game_state(data)
        assert restored.dispositions == DispositionState()
