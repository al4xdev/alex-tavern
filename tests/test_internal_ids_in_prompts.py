"""An internal character id must never reach a prompt that cannot resolve it.

Found on 2026-07-27 by scanning the debug logs of 17 real sessions, not by any
test: the whole suite stayed green both before and after the fix, because
nothing ever asserted what the transcript's SPEAKER column contains.

The mechanism. `speaker_label` translates only the internal ``Player`` marker;
every other speaker comes back as the stored token, and for a character that
token IS its id. The Director is fine - its prompt carries an
``ID=C2 | NAME=Marta`` roster, and 330/330 real Director calls resolved. Prose
and the Summarizer carry no such mapping, so they were handed ``C2`` with no way
to know who that is.

What it cost, measured in those sessions:

- 4968 raw ids across 356 prose prompts. Once, the renderer copied one into the
  narration the player reads: "raising his free hand in a short, decisive motion
  toward C2".
- 258 across 15 summarizer prompts, and this is the expensive one: 11 story
  summaries came back carrying the token, and the summary is the durable memory
  every later prompt reads. One invented a third person out of it - "a group
  (Thorn, Lyra, and a talkative companion called C2)" - and another collapsed
  two different people into it: "Lyra (C2) ... A hooded stranger (C2)".

So the test is not about tidiness. An unresolvable token in the summary corrupts
the cast for the rest of the session.
"""

from __future__ import annotations

import re

import pytest

from src.agents.narrator import build_narrator_messages
from src.agents.prose import build_prose_messages
from src.agents.summarizer import build_summarizer_messages
from src.models import display_name
from tests.factories import make_cast, make_record, make_scene

CAST = make_cast("Rui", "Marta", "Bento")
SCENE = make_scene(characters=CAST)
ID_RE = re.compile(r"\bC\d\b")


def _history() -> list:
    """Every speaker kind: a character, the human's character, the Narrator."""
    return [
        make_record(1, "C2", "Boa noite.", "speech"),
        make_record(2, "Player", "Quem e voce?", "speech"),
        make_record(3, "C3", "Ninguem importante.", "action"),
        make_record(4, "Narrator", "A porta bate.", "narration"),
        make_record(5, "C2", "Vamos embora.", "speech"),
    ]


def _text(messages: list[dict]) -> str:
    return "\n".join(message["content"] for message in messages)


class TestDisplayName:
    def test_a_character_id_resolves_to_the_name(self) -> None:
        assert display_name("C2", CAST, "C1") == "Marta"

    def test_the_player_marker_resolves_to_the_controlled_character(self) -> None:
        """The agency lock: the internal marker must never reach a model."""
        assert display_name("Player", CAST, "C1") == "Rui"

    def test_a_non_character_speaker_passes_through(self) -> None:
        assert display_name("Narrator", CAST, "C1") == "Narrator"

    def test_an_unknown_id_is_returned_unchanged(self) -> None:
        """A character who left the cast still needs SOME label, not a crash."""
        assert display_name("C9", CAST, "C1") == "C9"


class TestPromptsWithoutARoster:
    """These two prompts carry no id/name mapping, so they must carry no ids."""

    def test_the_prose_prompt_has_no_raw_id(self) -> None:
        prompt = _text(
            build_prose_messages(
                scene=SCENE,
                characters=CAST,
                controlled_id="C1",
                history=_history(),
                events=[
                    {
                        "event_kind": "observation",
                        "subject_id": "C2",
                        "content": "Alguem se move perto da porta.",
                        "witness_ids": ["C1", "C3"],
                    }
                ],
            )
        )
        found = ID_RE.search(prompt)
        assert not found, (
            f"raw id {found.group(0)!r} in the prose prompt: "
            f"{prompt[max(0, found.start() - 80) : found.start() + 80]!r}"
        )
        assert "Marta" in prompt, "the transcript must still say WHO spoke"

    def test_the_summarizer_prompt_has_no_raw_id(self) -> None:
        prompt = _text(
            build_summarizer_messages(
                characters=CAST,
                controlled_id="C1",
                story_summary="",
                evicted_turns=_history(),
            )
        )
        assert not ID_RE.search(prompt), (
            "a raw id here ends up in story_summary, which every later prompt reads"
        )
        assert "Marta" in prompt and "Rui" in prompt


