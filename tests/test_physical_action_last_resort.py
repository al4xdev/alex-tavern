"""A stylistic slip must not cost the turn (found by a real playtest run).

`character.act()` has three guards that all follow the same shape: retry once
with a correction, then fix the output deterministically. Two of them said so in
their own docstrings — the whisper guard redacts, the repetition guard drops a
field, both "never a failed turn".

The physical-action guard was the odd one out: it raised. A run of the task 38
measurement died on exactly that:

    ValueError: Invalid Character response after correction: Character response
    places physical action in speech/thought; it belongs in action_intent

One session lost, five turns of real provider calls discarded, because a
character wrote body movement in the wrong field twice.
"""

from __future__ import annotations

from src.agents.character import _normalize_output, _promote_physical_sentences


class TestPromotion:
    def test_movement_moves_and_dialogue_stays(self) -> None:
        fixed = _promote_physical_sentences(
            {
                "speech": "Inclino a cabeca. O que voce quer dizer com isso?",
                "thought": None,
                "action_intent": None,
            }
        )
        assert fixed["speech"] == "O que voce quer dizer com isso?"
        assert fixed["action_intent"] == "Inclino a cabeca."

    def test_a_field_that_is_only_movement_is_emptied(self) -> None:
        fixed = _promote_physical_sentences(
            {"speech": None, "thought": "Arrumo o cabelo.", "action_intent": None}
        )
        assert fixed["thought"] is None
        assert fixed["action_intent"] == "Arrumo o cabelo."

    def test_an_existing_intent_is_kept_and_extended(self) -> None:
        fixed = _promote_physical_sentences(
            {
                "speech": "Seguro a porta. Entre.",
                "thought": None,
                "action_intent": "Fico de pe.",
            }
        )
        assert fixed["speech"] == "Entre."
        assert fixed["action_intent"] == "Fico de pe. Seguro a porta."

    def test_both_fields_contribute_in_order(self) -> None:
        fixed = _promote_physical_sentences(
            {
                "speech": "Levanto a mao. Calma.",
                "thought": "Olho para a porta. Ele nao deveria estar aqui.",
                "action_intent": None,
            }
        )
        assert fixed["speech"] == "Calma."
        assert fixed["thought"] == "Ele nao deveria estar aqui."
        assert fixed["action_intent"] == "Levanto a mao. Olho para a porta."

    def test_clean_output_is_returned_untouched(self) -> None:
        clean = {"speech": "Boa noite.", "thought": "Ele mente.", "action_intent": None}
        assert _promote_physical_sentences(clean) == clean

    def test_english_movement_is_caught_too(self) -> None:
        fixed = _promote_physical_sentences(
            {"speech": "I tilt my head. What did you say?", "thought": None, "action_intent": None}
        )
        assert fixed["speech"] == "What did you say?"
        assert fixed["action_intent"] == "I tilt my head."

    def test_a_verb_the_detector_does_not_know_passes_through(self) -> None:
        """Documents a real asymmetry rather than pretending it is not there.

        The Portuguese list has `inclino`; the English list has no `lean`. This
        promotion can only move what the existing detector recognises, so the
        gap belongs to the detector, not here. Widening it changes how often the
        guard fires at all, which is a measured decision, not a tidy-up.
        """
        untouched = {
            "speech": "I lean closer. What did you say?",
            "thought": None,
            "action_intent": None,
        }
        assert _promote_physical_sentences(untouched) == untouched


class TestTheResultIsValid:
    def test_the_promoted_output_passes_the_guard_that_rejected_it(self) -> None:
        """The whole point: what raised before now normalizes cleanly."""
        offending = {
            "speech": "Inclino a cabeca. O que voce quer dizer?",
            "thought": None,
            "action_intent": None,
        }
        try:
            _normalize_output(offending)
        except ValueError as exc:
            assert "physical action" in str(exc)
        else:
            raise AssertionError("the fixture no longer trips the guard")

        output = _normalize_output(_promote_physical_sentences(offending))
        assert output["speech"] == "O que voce quer dizer?"
        assert output["action_intent"] == "Inclino a cabeca."

    def test_a_response_that_was_only_movement_still_says_something(self) -> None:
        """Emptying every field would trip the other guard; the intent survives."""
        output = _normalize_output(
            _promote_physical_sentences(
                {"speech": None, "thought": "Arrumo o cabelo.", "action_intent": None}
            )
        )
        assert output["speech"] is None
        assert output["thought"] is None
        assert output["action_intent"] == "Arrumo o cabelo."
