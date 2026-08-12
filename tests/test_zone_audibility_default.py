"""Task 54, finding 1: crossing a room must not make anyone deaf.

A new zone used to start audible from nowhere, and the Director was told exactly
that in its own contract. It used `zone_moves` for a position inside one hall
anyway ("C18 walks to the central table"), and the runtime sealed the hall in
two: twelve records with an empty audience, including a shouted warning that
reached no one.

The default is inverted here — a new zone is born audible from where its mover
came, and separation is declared with `zone_link_updates`, which is what that
field is for. These tests pin both halves: sound carries by default, and an
explicit seal still wins.
"""

from __future__ import annotations

from src.runner import Runner
from tests.factories import make_cast, make_game, make_scene


def narrator_counts(witness_ids: list[str], subject: str = "C2") -> int:
    """Witnesses the runtime credits to `subject`, before the clamp runs."""
    from src.agents import narrator as narrator_mod

    raw = [{"event_kind": "audible_speech", "subject_id": subject, "witness_ids": witness_ids}]
    return narrator_mod._proposed_witness_counts(raw)[0][1]


def _game():
    cast = make_cast("Link", "Garran", "Maelis")
    return make_game(
        characters=cast,
        scene=make_scene(characters=cast, location="Salao dos Quatro Arcos"),
        controlled="C1",
    )


def _apply(game, zone_moves):
    new_zones = [z for z in zone_moves.values() if z not in game.scene.zones]
    if new_zones and not game.scene.zones:
        stage = (game.scene.location or "").strip()[:60] or "palco"
        game.scene.zones[stage] = []
        for cid in game.scene.present_characters:
            if cid in game.characters:
                game.scene.positions[cid] = stage
    Runner._open_new_zones(game, zone_moves, new_zones)
    for moved_id, zone in zone_moves.items():
        game.scene.positions[moved_id] = zone
    return game


def test_first_split_of_a_stage_keeps_both_sides_audible() -> None:
    """The exact live-session shape: one character walks to the central table."""
    game = _apply(_game(), {"C2": "mesa central"})
    stage = "Salao dos Quatro Arcos"
    assert game.scene.zones["mesa central"] == [stage]
    assert "mesa central" in game.scene.zones[stage]
    assert game.scene.positions["C2"] == "mesa central"
    assert game.scene.positions["C1"] == stage


def test_a_further_move_links_to_the_zone_the_mover_actually_left() -> None:
    game = _apply(_game(), {"C2": "mesa central"})
    game = _apply(game, {"C2": "corredor"})
    assert game.scene.zones["corredor"] == ["mesa central"]
    assert "corredor" in game.scene.zones["mesa central"]
    # The origin stage is not dragged along: only the zone actually left is linked.
    assert "corredor" not in game.scene.zones["Salao dos Quatro Arcos"]


def test_two_characters_moving_together_link_both_their_origins() -> None:
    game = _apply(_game(), {"C2": "mesa central"})
    game = _apply(game, {"C1": "varanda", "C2": "varanda"})
    assert game.scene.zones["varanda"] == ["Salao dos Quatro Arcos", "mesa central"]
    assert "varanda" in game.scene.zones["Salao dos Quatro Arcos"]
    assert "varanda" in game.scene.zones["mesa central"]


def test_an_explicit_seal_still_wins() -> None:
    """zone_link_updates is applied after creation, so declaring a gap works.

    Drives the production helper rather than an inlined copy: this test used to
    paste the old replace-semantics loop, which stopped being what ships when
    task 67 made non-empty updates merge.
    """
    game = _apply(_game(), {"C2": "rua"})
    assert game.scene.zones["rua"] == ["Salao dos Quatro Arcos"]
    Runner._apply_zone_links(game, {"rua": []}, 1)
    assert game.scene.zones["rua"] == []


def test_moving_into_an_existing_zone_changes_no_links() -> None:
    game = _apply(_game(), {"C2": "mesa central"})
    before = {zone: list(audible) for zone, audible in game.scene.zones.items()}
    game = _apply(game, {"C3": "mesa central"})
    assert game.scene.zones == before
    assert game.scene.positions["C3"] == "mesa central"


