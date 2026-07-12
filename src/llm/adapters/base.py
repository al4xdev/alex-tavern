"""Provider adapter contract and shared response-envelope helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class PreparedRequest:
    """Provider-specific request parts consumed by the shared HTTP client."""

    messages: list[dict]
    response_format: dict[str, Any] | None
    extra_payload: dict[str, Any]


class ProviderResponseError(ValueError):
    """Raised when a provider response does not match its declared envelope."""


class ProviderAdapter(Protocol):
    """Complete contract for one server-side LLM provider integration."""

    name: str
    config_defaults: dict[str, Any]
    secret_fields: tuple[str, ...]
    model_required: bool
    requires_secret_when_active: bool
    forced_settings: dict[str, Any]

    def completion_url(self, api_base: str) -> str:
        """Return the absolute or client-relative chat completion URL."""

    def headers(self, api_key: str) -> dict[str, str] | None:
        """Return request headers without exposing credentials elsewhere."""

    def prepare_request(
        self,
        messages: list[dict],
        response_format: dict[str, Any] | None,
        json_schema: dict[str, Any] | None,
        thinking_enabled: bool,
    ) -> PreparedRequest:
        """Adapt capabilities while preserving the requested semantic contract."""

    def extract_content(self, response: object) -> str:
        """Extract generated content from this provider's response envelope."""


def extract_openai_content(response: object) -> str:
    """Strictly extract ``choices[0].message.content`` from an OpenAI envelope."""
    if not isinstance(response, dict):
        raise ProviderResponseError("Provider response must be a JSON object")
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderResponseError("Provider response must contain a non-empty choices array")
    first = choices[0]
    if not isinstance(first, dict):
        raise ProviderResponseError("Provider response choices[0] must be an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ProviderResponseError("Provider response choices[0].message must be an object")
    content = message.get("content")
    if not isinstance(content, str):
        raise ProviderResponseError("Provider response message.content must be a string")
    return content
