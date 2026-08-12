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

    def test_the_roster_names_only_this_cluster(self) -> None:
        """The residual leak, session `c76037ff`: the transcript reintroduced her.

        Scoping cast, staging and events was not enough. Narration rendered
        while the scene was still whole is `audience=None`, so it stays visible
        to every cluster - correctly, that reader did see it happen - and the
        renderer continued the thread into the present, showing Marta kneeling
        at a lock for three consecutive turns to a group that could no longer
        perceive her, with no event of the beat naming her.
        """
        user = self._user({"C3", "C4"})
        line = next(line for line in user.split("\n") if "IN THIS VIEW" in line)
        roster = user.split("IN THIS VIEW")[1].split("\n")[1]
        assert "Bento" in roster and "Nix" in roster
        assert "Marta" not in roster
        assert "PRESENT actions" in line

    def test_an_unsplit_scene_gets_no_roster_block(self) -> None:
        """It would be a lie there: everyone present is in the one cluster."""
        assert "IN THIS VIEW" not in self._user(None)

    def test_the_roster_carries_no_dashes(self) -> None:
        """House rule: prompts may not contain em or en dashes."""
        user = self._user({"C3", "C4"})
        assert "—" not in user and "–" not in user

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
            # An event reaching EACH cluster, or the events-fold below suppresses
            # the far one and these tests stop testing the split.
            return director_beat(
                next_speakers=["Narrator"],
                perception_events=[
                    {
                        "event_kind": "observation",
                        "subject_id": "C1",
                        "content": "Uma tocha cai no salao.",
                        "witness_ids": ["C3"],
                    },
                    {
                        "event_kind": "observation",
                        "subject_id": "C2",
                        "content": "O teto do corredor racha.",
                        "witness_ids": ["C4"],
                    },
                ],
            )

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
        # NOT "zone". `_report_speech` also appends a Narrator `narration`
        # record with a zone-derived audience, and without a distinct origin the
        # two are the same record shape - a paragraph of prose and a one-line
        # report that somebody spoke. Caught on a live session.
        assert {r.audience_origin for r in narrations} == {"cluster"}

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


class TestOffstageActorsAreStrippedDeterministically:
    """The structural half of the cross-cluster guard.

    The `IN THIS VIEW` roster asks the model not to stage someone the cluster
    cannot perceive. This makes it true whatever the model does, which is the
    difference task 59 finding 1 keeps re-teaching: a prompt promise with no
    structure behind it loses. Mirrors `_strip_echoed_sentences`, the guard that
    already sits beside it for the same reason.

    Measured on the split narrations of both post-71 sessions: fires on all
    three known leaks, and on none of the other thirty-nine.
    """

    CAST = make_cast("Link", "Marta Ferrolume", "Bento", "Noa Veu")

    def _scene(self) -> Scene:
        return Scene(
            location="Salao",
            time_of_day="Manha",
            present_characters=["C1", "C2", "C3", "C4", "Player"],
            physical_facts={},
            zones={"salao": [], "deposito": []},
            positions={"C1": "salao", "C3": "salao", "C2": "deposito", "C4": "deposito"},
        )

    def _strip(self, text: str, viewers: set[str] | None = None) -> str:
        from src.agents.prose import _strip_offstage_actors

        return _strip_offstage_actors(
            text, self._scene(), self.CAST, "C1", viewers or {"C1", "C3"}
        )

    def test_the_measured_leak_sentence_is_removed(self) -> None:
        """Verbatim from `c76037ff` T16, the group at the north exit."""
        text = (
            "Um rugido abafado brota do piso central do salao. "
            "Marta Ferrolume, ainda de joelhos diante do corredor A, ergue a cabeca, "
            "a chave de reserva esquecida na mao. "
            "O tremor que se segue abre ainda mais a fresta."
        )
        out = self._strip(text)
        assert "Marta Ferrolume" not in out
        assert "Um rugido abafado brota do piso central do salao." in out
        assert "O tremor que se segue abre ainda mais a fresta." in out

    def test_a_surname_that_is_an_ordinary_noun_does_not_fire(self) -> None:
        """The counter-example that killed the first version of this guard.

        `veu` is Portuguese for veil AND the surname of Noa Veu, who is not in
        this sentence. Matching name tokens case-insensitively deleted three
        atmospheric sentences from a real session for containing the noun. This
        is the `menos` bug of task 70 wearing a different hat.
        """
        text = (
            "Particulas de poeira e gas dancam em espirais lentas, criando um "
            "veu opaco que distorce os contornos das arquibancadas."
        )
        assert self._strip(text) == text

    def test_the_capitalised_noun_still_does_not_fire_on_a_partial_name(self) -> None:
        """A multi-token name must match in full and adjacent."""
        text = "Um Veu de poeira cobre o chao do salao inteiro, denso e imovel."
        assert self._strip(text) == text

    def test_a_character_inside_the_cluster_is_never_stripped(self) -> None:
        text = "Bento avanca ate a fresta e ergue a lamina, os olhos fixos na fenda."
        assert self._strip(text) == text

    def test_nothing_is_stripped_for_an_unsplit_render(self) -> None:
        """`viewers is None` never reaches this guard, but pin the shape anyway."""
        text = "Marta Ferrolume atravessa o salao com o martelo na mao."
        assert self._strip(text, {"C1", "C2", "C3", "C4"}) == text

    def test_an_ambiguous_name_is_left_alone(self) -> None:
        """Two characters sharing a name means the name decides nothing."""
        cast = make_cast("Link", "Marta Ferrolume", "Marta Ferrolume", "Nix")
        from src.agents.prose import _strip_offstage_actors

        text = "Marta Ferrolume ergue a cabeca diante da porta travada e espera."
        assert _strip_offstage_actors(text, self._scene(), cast, "C1", {"C1", "C3"}) == text

    def test_a_paragraph_that_is_entirely_offstage_returns_empty(self) -> None:
        """The caller then keeps the draft, exactly as the echo guard does."""
        text = "Marta Ferrolume ergue a cabeca. Marta Ferrolume solta a chave."
        assert self._strip(text) == ""