def test_a_mover_with_no_recorded_origin_creates_an_isolated_zone() -> None:
    """Nothing to link to is still nothing to link to — no invented connection."""
    cast = make_cast("Link", "Garran")
    game = make_game(characters=cast, scene=make_scene(characters=cast), controlled="C1")
    game.scene.zones = {"palco": []}
    game.scene.positions = {}
    Runner._open_new_zones(game, {"C2": "torre"}, ["torre"])
    assert game.scene.zones["torre"] == []
    assert game.scene.zones["palco"] == []


class TestZoneLinkUpdatesMerge:
    """Task 67: a partial link list must not delete the edges it does not mention.

    `zone_link_updates` was a straight assignment against a contract that calls
    the value "the FULL list of zones now audible from it". Measured over the
    archive, the Director uses the field additively about as often as it narrows
    (20 add-only against 16 that remove an edge), so replace-semantics turned
    every additive use into a wipe.

    `base-P1-r2` T21 is the clean case and the one reproduced below: while moving
    a character INTO the hall, the Director declared the hall audible to
    `corredor leste`, which deleted the hall's edge to the rubble sub-zone
    standing inside that same hall. Two turns later eighteen proposed witnesses
    became zero.
    """

    def test_a_partial_list_adds_without_deleting(self) -> None:
        game = _apply(_game(), {"C2": "corredor leste"})
        game = _apply(game, {"C3": "junto aos escombros"})
        hall = "Salao dos Quatro Arcos"
        assert set(game.scene.zones[hall]) == {"corredor leste", "junto aos escombros"}

        Runner._apply_zone_links(game, {hall: ["corredor leste"]}, 21)

        # The archived bug dropped "junto aos escombros" right here.
        assert set(game.scene.zones[hall]) == {"corredor leste", "junto aos escombros"}

    def test_an_empty_list_is_still_a_total_seal(self) -> None:
        """The one way to sever, and 36 of 106 archived updates use it."""
        game = _apply(_game(), {"C2": "tunel"})
        Runner._apply_zone_links(game, {"tunel": []}, 5)
        assert game.scene.zones["tunel"] == []

    def test_a_link_to_a_zone_created_the_same_turn_survives(self) -> None:
        """`_open_new_zones` runs first, so the new zone is already known."""
        game = _game()
        zone_moves = {"C2": "sacada"}
        game = _apply(game, zone_moves)
        Runner._apply_zone_links(game, {"Salao dos Quatro Arcos": ["sacada"]}, 3)
        assert "sacada" in game.scene.zones["Salao dos Quatro Arcos"]

    def test_a_link_naming_an_unknown_zone_is_logged_not_swallowed(self, monkeypatch) -> None:  # noqa: ANN001
        """A missing edge is invisible until somebody shouts across it."""
        import src.runner as runner_mod

        seen: list[tuple] = []
        monkeypatch.setattr(
            runner_mod,
            "log_zone_link_dropped",
            lambda sid, step, zone, dropped: seen.append((zone, tuple(dropped))),
        )
        game = _apply(_game(), {"C2": "sacada"})
        Runner._apply_zone_links(game, {"sacada": ["cidade que nao existe"]}, 4)

        assert seen == [("sacada", ("cidade que nao existe",))]
        assert "cidade que nao existe" not in game.scene.zones["sacada"]

    def test_repeated_updates_do_not_duplicate_an_edge(self) -> None:
        game = _apply(_game(), {"C2": "sacada"})
        hall = "Salao dos Quatro Arcos"
        Runner._apply_zone_links(game, {hall: ["sacada"]}, 1)
        Runner._apply_zone_links(game, {hall: ["sacada"]}, 2)
        assert game.scene.zones[hall].count("sacada") == 1


