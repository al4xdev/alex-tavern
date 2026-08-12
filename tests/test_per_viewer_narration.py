"""Task 71: a reader is never handed narration for a room they cannot reach.

The defect was structural, not a prompt failure. `prose.py`'s system prompt has
always carried *"Characters in zones that cannot perceive each other must NEVER
be staged as sharing space… cut between separated spaces explicitly"*, and the
renderer broke it because there was exactly one narration slot and a split scene
has two halves that both need narrating. It had no way to comply.

Measured before this shipped: on the post-67 graph **30 of 108 narrated turns
split (27.8%)**, and reading them, the separations are what the fiction says
they are - a corridor buried by a collapse, a dungeon door driven shut. In both
the people on the far side were handed prose describing the room they could not
see.

So the tests below are in two halves. The first pins that an unsplit scene is
untouched, because that is most turns and a regression there would be much
worse than the leak. The second pins the projection itself.
"""

from __future__ import annotations

import httpx
import pytest

from src.agents.prose import build_prose_messages
from src.models import CharacterPerspective, Scene, TurnRecord, deepcopy_scene
from src.perception import perception_clusters
from src.runner import Runner
from src.store.sessions import delete_session
from tests.factories import director_beat, make_cast, make_game, make_scene

CAST = make_cast("Link", "Marta", "Bento", "Nix")


def _split_scene() -> Scene:
    """Two people in the hall, two sealed in the corridor. The measured shape."""
    return Scene(
        location="Salao dos Quatro Arcos",
        time_of_day="Manha",
        present_characters=["C1", "C2", "C3", "C4", "Player"],
        physical_facts={},
        zones={"salao": [], "corredor": []},
        positions={"C1": "salao", "C2": "salao", "C3": "corredor", "C4": "corredor"},
    )


class TestPerceptionClusters:
    def test_a_flat_scene_is_one_cluster(self) -> None:
        scene = make_scene(characters=CAST)
        assert perception_clusters(scene, CAST) == [["C1", "C2", "C3", "C4"]]

    def test_a_sealed_split_is_two_clusters(self) -> None:
        assert perception_clusters(_split_scene(), CAST) == [["C1", "C2"], ["C3", "C4"]]

    def test_a_one_way_edge_does_not_join_a_cluster(self) -> None:
        """Mutual perception only. The deaf side must not get the hearing side's prose."""
        scene = _split_scene()
        scene.zones["corredor"] = ["salao"]
        assert perception_clusters(scene, CAST) == [["C1", "C2"], ["C3", "C4"]]

    def test_a_two_way_edge_joins_them(self) -> None:
        scene = _split_scene()
        scene.zones["corredor"] = ["salao"]
        scene.zones["salao"] = ["corredor"]
        assert perception_clusters(scene, CAST) == [["C1", "C2", "C3", "C4"]]

    def test_the_mirror_in_the_scanner_agrees(self) -> None:
        """The offline scanner reads snapshots; drift between them is silent."""
        from tools.acceptance.immersion_scanners import scene_clusters

        scene = _split_scene()
        mirrored = scene_clusters(
            {
                "present_characters": scene.present_characters,
                "positions": scene.positions,
                "zones": scene.zones,
            },
            CAST,
        )
        assert mirrored == perception_clusters(scene, CAST)


class TestUnsplitScenesAreUntouched:
    """The majority path. A regression here costs more than the leak."""

    def test_a_flat_scene_asks_for_one_public_narration(self) -> None:
        game = make_game(characters=CAST, scene=make_scene(characters=CAST), controlled="C1")
        assert Runner._narration_clusters(game) == [None]

    def test_a_connected_zone_graph_still_asks_for_one(self) -> None:
        scene = _split_scene()
        scene.zones = {"salao": ["corredor"], "corredor": ["salao"]}
        game = make_game(characters=CAST, scene=scene, controlled="C1")
        assert Runner._narration_clusters(game) == [None]

    def test_no_viewers_builds_the_pre_71_prompt_exactly(self) -> None:
        scene = _split_scene()
        events = [
            {
                "event_kind": "observation",
                "subject_id": "C3",
                "content": "O corredor desaba.",
                "witness_ids": ["C4"],
            }
        ]
        assert build_prose_messages(scene, CAST, "C1", [], events) == build_prose_messages(
            scene, CAST, "C1", [], events, viewers=None
        )


