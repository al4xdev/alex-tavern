"""A/B: o contexto do drive/watcher deve rotular por ID ou por nome?

`recent_event_lines(resolve_names=False)` alimenta `stalled_scene_context` (drive)
e o watcher. O mesmo elenco chega ao prompt sob DOIS sistemas de rótulo — `C2:`
para os personagens e `Thorn:` para o controlado, porque `speaker_label` só
traduz o marcador `Player`. Essa é a mesma forma do defeito que corrompeu 11
resumos (o summarizer leu `C2` como nome próprio e inventou uma pessoa).

O `event` devolvido aqui vira o `narrator_hint` do Diretor, que é instruído a
materializá-lo. Um ID cru no seed é, portanto, texto que o sistema empurra na
direção da narração.

REGRA PRE-REGISTRADA (escrita antes de rodar):

  O braco NOMES vence se, somadas todas as repeticoes:
    1. produzir ESTRITAMENTE MENOS seeds contendo um id cru (`\\bC\\d\\b`); E
    2. nao piorar a ancoragem: a taxa de seeds cujo `source_thread` cita algo
       literalmente presente no contexto fornecido nao pode cair.

  Empate no criterio 1, ou queda no criterio 2, significa que a mudanca NAO se
  justifica e o default fica como esta (AGENTS.md §6: prompt validado nao muda
  sem evidencia medida).
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import unicodedata
from pathlib import Path

import httpx

from src.drive import build_event_seed_messages, build_event_seed_schema  # noqa: E402
from src.llm.client import call_agent  # noqa: E402
from src.models import dict_to_game_state  # noqa: E402
from src.prompting import recent_event_lines, stalled_scene_context  # noqa: E402

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ID_RE = re.compile(r"\bC\d\b")


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def context_lines(game, *, resolve: bool) -> list[str]:
    """`stalled_scene_context` com o unico parametro em teste trocado."""
    lines = stalled_scene_context(game)
    if not resolve:
        return lines
    current = recent_event_lines(game)
    fixed = recent_event_lines(game, resolve_names=True)
    out = []
    for line in lines:
        out.append(fixed[current.index(line)] if line in current else line)
    return out


def anchored(source_thread: str, context: str) -> bool:
    """O `source_thread` cita algo que estava mesmo no contexto?

    Aproximacao deliberadamente grosseira e IGUAL nos dois bracos: uma janela de
    4 palavras do thread aparece no contexto. Serve para comparar bracos, nao
    para julgar qualidade em absoluto.
    """
    words = norm(source_thread).split()
    haystack = norm(context)
    return any(
        " ".join(words[i : i + 4]) in haystack for i in range(max(0, len(words) - 3))
    )


async def main() -> None:
    # `call_agent` le a config ACHATADA (model/api_base/api_key/thinking_enabled
    # no topo), que e o que o servidor monta no boot. Passar o JSON cru faz a URL
    # sair relativa e toda chamada falhar.
    from src.config import resolve_active_config

    config = resolve_active_config(json.loads(Path(".data/config.json").read_text(encoding="utf-8")))

    games = []
    for path in sorted(Path(".data/sessions").glob("*/state.json")):
        try:
            game = dict_to_game_state(json.loads(path.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001 — sessoes de schema antigo
            continue
        if len(game.history) >= 4:
            games.append((path.parent.name, game))
    print(f"estados reais utilizaveis: {len(games)}")

    schema = build_event_seed_schema()
    results: dict[str, list[dict]] = {"ids": [], "names": []}

    async with httpx.AsyncClient() as client:
        for sid, game in games:
            base = build_event_seed_messages(game)
            for arm, resolve in (("ids", False), ("names", True)):
                context = "\n".join(context_lines(game, resolve=resolve))
                # So o bloco de usuario muda; o system e o de producao, intacto.
                messages = [base[0], {"role": "user", "content": context}]
                for _ in range(REPS):
                    try:
                        # O caminho de PRODUCAO. Uma versao anterior montava o
                        # POST na mao e omitia `thinking_enabled: false`, entao o
                        # modelo gastava o budget inteiro raciocinando e devolvia
                        # conteudo vazio - erro do arnes, lido como ruido do braco.
                        result = await call_agent(
                            client,
                            config,
                            messages,
                            agent="drive:event_seed",
                            json_schema=schema,
                            max_tokens=256,
                            session_id=f"ab-{arm}-{sid}",
                            turn_number=0,
                        )
                    except Exception as exc:  # noqa: BLE001
                        print(f"  ERRO {arm} {sid}: {exc}", flush=True)
                        continue
                    event = str(result.get("event", ""))
                    thread = str(result.get("source_thread", ""))
                    row = {
                        "session": sid,
                        "ids_in_event": len(ID_RE.findall(event)),
                        "ids_in_thread": len(ID_RE.findall(thread)),
                        "anchored": anchored(thread, context),
                        "event": event,
                        "thread": thread,
                    }
                    results[arm].append(row)
                    print(
                        f"  {arm:5} {sid} ids_evento={row['ids_in_event']} "
                        f"ancorado={row['anchored']}",
                        flush=True,
                    )

    print("\n=== resultado ===")
    for arm in ("ids", "names"):
        rows = results[arm]
        if not rows:
            continue
        dirty = sum(1 for r in rows if r["ids_in_event"] or r["ids_in_thread"])
        anchor = sum(1 for r in rows if r["anchored"])
        print(
            f"{arm:5}: {dirty}/{len(rows)} seeds com id cru | "
            f"ancorados {anchor}/{len(rows)} ({100 * anchor / len(rows):.0f}%)"
        )
    Path("/tmp/claude-1000/-home-alex-git-my-alex-tavern/"
         "72a242b2-354f-4142-86b8-0945a83e0675/scratchpad/drive_ab_result.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )


asyncio.run(main())
