"""Shared deterministic token estimates used for budgeting and observability."""

from __future__ import annotations


def estimate_prompt_tokens(messages: list[dict]) -> int:
    prompt_chars = sum(len(str(message.get("content", ""))) for message in messages)
    return prompt_chars // 4