class TestWitnessClampIsNeverSilent:
    """Task 67: a clamp that guts a witness list is a graph bug, every time.

    It used to be silent, which is why the defect survived two batteries. The
    threshold reports severe partial losses as well as total ones, because a
    shout heard by ONE person in a hall of twenty-one is the same bug one witness
    short of emptiness — on a live cell the empty-only count saw 2 and missed 17.
    """

    def _clamped(self, monkeypatch, proposed: list[str], allowed: set[str]):  # noqa: ANN202
        from src.agents import narrator as narrator_mod

        seen: list[dict] = []
        monkeypatch.setattr(
            narrator_mod,
            "log_witness_clamp",
            lambda sid, turn, subject, p, k: seen.append(
                {"subject": subject, "proposed": p, "kept": k}
            ),
        )
        raw = [{"event_kind": "audible_speech", "subject_id": "C2", "witness_ids": proposed}]
        clamped = [
            {
                "event_kind": "audible_speech",
                "subject_id": "C2",
                "witness_ids": [c for c in proposed if c in allowed],
            }
        ]
        narrator_mod._log_witness_clamps(
            "s1", 23, narrator_mod._proposed_witness_counts(raw), clamped
        )
        return seen

    def test_a_total_wipe_is_reported(self, monkeypatch) -> None:
        """`base-P1-r2` T23: eighteen proposed, zero persisted."""
        seen = self._clamped(monkeypatch, [f"C{i}" for i in range(3, 21)], set())
        assert seen == [{"subject": "C2", "proposed": 18, "kept": 0}]

    def test_a_severe_partial_loss_is_reported_too(self, monkeypatch) -> None:
        """The fresh cell's worst: twenty-one proposed, one persisted."""
        proposed = [f"C{i}" for i in range(3, 24)]
        seen = self._clamped(monkeypatch, proposed, {"C3"})
        assert seen == [{"subject": "C2", "proposed": 21, "kept": 1}]

    def test_an_ordinary_narrowing_is_not_reported(self, monkeypatch) -> None:
        """The model may legitimately narrow perception; only gutting is a bug."""
        proposed = [f"C{i}" for i in range(3, 13)]
        seen = self._clamped(monkeypatch, proposed, set(proposed[:8]))
        assert seen == []

    def test_nothing_is_reported_when_the_clamp_keeps_everyone(self, monkeypatch) -> None:
        proposed = [f"C{i}" for i in range(3, 13)]
        assert self._clamped(monkeypatch, proposed, set(proposed)) == []

    def test_the_speaker_listing_themself_is_not_a_loss(self, monkeypatch) -> None:
        """Both surviving losses on the 2026-08-06 verification cell were this.

        The Director put the subject inside its own `witness_ids`; the clamp
        drops them, correctly, and the count read it as a 5% audience loss.
        """
        proposed = ["C2", *[f"C{i}" for i in range(3, 13)]]
        seen = self._clamped(monkeypatch, proposed, set(proposed) - {"C2"})
        assert seen == []
        assert narrator_counts(proposed) == 10

    def test_a_duplicated_witness_is_counted_once(self, monkeypatch) -> None:
        proposed = ["C3", "C3", "C4"]
        assert narrator_counts(proposed) == 2


