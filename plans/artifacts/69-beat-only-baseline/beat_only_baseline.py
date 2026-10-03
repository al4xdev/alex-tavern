"""Frozen synthetic beat-only diagnostic using production planning builders."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx

from src.llm.adapters.deepseek import DeepSeekAdapter
from src.llm.client import chat_completion
from src.llm.schema import validate_json_schema
from src.models import (
    GameState,
    Player,
    Roteiro,
    RoteiroAct,
    RoteiroBeat,
    Scene,
    TurnRecord,
    deepcopy_scene,
)
from src.roteiro import build_next_beat_messages, build_next_beat_schema, evaluate_roteiro
from tests.factories import make_character

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
RUNS = HERE / "runs"
PREREG = HERE / "PREREGISTRATION.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source_hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        PREREG,
        ROOT / "src/roteiro.py",
        ROOT / "src/prompting.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def config() -> dict[str, Any]:
    canonical = json.loads((ROOT / ".data/config.json").read_text())
    cfg = {**canonical["providers"]["deepseek"], "language": canonical["language"]}
    DeepSeekAdapter().validate_api_base(cfg["api_base"])
    return cfg


def fixtures() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = [
        {
            "id": "abandoned_room",
            "before": "Cofre do museu",
            "now": "Acampamento no cânion",
            "premise": "Iara e Bento procuram o mapa que permite chegar ao observatório.",
            "act": ("Proteger o mapa no cofre antes que os guardas entrem pela porta de serviço."),
            "act_exit": "Os guardas desistem da revista no cofre.",
            "next_act": "Levar o mapa até o observatório.",
            "intent": (
                "A aproximação dos guardas à porta de serviço pressiona quem protege o mapa."
            ),
            "anchors": ["porta de serviço", "lanterna dos guardas"],
            "question": "Podemos achar outro caminho até o observatório?",
            "accepted": [
                (
                    "Iara e Bento tocaram o mapa; um transporte os levou do cofre ao "
                    "acampamento distante no cânion."
                ),
                (
                    "O transporte terminou. Ambos estão no cânion com o mapa; a porta e os "
                    "guardas ficaram no museu, sem ligação aberta."
                ),
            ],
            "facts": {"mapa": "com Iara", "ligacao_museu": "nenhuma passagem aberta"},
        },
        {
            "id": "broken_bridge",
            "before": "Ponte da garganta",
            "now": "Margem oeste da garganta",
            "premise": "Iara e Bento escoltam uma mensagem destinada ao observatório.",
            "act": "Manter a ponte disponível para que o mensageiro alcance a outra margem.",
            "act_exit": "O mensageiro chega à margem leste.",
            "next_act": "Proteger a mensagem durante a subida ao observatório.",
            "intent": ("Um peso crescente nas cordas ameaça a passagem do mensageiro pela ponte."),
            "anchors": ["cordas tensionadas", "mensageiro na ponte"],
            "question": "Existe outra travessia por aqui?",
            "accepted": [
                (
                    "A ponte inteira se rompeu e caiu na garganta; nenhuma parte passável "
                    "permaneceu entre as margens."
                ),
                (
                    "Iara e Bento ficaram na margem oeste. O mensageiro ainda não "
                    "atravessou; nenhum conserto nem outra rota foi aberto."
                ),
            ],
            "facts": {"ponte": "destruída e intransitável", "mensageiro": "margem oeste"},
        },
        {
            "id": "within_room",
            "before": "Sala do conselho",
            "now": "Sala do conselho",
            "premise": "Iara e Bento buscam acesso ao arquivo para consultar um mapa.",
            "act": "Negociar uma autorização de acesso ao arquivo com o conselho.",
            "act_exit": "O conselho concede ou recusa formalmente o acesso ao arquivo.",
            "next_act": "Lidar com a consequência pública da decisão do conselho.",
            "intent": "Um prazo de consulta pressiona a negociação com o conselho.",
            "anchors": ["relógio de bronze", "registro de autorização"],
            "question": "Quanto tempo resta para apresentar o pedido?",
            "accepted": [
                (
                    "Iara e Bento saíram de perto da janela e passaram para o outro lado da "
                    "mesa, na mesma sala do conselho."
                ),
                (
                    "A negociação continua sem decisão. Ninguém saiu da sala e nenhum "
                    "conselheiro concedeu ou recusou o acesso."
                ),
            ],
            "facts": {"autorizacao": "ainda não decidida"},
            "required_act_completed": False,
        },
        {
            "id": "continuing_journey",
            "before": "Trilha da serra",
            "now": "Torre de vigia",
            "premise": "Iara e Bento precisam levar um aviso ao observatório da montanha.",
            "act": "Levar o aviso ao observatório antes do fechamento de sua recepção.",
            "act_exit": "O observatório recebe o aviso.",
            "next_act": "A resposta do observatório altera as condições na serra.",
            "intent": "O fechamento da recepção do observatório se aproxima durante a viagem.",
            "anchors": ["campainha da recepção", "registro da entrega"],
            "question": "Qual caminho segue daqui até o observatório?",
            "accepted": [
                (
                    "Iara e Bento chegaram à torre de vigia, uma parada intermediária da "
                    "trilha que não é o observatório."
                ),
                (
                    "O aviso continua com Bento, ainda não entregue. Ambos pretendem seguir "
                    "viagem; ninguém decidiu abandoná-lo."
                ),
            ],
            "facts": {"aviso": "com Bento, não entregue", "observatorio": "destino ainda distante"},
            "required_act_completed": False,
        },
        {
            "id": "completed_escape",
            "before": "Câmara inundada",
            "now": "Terraço exterior",
            "premise": (
                "Iara e Bento precisam tirar uma lente de sinalização da câmara e levá-la à torre."
            ),
            "act": "Escapar da câmara inundada antes que a água alcance o teto.",
            "act_exit": "Iara e Bento estão ambos fora da câmara.",
            "next_act": "Conseguir levar a lente de sinalização até a torre.",
            "intent": "A subida da água pressiona a saída pela escotilha.",
            "anchors": ["escotilha de bronze", "água no teto"],
            "question": "Como chegamos à torre levando a lente?",
            "accepted": [
                (
                    "Iara e Bento saíram da câmara pela escotilha e chegaram ao terraço "
                    "exterior com a lente de sinalização."
                ),
                (
                    "Ambos estão fora da câmara. A escotilha foi selada atrás deles; ainda "
                    "não chegaram à torre."
                ),
            ],
            "facts": {"escotilha": "selada atrás deles", "lente": "no terraço com a dupla"},
            "required_act_completed": True,
        },
        {
            "id": "split_party",
            "before": "Margem do rio",
            "now": "Margem do rio",
            "premise": (
                "Iara e Bento tentam lançar uma jangada com o aviso destinado ao observatório."
            ),
            "act": "Preparar o lançamento da jangada na margem do rio.",
            "act_exit": "A jangada está na água e apta a seguir pelo rio.",
            "next_act": "Enfrentar as condições do rio durante o transporte do aviso.",
            "intent": "A subida do rio ameaça a preparação da jangada antes de seu lançamento.",
            "anchors": ["jangada na água", "corda de reboque"],
            "question": "Bento conseguirá encontrar uma forma de avisar daqui a pouco?",
            "accepted": [
                (
                    "Bento foi levado à torre de vigia distante por um transporte que se "
                    "encerrou. Iara continuou na margem do rio."
                ),
                (
                    "Bento está na torre, Iara na margem. Não há canal de comunicação "
                    "aberto; a jangada ainda está seca na margem."
                ),
            ],
            "facts": {"jangada": "seca na margem", "comunicacao": "sem canal aberto"},
        },
    ]

    portal = {
        "before": "Salão do portal",
        "now": "Salão do portal",
        "premise": "Iara e Bento devem fechar o portal e levar o mapa à torre.",
        "act": "Fechar o portal do salão antes que a passagem se alargue.",
        "act_exit": "O portal está fechado.",
        "next_act": "Levar o mapa até a torre.",
        "intent": "A passagem aberta se alarga enquanto as runas perdem estabilidade.",
        "anchors": ["portal", "runas"],
        "question": "O que podemos fazer agora?",
    }
    for case_id, now, accepted, status, completed in (
        (
            "portal_attempt",
            "Salão do portal",
            [
                "Iara tentou encostar o mapa nas runas para fechar o portal.",
                "A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam.",
            ],
            "aberto",
            False,
        ),
        (
            "portal_closed",
            "Salão do portal",
            [
                "A passagem do portal se fechou por completo; as runas apagaram.",
                "Iara e Bento continuam no salão com o mapa. Não existe passagem aberta agora.",
            ],
            "fechado",
            True,
        ),
        (
            "portal_left",
            "Acampamento no cânion",
            [
                (
                    "Iara e Bento atravessaram a passagem até o cânion; o portal se fechou e "
                    "as runas apagaram depois."
                ),
                (
                    "Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma "
                    "passagem de volta está aberta."
                ),
            ],
            "fechado",
            True,
        ),
    ):
        cases.append(
            {
                **portal,
                "id": case_id,
                "now": now,
                "accepted": accepted,
                "facts": {"portal": status},
                "required_act_completed": completed,
            }
        )
    return cases


def game_for(case: dict[str, Any], late: bool) -> GameState:
    cast = {
        "C1": make_character("Iara", personality="Cartógrafa curiosa e cuidadosa."),
        "C2": make_character("Bento", personality="Guia pragmático e atento aos caminhos."),
    }
    scene = Scene(
        location=case["now"],
        time_of_day="tarde",
        present_characters=list(cast),
        physical_facts=case["facts"],
        positions={
            "C1": case["now"],
            "C2": "Torre de vigia" if case["id"] == "split_party" else case["now"],
        },
    )
    initial_scene = Scene(
        location=case["before"],
        time_of_day="tarde",
        present_characters=list(cast),
        physical_facts={},
    )
    history = [
        TurnRecord(
            1,
            "C2",
            "Precisamos avaliar o caminho antes de prosseguir.",
            "speech",
            deepcopy_scene(initial_scene),
        )
    ]
    history.extend(
        TurnRecord(2, "Narrator", text, "narration", deepcopy_scene(initial_scene))
        for text in case["accepted"]
    )
    if late:
        history.append(TurnRecord(3, "Player", case["question"], "speech", deepcopy_scene(scene)))
    assert all(len(record.content) <= 160 for record in history), (
        "Fixture history would be truncated"
    )
    return GameState(
        session_id="",
        characters=cast,
        player=Player(controlled_character_id="C1"),
        scene=scene,
        history=history,
        narrator_directives="Fantasia de aventura. Texto em português brasileiro.",
        roteiro=Roteiro(
            premise=case["premise"],
            acts=[
                RoteiroAct("a1", case["act"], case["act_exit"]),
                RoteiroAct(
                    "a2", case["next_act"], "A consequência desse objetivo foi estabelecida."
                ),
            ],
            beat=RoteiroBeat("a1-b1", case["intent"], ["C2"], case["anchors"], case["act_exit"], 6),
            beat_started_turn=1,
            beat_actions_elapsed=3 if late else 2,
        ),
    )


async def captured_request(
    game: GameState, reason: str, scope: str, cfg: dict[str, Any]
) -> dict[str, Any]:
    captured: list[dict[str, Any]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    assert game.roteiro is not None
    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        await chat_completion(
            client,
            build_next_beat_messages(game, game.roteiro, reason, scope),
            provider="deepseek",
            model=cfg["model"],
            language=cfg["language"],
            api_base=cfg["api_base"],
            api_key="",
            max_tokens=1024,
            json_schema=build_next_beat_schema(scope),
        )
    assert len(captured) == 1
    return captured[0]


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    cfg = config()
    cases = []
    for fixture in fixtures():
        early, late = game_for(fixture, False), game_for(fixture, True)
        assert early.roteiro is not None and late.roteiro is not None
        first = evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        later = evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        decision = first if first.action else later
        selected = early if first.action else late
        scope = "act" if decision.action == "replan_act" else "beat"
        cases.append(
            {
                "fixture": fixture,
                "early_decision": asdict(first),
                "later_decision": asdict(later),
                "selected_stage": "immediate" if first.action else "later",
                "canonical_scene": asdict(late.scene),
                "scope": scope,
                "schema": build_next_beat_schema(scope)["schema"],
                "request": await captured_request(selected, decision.reason, scope, cfg)
                if decision.action
                else None,
            }
        )
    write(
        MANIFEST,
        {
            "hashes": source_hashes(),
            "model": cfg["model"],
            "language": cfg["language"],
            "api_base": cfg["api_base"],
            "repeats": 4,
            "cases": cases,
        },
    )
    print(
        json.dumps(
            {
                "prepared": len(cases),
                "decisions": [
                    {
                        "case": row["fixture"]["id"],
                        "early": row["early_decision"]["reason"],
                        "later": row["later_decision"]["reason"],
                    }
                    for row in cases
                ],
            }
        )
    )


async def call_one(case: dict[str, Any], repeat: int, cfg: dict[str, Any]) -> None:
    label = f"{case['fixture']['id']}-{repeat}"
    req, raw = RUNS / f"{label}.request.json", RUNS / f"{label}.raw.json"
    write(req, case["request"])
    key = cfg["api_key"]
    if any(char in key for char in '\r\n\\"'):
        raise ValueError("Unsafe curl-config secret character")
    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-q",
        "--silent",
        "--show-error",
        "--max-time",
        str(cfg["llm_timeout_seconds"]),
        "--config",
        "-",
        "--request",
        "POST",
        "--header",
        "Content-Type: application/json",
        "--data-binary",
        f"@{req}",
        "--output",
        str(raw),
        "--write-out",
        "%{http_code}",
        DeepSeekAdapter().completion_url(cfg["api_base"]),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    started = time.monotonic()
    stdout, stderr = await proc.communicate(f'header = "Authorization: Bearer {key}"\n'.encode())
    result: dict[str, Any] = {
        "case": case["fixture"]["id"],
        "repeat": repeat,
        "valid": False,
        "http_status": stdout.decode().strip(),
        "exit_code": proc.returncode,
        "duration_ms": round(1000 * (time.monotonic() - started)),
        "stderr": stderr.decode().replace(key, "[REDACTED]"),
        "request_sha256": digest(req),
    }
    try:
        envelope = json.loads(raw.read_text())
        result["response_id"] = envelope.get("id")
        if result["http_status"] != "200" or proc.returncode:
            raise ValueError("HTTP or transport failure")
        output = json.loads(envelope["choices"][0]["message"]["content"])
        result["output"] = output
        validate_json_schema(output, case["schema"])
        result["valid"] = True
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    write(RUNS / f"{label}.result.json", result)


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    cfg = config()
    if RUNS.exists() or manifest["hashes"] != source_hashes():
        raise RuntimeError("Preserve existing runs; source/protocol changed")
    if (
        any(manifest[key] != cfg[key] for key in ("model", "language", "api_base"))
        or not cfg["api_key"]
    ):
        raise RuntimeError("Frozen provider configuration changed or secret missing")
    RUNS.mkdir()
    write(RUNS / "run.json", {"manifest_sha256": digest(MANIFEST), "started_unix": time.time()})
    jobs = [
        (case, repeat) for case in manifest["cases"] if case["request"] for repeat in range(1, 5)
    ]
    random.Random(6902).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    print(f"Completed {len(jobs)} frozen calls")


def grade() -> None:
    manifest = json.loads(MANIFEST.read_text())
    results = [json.loads(path.read_text()) for path in sorted(RUNS.glob("*.result.json"))]
    summary = []
    for case in manifest["cases"]:
        case_id = case["fixture"]["id"]
        rows = [row for row in results if row["case"] == case_id]
        valid = [row for row in rows if row["valid"]]
        complete = len(valid) >= 3 and len(
            {row["response_id"] for row in valid if row.get("response_id")}
        ) == len(valid)
        summary.append(
            {
                "case": case_id,
                "valid": len(valid),
                "calls": len(rows),
                "act_gate_failures": [
                    row["repeat"]
                    for row in valid
                    if "required_act_completed" in case["fixture"]
                    and row["output"]["act_completed"] != case["fixture"]["required_act_completed"]
                ],
                "status": "planning_not_evaluated"
                if not case["request"]
                else "content_pending"
                if complete
                else "technically_incomplete",
            }
        )
    write(RUNS / "grade.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "grade":
        grade()
    else:
        asyncio.run(prepare() if command == "prepare" else run())
