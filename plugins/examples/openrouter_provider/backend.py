"""OpenRouter provider plugin entrypoint."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.llm.adapters import register_provider_adapter
from src.llm.adapters.base import ParsedResponse, PreparedRequest, extract_openai_response


class OpenRouterAdapter:
    name = "openrouter"
    config_defaults: dict[str, Any] = {
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": "",
        "model": "deepseek/deepseek-chat-v3-0324",
        "thinking_enabled": False,
        "context_max": 131072,
        "max_tokens_narrator": 4096,
        "max_tokens_character": 2048,
        "summarizer_max_tokens": 2048,
        "llm_timeout_seconds": 90.0,
    }
    secret_fields: tuple[str, ...] = ("api_key",)
    model_required = True
    requires_secret_when_active = True
    forced_settings: dict[str, Any] = {"thinking_enabled": False}

    def completion_url(self, api_base: str) -> str:
        return f"{api_base.rstrip('/')}/chat/completions"

    def headers(self, api_key: str) -> dict[str, str] | None:
        if not api_key:
            return None
        return {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/al4xdev/alex-tavern",
            "X-Title": "Alex Tavern",
        }

    def prepare_request(
        self,
        messages: list[dict],
        response_format: dict[str, Any] | None,
        json_schema: dict[str, Any] | None,
        thinking_enabled: bool,
    ) -> PreparedRequest:
        return PreparedRequest(deepcopy(messages), response_format, {})

    def extract_response(self, response: object) -> ParsedResponse:
        return extract_openai_response(response)


def setup(context) -> None:  # noqa: ANN001
    register_provider_adapter(OpenRouterAdapter())
    context.contribute(
        "providers",
        {"id": "openrouter", "label": "OpenRouter", "transport": "openai-compatible"},
    )
    context.event("provider_registered", provider="openrouter")
