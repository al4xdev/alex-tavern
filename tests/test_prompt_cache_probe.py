"""Tests for the controlled provider-native prompt cache probe."""

from __future__ import annotations

from tools.prompt_cache_probe import build_probe_messages, summarize_probe


def test_probe_messages_are_repeatable_and_negative_changes_the_prefix() -> None:
    first = build_probe_messages("nonce")
    repeated = build_probe_messages("nonce")
    negative = build_probe_messages("nonce", negative=True)

    assert first == repeated
    assert first != negative
    assert first[0]["content"].splitlines()[1:] == negative[0]["content"].splitlines()[1:]
    assert len(first[0]["content"]) > 4096


def test_probe_summary_requires_positive_hit_and_smaller_negative_hit() -> None:
    entries = [
        {
            "agent": "prompt_cache_probe:warm",
            "duration_ms": 20,
            "usage": {"prompt_tokens": 100},
            "prompt_cache": {"hit_tokens": 0, "miss_tokens": 100},
            "error": None,
        },
        {
            "agent": "prompt_cache_probe:repeat-1",
            "duration_ms": 5,
            "usage": {"prompt_tokens": 100},
            "prompt_cache": {"hit_tokens": 90, "miss_tokens": 10},
            "error": None,
        },
        {
            "agent": "prompt_cache_probe:negative",
            "duration_ms": 18,
            "usage": {"prompt_tokens": 100},
            "prompt_cache": {"hit_tokens": 2, "miss_tokens": 98},
            "error": None,
        },
    ]

    result = summarize_probe(
        entries,
        provider="llama_cpp",
        model="model",
        api_base="http://localhost:8888/v1",
        session_id="cache-probe",
        prompt_sha256="abc",
        server_info={"build_info": "b9950-test"},
    )

    assert result["best_repeated_hit_tokens"] == 90
    assert result["negative_hit_tokens"] == 2
    assert result["positive_probe_verified"] is True
    assert result["negative_probe_verified"] is True
    assert result["verified"] is True
    assert result["server"] == {"build_info": "b9950-test"}


def test_probe_summary_does_not_claim_missing_cache_evidence() -> None:
    result = summarize_probe(
        [{"agent": "prompt_cache_probe:repeat-1", "usage": None, "prompt_cache": None}],
        provider="deepseek",
        model="model",
        api_base="https://api.deepseek.com",
        session_id="cache-probe",
        prompt_sha256="abc",
    )

    assert result["best_repeated_hit_tokens"] == 0
    assert result["positive_probe_verified"] is False
    assert result["negative_probe_verified"] is False
    assert result["verified"] is False
