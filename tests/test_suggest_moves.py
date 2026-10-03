"""Character-based suggestions preserve perception, agency and output guards."""

from __future__ import annotations

import httpx
import pytest

from src.agents import suggest as suggest_mod
from src.agents.suggest import suggest_moves
from src.models import CharacterPerspective, game_state_to_dict
from src.prompt_contract import leaks_operator_ontology
from tests.factories import make_character, make_game, make_record, make_scene


def _game():
    cast = {
        "C1": make_character(
            "Link",
            personality="Curioso e cauteloso.",
            knowledge=["A nevoa vem do arco leste."],
            current_mood="tenso",
        ),
        "C2": make_character(
            "Maelis",
            personality="Diretora severa.",
            knowledge=["O SEGREDO DE MAELIS: ela abriu a ferida."],
            current_mood="fria",
        ),
        "C3": make_character("Garran", personality="Instrutor pratico."),
    }
    game = make_game(
        characters=cast,
        scene=make_scene(characters=cast, location="Salao do Prisma", time_of_day="tarde"),
        controlled="C1",
    )
    game.scene.physical_facts = {"arco leste": "instavel"}
    game.narrator_directives = "Fantasia escolar. Magia e regulada."
    game.history = [
        make_record(1, "C1", "Alguem viu a nevoa?", scene=game.scene),
        make_record(1, "C1", "Preciso chegar perto do arco.", "thought", scene=game.scene),
        make_record(2, "C2", "Fiquem onde estao.", scene=game.scene),
        make_record(2, "C2", "ELES NAO PODEM SABER QUE FUI EU.", "thought", scene=game.scene),
        make_record(3, "C3", "O arco leste range.", scene=game.scene),
    ]
    return game


@pytest.mark.asyncio
async def test_suggestions_use_character_context_and_leave_session_untouched(monkeypatch):
    game = _game()
    game.character_perspectives["C1"] = CharacterPerspective(
        initialized_turn=0,
        processed_through_turn=0,
        memory_summary="Prometi proteger o arco, antes desta conversa.",
    )
    before = game_state_to_dict(game)
    requests = []

    async def fake_call(client, config, messages, **kwargs):
        requests.append((messages, kwargs))
        return {
            "suggestions": [
                {
                    "speech": "O que mudou?",
                    "thought": "Preciso entender melhor.",
                    "action_intent": "examinar o arco",
                },
                {"speech": None, "thought": None, "action_intent": "aproximar-se do arco"},
                {"speech": None, "thought": "Preciso esperar.", "action_intent": None},
            ]
        }

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        result = await suggest_moves(
            client,
            game.scene,
            game.characters,
            "C1",
            game.history,
            {"context_max": 8192, "max_tokens_character": 2048},
            game.narrator_directives,
            session_id="example",
            turn_number=3,
            viewer_perspective=game.character_perspectives["C1"],
            dispositions=game.dispositions,
        )
    assert game_state_to_dict(game) == before
    assert len(result) == 3
    assert len(requests) == 1
    assert result[0] == {
        "speech": "O que mudou?",
        "thought": "Preciso entender melhor.",
        "action": "examinar o arco",
    }
    for messages, kwargs in requests:
        text = "\n".join(message["content"] for message in messages)
        assert "Curioso e cauteloso." in text
        assert "A nevoa vem do arco leste." in text
        assert "Preciso chegar perto do arco." in text
        assert "Prometi proteger o arco" in text
        assert "Salao do Prisma" in text
        assert "Fantasia escolar. Magia e regulada." in text
        assert "ELES NAO PODEM SABER" not in text
        assert "O SEGREDO DE MAELIS" not in text
        assert "Diretora severa." not in text
        assert "arco leste: instavel" in text  # shared, unsplit surroundings
        assert not leaks_operator_ontology(text)
        assert kwargs["json_schema"]["name"] == "character_move_suggestions"
        assert kwargs["session_id"] == "example"
        assert kwargs["turn_number"] == 3
        assert kwargs["max_tokens"] == 6144
    assert requests[0][1]["agent"] == "suggest_moves"
    assert requests[0][1]["json_schema"]["schema"]["properties"]["suggestions"]["minItems"] == 3


@pytest.mark.asyncio
async def test_suggestions_exclude_whispers_outside_the_audience(monkeypatch):
    game = _game()
    game.history.append(
        make_record(4, "C2", "SEGREDO SUSSURRADO PARA GARRAN", scene=game.scene, audience=["C3"])
    )
    captured = []

    async def fake_call(client, config, messages, **kwargs):
        captured.append(str(messages))
        return {
            "suggestions": [{"speech": None, "thought": "Quero saber mais.", "action_intent": None}]
            * 3
        }

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        result = await suggest_moves(client, game.scene, game.characters, "C1", game.history, {})
    assert all("SEGREDO SUSSURRADO" not in text for text in captured)
    assert all(
        item == {"speech": "", "thought": "Quero saber mais.", "action": ""} for item in result
    )