class TestClusterProseIsDistinguishableFromASpeechReport:
    """Found on the first live post-71 session, not in review.

    `_report_speech` is the degradation path where the Narrator REPORTS a line
    instead of quoting it, and it appends `content_type="narration"`, speaker
    `Narrator`, `audience=heard_by`, `audience_origin="zone"`. The first version
    of this task wrote its cluster prose with exactly those four values, so a
    paragraph of narration and a one-line "X said something" report became the
    same record. The live read could not tell them apart, and neither could any
    scanner that counts the narration channel.
    """

    def test_the_two_paths_do_not_write_the_same_record_shape(self) -> None:
        import inspect

        from src.runner import Runner

        report = inspect.getsource(Runner._report_speech)
        assert 'audience_origin="zone"' in report, "the report path moved; re-check the collision"

        render = inspect.getsource(Runner._render_and_prepare)
        assert '"cluster"' in render
        assert 'audience_origin=None if cluster is None else "zone"' not in render


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


class TestAClusterWithNothingHappeningIsNotRendered:
    """Found by reading `c76037ff`, not by any counter.

    Its five-person cluster received sixteen narrations and eight of them had
    zero scoped events. What came back was the same room every time: `quietude`
    in 44% of them against 3% of the main cluster's, `penumbra` 50% against 0%,
    `halos` 19% against 0%. Consecutive ones score **0.02** on sequence
    similarity, so no repetition guard can see it, and a reader sees one
    paragraph four times over.

    The burst path already refuses to narrate a beat with no novel events, and
    its comment gives the reason exactly: the atmospheric fallback "would only
    re-describe the standing tableau (a null recap turn)". This applies the same
    rule per cluster.
    """

    EVENT_FOR_HALL = {
        "event_kind": "observation",
        "subject_id": "C1",
        "content": "Uma tocha cai no salao.",
        "witness_ids": ["C2"],
    }

    def _game(self, controlled: str = "C1"):  # noqa: ANN202
        return make_game(characters=CAST, scene=_split_scene(), controlled=controlled)

    def test_a_cluster_with_no_events_is_folded(self) -> None:
        clusters = Runner._narration_clusters(self._game(), [self.EVENT_FOR_HALL])
        assert clusters == [{"C1", "C2"}]

    def test_a_cluster_with_its_own_event_still_renders(self) -> None:
        corridor = {
            "event_kind": "observation",
            "subject_id": "C3",
            "content": "O teto do corredor racha.",
            "witness_ids": ["C4"],
        }
        clusters = Runner._narration_clusters(self._game(), [self.EVENT_FOR_HALL, corridor])
        assert clusters == [{"C1", "C2"}, {"C3", "C4"}]

    def test_the_player_is_rendered_even_with_nothing_happening(self) -> None:
        """Silence is honest for the room; an empty turn is not, for the reader."""
        corridor_only = {
            "event_kind": "observation",
            "subject_id": "C3",
            "content": "O teto do corredor racha.",
            "witness_ids": ["C4"],
        }
        clusters = Runner._narration_clusters(self._game("C1"), [corridor_only])
        assert {"C1", "C2"} in clusters

    def test_omitting_the_events_argument_folds_nothing(self) -> None:
        """Callers that predate this branch keep their behaviour."""
        assert Runner._narration_clusters(self._game()) == [{"C1", "C2"}, {"C3", "C4"}]
