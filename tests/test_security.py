"""Task 19: local API origin boundary, access token, and provider target policy."""

from __future__ import annotations

import pytest

from src.config import ConfigValidationError, validate_config
from src.llm.adapters.base import (
    ApiBasePolicyError,
    require_https_host,
    require_loopback_or_lan,
)
from src.llm.adapters.deepseek import DeepSeekAdapter
from src.llm.adapters.llama_cpp import LlamaCppAdapter
from src.security import (
    generate_access_token,
    is_origin_allowed,
    token_ok,
    unsafe_request_allowed,
)


class TestOriginAndToken:
    def test_loopback_origins_allowed_any_port(self) -> None:
        for origin in ("http://localhost:5173", "http://127.0.0.1:8000", "https://localhost"):
            assert is_origin_allowed(origin)

    def test_external_origin_rejected(self) -> None:
        assert not is_origin_allowed("http://evil.example.com")
        assert not is_origin_allowed("https://attacker.test:443")

    def test_native_absent_or_null_origin_allowed(self) -> None:
        assert is_origin_allowed(None)
        assert is_origin_allowed("null")
        assert is_origin_allowed("")

    def test_token_constant_time_compare(self) -> None:
        token = generate_access_token()
        assert token_ok(token, token)
        assert not token_ok("", token)
        assert not token_ok(None, token)
        assert not token_ok(token, "")
        assert not token_ok("wrong", token)

    def test_safe_methods_never_gated(self) -> None:
        for method in ("GET", "HEAD", "OPTIONS"):
            assert unsafe_request_allowed(method, "http://evil.com", None, "tok")

    def test_unsafe_needs_token_and_origin(self) -> None:
        tok = "secret"
        assert unsafe_request_allowed("POST", "http://localhost:3000", "secret", tok)
        assert not unsafe_request_allowed("POST", "http://localhost:3000", None, tok)  # no token
        assert not unsafe_request_allowed("POST", "http://localhost:3000", "bad", tok)  # wrong token
        assert not unsafe_request_allowed("POST", "http://evil.com", "secret", tok)  # bad origin
        assert unsafe_request_allowed("DELETE", None, "secret", tok)  # native + token

    def test_same_origin_lan_host_allowed(self) -> None:
        # The app served over a LAN IP or Docker host: Origin matches the Host
        # the server was reached on -> true same-origin, must pass.
        assert is_origin_allowed("http://192.168.0.10:8889", host="192.168.0.10:8889")
        assert unsafe_request_allowed(
            "POST", "http://192.168.0.10:8889", "secret", "secret", host="192.168.0.10:8889"
        )

    def test_cross_origin_not_legitimized_by_lan_host(self) -> None:
        # An attacker page's Origin never equals the server's Host (browsers do
        # not let pages forge Host), so the same-origin path stays closed.
        assert not is_origin_allowed("http://evil.example.com", host="192.168.0.10:8889")
        assert not unsafe_request_allowed(
            "POST", "http://evil.example.com", "secret", "secret", host="192.168.0.10:8889"
        )


class TestApiBasePolicy:
    def test_deepseek_requires_https_deepseek_host(self) -> None:
        DeepSeekAdapter().validate_api_base("https://api.deepseek.com")
        with pytest.raises(ApiBasePolicyError):
            DeepSeekAdapter().validate_api_base("http://api.deepseek.com")  # not https
        with pytest.raises(ApiBasePolicyError):
            DeepSeekAdapter().validate_api_base("https://evil.example.com")  # wrong host

    def test_llama_cpp_loopback_or_lan_only(self) -> None:
        for ok in ("http://127.0.0.1:8888", "http://192.168.0.183:8888", "http://localhost:5000", ""):
            LlamaCppAdapter().validate_api_base(ok)
        with pytest.raises(ApiBasePolicyError):
            LlamaCppAdapter().validate_api_base("https://evil.example.com")  # public host
        with pytest.raises(ApiBasePolicyError):
            LlamaCppAdapter().validate_api_base("http://8.8.8.8:80")  # public IP

    def test_llama_cpp_accepts_docker_and_private_names(self) -> None:
        # Docker service names and private-use suffixes cannot resolve on
        # public DNS; rejecting them would break container deployments at boot.
        for ok in (
            "http://llama-cpp:8080",
            "http://host.docker.internal:8888",
            "http://minha-maquina.lan:8888",
            "http://servidor.local:8888",
        ):
            LlamaCppAdapter().validate_api_base(ok)

    def test_helpers_reject_malformed(self) -> None:
        with pytest.raises(ApiBasePolicyError):
            require_https_host("not a url", ("api.deepseek.com",))
        with pytest.raises(ApiBasePolicyError):
            require_loopback_or_lan("ftp://127.0.0.1")