class TestTheProsePromptIsScopedToOneCluster:
    def _events(self) -> list[dict]:
        return [
            {
                "event_kind": "observation",
                "subject_id": "C1",
                "content": "Uma tocha cai no salao.",
                "witness_ids": ["C2"],
            },
            {
                "event_kind": "observation",
                "subject_id": "C3",
                "content": "O teto do corredor racha.",
                "witness_ids": ["C4"],
            },
        ]

    def _user(self, viewers: set[str] | None, history: list[TurnRecord] | None = None) -> str:
        return build_prose_messages(
            _split_scene(), CAST, "C1", history or [], self._events(), viewers=viewers
        )[1]["content"]

    def test_the_hall_is_not_told_about_the_corridor(self) -> None:
        user = self._user({"C1", "C2"})
        assert "tocha cai no salao" in user
        assert "teto do corredor racha" not in user

    def test_the_corridor_is_not_told_about_the_hall(self) -> None:
        user = self._user({"C3", "C4"})
        assert "teto do corredor racha" in user
        assert "tocha cai no salao" not in user

    def test_staging_names_only_the_zones_this_cluster_stands_in(self) -> None:
        """`prose.py`'s cut-between-spaces rule becomes followable here.

        It was unfollowable before: the renderer was told to cut between
        separated spaces and handed both of them with one slot to put them in.
        """
        user = self._user({"C3", "C4"})
        assert "corredor:" in user
        assert "salao:" not in user

    def test_the_cast_block_lists_only_this_cluster(self) -> None:
        user = self._user({"C3", "C4"})
        assert "Bento" in user and "Nix" in user
        assert "Marta" not in user

    def test_an_unreachable_record_stays_out_of_the_transcript(self) -> None:
        """Scoping events is not enough; the transcript carries the room too."""
        scene = _split_scene()
        history = [
            TurnRecord(1, "C2", "Alguem fechou a porta.", "speech", deepcopy_scene(scene)),
            TurnRecord(2, "C1", "Segura a tocha.", "speech", deepcopy_scene(scene)),
        ]
        history[0].audience = ["C1"]
        history[1].audience = ["C2"]
        user = self._user({"C3", "C4"}, history)
        assert "Marta" not in user
        assert "(story opening)" in user

    def test_an_event_reaching_both_clusters_is_narrated_to_both(self) -> None:
        """A tremor everyone feels is not a leak, and must not be filtered out."""
        quake = {
            "event_kind": "observation",
            "subject_id": "Narrator",
            "content": "O chao inteiro estremece.",
            "witness_ids": ["C1", "C2", "C3", "C4"],
        }
        for cluster in ({"C1", "C2"}, {"C3", "C4"}):
            user = build_prose_messages(
                _split_scene(), CAST, "C1", [], [quake], viewers=cluster
            )[1]["content"]
            assert "chao inteiro estremece" in user


