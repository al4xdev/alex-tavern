"""llama.cpp provider adapter."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.llm.adapters.base import PreparedRequest, extract_openai_content


class LlamaCppAdapter:
    """llama.cpp adapter with native JSON Schema grammar support."""

    name = "llama_cpp"
    config_defaults: dict[str, Any] = {
        "api_base": "http://localhost:8888/v1",
        "model": "",
        "context_max": 98304,
        "max_tokens_narrator": 2048,
        "max_tokens_character": 1024,
        "summarizer_max_tokens": 1024,
        "llm_timeout_seconds": 60.0,
    }
    secret_fields: tuple[str, ...] = ()
    model_required = False
    requires_secret_when_active = False
    forced_settings: dict[str, Any] = {}

    def completion_url(self, api_base: str) -> str:
        return f"{api_base.rstrip('/')}/chat/completions" if api_base else "/v1/chat/completions"

    def headers(self, api_key: str) -> dict[str, str] | None:  # noqa: ARG002
        return None

    def prepare_request(
        self,
        messages: list[dict],
        response_format: dict[str, Any] | None,
        json_schema: dict[str, Any] | None,  # noqa: ARG002
        thinking_enabled: bool,  # noqa: ARG002
    ) -> PreparedRequest:
        return PreparedRequest(deepcopy(messages), response_format, {})

    def extract_content(self, response: object) -> str:
        return extract_openai_content(response)
