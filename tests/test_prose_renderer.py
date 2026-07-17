"""Blind prose renderer hardening: spoken words never reach the prose prompt.

The renderer measurably re-voiced dialogue in narration despite an explicit
instruction not to. The fix is structural (selection of inputs): speech record
content and ``audible_speech`` event content are replaced by content-free
markers/staging lines before the prompt is built, so re-voicing is impossible
by construction. These tests pin that boundary at the unit level (no network).
"""

from __future__ import annotations

from typing import Any

import src.agents.prose as prose
from src.agents.prose import (
    PROSE_SYSTEM,
    REPETITION_CORRECTION,
    _repeats_prior_narration,
    build_prose_messages,
    render_narration,
)
from src.models import Character, CharacterBody, CharacterMind, Scene, TurnRecord


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Alice"), "C2": _char("Bruno"), "C3": _char("Vitor")}
CONTROLLED_ID = "C1"

SCENE = Scene(
    location="Embaixada",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _record(
    speaker: str,
    content: str,
    content_type: str,
    audience: list[str] | None = None,
    turn_number: int = 1,
) -> TurnRecord:
    return TurnRecord(
        turn_number=turn_number,
        speaker=speaker,
        content=content,
        content_type=content_type,
        scene_snapshot=SCENE,
        audience=audience,
    )


def _prompt(history: list[TurnRecord], events: list[dict[str, Any]]) -> str:
    messages = build_prose_messages(SCENE, CHARACTERS, CONTROLLED_ID, history, events)
    return "\n".join(message["content"] for message in messages)


class TestSpeechContentNeverReachesProse:
    def test_public_speech_content_replaced_by_marker(self) -> None:
        history = [_record("C2", "O código do cofre é 7-4-1-9.", "speech")]
        prompt = _prompt(history, [])
        assert "7-4-1-9" not in prompt
        assert "código do cofre" not in prompt
        assert "Bruno fala" in prompt

    def test_whispered_speech_content_replaced_by_scoped_marker(self) -> None:
        history = [_record("C2", "A senha secreta é rosa-espelho.", "speech", audience=["C3"])]
        prompt = _prompt(history, [])
        assert "rosa-espelho" not in prompt
        assert "senha secreta" not in prompt
        assert "Bruno fala baixo (só Vitor percebem)" in prompt

    def test_player_speech_marker_uses_controlled_character_name(self) -> None:
        history = [_record("Player", "Eu confesso tudo agora.", "speech")]
        prompt = _prompt(history, [])
        assert "confesso" not in prompt
        assert "Alice fala" in prompt

    def test_previous_turn_speech_also_withheld(self) -> None:
        history = [
            _record("C2", "Frase antiga que não pode reaparecer.", "speech", turn_number=1),
            _record("Narrator", "A sala esfria.", "narration", turn_number=2),
        ]
        prompt = _prompt(history, [])
        assert "Frase antiga" not in prompt


class TestAudibleSpeechEventsAreOmitted:
    """Dialogue renders itself as dialogue lines; the renderer narrates only
    NON-SPEECH events. Staging "someone says something" produced phantom
    unspecified speech and narrated the protagonist's silence."""

    def _prompt(self, events):  # noqa: ANN001, ANN202
        messages = build_prose_messages(SCENE, CHARACTERS, "C1", [], events)
        return "\n".join(m["content"] for m in messages)

    def test_audible_speech_events_never_reach_the_prompt(self) -> None:
        prompt = self._prompt(
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C1",
                    "content": "Alice pergunta sobre o cofre.",
                    "witness_ids": ["C2", "C3"],
                }
            ]
        )
        assert "cofre" not in prompt
        assert "diz algo" not in prompt
        # With only speech events, the renderer gets the atmospheric fallback.
        assert "Nothing new happens" in prompt

    def test_non_speech_events_still_render_alongside_omitted_speech(self) -> None:
        prompt = self._prompt(
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C1",
                    "content": "Alice pergunta.",
                    "witness_ids": ["C2"],
                },
                {
                    "event_kind": "physical_outcome",
                    "subject_id": "C2",
                    "content": "Bruno derruba a cadeira.",
                    "witness_ids": ["C1"],
                },
            ]
        )
        assert "derruba a cadeira" in prompt
        assert "Alice pergunta" not in prompt

    def test_system_prompt_forbids_unspecified_speech_and_silence(self) -> None:
        assert "unspecified speech" in PROSE_SYSTEM
        assert "silence" in PROSE_SYSTEM



