"""Task 54, finding 2: the Director re-voicing history must not persist it again.

`audible_speech` exists so a fact spoken to the room survives for witnesses who
did not reply that turn. In the live session `1cad8c55` the Director also used
it to restate lines already in history — including reformulations of the human's
own input as `Link diz: ...` — and `_persist_audible_speech` wrote every one of
them. The history grew with duplicates, and the duplicates came back as context
telling the model that restating counts as progress.
"""

from __future__ import annotations

from src.runner import _echoes_recent_speech
from tests.factories import make_cast, make_game, make_record


def _game_with(*records):
    cast = make_cast("Link", "Maelis")
    game = make_game(characters=cast, controlled="C1")
    game.history = list(records)
    return game


def test_verbatim_repeat_of_the_same_speaker_is_an_echo() -> None:
    line = "A nevoa esta saindo do arco leste e ninguem deveria chegar perto."
    game = _game_with(make_record(1, "C2", line))
    assert _echoes_recent_speech(game, "C2", line)


def test_the_directors_reformulation_of_the_player_input_is_an_echo() -> None:
    """The sentinel and the controlled character are the same voice."""
    game = _game_with(
        make_record(1, "Player", "Instrutor Garran, cuidado com a nevoa perto do arco!")
    )
    assert _echoes_recent_speech(
        game, "C1", "Instrutor Garran, cuidado com a nevoa perto do arco!"
    )


def test_a_reformulation_with_an_attribution_prefix_is_still_an_echo() -> None:
    game = _game_with(
        make_record(1, "Player", "A placa caiu antes do portal abrir, isso e um sinal claro.")
    )
    assert _echoes_recent_speech(
        game, "C1", "A placa caiu antes do portal abrir, isso e um sinal claro"
    )


def test_a_genuinely_new_line_is_not_an_echo() -> None:
    game = _game_with(make_record(1, "C2", "A nevoa esta saindo do arco leste, fiquem parados."))
    assert not _echoes_recent_speech(game, "C2", "Eu vou fechar o portal agora mesmo, afastem-se.")


def test_another_speaker_saying_the_same_thing_is_not_an_echo() -> None:
    """Two people can legitimately voice the same fact; only self-repeat is noise."""
    line = "A nevoa esta saindo do arco leste e ninguem deveria chegar perto."
    game = _game_with(make_record(1, "C2", line))
    assert not _echoes_recent_speech(game, "C1", line)


def test_short_lines_are_exempt() -> None:
    """"Sim." twice in a scene is dialogue, not duplication."""
    game = _game_with(make_record(1, "C2", "Sim."))
    assert not _echoes_recent_speech(game, "C2", "Sim.")


def test_only_recent_history_counts() -> None:
    """A callback to something said long ago is craft, not a doubled record."""
    line = "A nevoa esta saindo do arco leste e ninguem deveria chegar perto."
    old = make_record(1, "C2", line)
    filler = [make_record(turn, "C1", f"Falo alguma coisa diferente numero {turn}.")
              for turn in range(2, 12)]
    game = _game_with(old, *filler)
    assert not _echoes_recent_speech(game, "C2", line)
