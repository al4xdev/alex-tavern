"""Task 71's cost lever, made reproducible.

Every figure in task 71 was produced by an ad-hoc script that was never checked
in, against the pre-67 zone graph. Both of the graph bugs 67 fixed manufacture a
spurious singleton cluster, so those figures were upper bounds and the task is
explicitly blocked on re-deriving them. That is only worth anything if the
before and the after come out of the same code, which is what this pins.

The reproduction is recorded in `.plan/tasks/71-per-viewer-narration.md`: over
the 16 archived sessions this scanner returns 610 narrated turns, 168 split,
1.562 clusters per turn, 1.202 holding two or more, 8 of 16 never splitting -
matching the numbers already written in that task to every digit it reports.
"""

from __future__ import annotations

from tools.acceptance.immersion_scanners import (
    scan_cross_cluster_leak,
    scan_scene_splits,
    scene_clusters,
)

CHARACTERS = {f"C{i}": {"name": f"C{i}"} for i in range(1, 6)}


def _scene(zones: dict, positions: dict) -> dict:
    return {
        "present_characters": list(positions),
        "positions": positions,
        "zones": zones,
    }


def test_one_room_is_one_cluster() -> None:
    scene = _scene({"salao": []}, {"C1": "salao", "C2": "salao", "C3": "salao"})
    assert scene_clusters(scene, CHARACTERS) == [["C1", "C2", "C3"]]


def test_an_empty_zone_map_leaves_everyone_together() -> None:
    """`can_perceive` treats no graph as no separation, and so must this."""
    scene = _scene({}, {"C1": "a", "C2": "b"})
    assert scene_clusters(scene, CHARACTERS) == [["C1", "C2"]]


def test_two_sealed_zones_are_two_clusters() -> None:
    scene = _scene({"salao": [], "rua": []}, {"C1": "salao", "C2": "rua", "C3": "salao"})
    assert scene_clusters(scene, CHARACTERS) == [["C1", "C3"], ["C2"]]


def test_a_linked_pair_of_zones_is_one_cluster() -> None:
    scene = _scene(
        {"salao": ["sacada"], "sacada": ["salao"]},
        {"C1": "salao", "C2": "sacada"},
    )
    assert scene_clusters(scene, CHARACTERS) == [["C1", "C2"]]


def test_a_one_way_edge_does_not_join_a_cluster() -> None:
    """The whole reason components are built on MUTUAL perception.

    C2 can hear the hall; the hall cannot hear C2. Rendering them one narration
    hands the hall a scene it cannot perceive, which is the leak task 71 exists
    to close, arriving through the fix for it.
    """
    scene = _scene({"salao": [], "galeria": ["salao"]}, {"C1": "salao", "C2": "galeria"})
    assert scene_clusters(scene, CHARACTERS) == [["C1"], ["C2"]]


def test_a_chain_of_mutual_links_is_a_single_cluster() -> None:
    """Connected components, not cliques: A hears B hears C joins all three."""
    scene = _scene(
        {"a": ["b"], "b": ["a", "c"], "c": ["b"]},
        {"C1": "a", "C2": "b", "C3": "c"},
    )
    assert scene_clusters(scene, CHARACTERS) == [["C1", "C2", "C3"]]


def test_a_character_absent_from_the_cast_is_not_placed() -> None:
    scene = _scene({"salao": []}, {"C1": "salao", "C99": "salao"})
    assert scene_clusters(scene, CHARACTERS) == [["C1"]]