class TestTheRunnerRendersAndPersistsPerCluster:
    async def _turn(self, monkeypatch, scene: Scene, controlled: str = "C1"):  # noqa: ANN001, ANN202
        import src.runner as runner_mod

        async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return director_beat(next_speakers=["Narrator"])

        calls: list[set[str] | None] = []

        async def fake_prose(game, events, turn_number, viewers=None):  # noqa: ANN001, ANN202, ARG001
            calls.append(viewers)
            who = "todos" if viewers is None else "-".join(sorted(viewers))
            return f"Prosa para {who}."

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {"auto_event_enabled": False})
            sid = await runner.start_session(
                {
                    "characters": dict(CAST),
                    "scene": deepcopy_scene(scene),
                    "controlled_character_id": controlled,
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_render_narration", fake_prose)
            try:
                await runner.player_turn(sid, action="Olhar em volta")
                game = await runner.get_state(sid)
            finally:
                await delete_session(sid)
        return game, calls

    @pytest.mark.asyncio
    async def test_an_unsplit_scene_renders_once_publicly(self, monkeypatch) -> None:  # noqa: ANN001
        game, calls = await self._turn(monkeypatch, make_scene(characters=CAST))
        assert calls == [None]
        narrations = [r for r in game.history if r.content_type == "narration"]
        assert len(narrations) == 1
        assert narrations[0].audience is None

    @pytest.mark.asyncio
    async def test_a_split_scene_renders_once_per_cluster(self, monkeypatch) -> None:  # noqa: ANN001
        game, calls = await self._turn(monkeypatch, _split_scene())
        assert sorted(sorted(c) for c in calls) == [["C1", "C2"], ["C3", "C4"]]

    @pytest.mark.asyncio
    async def test_each_narration_is_persisted_to_its_own_cluster(self, monkeypatch) -> None:  # noqa: ANN001
        game, _ = await self._turn(monkeypatch, _split_scene())
        narrations = [r for r in game.history if r.content_type == "narration"]
        assert len(narrations) == 2
        by_audience = {tuple(r.audience or []): r.content for r in narrations}
        assert by_audience[("C1", "C2")] == "Prosa para C1-C2."
        assert by_audience[("C3", "C4")] == "Prosa para C3-C4."
        # Perception scoping, never a whisper secret - the same distinction the
        # speech records already draw.
        assert {r.audience_origin for r in narrations} == {"zone"}

    @pytest.mark.asyncio
    async def test_the_far_cluster_cannot_read_the_players_narration(self, monkeypatch) -> None:  # noqa: ANN001
        """The closure item, end to end: zone A does not receive zone B's prose."""
        from src.models import record_visible_to

        game, _ = await self._turn(monkeypatch, _split_scene())
        narrations = [r for r in game.history if r.content_type == "narration"]
        hall = next(r for r in narrations if r.audience == ["C1", "C2"])
        assert record_visible_to(hall, "C3") is False
        assert record_visible_to(hall, "C4") is False
        assert record_visible_to(hall, "C1") is True

    @pytest.mark.asyncio
    async def test_the_turn_returns_the_controlled_characters_cluster(self, monkeypatch) -> None:  # noqa: ANN001
        game, _ = await self._turn(monkeypatch, _split_scene(), controlled="C3")
        assert game is not None
        narrations = [r for r in game.history if r.content_type == "narration"]
        assert {tuple(r.audience or []) for r in narrations} == {("C1", "C2"), ("C3", "C4")}


class TestSingletonFolding:
    """Folded for redundancy, not for cost (`AGENTS.md` §2).

    A lone character already learns their surroundings through perception events
    and memory, both per-viewer today, and nobody reads their paragraph. The
    post-67 measurement found ZERO singleton clusters across four live sessions,
    so this is a guard against the shape returning rather than a saving.
    """

    def _lone(self, controlled: str) -> Scene:
        scene = _split_scene()
        scene.positions["C4"] = "torre"
        scene.zones["torre"] = []
        return scene

    def test_a_lone_non_player_cluster_is_not_rendered(self) -> None:
        game = make_game(characters=CAST, scene=self._lone("C1"), controlled="C1")
        assert Runner._narration_clusters(game) == [{"C1", "C2"}]

    def test_the_controlled_characters_cluster_is_never_folded(self) -> None:
        """Folding it hands the one human reader an empty turn."""
        game = make_game(characters=CAST, scene=self._lone("C4"), controlled="C4")
        assert Runner._narration_clusters(game) == [{"C1", "C2"}, {"C4"}]