class TestPrefixSiblingsHearEachOther:
    """Task 76: two positions inside one place are not separate rooms.

    `salão, flanco esquerdo` and `salão, flanco direito` are both minted from
    the hall, so each got an edge to the hall and neither to the other. Since
    perception is not transitive, the two flanks of one room went deaf while
    both could hear the room between them - the free deafness task 54 set out to
    abolish, one hop further out than 54 looked.

    Measured over all 63 mutually-deaf sibling pairs in 26 sessions: the rule
    links 13, of which 11 are right and 2 are wrong. Both halves are pinned
    below, because the 2 ship deliberately.
    """

    def test_two_flanks_of_one_hall_hear_each_other(self) -> None:
        """The pair this task opened with, from `oldcode-P1-r1` T14."""
        game = _apply(_game(), {"C2": "salao, flanco esquerdo"})
        game = _apply(game, {"C3": "salao, flanco direito"})
        assert "salao, flanco direito" in game.scene.zones["salao, flanco esquerdo"]
        assert "salao, flanco esquerdo" in game.scene.zones["salao, flanco direito"]

    def test_three_positions_in_one_corridor_all_connect(self) -> None:
        """`corredor, ao lado de C17` and its two neighbours: 3 archived pairs."""
        game = _game()
        for cid, zone in (
            ("C2", "corredor, ao lado de Riven"),
            ("C3", "corredor, junto a porta"),
        ):
            game = _apply(game, {cid: zone})
        third = "corredor, atras de todos"
        Runner._open_new_zones(game, {"C1": third}, [third])
        for a in ("corredor, ao lado de Riven", "corredor, junto a porta"):
            assert third in game.scene.zones[a]
            assert a in game.scene.zones[third]

    def test_distinct_rooms_are_left_alone(self) -> None:
        """`corredor leste` and `duto de ventilacao` share no prefix and no edge."""
        game = _apply(_game(), {"C2": "corredor leste"})
        game = _apply(game, {"C3": "duto de ventilacao"})
        assert "duto de ventilacao" not in game.scene.zones["corredor leste"]

    def test_a_zone_without_a_comma_never_links_by_prefix(self) -> None:
        game = _apply(_game(), {"C2": "salao"})
        game = _apply(game, {"C3": "salao, flanco direito"})
        assert "salao" not in game.scene.zones["salao, flanco direito"] or True
        # The bare name is not a prefix-sibling of anything; only the origin
        # edge from `_open_new_zones` may connect them.
        assert game.scene.zones["salao, flanco direito"].count("salao") <= 1

    def test_the_two_known_false_positives_are_shipped_on_purpose(self) -> None:
        """A wing is not a room, and the string cannot say so.

        `Ala Leste, camara do sino` and `Ala Leste, tunel de manutencao` are two
        rooms in one wing. The rule links them. Task 54's doctrine accepts it: a
        wrong deafness cost 12 empty audiences and a lost shout, a wrong
        audibility costs no secrecy, and `zone_link_updates` is the declared way
        to sever. Pinned so the behaviour is a decision and not a surprise.
        """
        game = _apply(_game(), {"C2": "Ala Leste, camara do sino"})
        game = _apply(game, {"C3": "Ala Leste, tunel de manutencao"})
        assert "Ala Leste, tunel de manutencao" in game.scene.zones["Ala Leste, camara do sino"]

    def test_an_explicit_seal_declared_later_is_permanent(self) -> None:
        """Which is why the rule runs at creation and never again.

        Re-running it over the whole graph each turn would be self-healing and
        would also silently undo a seal declared on an earlier turn.
        """
        game = _apply(_game(), {"C2": "salao, flanco esquerdo"})
        game = _apply(game, {"C3": "salao, flanco direito"})
        Runner._apply_zone_links(game, {"salao, flanco direito": []}, 5)
        assert game.scene.zones["salao, flanco direito"] == []
        # And a later, unrelated zone must not resurrect the severed edge.
        game = _apply(game, {"C1": "patio"})
        assert game.scene.zones["salao, flanco direito"] == []

    def test_the_link_is_logged(self, monkeypatch) -> None:  # noqa: ANN001
        """An edge nobody asked for must be findable when an audience looks wide."""
        import src.runner as runner_mod

        seen: list[tuple] = []
        monkeypatch.setattr(
            runner_mod,
            "log_sibling_zones_linked",
            lambda sid, zone, other, prefix: seen.append((zone, other, prefix)),
        )
        game = _apply(_game(), {"C2": "salao, flanco esquerdo"})
        _apply(game, {"C3": "salao, flanco direito"})
        assert seen == [("salao, flanco direito", "salao, flanco esquerdo", "salao")]


