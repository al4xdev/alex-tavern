"""Task 44 Toggle 2: the transient alignment impulse.

Locks the leak-safe-by-construction vocabulary, the enum-only Director call, and —
the sensitive part — the gating: both flags required, the impulse NEVER reaches the
controlled character (agency lock) nor a non-expected actor.
"""

from __future__ import annotations

import httpx
import pytest

from src.alignment import (
    IMPULSE_KEYS,
    IMPULSES,
    build_alignment_messages,
    build_alignment_schema,
    render_impulse,
)
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Roteiro,
    RoteiroBeat,
    Scene,
    deepcopy_scene,
)


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(
            name=name, personality="corajoso e protetor", knowledge=[], current_mood="m"
        ),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Link"), "C2": _char("Asword"), "C3": _char("Nix")}
SCENE = Scene(
    location="Masmorra",
    time_of_day="manhã",
    present_characters=["C1", "C2", "C3"],
    physical_facts={},
)


def _game(*, beat_actors=("C2",), with_beat=True) -> GameState:
    roteiro = Roteiro(premise="segredo", beat=None)
    if with_beat:
        roteiro.beat = RoteiroBeat(
            beat_id="b1",
            intent="a equipe precisa se dividir e arriscar",
            expected_actors=list(beat_actors),
        )
    return GameState(
        session_id="aligntest",
        characters=dict(CHARACTERS),
        player=Player(controlled_character_id="C1"),
        scene=deepcopy_scene(SCENE),
        roteiro=roteiro,
    )


class TestRenderImpulse:
    def test_known_key_renders_the_fixed_feeling(self) -> None:
        line = render_impulse("bold")
        assert "temerário" in line and "SEU ÍMPETO" in line

    def test_none_and_unknown_render_empty(self) -> None:
        assert render_impulse("none") == ""
        assert render_impulse("bogus") == ""

    def test_every_impulse_renders(self) -> None:
        assert all(render_impulse(k) for k in IMPULSES)


class TestSchemaAndMessages:
    def test_schema_enum_is_the_closed_vocabulary(self) -> None:
        enum = build_alignment_schema()["schema"]["properties"]["impulse"]["enum"]
        assert tuple(enum) == IMPULSE_KEYS and "none" in enum

    def test_messages_carry_beat_and_character_and_secrecy(self) -> None:
        joined = "\n".join(
            m["content"]
            for m in build_alignment_messages(
                "a equipe deve cruzar a ponte podre", CHARACTERS["C2"]
            )
        )
        assert "ponte podre" in joined  # the private beat feeds the Director-side call
        assert "Asword" in joined
        assert "never reveal" in joined.lower() and "enum" in joined.lower()
        assert "desired resolution" in joined and "stopping, containing" in joined