class TestScanSceneSplits:
    def _state(self, *snapshots: dict) -> dict:
        return {
            "characters": CHARACTERS,
            "history": [
                {"content_type": "narration", "turn_number": i + 1, "scene_snapshot": snap}
                for i, snap in enumerate(snapshots)
            ],
        }

    def test_only_narration_records_are_counted(self) -> None:
        state = self._state(_scene({"a": [], "b": []}, {"C1": "a", "C2": "b"}))
        state["history"].append(
            {
                "content_type": "speech",
                "turn_number": 2,
                "scene_snapshot": _scene({"a": [], "b": []}, {"C1": "a", "C2": "b"}),
            }
        )
        assert scan_scene_splits(state)["narrated_turns"] == 1

    def test_split_share_and_means(self) -> None:
        together = _scene({"a": []}, {"C1": "a", "C2": "a"})
        apart = _scene({"a": [], "b": []}, {"C1": "a", "C2": "b"})
        report = scan_scene_splits(self._state(together, apart, apart))
        assert report["narrated_turns"] == 3
        assert report["split_turns"] == 2
        assert report["split_share"] == round(2 / 3, 4)
        assert report["mean_clusters"] == round(5 / 3, 3)
        # Only the unsplit turn holds a cluster of two or more.
        assert report["mean_clusters_ge2"] == round(1 / 3, 3)
        assert report["max_clusters"] == 2

    def test_a_session_that_never_splits_reports_zero(self) -> None:
        together = _scene({"a": []}, {"C1": "a", "C2": "a"})
        report = scan_scene_splits(self._state(together, together))
        assert report["split_turns"] == 0
        assert report["mean_clusters"] == 1.0

    def test_a_session_with_no_narration_is_not_a_division_by_zero(self) -> None:
        report = scan_scene_splits({"characters": CHARACTERS, "history": []})
        assert report["narrated_turns"] == 0
        assert report["split_share"] is None


class TestCrossClusterLeakScan:
    """Task 71's defect counted by checked-in code, for the same reason.

    Reproduces the live sessions it was built from: `21f7c4e1` 0 of 10 and
    `c76037ff` 3 of 32, the residual that sent the guard back for a
    deterministic backstop.
    """

    CAST = {
        "C1": {"mind": {"name": "Link"}},
        "C2": {"mind": {"name": "Marta Ferrolume"}},
        "C3": {"mind": {"name": "Bento"}},
        "C4": {"mind": {"name": "Noa Veu"}},
    }

    def _state(self, content: str, audience: list[str] | None) -> dict:
        return {
            "characters": self.CAST,
            "history": [
                {
                    "content_type": "narration",
                    "turn_number": 1,
                    "content": content,
                    "audience": audience,
                    "scene_snapshot": {
                        "present_characters": ["C1", "C2", "C3", "C4"],
                        "positions": {
                            "C1": "salao",
                            "C3": "salao",
                            "C2": "deposito",
                            "C4": "deposito",
                        },
                        "zones": {"salao": [], "deposito": []},
                    },
                }
            ],
        }

    def _pad(self, text: str) -> str:
        return text + " " + "A pedra range sob o peso do silencio prolongado. " * 5

    def test_a_scoped_narration_naming_an_unreachable_character_leaks(self) -> None:
        report = scan_cross_cluster_leak(
            self._state(self._pad("Marta Ferrolume ergue a cabeca."), ["C1", "C3"])
        )
        assert report["split_narrations"] == 1
        assert report["leaking"] == 1

    def test_a_scoped_narration_about_its_own_cluster_does_not(self) -> None:
        report = scan_cross_cluster_leak(
            self._state(self._pad("Bento avanca ate a fresta."), ["C1", "C3"])
        )
        assert report["leaking"] == 0

    def test_a_public_narration_on_a_split_scene_leaks(self) -> None:
        """The pre-71 engine by construction: one paragraph, two halves.

        Counting over all readers at once would answer "somebody can reach
        this" for each half and find nothing. It is scored per reader cluster.
        """
        report = scan_cross_cluster_leak(
            self._state(self._pad("Marta Ferrolume ergue a cabeca."), None)
        )
        assert report["leaking"] == 1

    def test_a_surname_that_is_an_ordinary_noun_does_not_count(self) -> None:
        """`veu` is Portuguese for veil and also Noa Veu's surname.

        The ad-hoc script this scanner replaced matched first names and put the
        pre-71 rate at 21 of 29; strict matching puts it at 16 of 29. The
        difference is entirely this class of false positive.
        """
        report = scan_cross_cluster_leak(
            self._state(self._pad("Um veu de poeira cobre o chao."), ["C1", "C3"])
        )
        assert report["leaking"] == 0

    def test_a_one_line_speech_report_is_not_scored_as_prose(self) -> None:
        """`_report_speech` writes narration records too; length separates them."""
        report = scan_cross_cluster_leak(
            self._state("Marta Ferrolume diz algo.", ["C1", "C3"])
        )
        assert report["split_narrations"] == 0

    def test_an_unsplit_scene_is_not_scored(self) -> None:
        state = self._state(self._pad("Marta Ferrolume ergue a cabeca."), None)
        state["history"][0]["scene_snapshot"]["zones"] = {}
        assert scan_cross_cluster_leak(state)["split_narrations"] == 0
