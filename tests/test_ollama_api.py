"""Testes exploratórios da API Ollama/Gemma 4.

Uso:
    python tests/test_ollama_api.py              # todos os testes
    python tests/test_ollama_api.py --host :11434  # porta alternativa
    python tests/test_ollama_api.py --skip-chat     # pula chat/tools

Os resultados são salvos em /tmp/ollama_test_results.json.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

OLLAMA_HOST = "http://localhost:8888"
RESULTS: dict = {
    "host": OLLAMA_HOST,
    "timestamp": datetime.now().isoformat(),
    "tests": [],
}


def log_result(
    test_name: str, ok: bool, detail: str, data: dict | None = None
) -> None:
    entry = {"test": test_name, "ok": ok, "detail": detail}
    if data:
        entry["data"] = data
    RESULTS["tests"].append(entry)
    status = "\u2713" if ok else "\u2717"
    print(f"  {status} {test_name}: {detail}")


async def check_health(client: httpx.AsyncClient) -> bool:
    """Verifica se Ollama está respondendo."""
    try:
        r = await client.get("/api/tags", timeout=httpx.Timeout(5.0))
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            msg = f"OK \u2014 {len(models)} modelo(s): {models}"
            log_result("health_check", True, msg, {"models": models})
            return True
        log_result("health_check", False, f"HTTP {r.status_code}")
        return False
    except httpx.ConnectError:
        log_result("health_check", False, f"Sem conex\u00e3o com {OLLAMA_HOST}")
        return False
    except Exception as e:
        log_result("health_check", False, f"Erro: {e}")
        return False


# ── Teste 1: JSON Mode (/api/generate com format:json) ───────────────────────

JSON_SIMPLE_PROMPT = (
    "You are a narrator in a roleplay game. Return ONLY valid JSON.\n"
    "Describe the scene: a dark forest at midnight.\n"
    'Return: {"narration": "...", "mood": "...", "time_of_day": "..."}'
)


async def test_json_mode_simple(client: httpx.AsyncClient) -> None:
    """JSON mode com schema plano simples."""
    payload = {
        "model": "",
        "prompt": JSON_SIMPLE_PROMPT,
        "stream": False,
        "format": "json",
    }
    try:
        r = await client.post(
            "/api/generate", json=payload, timeout=httpx.Timeout(30.0)
        )
        body = r.json()
        parsed = json.loads(body.get("response", ""))
        required = ["narration", "mood", "time_of_day"]
        missing = [k for k in required if k not in parsed]
        if missing:
            log_result(
                "json_simple", False,
                f"Campos faltando: {missing}",
                {"response": body.get("response", "")},
            )
        else:
            log_result(
                "json_simple", True,
                "JSON v\u00e1lido com todos os campos",
                {"parsed": parsed},
            )
    except json.JSONDecodeError:
        log_result(
            "json_simple", False,
            "Resposta n\u00e3o \u00e9 JSON v\u00e1lido",
            {"raw": r.text[:500]},
        )
    except Exception as e:
        log_result("json_simple", False, f"Erro: {e}")


JSON_COMPLEX_PROMPT = (
    "You are a narrator in a roleplay game. "
    "Return ONLY valid JSON, no markdown.\n"
    "Scene: tavern. Characters present: C1 (warrior), C2 (mage).\n"
    "The player (controlling C1) just said: 'I order a drink.'\n"
    "Action: the player sits at the bar.\n\n"
    "Return a JSON object with exactly these keys:\n"
    '- "narration": a paragraph describing what happens next\n'
    '- "next_speaker": one of "C1","C2","Player","Narrator"\n'
    '- "context_for_character": string, filtered info for next speaker\n'
    '- "scene_update": object with any physical changes to the scene\n'
    '- "player_options": null or array of {index, label, description}\n'
)

REQUIRED_COMPLEX = [
    "narration", "next_speaker", "context_for_character",
    "scene_update", "player_options",
]
VALID_SPEAKERS = {"C1", "C2", "Player", "Narrator"}


async def test_json_mode_complex(client: httpx.AsyncClient) -> None:
    """JSON mode com schema aninhado (estilo Narrador)."""
    payload = {
        "model": "",
        "prompt": JSON_COMPLEX_PROMPT,
        "stream": False,
        "format": "json",
    }
    try:
        r = await client.post(
            "/api/generate", json=payload, timeout=httpx.Timeout(60.0)
        )
        body = r.json()
        parsed = json.loads(body.get("response", ""))
        missing = [k for k in REQUIRED_COMPLEX if k not in parsed]
        if missing:
            log_result(
                "json_complex", False,
                f"Campos faltando: {missing}",
                {"response": body.get("response", "")},
            )
        else:
            speaker = parsed["next_speaker"]
            speaker_ok = speaker in VALID_SPEAKERS
            detail = f"JSON aninhado v\u00e1lido, next_speaker={speaker}"
            log_result(
                "json_complex", speaker_ok, detail, {"parsed": parsed},
            )
    except json.JSONDecodeError:
        log_result(
            "json_complex", False,
            "Resposta n\u00e3o \u00e9 JSON v\u00e1lido",
            {"raw": r.text[:500]},
        )
    except Exception as e:
        log_result("json_complex", False, f"Erro: {e}")


# ── Teste 2: Tool Calling (/api/chat com tools) ──────────────────────────────

NARRATE_TOOL = {
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


async def test_tool_calling(client: httpx.AsyncClient) -> None:
    """Verifica se /api/chat com tools funciona."""
    payload = {
        "model": "",
        "messages": [
            {
                "role": "system",
                "content": "You are a narrator. Use the narrate tool.",
            },
            {
                "role": "user",
                "content": "Describe a dark forest at midnight.",
            },
        ],
        "tools": [NARRATE_TOOL],
        "stream": False,
    }
    try:
        r = await client.post(
            "/api/chat", json=payload, timeout=httpx.Timeout(30.0)
        )
        body = r.json()
        message = body.get("message", {})
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            fn = tool_calls[0].get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            log_result(
                "tool_calling", True,
                f"Tool call: {fn.get('name')}",
                {"args": args},
            )
        else:
            content = message.get("content", "")
            log_result(
                "tool_calling", False,
                f"Sem tool_calls. Content: {content[:200]}",
                {"message": message},
            )
    except Exception as e:
        log_result(
            "tool_calling", False,
            f"Erro/endpoint n\u00e3o suportado: {e}",
        )


# ── Teste 3: System Prompt ───────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Lyra, a cheerful elf bard. You speak in a poetic, "
    "musical tone. Always stay in character. Your responses are "
    "short (1-2 sentences maximum)."
)


async def test_system_prompt_chat(client: httpx.AsyncClient) -> None:
    """System prompt via /api/chat."""
    payload = {
        "model": "",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "What do you think of this dark forest?",
            },
        ],
        "stream": False,
    }
    try:
        r = await client.post(
            "/api/chat", json=payload, timeout=httpx.Timeout(30.0)
        )
        body = r.json()
        content = body.get("message", {}).get("content", "")
        if content:
            msg = f"Resposta ({len(content)} chars): {content[:200]}"
            log_result("system_prompt_chat", True, msg)
        else:
            log_result("system_prompt_chat", False, "Resposta vazia")
    except Exception as e:
        log_result("system_prompt_chat", False, f"Erro: {e}")


async def test_system_prompt_generate(client: httpx.AsyncClient) -> None:
    """System prompt via /api/generate (campo 'system')."""
    payload = {
        "model": "",
        "system": SYSTEM_PROMPT,
        "prompt": "What do you think of this dark forest?",
        "stream": False,
    }
    try:
        r = await client.post(
            "/api/generate", json=payload, timeout=httpx.Timeout(30.0)
        )
        body = r.json()
        content = body.get("response", "")
        if content:
            msg = f"Resposta ({len(content)} chars): {content[:200]}"
            log_result("system_prompt_generate", True, msg)
        else:
            log_result("system_prompt_generate", False, "Resposta vazia")
    except Exception as e:
        log_result("system_prompt_generate", False, f"Erro: {e}")


# ── Teste 4: Latência ────────────────────────────────────────────────────────

LATENCY_PROMPT = "Describe a sunset in one sentence."


async def test_latency(client: httpx.AsyncClient) -> None:
    """Mede latência com e sem format:json."""
    base = {"model": "", "prompt": LATENCY_PROMPT, "stream": False}
    timeout = httpx.Timeout(30.0)

    t0 = datetime.now()
    await client.post("/api/generate", json=base, timeout=timeout)
    t_plain = (datetime.now() - t0).total_seconds()

    t0 = datetime.now()
    await client.post(
        "/api/generate", json={**base, "format": "json"}, timeout=timeout,
    )
    t_json = (datetime.now() - t0).total_seconds()

    log_result(
        "latency", True,
        f"Plain={t_plain:.2f}s | JSON={t_json:.2f}s "
        f"| delta={t_json - t_plain:+.2f}s",
    )


# ── Main ─────────────────────────────────────────────────────────────────────


async def main(skip_chat: bool = False) -> None:
    print(f"=== Testes API Ollama \u2014 {OLLAMA_HOST} ===\n")

    async with httpx.AsyncClient(base_url=OLLAMA_HOST) as client:
        if not await check_health(client):
            print("\n\u274c Ollama n\u00e3o est\u00e1 acess\u00edvel. Abortei.")
            return

        print("\n── 1. JSON Mode ──")
        await test_json_mode_simple(client)
        await test_json_mode_complex(client)

        if not skip_chat:
            print("\n── 2. Tool Calling ──")
            await test_tool_calling(client)

        print("\n── 3. System Prompt ──")
        await test_system_prompt_chat(client)
        await test_system_prompt_generate(client)

        print("\n── 4. Lat\u00eancia ──")
        await test_latency(client)

    out = Path("/tmp/ollama_test_results.json")
    out.write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False))
    print(f"\n\U0001f4c4 Resultados salvos em {out}")

    passed = sum(1 for t in RESULTS["tests"] if t["ok"])
    total = len(RESULTS["tests"])
    print(f"\n{'=' * 40}\nResultado: {passed}/{total} testes passaram")


def _parse_host() -> str:
    host = OLLAMA_HOST
    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            host = arg.split("=", 1)[1]
        elif arg.startswith("--host"):
            continue
    return host


if __name__ == "__main__":
    skip_chat = "--skip-chat" in sys.argv
    OLLAMA_HOST = _parse_host()
    RESULTS["host"] = OLLAMA_HOST
    asyncio.run(main(skip_chat=skip_chat))
