"""Response-length settings survive configuration and reach production prompts."""

from copy import deepcopy

import pytest

from src.agents.character import build_character_messages
from src.agents.prose import render_narration
from src.config import (
    DEFAULT_CONFIG,
    ConfigValidationError,
    load_config,
    public_config,
    resolve_active_config,
    save_config,
    validate_config,
)
from tests.factories import make_cast, make_scene


def test_length_settings_round_trip_and_character_prompt(tmp_path):
    config = deepcopy(DEFAULT_CONFIG)
    provider = config["providers"][config["active_provider"]]
    provider["narrator_min_words"] = 350
    provider["character_max_sentences"] = 7
    path = tmp_path / "config.json"
    save_config(config, path)
    loaded = load_config(path)
    resolved = resolve_active_config(loaded)
    assert resolved["narrator_min_words"] == 350
    assert resolved["character_max_sentences"] == 7
    assert public_config(loaded)["providers"][config["active_provider"]] == provider
    cast = make_cast("Alice")
    messages = build_character_messages(cast["C1"], "", [], cast, "C1", "C1", resolved)
    assert "1-7 sentences" in messages[0]["content"]
    assert "1-3 sentences" not in messages[0]["content"]


@pytest.mark.parametrize("field", ["narrator_min_words", "character_max_sentences"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5, "3", None])
def test_length_settings_reject_invalid_values(field, value):
    config = deepcopy(DEFAULT_CONFIG)
    config["providers"][config["active_provider"]][field] = value
    with pytest.raises(ConfigValidationError, match=field):
        validate_config(config)


@pytest.mark.asyncio
async def test_prose_call_uses_configured_word_floor(monkeypatch):
    async def capture(client, config, messages, **kwargs):
        assert "at least 350 words" in messages[0]["content"]
        assert "at least 150 words" not in messages[0]["content"]
        assert kwargs["max_tokens"] == 2048
        return {"narration": "A porta se abre."}

    monkeypatch.setattr("src.agents.prose.call_agent", capture)
    result = await render_narration(
        None,
        make_scene(),
        make_cast("Alice"),
        "C1",
        [],
        [],
        {"narrator_min_words": 350, "max_tokens_narrator": 2048},
    )
    assert result == "A porta se abre."
