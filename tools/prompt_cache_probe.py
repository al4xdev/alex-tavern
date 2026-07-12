#!/usr/bin/env python3
"""Run a controlled repeated-prefix probe through Alex Tavern's provider path."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from src.config import load_config
from src.llm.client import chat_completion, resolve_llm_timeout
from src.llm.debug_log import read_entries
from src.paths import CONFIG_PATH


def build_probe_messages(probe_nonce: str, *, negative: bool = False) -> list[dict[str, str]]:
    """Build a long unique prefix; the negative variant changes token zero."""
    marker = "NEGATIVE early-prefix variant" if negative else "CONTROL repeated-prefix variant"
    stable_lines = [
        f"Alex Tavern cache probe {probe_nonce} immutable reference line {index:03d}."
        for index in range(128)
    ]
    return [
        {
            "role": "system",
            "content": f"{marker}.\n" + "\n".join(stable_lines),
        },
        {"role": "user", "content": "Reply with only the word OK."},
    ]


def summarize_probe(
    entries: list[dict[str, Any]],
    *,
    provider: str,
    model: str,
    api_base: str,
    session_id: str,
    prompt_sha256: str,
    server_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a secret-free evidence object from JSONL call entries."""
    calls: list[dict[str, Any]] = []
    for entry in entries:
        agent = str(entry.get("agent", ""))
        if not agent.startswith("prompt_cache_probe:"):
            continue
        calls.append(
            {
                "phase": agent.removeprefix("prompt_cache_probe:"),
                "duration_ms": entry.get("duration_ms"),
                "usage": entry.get("usage"),
                "prompt_cache": entry.get("prompt_cache"),
                "error": entry.get("error"),
            }
        )

    repeated_hits = [
        cache.get("hit_tokens")
        for call in calls
        if str(call["phase"]).startswith("repeat-")
        and isinstance((cache := call.get("prompt_cache")), dict)
        and isinstance(cache.get("hit_tokens"), int)
    ]
    negative_hits = [
        cache.get("hit_tokens")
        for call in calls
        if call["phase"] == "negative"
        and isinstance((cache := call.get("prompt_cache")), dict)
        and isinstance(cache.get("hit_tokens"), int)
    ]
    best_repeated_hit = max(repeated_hits, default=0)
    negative_hit = max(negative_hits, default=0)
    positive_verified = best_repeated_hit > 0
    negative_verified = bool(negative_hits) and negative_hit < best_repeated_hit
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "provider": provider,
        "model": model,
        "api_base": api_base,
        "session_id": session_id,
        "prompt_sha256": prompt_sha256,
        "server": server_info,
        "calls": calls,
        "best_repeated_hit_tokens": best_repeated_hit,
        "negative_hit_tokens": negative_hit,
        "positive_probe_verified": positive_verified,
        "negative_probe_verified": negative_verified,
        "verified": positive_verified and negative_verified,
    }


async def run_probe(
    provider: str,
    config_path: Path,
    repeats: int,
    settle_seconds: float,
) -> dict[str, Any]:
    """Call one provider through the production adapter and JSONL logger."""
    config = load_config(config_path)
    provider_config = config["providers"][provider]
    nonce = uuid4().hex
    messages = build_probe_messages(nonce)
    serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))
    prompt_sha256 = hashlib.sha256(serialized.encode()).hexdigest()
    session_id = f"cache-probe-{provider}-{nonce[:8]}"
    common = {
        "model": provider_config.get("model", ""),
        "language": config.get("language", ""),
        "max_tokens": 8,
        "timeout": resolve_llm_timeout(provider_config),
        "session_id": session_id,
        "provider": provider,
        "api_base": provider_config.get("api_base", ""),
        "api_key": provider_config.get("api_key", ""),
        "thinking_enabled": provider_config.get("thinking_enabled", False),
    }
    server_info: dict[str, Any] | None = None

    async with httpx.AsyncClient() as client:
        if provider == "llama_cpp":
            api_root = str(provider_config.get("api_base", "")).rstrip("/").removesuffix("/v1")
            props_url = api_root + "/props"
            props_response = await client.get(props_url, timeout=httpx.Timeout(common["timeout"]))
            props_response.raise_for_status()
            props = props_response.json()
            defaults = props.get("default_generation_settings", {})
            model_alias = props.get("model_alias")
            server_info = {
                "build_info": props.get("build_info"),
                "model_alias": Path(model_alias).name if isinstance(model_alias, str) else None,
                "model_ftype": props.get("model_ftype"),
                "context_tokens": defaults.get("n_ctx") if isinstance(defaults, dict) else None,
                "total_slots": props.get("total_slots"),
                "endpoint_metrics": props.get("endpoint_metrics"),
                "endpoint_slots": props.get("endpoint_slots"),
            }
        await chat_completion(client, messages, agent="prompt_cache_probe:warm", **common)
        for index in range(1, repeats + 1):
            if settle_seconds:
                await asyncio.sleep(settle_seconds)
            await chat_completion(
                client,
                messages,
                agent=f"prompt_cache_probe:repeat-{index}",
                **common,
            )
        if settle_seconds:
            await asyncio.sleep(settle_seconds)
        await chat_completion(
            client,
            build_probe_messages(nonce, negative=True),
            agent="prompt_cache_probe:negative",
            **common,
        )

    entries = read_entries(session_id, repeats + 2)
    return summarize_probe(
        entries,
        provider=provider,
        model=str(provider_config.get("model", "")),
        api_base=str(provider_config.get("api_base", "")),
        session_id=session_id,
        prompt_sha256=prompt_sha256,
        server_info=server_info,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("deepseek", "llama_cpp"), required=True)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=None,
        help="Delay between calls; defaults to 2s for DeepSeek and 0s for llama.cpp.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be at least 1")
    settle_seconds = (
        args.settle_seconds
        if args.settle_seconds is not None
        else (2.0 if args.provider == "deepseek" else 0.0)
    )
    if settle_seconds < 0:
        raise SystemExit("--settle-seconds cannot be negative")
    result = asyncio.run(run_probe(args.provider, args.config, args.repeats, settle_seconds))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