class TestConfigRejectsAttackerTarget:
    def _config(self, deepseek_base: str) -> dict:
        return {
            "active_provider": "deepseek",
            "language": "",
            "compaction_keep_recent_turns": 8,
            "automatic_compaction_enabled": False,
            "automatic_compaction_threshold_percent": 80,
            "providers": {
                "deepseek": {
                    "api_base": deepseek_base,
                    "model": "deepseek-v4-flash",
                    "context_max": 8192,
                    "max_tokens_narrator": 2048,
                    "max_tokens_character": 2048,
                    "summarizer_max_tokens": 512,
                    "llm_timeout_seconds": 60.0,
                    "thinking_enabled": False,
                    "api_key": "sk-secret",
                },
            },
        }

    def test_attacker_api_base_rejected(self) -> None:
        # The Task 19 threat path: repoint the cloud secret at an attacker host.
        with pytest.raises(ConfigValidationError):
            validate_config(self._config("https://attacker.example.com"))

    def test_legitimate_api_base_accepted(self) -> None:
        canonical = validate_config(self._config("https://api.deepseek.com"))
        assert canonical["providers"]["deepseek"]["api_base"] == "https://api.deepseek.com"


class TestMiddlewareBoundary:
    @pytest.fixture()
    def client(self):  # noqa: ANN202
        from fastapi.testclient import TestClient

        from src import main

        with TestClient(main.app) as client:
            yield client, main.ACCESS_TOKEN

    def test_bootstrap_returns_token(self, client) -> None:  # noqa: ANN001
        c, token = client
        res = c.get("/bootstrap")
        assert res.status_code == 200
        assert res.json()["access_token"] == token

    def test_safe_get_needs_no_token(self, client) -> None:  # noqa: ANN001
        c, _ = client
        assert c.get("/health").status_code == 200

    def test_unsafe_without_token_forbidden(self, client) -> None:  # noqa: ANN001
        c, _ = client
        res = c.put("/config", json={})
        assert res.status_code == 403

    def test_unsafe_with_token_passes_the_gate(self, client) -> None:  # noqa: ANN001
        c, token = client
        res = c.put("/config", json={}, headers={"X-Tavern-Token": token})
        assert res.status_code != 403  # reaches the handler (validation error, not the gate)

    def test_cross_origin_rejected_even_with_token(self, client) -> None:  # noqa: ANN001
        c, token = client
        res = c.put(
            "/config",
            json={},
            headers={"X-Tavern-Token": token, "Origin": "http://evil.example.com"},
        )
        assert res.status_code == 403

    def test_loopback_origin_with_token_passes(self, client) -> None:  # noqa: ANN001
        c, token = client
        res = c.put(
            "/config",
            json={},
            headers={"X-Tavern-Token": token, "Origin": "http://localhost:5173"},
        )
        assert res.status_code != 403

    def test_null_origin_cannot_read_bootstrap_via_cors(self, client) -> None:  # noqa: ANN001
        """The token-theft path: a sandboxed attacker iframe has Origin "null".

        CORS must NOT reflect it back — otherwise the iframe could read
        /bootstrap, steal the token, and defeat the whole boundary.
        """
        c, _ = client
        res = c.get("/bootstrap", headers={"Origin": "null"})
        assert res.headers.get("access-control-allow-origin") != "null"
        assert "access-control-allow-origin" not in res.headers

    def test_loopback_origin_can_read_bootstrap_via_cors(self, client) -> None:  # noqa: ANN001
        c, _ = client
        res = c.get("/bootstrap", headers={"Origin": "http://localhost:5173"})
        assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_same_origin_lan_mutation_passes(self, client) -> None:  # noqa: ANN001
        c, token = client
        res = c.put(
            "/config",
            json={},
            headers={
                "X-Tavern-Token": token,
                "Origin": "http://testserver",
                "Host": "testserver",
            },
        )
        assert res.status_code != 403
