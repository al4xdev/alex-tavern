"""Testes da API llama.cpp (OpenAI-compatible) com Gemma 4.

Uso:
    uv run python tests/test_llama_api.py
    uv run python tests/test_llama_api.py --skip-chat

Resultados salvos em /tmp/llama_test_results.json.

Resultados obtidos em 2026-07-10:
    - JSON mode (response_format: json_object): FUNCIONA, JSON sempre válido
    - JSON sem response_format: FUNCIONA, mas valores de enum menos estritos
    - Tool calling: FUNCIONA, OpenAI-compatible
    - System prompt: FUNCIONA, boa aderência a personalidade
    - Latência: ~0.8s plain, ~1.9s JSON mode
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

HOST = "http://localhost:8888"
RESULTS: dict = {
    "host": HOST,
    "server": "llama.cpp",
    "model": "supergemma4-26b-uncensored-fast-v2-Q4_K_M",
    "timestamp": datetime.now().isoformat(),
    "tests": [],
}


def log(test_name: str, ok: bool, detail: str, data: dict | None = None) -> None:
    entry = {"test": test_name, "ok": ok, "detail": detail}
    if data:
        entry["data"] = data
    RESULTS["tests"].append(entry)
    status = "\u2713" if ok else "\u2717"
    print(f"  {status} {test_name}: {detail}")


async def check_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get("/health", timeout=httpx.Timeout(5.0))
        ok: bool = r.status_code == 200
        log("health_check", ok, f"HTTP {r.status_code}: {r.text.strip()}")
        return ok
    except Exception as e:
        log("health_check", False, str(e))
        return False


# ── Teste 1: JSON mode (response_format) ─────────────────────────────────────


async def test_json_mode_simple(client: httpx.AsyncClient) -> None:
    payload = {
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON, no markdown."},
            {
                "role": "user",
                "content": ('Describe a dark forest. Return: {"narration":"...","mood":"..."}'),
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 150,
        "temperature": 0,
    }
    try:
        r = await client.post("/v1/chat/completions", json=payload, timeout=httpx.Timeout(30.0))
        content = r.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        missing = [k for k in ["narration", "mood"] if k not in parsed]
        if missing:
            log("json_simple", False, f"Missing keys: {missing}")
        else:
            log(
                "json_simple",
                True,
                f"narration={parsed['narration'][:60]}... mood={parsed['mood']}",
            )
    except (json.JSONDecodeError, KeyError) as e:
        log("json_simple", False, str(e))


async def test_json_mode_complex(client: httpx.AsyncClient) -> None:
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a narrator. Return ONLY valid JSON, no markdown.",
            },
            {
                "role": "user",
                "content": (
                    "Scene: tavern. C1 (warrior), C2 (mage). "
                    "Player (controlling C1) said: 'I order a drink.' Action: sits at bar.\n"
                    "Return JSON with keys: narration, next_speaker (C1/C2/Player/Narrator), "
                    "context_for_character, scene_update (object), "
                    "player_options (null or array of {index, label, description})"
                ),
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 400,
        "temperature": 0,
    }
    try:
        r = await client.post("/v1/chat/completions", json=payload, timeout=httpx.Timeout(60.0))
        content = r.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        required = [
            "narration",
            "next_speaker",
            "context_for_character",
            "scene_update",
            "player_options",
        ]
        missing = [k for k in required if k not in parsed]
        if missing:
            log("json_complex", False, f"Missing: {missing}")
        else:
            opts = parsed.get("player_options")
            opts_detail = f"{len(opts)} options" if isinstance(opts, list) else str(opts)
            log(
                "json_complex",
                True,
                f"All 5 keys. next_speaker={parsed['next_speaker']}, player_options={opts_detail}",
            )
    except (json.JSONDecodeError, KeyError) as e:
        log("json_complex", False, str(e))


async def test_json_no_format(client: httpx.AsyncClient) -> None:
    """JSON via prompt engineering apenas, sem response_format."""
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a narrator. Return ONLY valid JSON. No markdown.",
            },
            {
                "role": "user",
                "content": (
                    "Scene: tavern. C1 warrior, C2 mage. Player said Hello.\n"
                    "Return JSON with keys: narration, next_speaker, mood"
                ),
            },
        ],
        "max_tokens": 200,
        "temperature": 0,
    }
    try:
        r = await client.post("/v1/chat/completions", json=payload, timeout=httpx.Timeout(30.0))
        content = r.json()["choices"][0]["message"]["content"]
        clean = (
            content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        parsed = json.loads(clean)
        speaker = parsed.get("next_speaker", "")
        strict = speaker in ("C1", "C2", "Player", "Narrator")
        log(
            "json_no_format",
            True,
            f"Parses OK. next_speaker='{speaker}' (strict={strict})",
        )
    except (json.JSONDecodeError, KeyError) as e:
        log("json_no_format", False, str(e))


# ── Teste 2: Tool Calling ────────────────────────────────────────────────────


async def test_tool_calling(client: httpx.AsyncClient) -> None:
    payload = {
        "messages": [
            {"role": "system", "content": "You are a narrator. Use the narrate tool."},
            {"role": "user", "content": "Describe a dark forest at midnight."},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "narrate",
                    "description": "Narrate what happens in the scene",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "narration": {"type": "string"},
                            "next_speaker": {
                                "type": "string",
                                "enum": ["C1", "C2", "Player", "Narrator"],
                            },
                            "mood": {"type": "string"},
                        },
                        "required": ["narration", "next_speaker", "mood"],
                    },
                },
            }
        ],
        "max_tokens": 300,
        "temperature": 0,
    }
    try:
        r = await client.post("/v1/chat/completions", json=payload, timeout=httpx.Timeout(30.0))
        msg = r.json()["choices"][0]["message"]
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            fn = tool_calls[0]["function"]
            raw_args = fn["arguments"]
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            log(
                "tool_calling",
                True,
                f"Tool={fn['name']}, args keys={list(args.keys())}",
            )
        else:
            log(
                "tool_calling",
                False,
                f"No tool_calls. Content: {msg.get('content', '')[:100]}",
            )
    except Exception as e:
        log("tool_calling", False, str(e))


# ── Teste 3: System Prompt (personagem) ──────────────────────────────────────


async def test_character_personality(client: httpx.AsyncClient) -> None:
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Lyra, a cheerful elf bard. You speak in a poetic, "
                    "musical tone. Always stay in character. 1-2 sentences max. "
                    "Use **text** for internal thoughts."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Context: You are in a dark forest. "
                    "Narrator: 'Ancient oaks creak under a moonless sky.'\n"
                    "What do you say or think?"
                ),
            },
        ],
        "max_tokens": 150,
        "temperature": 0.8,
    }
    try:
        r = await client.post("/v1/chat/completions", json=payload, timeout=httpx.Timeout(30.0))
        content = r.json()["choices"][0]["message"]["content"]
        has_thought = "**" in content
        log("character_personality", has_thought, content[:200])
    except Exception as e:
        log("character_personality", False, str(e))


# ── Teste 4: Latência ────────────────────────────────────────────────────────


async def test_latency(client: httpx.AsyncClient) -> None:
    base = {
        "messages": [{"role": "user", "content": "Describe a sunset in one sentence."}],
        "max_tokens": 100,
        "temperature": 0,
    }
    timeout = httpx.Timeout(30.0)

    t0 = datetime.now()
    await client.post("/v1/chat/completions", json=base, timeout=timeout)
    t_plain = (datetime.now() - t0).total_seconds()

    t0 = datetime.now()
    await client.post(
        "/v1/chat/completions",
        json={**base, "response_format": {"type": "json_object"}},
        timeout=timeout,
    )
    t_json = (datetime.now() - t0).total_seconds()

    log(
        "latency",
        True,
        f"Plain={t_plain:.2f}s | JSON={t_json:.2f}s | delta={t_json - t_plain:+.2f}s",
    )


# ── Main ─────────────────────────────────────────────────────────────────────


async def main(skip_chat: bool = False) -> None:
    print(f"=== Testes llama.cpp API — {HOST} ===\n")
    async with httpx.AsyncClient(base_url=HOST) as client:
        if not await check_health(client):
            print("\n❌ Servidor não acessível.")
            return

        print("\n── 1. JSON Mode ──")
        await test_json_mode_simple(client)
        await test_json_mode_complex(client)
        await test_json_no_format(client)

        if not skip_chat:
            print("\n── 2. Tool Calling ──")
            await test_tool_calling(client)

        print("\n── 3. System Prompt (Personagem) ──")
        await test_character_personality(client)

        print("\n── 4. Latência ──")
        await test_latency(client)

    out = Path("/tmp/llama_test_results.json")
    out.write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False))
    print(f"\n📄 Resultados: {out}")

    passed = sum(1 for t in RESULTS["tests"] if t["ok"])
    total = len(RESULTS["tests"])
    print(f"\n{'=' * 40}\n{passed}/{total} testes passaram")


def _parse_host() -> str:
    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            return arg.split("=", 1)[1]
    return HOST


# Mark: not a pytest module (standalone script)
__test__ = False

if __name__ == "__main__":
    skip_chat = "--skip-chat" in sys.argv
    HOST = _parse_host()
    RESULTS["host"] = HOST
    asyncio.run(main(skip_chat=skip_chat))
