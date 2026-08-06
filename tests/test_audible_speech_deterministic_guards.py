"""Task 65, item 4: two guards on what the audible_speech channel may persist.

Both are deterministic, both are independent of who authors the text, and both
were sized against the archive rather than guessed:

- an internal character id must never reach a record the player can read.
  `oldcode-P1-r1` T39 persisted "C17 ordena que C20 permaneça com os estilhaços e
  que C18 a acompanhe" — n=1 in the corpus, and this channel is the only path
  left after task 36 stripped ids from the prose and summarizer prompts.
- a line in the wrong language must not persist. `null-P1-r2` T2 emitted four
  English `audible_speech` events under a Brazilian-Portuguese session and every
  one of them became a record. Scored over all 3,936 speech/narration/action
  records in the 16 archived sessions, the two populations do not touch: the most
  English-looking Portuguese record scores 0.012, the nine English ones score
  1.000, and all nine arrived through this channel.
"""

from __future__ import annotations

import pytest

from src.runner import _foreign_language, _leaks_internal_id
from tests.factories import make_cast, make_game

PT = "Portuguese"


def _game():
    return make_game(characters=make_cast("Link", "Maelis", "Garran"), controlled="C1")


# ── the internal-id guard ─────────────────────────────────────────────────


def test_the_archived_id_leak_is_refused() -> None:
    leak = "C17 ordena que C20 permaneça com os estilhaços e que C18 a acompanhe"
    game = make_game(characters=make_cast(*[f"N{i}" for i in range(1, 21)]), controlled="C1")
    assert _leaks_internal_id(game, leak)


def test_a_single_id_is_enough() -> None:
    assert _leaks_internal_id(_game(), "Maelis manda C2 fechar a porta.")


def test_two_digit_ids_are_caught() -> None:
    """The pre-existing `\\bC\\d\\b` in tests/tools stops at C9 by construction."""
    game = make_game(characters=make_cast(*[f"N{i}" for i in range(1, 21)]), controlled="C1")
    assert _leaks_internal_id(game, "C17 avança.")


def test_ordinary_dialogue_passes() -> None:
    assert not _leaks_internal_id(_game(), "Garran fecha a entrada e chama Maelis.")


def test_an_id_shaped_token_outside_this_cast_is_not_a_leak() -> None:
    """The guard confirms candidates against the session's own characters, so a
    scenario where C4 is an explosive does not lose the line."""
    game = _game()  # C1..C3 only
    assert not _leaks_internal_id(game, "Ele prende a carga de C4 na viga.")
    assert _leaks_internal_id(game, "Ele chama C3 para a viga.")


# ── the language guard ────────────────────────────────────────────────────


def test_the_four_archived_english_events_are_refused() -> None:
    """Verbatim from `null-P1-r2` T2 — all four persisted before this guard."""
    for line in (
        "Asword said that Link's portal showed precise control, more than many "
        "who brag about brute strength.",
        "Liora cut in with a cold remark, saying control means little when the "
        "power behind it is almost nothing.",
        "Bruna answered in a low voice, saying that in a dungeon a well-placed "
        "tool can matter more than a flashy spell.",
        "Director Maelis struck her bengala on the stone floor and ordered "
        "silence, reminding everyone that the selection had begun.",
    ):
        assert _foreign_language(line, PT), line


def test_the_shortest_archived_english_record_is_refused() -> None:
    """`drive-P1-r1` T10, two markers — the reason the floor is 2 and not 3."""
    assert _foreign_language("Guard, report! What breached the wall?", PT)


@pytest.mark.parametrize(
    "line",
    [
        "Diretora Maelis, antes de começarmos, gostaria de lembrar a todos que "
        "esta seleção testará não apenas o poder.",
        "Meu lugar é à frente, como a Diretora ordenou. Link, fique perto de mim.",
        "Liora, se essa descarga for sua, faça logo ou vamos ficar presos neste lado!",
        "Nix, se a fenda for selada, a prova some. Deixa eu olhar com você.",
    ],
)
def test_portuguese_dialogue_passes(line: str) -> None:
    """The last two carry `for`, the Portuguese subjunctive that also spells an
    English preposition — the collision that produced the only overlap between
    the populations until it was excluded from both marker lists."""
    assert not _foreign_language(line, PT)


def test_a_short_line_with_too_little_evidence_is_left_alone() -> None:
    assert not _foreign_language("Silêncio!", PT)
    assert not _foreign_language("Agora, Link.", PT)


def test_an_english_session_is_not_guarded() -> None:
    """Pinned to English, English is not a flip."""
    assert not _foreign_language("Guard, report! What breached the wall?", "English")


def test_an_unmeasured_language_returns_false_rather_than_guessing() -> None:
    """The marker lists separate one pair. Anything else is out of scope, and
    saying so is cheaper than a false positive that deletes a real line."""
    assert not _foreign_language("Guard, report! What breached the wall?", "French")