@pytest.mark.asyncio
async def test_suggestions_use_character_repetition_retry(monkeypatch):
    game = _game()
    repeated = "Precisamos proteger o arco antes que seja tarde demais."
    game.history.append(make_record(4, "C1", repeated, scene=game.scene))
    attempts = {}

    async def fake_call(client, config, messages, **kwargs):
        agent = kwargs["agent"]
        attempts[agent] = attempts.get(agent, 0) + 1
        if attempts[agent] == 1:
            return {
                "suggestions": [{"speech": repeated, "thought": None, "action_intent": None}] * 3
            }
        assert kwargs["guard_retry"] == "suggestion_output"
        return {
            "suggestions": [
                {"speech": "Quem pode me ajudar?", "thought": None, "action_intent": None}
            ]
            * 3
        }

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        result = await suggest_moves(client, game.scene, game.characters, "C1", game.history, {})
    assert set(attempts.values()) == {2}
    assert all(item["speech"] == "Quem pode me ajudar?" for item in result)


@pytest.mark.asyncio
async def test_invalid_character_output_does_not_become_a_suggestion(monkeypatch):
    game = _game()

    async def fake_call(*args, **kwargs):
        return {"suggestions": [{"speech": None, "thought": None, "action_intent": None}] * 3}

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="Character response must contain"):
            await suggest_moves(client, game.scene, game.characters, "C1", game.history, {})


def test_suggestion_schema_reuses_character_fields_and_requires_three():
    from src.agents.character import build_character_json_schema
    from src.agents.suggest import build_suggestion_schema
    from src.llm.schema import JSONSchemaValidationError, validate_json_schema

    schema = build_suggestion_schema()["schema"]
    assert schema["properties"]["suggestions"]["items"] == build_character_json_schema()["schema"]
    item = {"speech": None, "thought": "Preciso esperar.", "action_intent": None}
    validate_json_schema({"suggestions": [item] * 3}, schema)
    with pytest.raises(JSONSchemaValidationError):
        validate_json_schema({"suggestions": [item] * 2}, schema)


@pytest.mark.asyncio
async def test_split_scene_facts_do_not_reach_drafts(monkeypatch):
    game = _game()
    game.scene.zones = {"sala": [], "cozinha": []}
    game.scene.positions = {"C1": "sala", "C2": "cozinha", "C3": "sala"}
    game.scene.physical_facts = {"cozinha": "SEGREDO ATRAS DA PAREDE"}

    async def fake_call(client, config, messages, **kwargs):
        assert "SEGREDO ATRAS DA PAREDE" not in str(messages)
        return {
            "suggestions": [{"speech": "Quem esta aqui?", "thought": None, "action_intent": None}]
            * 3
        }

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        await suggest_moves(client, game.scene, game.characters, "C1", game.history, {})


@pytest.mark.asyncio
async def test_suggestion_speech_cannot_expose_a_known_whisper(monkeypatch):
    game = _game()
    game.history.append(
        make_record(4, "C2", "O codigo e ORQUIDEA-741.", scene=game.scene, audience=["C1"])
    )
    attempts = []

    async def fake_call(client, config, messages, **kwargs):
        attempts.append(kwargs)
        return {
            "suggestions": [
                {"speech": "ORQUIDEA-741", "thought": "Sei o codigo.", "action_intent": None}
            ]
            * 3
        }

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        result = await suggest_moves(client, game.scene, game.characters, "C1", game.history, {})
    assert len(attempts) == 2
    assert all("ORQUIDEA" not in item["speech"] and "741" not in item["speech"] for item in result)
    assert all(item["thought"] == "Sei o codigo." for item in result)


@pytest.mark.asyncio
async def test_http_suggestion_preserves_state_and_returns_thought(monkeypatch):
    from types import SimpleNamespace

    from src import main
    from src.runner import Runner
    from src.store.sessions import save_game, session_state_path
    from tests.conftest import sec_headers

    game = _game()
    save_game(game)
    path = session_state_path(game.session_id)
    before = path.read_bytes()

    async def fake_call(client, config, messages, **kwargs):
        return {
            "suggestions": [
                {
                    "speech": "Quem pode ajudar?",
                    "thought": "Preciso de apoio.",
                    "action_intent": "examinar o arco",
                }
            ]
            * 3
        }

    monkeypatch.setattr(suggest_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as llm_client:
        runner = Runner(llm_client, {})
        monkeypatch.setattr(main, "_runtime", lambda: SimpleNamespace(runner=runner))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://localhost"
        ) as client:
            response = await client.post(
                f"/session/{game.session_id}/suggest", headers=sec_headers()
            )
    assert response.status_code == 200
    assert (
        response.json()["suggestions"]
        == [
            {
                "speech": "Quem pode ajudar?",
                "thought": "Preciso de apoio.",
                "action": "examinar o arco",
            }
        ]
        * 3
    )
    assert path.read_bytes() == before
