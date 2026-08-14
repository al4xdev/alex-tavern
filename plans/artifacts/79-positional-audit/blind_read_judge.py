"""Task 79: room-vs-position judged by a blind reader of the prose.

Rule pre-registered in `.plan/tasks/79-blocking-as-durable-state.md` under "The
structural test, second attempt", before this ran.

The first structural attempt - the Director's own `witness_ids` - failed its
validity check: the median witness list is 95% of the cast, so it cannot
discriminate. This is the remaining independent signal the owner named: "the
narration either describes a room change or does not".

BLINDNESS is the whole design. The judge receives the narration of the turn and
the moving character's name. It never receives: the destination string, the
origin, the zone graph, the string rule's verdict, which stratum the case came
from, or any hint that a comparison exists. It therefore cannot reproduce the
naming failure it is being used to check for.

Sample: 40 moves, stratified 20/20 on the corrected string rule's verdict,
systematic within each stratum, shuffled before dispatch with a fixed seed.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import random
import sys
from dataclasses import dataclass, field

sys.path.insert(0, "/home/alex/git/my/alex-tavern")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import httpx  # noqa: E402

from classify_positional import distinct_sessions  # noqa: E402
from find_reproducible_payloads import is_positional, positions_by_turn  # noqa: E402

OUT = pathlib.Path(__file__).parent / "blind_read"
PER_STRATUM = 20
SEED = 11

PROMPT = """Voce recebe um trecho de narracao de uma cena de roleplay e o nome de um personagem.

Responda APENAS com um objeto JSON:
{"verdict": "MUDOU_DE_LUGAR" | "REPOSICIONOU_NO_MESMO_LUGAR" | "NAO_DA_PARA_SABER",
 "evidence": "a frase exata da narracao que sustenta sua resposta, ou vazio",
 "confidence": "alta" | "media" | "baixa"}

Criterio:
- MUDOU_DE_LUGAR: a narracao mostra o personagem indo para outro ambiente (outra
  sala, outro corredor, o patio, fora do recinto).
- REPOSICIONOU_NO_MESMO_LUGAR: a narracao mostra o personagem mudando de posicao
  dentro do ambiente onde ja estava (aproximar-se de algo, recuar, ficar ao lado
  de alguem, atravessar o salao).
- NAO_DA_PARA_SABER: a narracao nao diz o suficiente sobre este personagem.

Nao adivinhe. NAO_DA_PARA_SABER e uma resposta correta e esperada quando o texto
nao mostra o movimento deste personagem.

PERSONAGEM: {character}

