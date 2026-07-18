"""Provider adapter contract and shared response-envelope helpers."""

from __future__ import annotations

import ipaddress
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit


class ApiBasePolicyError(ValueError):
    """Raised when an ``api_base`` violates an adapter's endpoint policy."""


def parse_api_base(api_base: str) -> tuple[str, str]:
    """Return ``(scheme, host)`` for a well-formed http(s) ``api_base``."""
    parts = urlsplit(api_base.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ApiBasePolicyError(f"api_base must be an http(s) URL with a host: {api_base!r}")
    return parts.scheme, parts.hostname


def require_https_host(api_base: str, allowed_hosts: tuple[str, ...]) -> None:
    """Cloud policy: HTTPS only, and the host must be on the explicit allowlist.

    This is what keeps a stored cloud secret from being sent to an
    attacker-controlled endpoint (Task 19 threat path).
    """
    scheme, host = parse_api_base(api_base)
    if scheme != "https":
        raise ApiBasePolicyError("cloud api_base must use https")
    if host.lower() not in {h.lower() for h in allowed_hosts}:
        raise ApiBasePolicyError(
            f"api_base host {host!r} is not permitted (allowed: {', '.join(allowed_hosts)})"
        )


# Name suffixes that cannot resolve on public DNS (private-use / local zones).
_PRIVATE_NAME_SUFFIXES = (".local", ".lan", ".internal", ".home.arpa")


def require_loopback_or_lan(api_base: str) -> None:
    """Local policy: loopback or private-network targets only, never a public host.

    Accepted names besides loopback/private IPs: ``localhost``, single-label
    hostnames (Docker service names, LAN hosts resolved via search domain —
    these cannot resolve on public DNS), and private-use suffixes such as
    ``.local``/``.internal`` (covers ``host.docker.internal``).
    """
    _, host = parse_api_base(api_base)
    lowered = host.lower()
    if lowered == "localhost" or lowered.endswith(_PRIVATE_NAME_SUFFIXES):
        return
    if "." not in lowered:
        return  # single-label name: Docker/LAN-only resolution
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ApiBasePolicyError(
            f"local api_base host {host!r} must be loopback, a private address, "
            "a single-label name, or a private-use suffix (.local/.internal)"
        ) from exc
    if not (address.is_loopback or address.is_private):
        raise ApiBasePolicyError(f"local api_base {host!r} must be loopback or a private address")


@dataclass(frozen=True, slots=True)
class PreparedRequest:
    """Provider-specific request parts consumed by the shared HTTP client."""

    messages: list[dict]
    response_format: dict[str, Any] | None
    extra_payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ParsedResponse:
    """Provider response content plus optional token/cache evidence."""

    content: str
    usage: dict[str, Any] | None
    cache_hit_tokens: int | None = None
    cache_miss_tokens: int | None = None


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

    def validate_api_base(self, api_base: str) -> None:
        """Enforce the adapter's endpoint policy; raise on a disallowed target.

        Cloud adapters restrict to HTTPS + an explicit host allowlist; local
        adapters restrict to loopback/LAN. Config validation calls this; an
        adapter without it falls back to a conservative http(s)+host check.
        """

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

    def extract_response(self, response: object) -> ParsedResponse:
        """Extract content and usage evidence from the provider envelope."""


def extract_openai_response(response: object) -> ParsedResponse:
    """Strictly extract content while retaining optional OpenAI-style usage."""
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
    raw_usage = response.get("usage")
    usage = deepcopy(raw_usage) if isinstance(raw_usage, dict) else None
    return ParsedResponse(content=content, usage=usage)


def nonnegative_int(value: object) -> int | None:
    """Return a non-negative integer metric without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