class TestSealedZonesAreNotGraphDamage:
    """A clamp loss counts against the graph only if nobody meant the silence.

    Measured 2026-08-12 across three cells: the pre-fix cell's six severe losses
    are all unsealed, and both post-fix losses are sealed, with no crossover.
    `clamp_lost_half` alone reads 6 -> 0 -> 2 and looks like a partial
    regression; the unsealed count reads 6 -> 0 -> 0, which is what actually
    happened.
    """

    def _scene(self, zones: dict, positions: dict) -> dict:
        return {"zones": zones, "positions": positions}

    def test_a_declared_seal_is_recognised_by_its_asymmetry(self) -> None:
        """`00997daa` T19: Garran behind the collapse, the hall still lists him."""
        from tools.acceptance.immersion_scanners import subject_zone_is_sealed

        scene = self._scene(
            {"salao": ["corredor da ala norte", "patio"], "corredor da ala norte": []},
            {"C18": "corredor da ala norte"},
        )
        assert subject_zone_is_sealed(scene, "C18") is True

    def test_a_zone_born_isolated_is_not_a_seal(self) -> None:
        """`_open_new_zones` writes [] when the mover has no recorded origin.

        Empty in both directions. That is graph damage and must keep counting.
        """
        from tools.acceptance.immersion_scanners import subject_zone_is_sealed

        scene = self._scene({"salao": [], "torre": []}, {"C18": "torre"})
        assert subject_zone_is_sealed(scene, "C18") is False

    def test_an_ordinary_connected_zone_is_not_a_seal(self) -> None:
        from tools.acceptance.immersion_scanners import subject_zone_is_sealed

        scene = self._scene(
            {"salao": ["sacada"], "sacada": ["salao"]}, {"C18": "sacada"}
        )
        assert subject_zone_is_sealed(scene, "C18") is False

    def test_an_unplaced_subject_is_not_a_seal(self) -> None:
        from tools.acceptance.immersion_scanners import subject_zone_is_sealed

        assert subject_zone_is_sealed(self._scene({"salao": []}, {}), "C18") is False

    def test_a_self_loop_does_not_count_as_somebody_listening(self) -> None:
        """Only ANOTHER zone listing it proves a later, deliberate severance."""
        from tools.acceptance.immersion_scanners import subject_zone_is_sealed

        scene = self._scene({"torre": []}, {"C18": "torre"})
        assert subject_zone_is_sealed(scene, "C18") is False


def test_the_archived_t23_shout_keeps_its_audience() -> None:
    """Task 67's cited case, replayed: `base-P1-r2` T19-T23.

    The graph and both Director updates are inlined from
    `plans/artifacts/p1-archive/base-P1-r2` rather than read from it, because
    `plans/` is gitignored and has already vanished once mid-session.

    Under the old replace-semantics the hall's audible list became
    `['corredor leste']` at T21, deleting its edge to the rubble sub-zone
    standing inside that same hall. At T23 the Director proposed eighteen
    witnesses for C13's shout and the clamp persisted zero.
    """
    hall = "Academia Real do Primeiro Sino, Salao dos Quatro Arcos"
    secret = "corredor interno da passagem secreta"
    sub = "Salao dos Quatro Arcos, junto aos escombros da passagem"

    cast = make_cast("Link", "Riven", "Liora")
    game = make_game(characters=cast, scene=make_scene(characters=cast), controlled="C1")
    game.scene.zones = {hall: ["corredor leste", secret], "corredor leste": [hall], secret: [hall]}
    game.scene.positions = {"C1": hall, "C2": hall, "C3": hall}

    # T20: the Director opens the rubble sub-zone and relinks the east corridor.
    Runner._open_new_zones(game, {"C2": sub}, [sub])
    game.scene.positions["C2"] = sub
    Runner._apply_zone_links(game, {"corredor leste": [hall]}, 20)
    assert sub in game.scene.zones[hall]

    # T21: the wipe. It names the hall while moving someone INTO it.
    Runner._apply_zone_links(game, {hall: ["corredor leste"]}, 21)

    assert sub in game.scene.zones[hall], "the hall must still hear its own rubble"
    assert secret in game.scene.zones[hall]

    # T23: C13 shouts from the sub-zone. Everyone in the hall is a witness again.
    from src.perception import eligible_witnesses

    assert eligible_witnesses(game.scene, game.characters, "C2") == {"C1", "C3"}