class TestTheDirectorIsDeliberatelyDifferent:
    """Not an oversight to fix later: the Director needs stable ids.

    Its typed events reference `subject_id`/`witness_ids` by id, so its prompt
    speaks ids AND ships the roster that resolves them. Changing that is a
    Director prompt change and belongs to its own measured decision, not to a
    tidy-up.
    """

    def test_the_director_gets_ids_and_the_roster_that_resolves_them(self) -> None:
        prompt = _text(
            build_narrator_messages(
                scene=SCENE,
                characters=CAST,
                player_controlled_id="C1",
                history=_history(),
            )
        )
        assert ID_RE.search(prompt)
        for cid, character in CAST.items():
            assert f"ID={cid} | NAME={character.mind.name}" in prompt


@pytest.mark.parametrize("speaker", ["C2", "Player", "Narrator"])
def test_no_builder_without_a_roster_echoes_the_stored_token(speaker: str) -> None:
    """One record at a time, so a failure names the speaker kind that broke."""
    history = [make_record(1, speaker, "Uma linha qualquer.", "speech")]
    prose = _text(
        build_prose_messages(
            scene=SCENE, characters=CAST, controlled_id="C1", history=history, events=[]
        )
    )
    summary = _text(
        build_summarizer_messages(
            characters=CAST, controlled_id="C1", story_summary="", evicted_turns=history
        )
    )
    for label, prompt in (("prose", prose), ("summarizer", summary)):
        assert not ID_RE.search(prompt), f"{label} echoed the stored token for {speaker!r}"
        assert "Player" not in prompt, f"{label} leaked the internal Player marker"


class TestTheDirectorsFreeTextIsProjected:
    """The third path, and the one the ledger could not close on its own.

    `context_for_character` is free prose the Director writes, and the Director
    thinks in ids. `project_text_for_viewer` rewrote every id it held a
    `PersonView` for - but a viewer holds no view of THEMSELVES, so their own id
    was the one token that always survived. Two real sessions show it reaching
    the character: "a sharp, scraping sound comes from the drain grate near C2's
    feet", handed to C2.
    """

    def _perspective(self, known: dict[str, tuple[str | None, str]]):  # noqa: ANN202
        from src.models import CharacterPerspective, PersonView

        return CharacterPerspective(
            initialized_turn=0,
            processed_through_turn=0,
            people={
                sid: PersonView(known_name=name, reference=ref, source_turn=0)
                for sid, (name, ref) in known.items()
            },
        )

    def test_the_viewer_never_reads_their_own_id(self) -> None:
        from src.agents.perspective import project_text_for_viewer

        projected = project_text_for_viewer(
            "Um som raspa perto dos pes de C2.",
            CAST,
            self._perspective({"C1": ("Rui", "o homem alto")}),
            viewer_id="C2",
        )
        assert "C2" not in projected
        assert "Marta" in projected, "the viewer knows their own name"

    def test_a_stranger_id_becomes_the_reference_not_the_name(self) -> None:
        """The dangerous repair: resolving every id to its canonical name would
        hand out acquaintance nobody earned. An id is not an introduction."""
        from src.agents.perspective import FALLBACK_REFERENCE, project_text_for_viewer

        projected = project_text_for_viewer(
            "C3 entra pela porta dos fundos.",
            CAST,
            self._perspective({"C1": ("Rui", "o homem alto")}),
            viewer_id="C2",
        )
        assert "C3" not in projected
        assert "Bento" not in projected, "C3 was never introduced to this viewer"
        assert FALLBACK_REFERENCE in projected

    def test_the_ledger_still_wins_for_people_it_knows(self) -> None:
        from src.agents.perspective import project_text_for_viewer

        projected = project_text_for_viewer(
            "C1 levanta a mao.",
            CAST,
            self._perspective({"C1": (None, "o homem de capa")}),
            viewer_id="C2",
        )
        assert projected == "o homem de capa levanta a mao."

    def test_without_a_ledger_the_sweep_still_runs(self) -> None:
        """A perspective is built lazily; the first turn can precede it."""
        from src.agents.perspective import FALLBACK_REFERENCE, project_text_for_viewer

        projected = project_text_for_viewer("C1 e C2 se olham.", CAST, None, viewer_id="C2")
        assert "C1" not in projected and "C2" not in projected
        assert FALLBACK_REFERENCE in projected and "Marta" in projected
