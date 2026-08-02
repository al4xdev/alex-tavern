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


# ---------------------------------------------------------------------------
# Regression: the two ways the guard was defeated in live sessions.
# Every string below is verbatim from .data/sessions/{15d40dfa,20d4cdb3} and
# every pair scored 1.0000 on the payload alone. See
# docs/cases/20-repetition-baseline-2026-08-01.md for the per-pair mechanism.
# ---------------------------------------------------------------------------

MAELIS_LINE = (
    "A seleção começa. As equipes serão formadas por escolha mútua e não por "
    "imposição. Quando seus nomes forem chamados, dirijam-se à mesa."
)
CASSIAN_LINE = (
    "Pois então, que comecemos. Tenho interesse em ver como os jovens se "
    "organizam sem uma mão firme guiando-os."
)


def test_attribution_frame_does_not_hide_a_verbatim_repeat() -> None:
    """15d40dfa T1: raw similarity 0.8207, under the 0.88 threshold, persisted.

    The frame is the whole difference — the payload is character-for-character
    the line C17 had just spoken.
    """
    game = _game_with(make_record(1, "C17", MAELIS_LINE))
    revoiced = f"A Diretora Maelis Ordan, do pódio, anuncia em voz clara: '{MAELIS_LINE}'"
    assert _echoes_recent_speech(game, "C17", revoiced)


def test_attribution_frame_across_a_turn_boundary_is_still_an_echo() -> None:
    """15d40dfa T3 -> T4: raw 0.8327, persisted as a second C19 speech record."""
    game = _game_with(
        make_record(3, "C19", CASSIAN_LINE),
        make_record(3, "C17", "Chamem os primeiros nomes."),
    )
    revoiced = f"Lorde Cassian Aurel comenta em voz alta: '{CASSIAN_LINE}'"
    assert _echoes_recent_speech(game, "C19", revoiced)


def test_a_large_cast_does_not_push_last_turn_out_of_the_window() -> None:
    """20d4cdb3: every duplicate sat 10-19 records back, three of them above 0.88.

    The old window was eight RECORDS, which at a 21-character cast is about one
    turn. Counting turns is what makes the guard independent of cast size.
    """
    line = "O tempo está se esgotando. Quem não se agrupar em meio minuto será realocado."
    chatter = [
        make_record(2, f"C{index}", f"Comento uma coisa completamente diferente, numero {index}.")
        for index in range(1, 16)
    ]
    game = _game_with(make_record(1, "C17", line), *chatter)
    assert _echoes_recent_speech(game, "C17", f"Diretora Maelis diz: '{line}'")


def test_unframing_does_not_swallow_a_genuinely_new_quoted_line() -> None:
    """The frame is stripped from BOTH sides; it must not collapse distinct lines."""
    prior = "Selos reais e discursos sempre tentam adornar o que é apenas um teste cruel."
    game = _game_with(make_record(1, "C13", f"Riven diz, desafiador: '{prior}'"))
    assert not _echoes_recent_speech(
        game, "C13", "Riven aponta para a porta e diz: 'Vou entrar na masmorra sozinho, agora.'"
    )
