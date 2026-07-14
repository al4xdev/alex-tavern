"""Provider configuration and DeepSeek compatibility adapter tests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import httpx
import pytest

from src.config import (
    DEFAULT_CONFIG,
    ConfigValidationError,
    load_config,
    merge_config_update,
    public_config,
    resolve_active_config,
    save_config,
    validate_config,
)
from src.llm.adapters import ProviderResponseError, get_provider_adapter
from src.llm.client import chat_completion_json
from src.llm.schema import validate_json_schema


def test_config_round_trip_resolution_and_key_redaction(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    value = deepcopy(DEFAULT_CONFIG)
    value["active_provider"] = "deepseek"
    value["providers"]["deepseek"]["api_key"] = "secret-value"

    saved = save_config(value, path)
    loaded = load_config(path)
    resolved = resolve_active_config(loaded)
    safe = public_config(loaded)

    assert loaded == saved
    assert resolved["provider"] == "deepseek"
    assert resolved["model"] == "deepseek-v4-flash"
    assert resolved["api_key"] == "secret-value"
    assert resolved["automatic_compaction_enabled"] is False
    assert resolved["automatic_compaction_threshold_percent"] == 80
    assert "api_key" not in safe["providers"]["deepseek"]
    assert safe["providers"]["deepseek"]["api_key_configured"] is True
    assert "secret-value" not in json.dumps(safe)
    assert safe["automatic_compaction_enabled"] is False
    assert safe["automatic_compaction_threshold_percent"] == 80


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("automatic_compaction_enabled", "yes", "must be a boolean"),
        ("automatic_compaction_threshold_percent", True, "integer from 1 to 100"),
        ("automatic_compaction_threshold_percent", 0, "integer from 1 to 100"),
        ("automatic_compaction_threshold_percent", 101, "integer from 1 to 100"),
    ],
)
def test_automatic_compaction_config_is_strict(field: str, value: object, message: str) -> None:
    config = deepcopy(DEFAULT_CONFIG)
    config[field] = value
    with pytest.raises(ConfigValidationError, match=message):
        validate_config(config)

    missing = deepcopy(DEFAULT_CONFIG)
    missing.pop(field)
    with pytest.raises(ConfigValidationError, match=message):
        validate_config(missing)


def test_blank_ui_key_preserves_persisted_secret(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    existing = deepcopy(DEFAULT_CONFIG)
    existing["providers"]["deepseek"]["api_key"] = "keep-me"
    save_config(existing, path)
    submitted = deepcopy(existing)
    submitted["providers"]["deepseek"]["api_key"] = ""

    merged = merge_config_update(submitted, path)
    merged_again = merge_config_update(public_config(merged), path)

    assert merged["providers"]["deepseek"]["api_key"] == "keep-me"
    assert merged_again["providers"]["deepseek"]["api_key"] == "keep-me"


def test_config_rejects_reasoning_for_deepseek() -> None:
    value = deepcopy(DEFAULT_CONFIG)
    value["providers"]["deepseek"]["thinking_enabled"] = True

    with pytest.raises(ConfigValidationError, match="must remain False"):
        save_config(value, Path("/unused"))


def test_config_rejects_deepseek_without_key_when_active() -> None:
    value = deepcopy(DEFAULT_CONFIG)
    value["active_provider"] = "deepseek"

    with pytest.raises(ConfigValidationError, match="requires its secret fields"):
        save_config(value, Path("/unused"))


@pytest.mark.asyncio
async def test_deepseek_adapts_json_schema_and_disables_thinking() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok":true,"label":"flash"}'}}]},
            request=request,
        )

    schema = {
        "name": "probe",
        "schema": {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "label": {"type": "string"}},
            "required": ["ok", "label"],
            "additionalProperties": False,
        },
    }
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await chat_completion_json(
            client,
            [{"role": "system", "content": "Return JSON."}],
            model="deepseek-v4-flash",
            json_schema=schema,
            provider="deepseek",
            api_base="https://api.deepseek.com",
            api_key="test-key",
            thinking_enabled=False,
        )

    assert result == {"ok": True, "label": "flash"}
    assert len(requests) == 1
    request = requests[0]
    payload = json.loads(request.content)
    assert str(request.url) == "https://api.deepseek.com/chat/completions"
    assert request.headers["authorization"] == "Bearer test-key"
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["response_format"] == {"type": "json_object"}
    assert "conforms exactly to this JSON Schema" in payload["messages"][0]["content"]


def test_local_schema_validator_rejects_extra_and_missing_fields() -> None:
    schema = {
        "type": "object",
        "properties": {"speaker": {"type": "string", "enum": ["C1", "Narrator"]}},
        "required": ["speaker"],
        "additionalProperties": False,
    }

    validate_json_schema({"speaker": "C1"}, schema)
    with pytest.raises(ValueError, match="missing required"):
        validate_json_schema({}, schema)
    with pytest.raises(ValueError, match="unexpected key"):
        validate_json_schema({"speaker": "C1", "extra": True}, schema)
    with pytest.raises(ValueError, match="must be one of"):
        validate_json_schema({"speaker": "Player"}, schema)
    with pytest.raises(ValueError, match="unsupported types"):
        validate_json_schema("value", {"type": "future-type"})
    with pytest.raises(ValueError, match="unsupported keywords"):
        validate_json_schema("value", {"type": "string", "oneOf": []})


def test_schema_validator_enforces_declared_string_and_numeric_constraints() -> None:
    validate_json_schema("C12", {"type": "string", "pattern": r"^C\d+$", "minLength": 2})
    validate_json_schema(3, {"type": "integer", "minimum": 1, "maximum": 4})
    with pytest.raises(ValueError, match="match pattern"):
        validate_json_schema("Narrator", {"type": "string", "pattern": r"^C\d+$"})
    with pytest.raises(ValueError, match="at most 4"):
        validate_json_schema(5, {"type": "integer", "maximum": 4})


def test_response_envelope_extraction_belongs_to_each_adapter() -> None:
    deepseek_response = {
        "choices": [{"message": {"content": "ready"}}],
        "usage": {
            "prompt_tokens": 13,
            "prompt_cache_hit_tokens": 8,
            "prompt_cache_miss_tokens": 5,
        },
    }
    llama_response = {
        "choices": [{"message": {"content": "ready"}}],
        "usage": {
            "prompt_tokens": 13,
            "prompt_tokens_details": {"cached_tokens": 8},
        },
    }

    deepseek = get_provider_adapter("deepseek").extract_response(deepseek_response)
    llama = get_provider_adapter("llama_cpp").extract_response(llama_response)
    assert deepseek.content == llama.content == "ready"
    assert (deepseek.cache_hit_tokens, deepseek.cache_miss_tokens) == (8, 5)
    assert (llama.cache_hit_tokens, llama.cache_miss_tokens) == (8, 5)
    assert deepseek.usage == deepseek_response["usage"]
    assert llama.usage == llama_response["usage"]
    with pytest.raises(ProviderResponseError, match="choices"):
        get_provider_adapter("deepseek").extract_response({"output": "wrong envelope"})


def test_llama_cache_control_is_adapter_specific() -> None:
    messages = [{"role": "user", "content": "hello"}]
    llama = get_provider_adapter("llama_cpp").prepare_request(messages, None, None, False)
    deepseek = get_provider_adapter("deepseek").prepare_request(messages, None, None, False)

    assert llama.extra_payload == {"cache_prompt": True}
    assert "cache_prompt" not in deepseek.extra_payload