class TestNonSpeechRecordsKeepContent:
    def test_narration_records_keep_full_content(self) -> None:
        history = [_record("Narrator", "A chuva bate nas janelas do salão.", "narration")]
        prompt = _prompt(history, [])
        assert "A chuva bate nas janelas do salão." in prompt

    def test_public_action_records_keep_full_content(self) -> None:
        history = [_record("C3", "Vitor guarda o envelope no bolso interno.", "action")]
        prompt = _prompt(history, [])
        assert "Vitor guarda o envelope no bolso interno." in prompt

    def test_thoughts_never_enter_the_reader_transcript(self) -> None:
        history = [_record("C2", "Preciso esconder o mapa.", "thought")]
        prompt = _prompt(history, [])
        assert "esconder o mapa" not in prompt


REPEATED_PARAGRAPH = (
    "Rafa entra na sala com passos hesitantes, os olhos varrendo os rostos "
    "desconhecidos. A música pulsa nas paredes enquanto ele procura um canto "
    "menos iluminado. Ninguém parece notar a sua chegada silenciosa."
)

NEAR_IDENTICAL_PARAGRAPH = (
    "Rafa entra na sala com passos hesitantes, os olhos varrendo os rostos "
    "desconhecidos. A música pulsa nas paredes enquanto ele busca um canto "
    "menos iluminado. Ninguém parece notar a sua chegada silenciosa."
)

FRESH_PARAGRAPH = (
    "Do outro lado do salão, Bruno equilibra dois copos e abre caminho entre "
    "os convidados. Uma rajada de vento derruba um guardanapo da mesa. O riso "
    "de Alice corta o burburinho por um instante breve."
)


class TestRepeatsPriorNarration:
    def test_near_identical_paragraph_detected(self) -> None:
        history = [_record("Narrator", REPEATED_PARAGRAPH, "narration")]
        assert _repeats_prior_narration(NEAR_IDENTICAL_PARAGRAPH, history) is True

    def test_identical_paragraph_detected(self) -> None:
        history = [_record("Narrator", REPEATED_PARAGRAPH, "narration")]
        assert _repeats_prior_narration(REPEATED_PARAGRAPH, history) is True

    def test_fresh_prose_passes(self) -> None:
        history = [_record("Narrator", REPEATED_PARAGRAPH, "narration")]
        assert _repeats_prior_narration(FRESH_PARAGRAPH, history) is False

    def test_single_near_verbatim_sentence_echo_detected(self) -> None:
        # Mostly-fresh beat that reuses ONE distinctive prior sentence verbatim
        # (the "a lareira apaga de repente" ×2 failure): the old >half rule let
        # this through; lexical variation now flags it.
        prior = (
            "A lareira apaga de repente, mergulhando o salão na escuridão. "
            "Marta recua um passo, a respiração presa na garganta."
        )
        new = (
            "Bento avança em direção à porta com o facão erguido. "
            "A lareira apaga de repente, mergulhando o salão na escuridão."
        )
        history = [_record("Narrator", prior, "narration")]
        assert _repeats_prior_narration(new, history) is True

    def test_no_narration_in_history_passes(self) -> None:
        history = [
            _record("C2", "Bruno fala alguma coisa longa e detalhada aqui.", "speech"),
            _record("C3", "Vitor guarda o envelope no bolso interno do paletó.", "action"),
        ]
        assert _repeats_prior_narration(REPEATED_PARAGRAPH, history) is False

    def test_empty_history_passes(self) -> None:
        assert _repeats_prior_narration(REPEATED_PARAGRAPH, []) is False


