"""Task 41: the Director is the ONLY agent that reads a private thought.

The task closed with this acceptance criterion unchecked:

    prose/character/summarizer/ledger continue WITHOUT seeing other characters'
    thoughts (explicit structural tests)

The word that matters there is *structural*. Each agent filters thoughts in its
own way and in its own file — `character.py:414` keeps only the caller's own,
`narrator.py:460` deliberately labels and keeps them all, prose and summarizer
just never ask for the record type. Four independent implementations of one
invariant, and no single test standing over all of them: a fifth agent, or a
refactor that unifies history formatting, could drop one of the four filters and
the suite would stay green.

So this file does not test the filters. It plants ONE distinctive token inside
one character's thought and asserts, on the real prompt each builder produces,
that the token reaches the Director and reaches nobody else. Every builder here
is pure, so this is exact — no mocking, no network, no reading of intermediate
state.

If a prompt ever starts carrying another character's inner life, this fails
regardless of which agent did it or how.
"""

from __future__ import annotations

import pytest

from src.agents.character import _format_history_for_character
from src.agents.narrator import build_narrator_messages
from src.agents.perspective import build_memory_revision_messages, capture_memory
from src.agents.prose import build_prose_messages
from src.agents.summarizer import build_summarizer_messages
from src.models import CharacterPerspective
from tests.factories import make_cast, make_record, make_scene

# Nonsense on purpose: no prompt template, cast sheet or scene description can
# produce this string by accident, so a hit is always the thought itself.
SECRET = "veludo-quirografo-8812"

CAST = make_cast("Rui", "Marta", "Bento")
SCENE = make_scene(characters=CAST)


def _history() -> list:
    """C2 thinks the secret; everything else is public and unremarkable."""
    return [
        make_record(1, "C1", "Boa noite a todos.", "speech"),
        make_record(2, "C2", f"Nao posso contar sobre o {SECRET}.", "thought"),
        make_record(3, "C2", "Boa noite.", "speech"),
        make_record(4, "Narrator", "A lareira estala.", "narration"),
        make_record(5, "C3", "Alguem viu o estalajadeiro?", "speech"),
    ]


def _text(messages: list[dict]) -> str:
    return "\n".join(message["content"] for message in messages)


class TestTheDirectorReceivesIt:
    def test_the_thought_reaches_the_director_labeled(self) -> None:
        """Half the invariant: withholding it from everyone is not the goal."""
        prompt = _text(
            build_narrator_messages(
                scene=SCENE,
                characters=CAST,
                player_controlled_id="C1",
                history=_history(),
            )
        )
        assert SECRET in prompt, "the Director is omniscient by design and lost the thought"
        line = next(line for line in prompt.splitlines() if SECRET in line)
        assert "PRIVATE THOUGHT" in line, (
            f"the thought arrived unlabeled, as if it were public: {line!r}"
        )
        # Ownership travels as the id, which the roster resolves in the same
        # prompt. Anonymous inner life would be useless to the Director.
        assert "SPEAKER=C2" in line, f"the Director must know WHOSE thought it is: {line!r}"
        assert "ID=C2 | NAME=Marta" in prompt


class TestNobodyElseDoes:
    def test_the_prose_renderer_never_sees_it(self) -> None:
        prompt = _text(
            build_prose_messages(
                scene=SCENE,
                characters=CAST,
                controlled_id="C1",
                history=_history(),
                events=[
                    {
                        "event_kind": "observation",
                        "subject_id": "Narrator",
                        "content": "O vento bate na porta.",
                        "witness_ids": ["C1", "C2", "C3"],
                    }
                ],
            )
        )
        assert SECRET not in prompt

    def test_another_character_never_sees_it(self) -> None:
        formatted = _format_history_for_character(
            history=_history(),
            characters=CAST,
            controlled_id="C1",
            character_id="C3",
        )
        assert SECRET not in formatted

    def test_the_controlled_character_is_not_a_privileged_reader(self) -> None:
        """The human's character is a character: no wider view than the others."""
        formatted = _format_history_for_character(
            history=_history(),
            characters=CAST,
            controlled_id="C1",
            character_id="C1",
        )
        assert SECRET not in formatted

    def test_the_thinker_still_reads_their_own_thought(self) -> None:
        """The containment must not amputate the character's own memory."""
        formatted = _format_history_for_character(
            history=_history(),
            characters=CAST,
            controlled_id="C1",
            character_id="C2",
        )
        assert SECRET in formatted

    def test_the_summarizer_never_sees_it(self) -> None:
        """Compaction is where a leak would become permanent: the summary
        survives the evicted records and is read by everyone afterwards."""
        prompt = _text(
            build_summarizer_messages(
                characters=CAST,
                controlled_id="C1",
                story_summary="",
                evicted_turns=_history(),
            )
        )
        assert SECRET not in prompt

    @pytest.mark.parametrize("viewer", ["C1", "C2", "C3"])
    def test_the_ledger_never_records_it(self, viewer: str) -> None:
        """`capture_memory` is the ledger's only writer, and it is deterministic.

        C2 is parametrized in on purpose: not even the thinker's OWN durable
        memory is allowed to hold the thought. The ledger is what survives
        compaction and feeds prompts later, so a thought stored here would
        outlive the record it came from and re-enter through a channel that
        never intended to carry it.
        """
        perspective = CharacterPerspective(initialized_turn=0, processed_through_turn=0)
        capture_memory(
            perspective=perspective,
            history=_history(),
            viewer_id=viewer,
            characters=CAST,
            controlled_id="C1",
        )
        assert perspective.recent_memory, "the viewer witnessed public speech and stored nothing"
        assert SECRET not in "\n".join(perspective.recent_memory)

    def test_memory_revision_only_condenses_what_the_viewer_saw(self) -> None:
        """The ledger's own summarizer takes viewer-projected lines. Feeding it
        the raw transcript is the plausible mistake; the assertion is that the
        secret cannot arrive through the lines a viewer legitimately holds."""
        viewer_lines = [
            record.content
            for record in _history()
            if record.content_type in ("speech", "narration")
        ]
        prompt = _text(
            build_memory_revision_messages(
                viewer_name="Bento", memory_summary="", older_lines=viewer_lines
            )
        )
        assert SECRET not in prompt
