"""Retenção de memória multi-personagem com foco narrativo alternado (X/Y/Z).

Cenário espelhado do playtest ``tools/playtests/memory_focus_xyz.json``: X (jogador)
confia um fato exclusivo a Y como speech, o foco desvia para X+Z com ruído longo e
volta a X+Y para verificar o recall. Estes testes pinam cada camada determinística
do caminho (gravação → seleção → prompt); a camada do provider só é observável no
playtest com LLM real.

A classe ``TestTrimCompactionGapFinding`` documenta um achado independente (trim
silencioso sem compactação) com ``xfail(strict=True)`` — a correção pertence a um
passe separado.
"""

from __future__ import annotations

import copy
import shutil

import httpx
import pytest

import src.agents.character as character_mod
from src import runner as runner_mod
from src.agents.character import _format_history_for_character
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    deepcopy_scene,
    speaker_label,
)
from src.runner import Runner
from src.store.sessions import generate_session_id, save_game, session_dir

MARKER = "ORQUÍDEA-741"
PASSWORD_FACT = f"Guarda isto com a vida: a senha do meu cofre é {MARKER}."
NOISE_FILLER = "Carga na segunda lua, pedágio no posto velho, prata miúda no cambista. " * 5


def _character(name: str, personality: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality=personality, knowledge=[], current_mood="calmo"),
        body=CharacterBody(name=name, physical_description="—", outfit="—"),
    )


THREE_CHARACTERS: dict[str, Character] = {
    "C1": _character("Dario", "Mercador metódico que testa a memória dos parceiros."),
    "C2": _character("Vela", "Escriba de memória afiada; responde com exatidão."),
    "C3": _character("Rook", "Contrabandista falante, mistura números e rotas."),
}