class TestGatingAndAgencyLock:
    """The confidentiality/agency-critical logic: who gets an impulse, and when."""

    async def _impulse(self, monkeypatch, config, cid, game=None) -> str:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        calls = {"n": 0}

        async def fake_derive(client, beat_intent, character, cfg, **kwargs):  # noqa: ANN001, ANN003, ARG001
            calls["n"] += 1
            return render_impulse("bold")

        monkeypatch.setattr(runner_mod, "derive_alignment_impulse", fake_derive)
        async with httpx.AsyncClient() as client:
            runner = Runner(client, dict(config))
            out = await runner._alignment_impulse(game or _game(), cid, 1)
        return out, calls["n"]

    BOTH_ON = {"roteiro_enabled": True, "character_roteiro_alignment_enabled": True}

    @pytest.mark.parametrize(
        ("roteiro_enabled", "alignment_enabled", "expects_impulse"),
        [
            (False, False, False),
            (False, True, False),
            (True, False, False),
            (True, True, True),
        ],
    )
    async def test_all_toggle_combinations(
        self,
        monkeypatch,
        roteiro_enabled: bool,
        alignment_enabled: bool,
        expects_impulse: bool,
    ) -> None:  # noqa: ANN001
        out, calls = await self._impulse(
            monkeypatch,
            {
                "roteiro_enabled": roteiro_enabled,
                "character_roteiro_alignment_enabled": alignment_enabled,
            },
            "C2",
        )
        assert bool(out) is expects_impulse
        assert calls == int(expects_impulse)

    @pytest.mark.asyncio
    async def test_expected_actor_gets_the_impulse(self, monkeypatch) -> None:  # noqa: ANN001
        out, n = await self._impulse(monkeypatch, self.BOTH_ON, "C2")
        assert "temerário" in out and n == 1

    @pytest.mark.asyncio
    async def test_controlled_character_never_aligned(self, monkeypatch) -> None:  # noqa: ANN001
        # C1 is controlled AND an expected actor -> still NO impulse, deriver not called
        out, n = await self._impulse(
            monkeypatch, self.BOTH_ON, "C1", game=_game(beat_actors=("C1", "C2"))
        )
        assert out == "" and n == 0

    @pytest.mark.asyncio
    async def test_non_expected_actor_gets_nothing(self, monkeypatch) -> None:  # noqa: ANN001
        out, n = await self._impulse(monkeypatch, self.BOTH_ON, "C3")
        assert out == "" and n == 0

    @pytest.mark.asyncio
    async def test_alignment_flag_off_is_noop(self, monkeypatch) -> None:  # noqa: ANN001
        out, n = await self._impulse(
            monkeypatch,
            {"roteiro_enabled": True, "character_roteiro_alignment_enabled": False},
            "C2",
        )
        assert out == "" and n == 0

    @pytest.mark.asyncio
    async def test_roteiro_flag_off_is_noop(self, monkeypatch) -> None:  # noqa: ANN001
        out, n = await self._impulse(
            monkeypatch,
            {"roteiro_enabled": False, "character_roteiro_alignment_enabled": True},
            "C2",
        )
        assert out == "" and n == 0

    @pytest.mark.asyncio
    async def test_no_beat_is_noop(self, monkeypatch) -> None:  # noqa: ANN001
        out, n = await self._impulse(monkeypatch, self.BOTH_ON, "C2", game=_game(with_beat=False))
        assert out == "" and n == 0


class TestPromptInjection:
    def test_impulse_reaches_the_character_prompt_from_fixed_vocab(self) -> None:
        from src.agents.character import _build_user_prompt

        impulse = render_impulse("cautious")
        prompt = _build_user_prompt("ctx", "hist", "mood", alignment_impulse=impulse)
        assert "cauteloso" in prompt and "SEU ÍMPETO" in prompt
        # the injected line is nothing but the fixed vocabulary (no plot could ride it)
        assert impulse in IMPULSES["cautious"] or "cauteloso" in IMPULSES["cautious"]


class TestRuntimeSwap:
    @pytest.mark.asyncio
    async def test_config_update_replaces_runner_with_new_toggle_values(self, monkeypatch) -> None:  # noqa: ANN001
        from src import main
        from src.main import RuntimeState
        from src.runner import Runner

        old_client = httpx.AsyncClient()
        old_runner = Runner(old_client, {"roteiro_enabled": False})
        runtime = RuntimeState(
            stored_config={"roteiro_enabled": False},
            server_config={"roteiro_enabled": False},
            llm_client=old_client,
            runner=old_runner,
        )
        main.app.state.runtime = runtime
        submitted = {
            "roteiro_enabled": True,
            "character_roteiro_alignment_enabled": True,
        }
        monkeypatch.setattr(main, "merge_config_update", lambda body: dict(body))
        monkeypatch.setattr(main, "resolve_active_config", lambda stored: dict(stored))
        monkeypatch.setattr(main, "public_config", lambda stored: dict(stored))

        result = main.put_runtime_config(submitted)

        assert result == submitted
        assert runtime.runner is not old_runner
        assert runtime.runner.config["roteiro_enabled"] is True
        assert runtime.runner.config["character_roteiro_alignment_enabled"] is True
        await old_client.aclose()
