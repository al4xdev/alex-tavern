"""A/B do Diretor: a ROUTING CONSTRAINT reescrita as cegas (AGENTS.md secao 6).

A frase antiga era:

    Do not include C1 in next_speakers this turn; they just spoke or passed.

O problema nao e a palavra "player" - ela nao aparece. E que a justificativa e
VERDADEIRA no primeiro beat e FALSA no segundo beat de uma rajada: o mesmo id
continua excluido enquanto o motivo declarado deixou de valer, e quem resolve
essa contradicao so pode concluir que aquele id tem funcao especial.

A frase nova declara o motivo dramatico, que vale em todo beat:

    Let someone other than C1 carry this beat; the scene is more interesting
    when attention moves.

REGRA PRE-REGISTRADA (escrita antes de rodar):

  A variante nova so e aceita se, sobre os MESMOS payloads reais:
    1. NUNCA escolher o personagem excluido em `next_speakers`; E
    2. produzir fila nao-vazia pelo menos tantas vezes quanto a atual.

  Qualquer escolha do excluido reprova de imediato - essa e a funcao da regra,
  e uma reescrita mais bonita que a afrouxe nao serve.

Uso: python -m tools.acceptance.director_routing_ab [runs_por_payload]
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx

from src.config import resolve_active_config

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
#  e nao um diretorio temporario: uma medicao cujos payloads
# desaparecem nao pode ser refeita por ninguem. A primeira versao apontava para
# /tmp e o SO recolheu os arquivos antes da segunda execucao.
SESSIONS = Path(".data/sessions")

# Reconhece AS DUAS redacoes. A primeira versao so reconhecia a antiga e, como o
# codigo ja tinha sido trocado, colheu zero payloads de sessoes recem-geradas -
# um passo a mais e teria medido a variante nova contra ela mesma.
CONSTRAINT_LINE = re.compile(
    r"  (?:Do not include (?P<a>\S+) in next_speakers this turn; they just spoke or passed\."
    r"|Let someone other than (?P<b>\S+) carry this beat; the scene is more interesting "
    r"when attention moves\.)"
)


def variants(text: str) -> tuple[str, str, str] | None:
    """(excluded_id, prompt com a frase antiga, prompt com a nova)."""
    match = CONSTRAINT_LINE.search(text)
    if not match:
        return None
    excluded = match.group("a") or match.group("b")
    old_line = (
        f"  Do not include {excluded} in next_speakers this turn; "
        "they just spoke or passed."
    )
    new_line = (
        f"  Let someone other than {excluded} carry this beat; the scene is "
        "more interesting when attention moves."
    )
    head, tail = text[: match.start()], text[match.end() :]
    return excluded, head + old_line + tail, head + new_line + tail


async def main() -> None:
    config = resolve_active_config(
        json.loads(Path(".data/config.json").read_text(encoding="utf-8"))
    )
    provider_key = config.get("api_key", "")
    api_base = config.get("api_base", "")

    payloads = []
    for path in sorted(SESSIONS.glob("*/debug.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("agent") != "director":
                continue
            request = record.get("request")
            if not isinstance(request, dict) or "messages" not in request:
                continue
            user = request["messages"][-1]["content"]
            built = variants(user)
            if built:
                payloads.append((path.parent.name, record["turn_number"], request, built))
            if len(payloads) >= 4:
                break
        if len(payloads) >= 4:
            break

    print(f"payloads reais com ROUTING CONSTRAINT: {len(payloads)}")
    if not payloads:
        raise SystemExit("nenhum payload — sem base para medir")

    results: dict[str, list[dict]] = {"atual": [], "nova": []}
    async with httpx.AsyncClient(
        base_url=api_base, headers={"Authorization": f"Bearer {provider_key}"}
    ) as client:
        for sid, turn, request, (excluded, old_text, new_text) in payloads:
            for arm, text in (("atual", old_text), ("nova", new_text)):
                messages = [*request["messages"][:-1], {"role": "user", "content": text}]
                for _ in range(RUNS):
                    body = {
                        "model": config.get("model", ""),
                        "messages": messages,
                        "max_tokens": request.get("max_tokens", 24576),
                        "stream": False,
                        "response_format": {"type": "json_object"},
                    }
                    parsed = None
                    for _attempt in range(3):
                        try:
                            response = await client.post(
                                "/chat/completions", json=body, timeout=300
                            )
                            response.raise_for_status()
                            raw = response.json()["choices"][0]["message"]["content"] or ""
                            start, end = raw.find("{"), raw.rfind("}")
                            if start < 0 or end <= start:
                                continue
                            parsed = json.loads(raw[start : end + 1], strict=False)
                            break
                        except Exception:  # noqa: BLE001, S112
                            continue
                    if parsed is None:
                        print(f"  ERRO {arm} {sid} t{turn}: sem JSON", flush=True)
                        continue
                    queue = list(parsed.get("next_speakers") or [])
                    row = {
                        "session": sid,
                        "turn": turn,
                        "excluded": excluded,
                        "queue": queue,
                        "violates": excluded in queue,
                        "empty": not queue,
                    }
                    results[arm].append(row)
                    flag = "  <-- ESCOLHEU O EXCLUIDO" if row["violates"] else ""
                    print(f"  {arm:5} {sid} t{turn} fila={queue}{flag}", flush=True)

    print("\n=== resultado ===")
    verdict_ok = True
    for arm in ("atual", "nova"):
        rows = results[arm]
        if not rows:
            continue
        violations = sum(1 for r in rows if r["violates"])
        empties = sum(1 for r in rows if r["empty"])
        print(
            f"{arm:5}: {len(rows)} runs | escolheu o excluido {violations}x | "
            f"fila vazia {empties}x"
        )
    atual, nova = results["atual"], results["nova"]
    if nova:
        if any(r["violates"] for r in nova):
            verdict_ok = False
            print("\nREPROVADA: a variante nova escolheu o personagem excluido.")
        nova_ok = sum(1 for r in nova if not r["empty"])
        atual_ok = sum(1 for r in atual if not r["empty"])
        if nova_ok < atual_ok:
            verdict_ok = False
            print(f"\nREPROVADA: filas nao-vazias {nova_ok} < {atual_ok}.")
    print("\nVEREDITO:", "aprovada pela regra pre-registrada" if verdict_ok else "reprovada")
    Path("director_routing_ab_result.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )


asyncio.run(main())