NARRACAO:
{narration}
"""


@dataclass
class Case:
    session: str
    turn: int
    cid: str
    character: str
    narration: str
    string_says_position: bool
    verdict: str = ""
    evidence: str = ""
    confidence: str = ""
    error: str = ""
    raw: dict = field(default_factory=dict)


def collect() -> tuple[list[Case], list[Case]]:
    pos_cases: list[Case] = []
    room_cases: list[Case] = []
    for sid, base in sorted(distinct_sessions().items()):
        positions = positions_by_turn(base)
        state = json.loads((base / "state.json").read_text(encoding="utf-8"))
        names = {cid: c.get("name") or cid for cid, c in (state.get("characters") or {}).items()}
        narration: dict[int, list[str]] = {}
        for record in state.get("history", []):
            if record.get("content_type") == "narration" and record.get("turn_number") is not None:
                narration.setdefault(int(record["turn_number"]), []).append(
                    str(record.get("content") or "")
                )
        debug = base / "debug.jsonl"
        if not debug.exists():
            continue
        with debug.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("agent") != "director":
                    continue
                try:
                    parsed = json.loads(record.get("response") or "{}")
                except json.JSONDecodeError:
                    continue
                turn = int(record["turn_number"])
                text = "\n\n".join(narration.get(turn, []))
                if len(text) < 200:
                    continue
                moves = parsed.get("zone_moves") or {}
                if not isinstance(moves, dict):
                    continue
                prior = positions.get(turn - 1, {})
                for cid, dest in moves.items():
                    origin = prior.get(str(cid))
                    if not origin:
                        continue
                    case = Case(
                        sid, turn, str(cid), names.get(str(cid), str(cid)), text,
                        is_positional(str(dest), origin),
                    )
                    (pos_cases if case.string_says_position else room_cases).append(case)
    return pos_cases, room_cases


def sample(cases: list[Case], want: int) -> list[Case]:
    step = max(1, len(cases) // want)
    return cases[::step][:want]


async def judge(client: httpx.AsyncClient, cfg: dict, case: Case) -> Case:
    body = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "user",
                "content": PROMPT.replace("{character}", case.character).replace(
                    "{narration}", case.narration[:4000]
                ),
            }
        ],
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }
    try:
        response = await client.post(
            f"{cfg['api_base']}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json=body,
            timeout=300.0,
        )
        response.raise_for_status()
        parsed = json.loads(response.json()["choices"][0]["message"]["content"])
    except Exception as exc:  # noqa: BLE001
        case.error = f"{type(exc).__name__}: {exc}"
        return case
    case.raw = parsed
    case.verdict = str(parsed.get("verdict") or "")
    case.evidence = str(parsed.get("evidence") or "")
    case.confidence = str(parsed.get("confidence") or "")
    return case


async def main() -> None:
    cfg = json.loads(
        pathlib.Path("/home/alex/git/my/alex-tavern/.data/config.json").read_text(encoding="utf-8")
    )["providers"]["deepseek"]
    pos_cases, room_cases = collect()
    print(f"population: string=POSITION {len(pos_cases)}, string=ROOM {len(room_cases)}")
    cases = sample(pos_cases, PER_STRATUM) + sample(room_cases, PER_STRATUM)
    random.Random(SEED).shuffle(cases)
    print(f"dispatching {len(cases)} blind reads\n", flush=True)

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(5)

        async def guarded(case: Case) -> Case:
            async with semaphore:
                out = await judge(client, cfg, case)
                print(f"  {out.session} T{out.turn} {out.character[:18]:18} -> "
                      f"{out.verdict or out.error}", flush=True)
                return out

        done = await asyncio.gather(*(guarded(c) for c in cases))

    determinable = [c for c in done if c.verdict in ("MUDOU_DE_LUGAR", "REPOSICIONOU_NO_MESMO_LUGAR")]
    undet = [c for c in done if c.verdict == "NAO_DA_PARA_SABER"]
    failed = [c for c in done if c.error]

    print(f"\n=== RESULT ===")
    print(f"  dispatched      {len(done)}")
    print(f"  failed          {len(failed)}")
    print(f"  NAO_DA_PARA_SABER {len(undet)}  ({len(undet) / max(1, len(done)):.0%})")
    print(f"  determinable    {len(determinable)}")

    if determinable:
        agree = sum(
            1 for c in determinable
            if (c.verdict == "REPOSICIONOU_NO_MESMO_LUGAR") == c.string_says_position
        )
        print(f"\n  agreement with the corrected string rule: {agree}/{len(determinable)} "
              f"= {agree / len(determinable):.1%}")
        print("\n  confusion:")
        for jv in ("REPOSICIONOU_NO_MESMO_LUGAR", "MUDOU_DE_LUGAR"):
            for sv in (True, False):
                n = sum(1 for c in determinable if c.verdict == jv and c.string_says_position == sv)
                print(f"    judge={jv[:12]:12}  string={'POS' if sv else 'ROOM'}: {n}")

        print("\n=== DISAGREEMENTS (read these) ===")
        for c in determinable:
            if (c.verdict == "REPOSICIONOU_NO_MESMO_LUGAR") != c.string_says_position:
                print(f"\n  [{c.session} T{c.turn} {c.character}] judge={c.verdict} "
                      f"string={'POSITION' if c.string_says_position else 'ROOM'} ({c.confidence})")
                print(f"     evidence: {c.evidence[:220]}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps([{k: v for k, v in c.__dict__.items() if k != "narration"} for c in done],
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