SCENE = Scene(
    location="Taverna do Velho Mork",
    time_of_day="noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)


def _record(
    turn_number: int, speaker: str, content: str, content_type: str = "speech"
) -> TurnRecord:
    return TurnRecord(turn_number, speaker, content, content_type, deepcopy_scene(SCENE))


def _seed_focus_history(noise_pairs: int = 30) -> list[TurnRecord]:
    """Fase A (X confia o fato a Y) seguida de um desvio longo de foco X+Z."""
    history = [
        _record(1, "Player", PASSWORD_FACT),
        _record(2, "C2", "Prometo guardar essa senha com a vida, Dario."),
    ]
    turn = 3
    for index in range(noise_pairs):
        history.append(_record(turn, "Player", f"Rook, rota {index} desta estação: {NOISE_FILLER}"))
        turn += 1
        history.append(_record(turn, "C3", f"Anotado, Dario. Rota {index} confirmada."))
        turn += 1
    return history


def _make_game(session_id: str, history: list[TurnRecord]) -> GameState:
    return GameState(
        session_id=session_id,
        characters=copy.deepcopy(THREE_CHARACTERS),
        player=Player(controlled_character_id="C1"),
        scene=deepcopy_scene(SCENE),
        history=history,
    )


# Espelha o provider deepseek (context_max enorme): o trim nunca dispara aqui,
# isolando o comportamento de alternância de foco de qualquer pressão de contexto.
NO_TRIM_CONFIG = {"context_max": 524288, "max_tokens_character": 2048}


class TestFocusSwitchWithoutTrim:
    """Alternância de foco sem compactação e sem trim: nada pode sumir do prompt."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, dict(NO_TRIM_CONFIG))
        save_game(_make_game(self.sid, _seed_focus_history()))

    def teardown_method(self) -> None:
        directory = session_dir(self.sid)
        if directory.exists():
            shutil.rmtree(directory)

    @pytest.mark.asyncio
    async def test_focus_switch_keeps_speech_in_character_prompt(self, monkeypatch) -> None:  # noqa: ANN001
        """O fato da Fase A chega intacto ao prompt real de Y na volta do foco."""
        captured: list[list[dict]] = []

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {
                "narration": "A taverna murmura ao redor da mesa.",
                "next_speaker": "C2",
                "context_for_character": "Dario aguarda a resposta de Vela.",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_chat_completion_json(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured.append(messages)
            return {"speech": "Era a senha que me confiaste no início.", "thought": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(character_mod, "chat_completion_json", fake_chat_completion_json)

        result = await self.runner.player_turn(
            self.sid,
            speech="Vela, qual era exatamente a senha que te contei no início?",
            force_speaker="C2",
        )

        assert result["character_response"]["speech"] == "Era a senha que me confiaste no início."
        assert len(captured) == 1
        user_prompt = captured[0][-1]["content"]
        assert MARKER in user_prompt, "o fato da Fase A sumiu do prompt do personagem"
        marker_lines = [line for line in user_prompt.splitlines() if MARKER in line]
        assert any("SPEAKER=Dario" in line for line in marker_lines), (
            "o fato perdeu a atribuição ao personagem controlado"
        )

    def test_public_speech_remains_visible_to_all_characters(self) -> None:
        """Speech sem audiência (público) continua visível a todos os presentes."""
        history = _seed_focus_history()
        for character_id in ("C2", "C3"):
            formatted = _format_history_for_character(
                history,
                THREE_CHARACTERS,
                "C1",
                character_id,
                context_max=NO_TRIM_CONFIG["context_max"],
                max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
            )
            assert MARKER in formatted

    def test_whispered_speech_visible_only_to_its_audience(self) -> None:
        """Task 22: registro com audiência é sussurro — só a audiência (e o autor) veem."""
        whispered = _record(1, "Player", PASSWORD_FACT)
        whispered.audience = ["C1", "C2"]
        history = [
            whispered,
            _record(2, "C2", "Guardado, Dario."),
        ]
        seen_by_vela = _format_history_for_character(
            history, THREE_CHARACTERS, "C1", "C2",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        seen_by_rook = _format_history_for_character(
            history, THREE_CHARACTERS, "C1", "C3",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        assert MARKER in seen_by_vela
        assert "WHISPERED" in seen_by_vela
        assert MARKER not in seen_by_rook

    def test_whispered_action_visible_only_to_its_audience(self) -> None:
        whispered = _record(1, "Player", f"Dario mostra a Vela um papel: {MARKER}.", "action")
        whispered.audience = ["C1", "C2"]
        history = [whispered, _record(2, "C2", "Entendido.")]
        assert MARKER in _format_history_for_character(
            history, THREE_CHARACTERS, "C1", "C2",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        assert MARKER not in _format_history_for_character(
            history, THREE_CHARACTERS, "C1", "C3",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )

    def test_whisper_speaker_always_sees_its_own_record(self) -> None:
        whispered = _record(1, "C2", "Segredo que eu mesma disse.")
        whispered.audience = ["C1"]
        formatted = _format_history_for_character(
            [whispered], THREE_CHARACTERS, "C1", "C2",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        assert "Segredo que eu mesma disse." in formatted

    @pytest.mark.asyncio
    async def test_whispered_turn_reply_inherits_audience(self, monkeypatch) -> None:  # noqa: ANN001
        """Task 22 ponta a ponta: sussurro do jogador + resposta do personagem ficam
        invisíveis para quem está fora da audiência, e o narrador vê o marcador."""
        narrator_prompts: list[str] = []

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            from src.agents.narrator import _build_user_prompt

            narrator_prompts.append(
                _build_user_prompt(
                    scene=game.scene,
                    characters=game.characters,
                    player_controlled_id=game.player.controlled_character_id,
                    history=game.history,
                )
            )
            return {
                "narration": "Dario se inclina e sussurra algo a Vela.",
                "next_speaker": "C2",
                "context_for_character": "Dario sussurra para você.",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_chat_completion_json(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {"speech": f"Confirmo baixinho: {MARKER}.", "thought": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(character_mod, "chat_completion_json", fake_chat_completion_json)

        await self.runner.player_turn(
            self.sid,
            speech=f"Vela, só entre nós: a senha nova é {MARKER}-B.",
            force_speaker="C2",
            audience=["C1", "C2"],
        )

        from src.store.sessions import load_game

        game = load_game(self.sid)
        assert game is not None
        whispered_records = [rec for rec in game.history if rec.audience == ["C1", "C2"]]
        speakers = {rec.speaker for rec in whispered_records}
        assert "Player" in speakers, "a fala sussurrada do jogador não guardou a audiência"
        assert "C2" in speakers, "a resposta do personagem não herdou a audiência do sussurro"
        rook_view = _format_history_for_character(
            game.history, game.characters, "C1", "C3",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        assert f"{MARKER}-B" not in rook_view
        assert f"Confirmo baixinho: {MARKER}." not in rook_view
        assert narrator_prompts, "o narrador não foi chamado"
        assert "[WHISPERED, perceived only by: Dario, Vela]" in narrator_prompts[-1]

    @pytest.mark.asyncio
    async def test_whisper_audience_validation(self) -> None:
        with pytest.raises(ValueError, match="unknown character"):
            await self.runner.player_turn(
                self.sid, speech="oi", force_speaker="C2", audience=["C9"]
            )
        with pytest.raises(ValueError, match="requires speech or action"):
            await self.runner.player_turn(
                self.sid, thought="só pensando", audience=["C2"]
            )

    def test_action_facts_are_visible_to_present_characters(self) -> None:
        """Task 24: um fato que entra como ``action`` é testemunhado pelos presentes.

        Fecha o buraco em que uma auto-sugestão enviada no campo de ação tornava o
        fato permanentemente invisível a todos os personagens.
        """
        history = [
            _record(1, "Player", f"Dario mostra um pergaminho onde se lê {MARKER}.", "action"),
            _record(2, "C2", "Uma fala qualquer para o histórico não ficar vazio."),
        ]
        formatted = _format_history_for_character(
            history,
            THREE_CHARACTERS,
            "C1",
            "C2",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        marker_lines = [line for line in formatted.splitlines() if MARKER in line]
        assert marker_lines, "a ação testemunhada sumiu do contexto do personagem"
        assert all("TYPE=ACTION" in line and "SPEAKER=Dario" in line for line in marker_lines)

    def test_narration_facts_remain_invisible_to_characters(self) -> None:
        """A prosa onisciente do narrador continua fora do contexto dos personagens."""
        history = [
            _record(1, "Narrator", PASSWORD_FACT, "narration"),
            _record(2, "C2", "Uma fala qualquer para o histórico não ficar vazio."),
        ]
        formatted = _format_history_for_character(
            history,
            THREE_CHARACTERS,
            "C1",
            "C2",
            context_max=NO_TRIM_CONFIG["context_max"],
            max_tokens_character=NO_TRIM_CONFIG["max_tokens_character"],
        )
        assert MARKER not in formatted

    @pytest.mark.asyncio
    async def test_action_planted_fact_reaches_character_prompt_end_to_end(
        self, monkeypatch  # noqa: ANN001
    ) -> None:
        """Task 24 ponta a ponta: fato plantado via campo ``action`` do turno do
        jogador chega ao prompt real do personagem na mesma sessão."""
        captured: list[list[dict]] = []

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {
                "narration": "O pergaminho brilha à luz das velas.",
                "next_speaker": "C2",
                "context_for_character": "Dario mostra algo a Vela.",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_chat_completion_json(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured.append(messages)
            return {"speech": "Entendi o que está escrito.", "thought": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(character_mod, "chat_completion_json", fake_chat_completion_json)

        await self.runner.player_turn(
            self.sid,
            action=f"Dario desliza para Vela um pergaminho onde se lê {MARKER}, e o queima.",
            force_speaker="C2",
        )

        assert len(captured) == 1
        user_prompt = captured[0][-1]["content"]
        marker_lines = [line for line in user_prompt.splitlines() if MARKER in line]
        assert any("TYPE=ACTION" in line for line in marker_lines), (
            "o fato plantado via action não chegou ao prompt do personagem"
        )

    def test_player_speech_label_translates_to_controlled_name(self) -> None:
        assert speaker_label("Player", THREE_CHARACTERS, "C1") == "Dario"

    def test_audience_survives_serialization_round_trip(self) -> None:
        from src.models import dict_to_game_state, game_state_to_dict

        whispered = _record(1, "Player", PASSWORD_FACT)
        whispered.audience = ["C1", "C2"]
        game = _make_game("roundtrip", [whispered, _record(2, "C2", "Guardado.")])
        restored = dict_to_game_state(game_state_to_dict(game))
        assert restored.history[0].audience == ["C1", "C2"]
        assert restored.history[1].audience is None


def _whispered(
    turn_number: int,
    speaker: str,
    content: str,
    audience: list[str],
    content_type: str = "speech",
) -> TurnRecord:
    record = _record(turn_number, speaker, content, content_type)
    record.audience = audience
    return record


class TestWhisperLeakRedaction:
    """Task 25: guarda determinística contra o padrão "negar citando".

    O Narrador às vezes entrega o segredo exatamente ao negá-lo ("a senha
    ORQUÍDEA-741 é desconhecida para você"). ``redact_whisper_leaks`` remove do
    ``context_for_character`` de quem está FORA da audiência qualquer token que
    só exista em sussurros invisíveis a ele.
    """

    def _history(self) -> list[TurnRecord]:
        return [
            _whispered(1, "Player", PASSWORD_FACT, ["C1", "C2"]),
            _record(2, "C2", "Prometo guardar essa senha com a vida, Dario."),
            _record(3, "Player", "Rook, conheces alguma senha de cofre minha?"),
        ]

    def test_denial_that_reveals_is_redacted_for_outsider(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        context = (
            "Você não ouviu o que foi sussurrado entre Dario e Vela; "
            f"a senha {MARKER} é desconhecida para você."
        )
        redacted = redact_whisper_leaks(
            context, self._history(), "C3", THREE_CHARACTERS, SCENE
        )
        assert "ORQUÍDEA" not in redacted
        assert "741" not in redacted
        assert "[indistinct]" in redacted
        # Palavras ditas publicamente (turno 3) continuam intactas.
        assert "senha" in redacted
        assert "Dario" in redacted and "Vela" in redacted

    def test_adjacent_secret_tokens_collapse_into_one_marker(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        context = f"A senha {MARKER} é desconhecida para você."
        redacted = redact_whisper_leaks(
            context, self._history(), "C3", THREE_CHARACTERS, SCENE
        )
        assert redacted.count("[indistinct]") == 1

    def test_redaction_is_case_insensitive(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        context = "Alguém murmura algo sobre uma orquídea."
        redacted = redact_whisper_leaks(
            context, self._history(), "C3", THREE_CHARACTERS, SCENE
        )
        assert "orquídea" not in redacted.casefold()

    def test_audience_member_context_is_never_touched(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        context = f"Dario espera que você confirme a senha {MARKER} que ele sussurrou."
        assert (
            redact_whisper_leaks(context, self._history(), "C2", THREE_CHARACTERS, SCENE)
            == context
        )

    def test_whisper_speaker_context_is_never_touched(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        history = [_whispered(1, "C2", f"Só entre nós: {MARKER}.", ["C1"])]
        context = f"Você acabou de sussurrar {MARKER} a Dario."
        assert (
            redact_whisper_leaks(context, history, "C2", THREE_CHARACTERS, SCENE) == context
        )

    def test_history_without_whispers_returns_context_unchanged(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        history = [_record(1, "Player", PASSWORD_FACT)]
        context = f"Todos ouviram a senha {MARKER}."
        assert (
            redact_whisper_leaks(context, history, "C3", THREE_CHARACTERS, SCENE) == context
        )

    def test_empty_context_returns_empty(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        assert redact_whisper_leaks("", self._history(), "C3", THREE_CHARACTERS, SCENE) == ""

    def test_short_function_words_from_whisper_do_not_garble_context(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        # "com", "a", "do", "é" aparecem no sussurro mas têm menos de 4 letras
        # e nenhum dígito: nunca viram alvo de redação.
        context = "Rook fala com Dario e ri do balcão."
        assert (
            redact_whisper_leaks(context, self._history(), "C3", THREE_CHARACTERS, SCENE)
            == context
        )

    def test_scene_facts_whitelist_tokens_the_character_can_see(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        history = [_whispered(1, "Player", "Cuidado: a orquídea esconde a chave.", ["C2"])]
        scene = deepcopy_scene(SCENE)
        scene.physical_facts = {"flor_na_mesa": "orquídea murcha"}
        context = "Você repara na orquídea murcha sobre a mesa."
        assert (
            redact_whisper_leaks(context, history, "C3", THREE_CHARACTERS, scene) == context
        )

    def test_narration_leak_does_not_whitelist_the_secret(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        # Prosa do narrador nunca chega ao personagem, então uma narração que
        # vazou o segredo não pode transformá-lo em conhecimento legítimo.
        history = [
            *self._history(),
            _record(4, "Narrator", f"O segredo {MARKER} paira no ar.", "narration"),
        ]
        context = f"A senha {MARKER} é desconhecida para você."
        redacted = redact_whisper_leaks(context, history, "C3", THREE_CHARACTERS, SCENE)
        assert MARKER not in redacted
        assert "741" not in redacted

    def test_narrator_system_prompt_pins_whisper_and_denial_rules(self) -> None:
        from src.agents.narrator import _build_system_prompt

        prompt = _build_system_prompt(["C1", "C2", "C3"])
        assert "[WHISPERED, perceived only by: ...]" in prompt
        assert "denials that reveal" in prompt
        assert "—" not in prompt
        assert "–" not in prompt


class TestWhisperLeakGuardEndToEnd:
    """Task 25 ponta a ponta: o contexto que o personagem de fora recebe já
    chega saneado pelo runner, e o de quem está na audiência chega intacto."""

    def setup_method(self) -> None:
        self.sid = generate_session_id()
        self.client = httpx.AsyncClient(base_url="http://localhost:8888")
        self.runner = Runner(self.client, dict(NO_TRIM_CONFIG))
        whispered = _record(1, "Player", PASSWORD_FACT)
        whispered.audience = ["C1", "C2"]
        history = [
            whispered,
            _record(2, "C2", "Prometo guardar essa senha com a vida, Dario."),
        ]
        save_game(_make_game(self.sid, history))

    def teardown_method(self) -> None:
        directory = session_dir(self.sid)
        if directory.exists():
            shutil.rmtree(directory)

    @pytest.mark.asyncio
    async def test_outsider_receives_redacted_context(self, monkeypatch) -> None:  # noqa: ANN001
        captured: dict[str, str] = {}

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {
                "narration": "Rook coça a nuca, alheio ao que foi murmurado.",
                "next_speaker": "C3",
                "context_for_character": (
                    "Dario pergunta se conheces alguma senha de cofre dele. "
                    "Você não ouviu o que foi sussurrado entre Dario e Vela; "
                    f"a senha {MARKER} é desconhecida para você."
                ),
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["context"] = context
            return {"speech": "Senha? Nunca ouvi nada disso.", "thought": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_call_character", fake_character)

        await self.runner.player_turn(
            self.sid,
            speech="Rook, última pergunta da noite: conheces alguma senha de cofre minha?",
            force_speaker="C3",
        )

        assert "context" in captured, "o personagem de fora não foi chamado"
        assert MARKER not in captured["context"]
        assert "741" not in captured["context"]
        assert "[indistinct]" in captured["context"]
        # O resto do contexto sobrevive: a pergunta pública continua legível.
        assert "senha" in captured["context"]

    @pytest.mark.asyncio
    async def test_audience_member_receives_whisper_content_intact(self, monkeypatch) -> None:  # noqa: ANN001
        captured: dict[str, str] = {}
        context_in = f"Dario sussurrou para você: a senha é {MARKER}. Ele espera confirmação."

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {
                "narration": "Vela inclina a cabeça, atenta.",
                "next_speaker": "C2",
                "context_for_character": context_in,
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202
            captured["context"] = context
            return {"speech": "Guardado, Dario.", "thought": None}

        monkeypatch.setattr(self.runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(self.runner, "_call_character", fake_character)

        await self.runner.player_turn(
            self.sid,
            speech="Vela, confirma baixinho o que te disse.",
            force_speaker="C2",
            audience=["C1", "C2"],
        )

        assert captured["context"] == context_in
        assert MARKER in captured["context"]


class TestSecretTokensExposedTo:
    """Task 25: derivação determinística dos tokens-segredo por exposição."""

    def _base_history(self) -> list[TurnRecord]:
        whispered = _record(1, "Player", PASSWORD_FACT)
        whispered.audience = ["C1", "C2"]
        return [
            whispered,
            _record(2, "Player", "Vela, guarda bem a senha que te confiei."),
        ]

    def test_speaker_outside_whisper_has_no_secrets(self) -> None:
        from src.confidentiality import secret_tokens_exposed_to

        secret = secret_tokens_exposed_to(
            self._base_history(), "C3", {"C2"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )
        assert secret == set()

    def test_insider_exposing_public_yields_secret_tokens(self) -> None:
        from src.confidentiality import secret_tokens_exposed_to

        secret = secret_tokens_exposed_to(
            self._base_history(), "C2", {"C3"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )
        assert "orquídea" in secret and "741" in secret
        # "senha" foi dita em registro público (turno 2): conhecimento ganho.
        assert "senha" not in secret

    def test_reply_audience_covering_secret_is_clean(self) -> None:
        from src.confidentiality import secret_tokens_exposed_to

        secret = secret_tokens_exposed_to(
            self._base_history(), "C2", {"C1"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )
        assert secret == set()

    def test_player_marker_counts_as_controlled_for_cover(self) -> None:
        from src.confidentiality import secret_tokens_exposed_to

        whispered = _record(1, "Player", f"Rook, só para ti: o esconderijo é {MARKER}.")
        whispered.audience = ["C3"]
        secret = secret_tokens_exposed_to(
            [whispered], "C3", {"C1"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )
        assert secret == set(), "o autor do sussurro (Player=C1) não é um vazamento"

    def test_secret_already_public_is_earned_knowledge(self) -> None:
        from src.confidentiality import secret_tokens_exposed_to

        history = self._base_history() + [
            _record(3, "C2", f"A senha {MARKER} está segura comigo!"),
        ]
        secret = secret_tokens_exposed_to(
            history, "C2", {"C3"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )
        assert "orquídea" not in secret and "741" not in secret


GIRASSOL_WHISPER = (
    "Assunto de trabalho, só entre nós dois: escondi as cartas de crédito debaixo "
    "da ponte GIRASSOL-222, no terceiro pilar contando da margem norte. Só tu sabes disso."
)
CASUAL_WHISPER_REPLY = (
    "Entendi, chefe, pode deixar. Peguei só a metade e não faço barulho com esse "
    "negócio; ninguém aqui fala alto, sabe como é."
)


class TestSecretPayloadDerivation:
    """Relato 1: segredo é o conteúdo informacional do sussurro, nunca o fraseado.

    Tokens raros de conversa casual ("alto", "sabe", "negócio") não podem
    envenenar o vocabulário público do personagem; o payload (código, número e
    as palavras que o localizam) continua bloqueado.
    """

    def _history(self) -> list[TurnRecord]:
        whispered = _record(1, "Player", GIRASSOL_WHISPER)
        whispered.audience = ["C3"]
        reply = _record(2, "C3", CASUAL_WHISPER_REPLY)
        reply.audience = ["C3"]
        return [whispered, reply]

    def _secret(self) -> set[str]:
        from src.confidentiality import secret_tokens_exposed_to

        return secret_tokens_exposed_to(
            self._history(), "C3", {"C2"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )

    def test_informational_payload_tokens_fire(self) -> None:
        secret = self._secret()
        assert {
            "girassol",
            "222",
            "ponte",
            "pilar",
            "terceiro",
            "margem",
            "norte",
            "cartas",
        } <= secret

    def test_casual_phrasing_of_the_whisper_never_fires(self) -> None:
        secret = self._secret()
        assert secret.isdisjoint(
            {
                "alto",
                "fala",
                "sabe",
                "sabes",
                "entre",
                "negócio",
                "barulho",
                "metade",
                "peguei",
                "assunto",
                "trabalho",
                "entendi",
                "chefe",
            }
        )

    def test_whisper_without_anchor_has_no_guardable_payload(self) -> None:
        from src.confidentiality import secret_tokens_exposed_to

        whispered = _record(
            1, "Player", "Fica de olho no balcão e não comenta nada com ninguém."
        )
        whispered.audience = ["C3"]
        secret = secret_tokens_exposed_to(
            [whispered], "C3", {"C2"}, THREE_CHARACTERS, SCENE, controlled_id="C1"
        )
        assert secret == set()

    def test_payload_tokens_keeps_code_and_neighbors_drops_framing(self) -> None:
        from src.confidentiality import payload_tokens

        payload = payload_tokens(GIRASSOL_WHISPER)
        assert {"girassol", "222", "ponte", "pilar"} <= payload
        assert payload.isdisjoint({"assunto", "trabalho", "entre", "sabes", "disso"})

    def test_narrator_guard_leaves_casual_words_intact_for_outsider(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        context = (
            "Rook resmunga alto sobre um negócio qualquer; "
            "você não sabe do que ele fala."
        )
        assert (
            redact_whisper_leaks(context, self._history(), "C2", THREE_CHARACTERS, SCENE)
            == context
        )

    def test_narrator_guard_still_redacts_payload_for_outsider(self) -> None:
        from src.agents.narrator import redact_whisper_leaks

        context = "Você ouviu de relance algo sobre a ponte GIRASSOL-222."
        redacted = redact_whisper_leaks(
            context, self._history(), "C2", THREE_CHARACTERS, SCENE
        )
        assert "girassol" not in redacted.casefold()
        assert "222" not in redacted
        assert "[indistinct]" in redacted


class TestCharacterOutputGuard:
    """Task 25: guarda determinística na SAÍDA do personagem — retry e redação."""

    def _history(self) -> list[TurnRecord]:
        whispered = _record(1, "Player", PASSWORD_FACT)
        whispered.audience = ["C1", "C2"]
        return [
            whispered,
            _record(2, "Player", "Vela, guarda bem a senha que te confiei."),
        ]

    async def _act(self, monkeypatch, responses: list[dict], reply_audience=None):  # noqa: ANN001, ANN202
        calls: list[list[dict]] = []
        queue = list(responses)

        async def fake_chat_completion_json(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            calls.append(messages)
            return queue.pop(0)

        monkeypatch.setattr(character_mod, "chat_completion_json", fake_chat_completion_json)
        output = await character_mod.act(
            client=None,
            character=THREE_CHARACTERS["C2"],
            context="Dario pergunta sobre a noite.",
            history=self._history(),
            characters=THREE_CHARACTERS,
            controlled_id="C1",
            character_id="C2",
            config={},
            scene=SCENE,
            reply_audience=reply_audience,
        )
        return output, calls

    @pytest.mark.asyncio
    async def test_public_leak_gets_correction_then_clean_reply_passes(self, monkeypatch) -> None:  # noqa: ANN001
        output, calls = await self._act(
            monkeypatch,
            [
                {"speech": f"Claro, a senha era {MARKER}!", "thought": None},
                {"speech": "Prefiro guardar certos assuntos para mim.", "thought": None},
            ],
        )
        assert len(calls) == 2
        assert "CORRECTION" in calls[1][-1]["content"]
        assert "whispered confidential content" in calls[1][-1]["content"]
        assert output["speech"] == "Prefiro guardar certos assuntos para mim."

    @pytest.mark.asyncio
    async def test_persistent_leak_is_redacted_never_raises(self, monkeypatch) -> None:  # noqa: ANN001
        output, calls = await self._act(
            monkeypatch,
            [
                {"speech": f"A senha era {MARKER}!", "thought": None},
                {"speech": f"Insisto: {MARKER}, essa era a senha.", "thought": "Eu sei tudo."},
            ],
        )
        assert len(calls) == 2
        assert MARKER not in (output["speech"] or "")
        assert "741" not in (output["speech"] or "")
        assert "[indistinct]" in (output["speech"] or "")
        assert output["thought"] == "Eu sei tudo."

    @pytest.mark.asyncio
    async def test_whispered_reply_to_confidant_passes_intact(self, monkeypatch) -> None:  # noqa: ANN001
        output, calls = await self._act(
            monkeypatch,
            [{"speech": f"Era {MARKER}, exatamente.", "thought": None}],
            reply_audience=["C1", "C2"],
        )
        assert len(calls) == 1
        assert output["speech"] == f"Era {MARKER}, exatamente."

    @pytest.mark.asyncio
    async def test_whispered_turn_prompt_signals_confidential_speech(self, monkeypatch) -> None:  # noqa: ANN001
        """Relato 2: o prompt do turno sussurrado declara a fala confidencial e
        nomeia o confidente, autorizando o segredo por extenso."""
        _, calls = await self._act(
            monkeypatch,
            [{"speech": f"Era {MARKER}, exatamente.", "thought": None}],
            reply_audience=["C1", "C2"],
        )
        prompt = calls[0][-1]["content"]
        assert "THIS TURN IS A WHISPER" in prompt
        assert "Dario" in prompt
        assert "fully and exactly" in prompt

    @pytest.mark.asyncio
    async def test_public_turn_prompt_has_no_whisper_marker(self, monkeypatch) -> None:  # noqa: ANN001
        _, calls = await self._act(
            monkeypatch,
            [{"speech": "Boa noite a todos.", "thought": None}],
        )
        assert "THIS TURN IS A WHISPER" not in calls[0][-1]["content"]

    @pytest.mark.asyncio
    async def test_guard_disabled_without_scene(self, monkeypatch) -> None:  # noqa: ANN001
        calls: list[list[dict]] = []

        async def fake_chat_completion_json(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            calls.append(messages)
            return {"speech": f"A senha era {MARKER}!", "thought": None}

        monkeypatch.setattr(character_mod, "chat_completion_json", fake_chat_completion_json)
        output = await character_mod.act(
            client=None,
            character=THREE_CHARACTERS["C2"],
            context="ctx",
            history=self._history(),
            characters=THREE_CHARACTERS,
            controlled_id="C1",
            character_id="C2",
            config={},
        )
        assert len(calls) == 1
        assert MARKER in (output["speech"] or "")

    @pytest.mark.asyncio
    async def test_end_to_end_public_record_never_contains_secret(self, monkeypatch) -> None:  # noqa: ANN001
        """Via player_turn real: fake que insiste em vazar → registro público redigido."""
        sid = generate_session_id()
        whispered = _record(1, "Player", PASSWORD_FACT)
        whispered.audience = ["C1", "C2"]
        save_game(
            _make_game(
                sid,
                [whispered, _record(2, "Player", "Vela, guarda bem a senha que te confiei.")],
            )
        )
        runner = Runner(httpx.AsyncClient(base_url="http://localhost:8888"), dict(NO_TRIM_CONFIG))

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {
                "narration": "A taverna murmura.",
                "next_speaker": "C2",
                "context_for_character": "Rook pergunta em voz alta sobre segredos.",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_chat_completion_json(client, messages, **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {"speech": f"Todos deviam saber: a senha é {MARKER}!", "thought": None}

        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(character_mod, "chat_completion_json", fake_chat_completion_json)

        try:
            result = await runner.player_turn(
                sid, speech="Vela, o que dizes em voz alta?", force_speaker="C2"
            )
            from src.store.sessions import load_game

            game = load_game(sid)
            assert game is not None
            public_speech = [
                rec
                for rec in game.history
                if rec.speaker == "C2" and rec.content_type == "speech"
            ]
            assert public_speech, "a fala do personagem não foi gravada"
            assert all(MARKER not in rec.content for rec in public_speech)
            assert any("[indistinct]" in rec.content for rec in public_speech)
            assert MARKER not in (result["character_response"]["speech"] or "")
        finally:
            directory = session_dir(sid)
            if directory.exists():
                shutil.rmtree(directory)


class TestTrimCompactionGapFinding:
    """Achado independente: o trim corta histórico antigo sem nenhum fallback.

    Não é a causa confirmada do cenário de foco (lá o trim nem dispara); é um gap
    real em sessões que excedem ~70% do context_max sem compactação. Os xfail
    especificam o comportamento desejado e devem virar verdes no passe de correção.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="gap trim/compactação: histórico cortado não é preservado em resumo/nota",
    )
    def test_trim_preserves_early_fact_or_summarizes_it(self) -> None:
        history = _seed_focus_history(noise_pairs=30)
        formatted = _format_history_for_character(
            history,
            THREE_CHARACTERS,
            "C1",
            "C2",
            context_max=2000,
            max_tokens_character=100,
        )
        assert MARKER in formatted

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "compaction_keep_recent_turns=200 bloqueia a compactação automática sob "
            "pressão de contexto em sessões curtas"
        ),
    )
    @pytest.mark.asyncio
    async def test_automatic_compaction_unblocked_under_context_pressure(
        self, monkeypatch  # noqa: ANN001
    ) -> None:
        session_id = generate_session_id()
        save_game(_make_game(session_id, _seed_focus_history(noise_pairs=10)))
        client = httpx.AsyncClient(base_url="http://localhost:8888")
        runner = Runner(
            client,
            {
                "context_max": 10000,
                "max_tokens_narrator": 100,
                "automatic_compaction_enabled": True,
                "automatic_compaction_threshold_percent": 60,
                "compaction_keep_recent_turns": 200,
            },
        )

        async def fake_summarize(**kwargs):  # noqa: ANN003, ANN202
            return "Resumo durável.", {"C2": f"Vela lembra que a senha é {MARKER}."}

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {
                "narration": "A taverna murmura.",
                "next_speaker": "C2",
                "context_for_character": "Dario aguarda.",
                "scene_update": None,
                "mood_updates": None,
            }

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202
            return {"speech": "Entendido.", "thought": None}

        monkeypatch.setattr(runner_mod, "summarize", fake_summarize)
        monkeypatch.setattr(runner_mod, "estimate_prompt_tokens", lambda messages: 100000)
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(runner, "_call_character", fake_character)

        try:
            result = await runner.player_turn(
                session_id,
                speech="Vela, continua o registro.",
                force_speaker="C2",
            )
            assert result["automatic_compaction"]["status"] == "compacted"
        finally:
            directory = session_dir(session_id)
            if directory.exists():
                shutil.rmtree(directory)
