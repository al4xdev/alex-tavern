"""llama.cpp provider adapter."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.llm.adapters.base import (
    ParsedResponse,
    PreparedRequest,
    extract_openai_response,
    nonnegative_int,
)


class LlamaCppAdapter:
    """llama.cpp adapter with native JSON Schema grammar support."""

    name = "llama_cpp"
    config_defaults: dict[str, Any] = {
        "api_base": "http://localhost:8888/v1",
        "model": "",
        "context_max": 98304,
        "max_tokens_narrator": 4096,
        "max_tokens_character": 2048,
        "summarizer_max_tokens": 2048,
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
        return PreparedRequest(deepcopy(messages), response_format, {"cache_prompt": True})

    def extract_response(self, response: object) -> ParsedResponse:
        parsed = extract_openai_response(response)
        usage = parsed.usage or {}
        details = usage.get("prompt_tokens_details")
        hit_tokens = (
            nonnegative_int(details.get("cached_tokens")) if isinstance(details, dict) else None
        )
        prompt_tokens = nonnegative_int(usage.get("prompt_tokens"))
        miss_tokens = (
            prompt_tokens - hit_tokens
            if prompt_tokens is not None and hit_tokens is not None and prompt_tokens >= hit_tokens
            else None
        )
        return ParsedResponse(
            content=parsed.content,
            usage=parsed.usage,
            cache_hit_tokens=hit_tokens,
            cache_miss_tokens=miss_tokens,
        )
