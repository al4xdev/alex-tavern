"""DeepSeek provider adapter."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from src.llm.adapters.base import (
    ParsedResponse,
    PreparedRequest,
    extract_openai_response,
    nonnegative_int,
)


class DeepSeekAdapter:
    """DeepSeek adapter using JSON Object mode plus local schema validation."""

    name = "deepseek"
    config_defaults: dict[str, Any] = {
        "api_base": "https://api.deepseek.com",
        "api_key": "",
        "model": "deepseek-v4-flash",
        "thinking_enabled": False,
        "context_max": 524288,
        "max_tokens_narrator": 2048,
        "max_tokens_character": 1024,
        "summarizer_max_tokens": 1024,
        "llm_timeout_seconds": 60.0,
    }
    secret_fields: tuple[str, ...] = ("api_key",)
    model_required = True
    requires_secret_when_active = True
    forced_settings: dict[str, Any] = {"thinking_enabled": False}

    def completion_url(self, api_base: str) -> str:
        return f"{api_base.rstrip('/')}/chat/completions"

    def headers(self, api_key: str) -> dict[str, str] | None:
        return {"Authorization": f"Bearer {api_key}"} if api_key else None

    def prepare_request(
        self,
        messages: list[dict],
        response_format: dict[str, Any] | None,
        json_schema: dict[str, Any] | None,
        thinking_enabled: bool,
    ) -> PreparedRequest:
        prepared_messages = deepcopy(messages)
        prepared_format = response_format
        if json_schema is not None:
            schema_instruction = (
                "Return only one JSON object that conforms exactly to this JSON Schema. "
                "Do not add markdown or keys outside the schema:\n"
                f"{json.dumps(json_schema['schema'], ensure_ascii=False, separators=(',', ':'))}"
            )
            system_message = next(
                (message for message in prepared_messages if message.get("role") == "system"),
                None,
            )
            if system_message is None:
                prepared_messages.insert(0, {"role": "system", "content": schema_instruction})
            else:
                system_message["content"] = (
                    str(system_message.get("content", "")).rstrip() + "\n\n" + schema_instruction
                )
            prepared_format = {"type": "json_object"}
        return PreparedRequest(
            messages=prepared_messages,
            response_format=prepared_format,
            extra_payload={"thinking": {"type": "enabled" if thinking_enabled else "disabled"}},
        )

    def extract_response(self, response: object) -> ParsedResponse:
        parsed = extract_openai_response(response)
        usage = parsed.usage or {}
        return ParsedResponse(
            content=parsed.content,
            usage=parsed.usage,
            cache_hit_tokens=nonnegative_int(usage.get("prompt_cache_hit_tokens")),
            cache_miss_tokens=nonnegative_int(usage.get("prompt_cache_miss_tokens")),
        )
