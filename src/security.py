"""Local API origin boundary and access token (Task 19).

The control plane is unauthenticated and single-user, but reachable from a
browser. These helpers stop an arbitrary web page from driving state-changing
endpoints (config, sessions, scenarios, plugins, Experiences) or repointing a
cloud secret at an attacker ``api_base``.

Two layers, both required for an unsafe method:
- a server-generated, non-persisted access token the served document carries and
  a cross-origin page cannot read (CORS blocks reading the response/document);
- an Origin allowlist (loopback/native only) as defense in depth.

Safe methods (GET/HEAD/OPTIONS) are exempt; a short bootstrap path delivers the
token to the same-origin app.
"""

from __future__ import annotations

import secrets
from urllib.parse import urlsplit

# Methods that can change server state; only these are guarded.
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Loopback hosts always permitted as a browser origin for desktop/Docker/dev.
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})

# Native/WebView clients (file:// documents, CLI) present no Origin or "null".
_NATIVE_ORIGINS = frozenset({"", "null"})

ACCESS_TOKEN_HEADER = "x-tavern-token"


def generate_access_token() -> str:
    """A fresh per-process token; never persisted, never logged."""
    return secrets.token_urlsafe(32)


def _origin_host_allowed(origin: str) -> bool:
    parts = urlsplit(origin)
    host = parts.hostname
    return host is not None and host.lower() in _LOOPBACK_HOSTS


def is_origin_allowed(
    origin: str | None,
    host: str | None = None,
    extra_origins: frozenset[str] = frozenset(),
) -> bool:
    """Whether a request Origin may drive unsafe endpoints.

    Allowed: loopback hosts (any port), native/WebView (absent/``null``
    Origin), a true same-origin request (the Origin's authority equals the
    ``Host`` the server was reached on — covers LAN-IP and Docker access,
    where the app is served by this very server), and configured extras. A
    remote attacker page matches none of these: a browser never lets a page
    forge ``Host``, and its Origin is the attacker's own host.
    """
    if origin is None or origin in _NATIVE_ORIGINS:
        return True
    if origin in extra_origins:
        return True
    if _origin_host_allowed(origin):
        return True
    if host:
        netloc = urlsplit(origin).netloc
        if netloc and netloc.lower() == host.strip().lower():
            return True
    return False


def token_ok(provided: str | None, expected: str) -> bool:
    """Constant-time token comparison; a missing/blank token always fails."""
    if not provided or not expected:
        return False
    return secrets.compare_digest(provided, expected)


def unsafe_request_allowed(
    method: str,
    origin: str | None,
    token_header: str | None,
    expected_token: str,
    host: str | None = None,
    extra_origins: frozenset[str] = frozenset(),
) -> bool:
    """The full gate for one request: safe methods pass; unsafe methods need a
    valid token AND an allowed Origin."""
    if method.upper() not in UNSAFE_METHODS:
        return True
    return token_ok(token_header, expected_token) and is_origin_allowed(origin, host, extra_origins)