class _FakeCompletion:
    """Fake for chat_completion_json returning queued narrations in order."""

    def __init__(self, narrations: list[str]) -> None:
        self.narrations = list(narrations)
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, client: Any, messages: list[dict], **kwargs: Any) -> dict:
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return {"narration": self.narrations[len(self.calls) - 1]}


class TestRepetitionRetry:
    HISTORY = [_record("Narrator", REPEATED_PARAGRAPH, "narration")]

    async def _render(self, fake: _FakeCompletion, monkeypatch: Any) -> str:
        monkeypatch.setattr(prose, "chat_completion_json", fake)
        return await render_narration(
            None, SCENE, CHARACTERS, CONTROLLED_ID, self.HISTORY, [], {}
        )

    async def test_repeated_then_fresh_retries_once_and_returns_second(
        self, monkeypatch: Any
    ) -> None:
        fake = _FakeCompletion([NEAR_IDENTICAL_PARAGRAPH, FRESH_PARAGRAPH])
        result = await self._render(fake, monkeypatch)
        assert len(fake.calls) == 2
        assert result == FRESH_PARAGRAPH
        assert fake.calls[1]["messages"][-1] == {
            "role": "user",
            "content": REPETITION_CORRECTION,
        }

    async def test_repeated_twice_still_two_calls_and_second_accepted(
        self, monkeypatch: Any
    ) -> None:
        fake = _FakeCompletion([NEAR_IDENTICAL_PARAGRAPH, NEAR_IDENTICAL_PARAGRAPH])
        result = await self._render(fake, monkeypatch)
        assert len(fake.calls) == 2
        assert result == NEAR_IDENTICAL_PARAGRAPH

    async def test_fresh_first_draft_makes_single_call(self, monkeypatch: Any) -> None:
        fake = _FakeCompletion([FRESH_PARAGRAPH])
        result = await self._render(fake, monkeypatch)
        assert len(fake.calls) == 1
        assert result == FRESH_PARAGRAPH


ZONED_SCENE = Scene(
    location="Mansão",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3"],
    physical_facts={},
    zones={"salao": [], "biblioteca": []},
    positions={"C1": "salao", "C2": "salao", "C3": "biblioteca"},
)


class TestZoneStagingBlock:
    def test_zoned_scene_adds_staging_block(self) -> None:
        messages = build_prose_messages(ZONED_SCENE, CHARACTERS, CONTROLLED_ID, [], [])
        user = messages[1]["content"]
        assert "STAGING" in user
        assert (
            "salao: hears nothing outside itself (acoustically isolated) | "
            "isolated from: biblioteca | inside: Alice, Bruno" in user
        )
        assert (
            "biblioteca: hears nothing outside itself (acoustically isolated) | "
            "isolated from: salao | inside: Vitor" in user
        )

    def test_audible_zone_listed_as_heard(self) -> None:
        scene = Scene(
            location="Mansão",
            time_of_day="Noite",
            present_characters=["C1", "C3"],
            physical_facts={},
            zones={"salao": ["varanda"], "varanda": ["salao"]},
            positions={"C1": "salao", "C3": "varanda"},
        )
        messages = build_prose_messages(scene, CHARACTERS, CONTROLLED_ID, [], [])
        user = messages[1]["content"]
        assert "salao: hears varanda | isolated from: none | inside: Alice" in user
        assert "varanda: hears salao | isolated from: none | inside: Vitor" in user

    def test_separation_rule_reaches_system_prompt(self) -> None:
        messages = build_prose_messages(ZONED_SCENE, CHARACTERS, CONTROLLED_ID, [], [])
        system = messages[0]["content"]
        assert "zones that cannot perceive each other" in system
        assert "cut between separated spaces explicitly" in system

    def test_flat_scene_has_no_staging_block(self) -> None:
        messages = build_prose_messages(SCENE, CHARACTERS, CONTROLLED_ID, [], [])
        assert "STAGING" not in messages[1]["content"]
