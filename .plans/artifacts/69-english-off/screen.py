"""Fresh paired-language replay of the historical three act-completion cases."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import random
import time
from pathlib import Path
from uuid import uuid4

from src.llm.adapters.deepseek import DeepSeekAdapter
from src.llm.schema import validate_json_schema

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / ".plans/artifacts/69-descriptions-applied/manifest.json"
TRANSLATIONS = {
    ("Always respond and write in Brazilian Portuguese."): ("Always respond and write in English."),
    ("Salão do portal"): ("Portal hall"),
    ("Acampamento no cânion"): ("Canyon camp"),
    ("TIME: tarde"): ("TIME: afternoon"),
    ("Cartógrafa curiosa e cuidadosa."): ("Curious and careful cartographer."),
    ("Guia pragmático e atento aos caminhos."): ("Pragmatic guide attentive to paths."),
    ("Fantasia de aventura. Texto em português brasileiro."): (
        "Adventure fantasy. Text in English."
    ),
    ("Precisamos avaliar o caminho antes de prosseguir."): (
        "We need to assess the path before proceeding."
    ),
    ("Iara e Bento devem fechar o portal e levar o mapa à torre."): (
        "Iara and Bento must close the portal and take the map to the tower."
    ),
    ("Fechar o portal do salão antes que a passagem se alargue."): (
        "Close the hall portal before the passage widens."
    ),
    ("O portal está fechado."): ("The portal is closed."),
    ("Levar o mapa até a torre."): ("Take the map to the tower."),
    ("A consequência desse objetivo foi estabelecida."): (
        "The consequence of this objective has been established."
    ),
    ("A passagem aberta se alarga enquanto as runas perdem estabilidade."): (
        "The open passage widens as the runes lose stability."
    ),
    ("Iara tentou encostar o mapa nas runas para fechar o portal."): (
        "Iara tried touching the runes with the map to close the portal."
    ),
    ("A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."): (
        "The attempt did not work: the portal remains open and the runes still fluctuate."
    ),
    ("A passagem do portal se fechou por completo; as runas apagaram."): (
        "The portal passage closed completely; the runes went dark."
    ),
    ("Iara e Bento continuam no salão com o mapa. Não existe passagem aberta agora."): (
        "Iara and Bento remain in the hall with the map. There is no open passage now."
    ),
    (
        "Iara e Bento atravessaram a passagem até o cânion; o portal se fechou "
        "e as runas apagaram depois."
    ): (
        "Iara and Bento crossed the passage to the canyon; the portal closed "
        "and the runes went dark afterward."
    ),
    (
        "Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma "
        "passagem de volta está aberta."
    ): (
        "Both are in the canyon with the map. The hall was left far behind; "
        "no return passage is open."
    ),
}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def hashes():
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        PRIOR,
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/llm/schema.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def guard(body):
    assert body["model"] == "deepseek-v4-flash", "Pro and model substitution forbidden"
    assert body["thinking"] == {"type": "disabled"}
    assert "reasoning_effort" not in body
    assert body["max_tokens"] == 8192


def prepare():
    assert not (HERE / "manifest.json").exists(), "Preserve frozen requests"
    prior = json.loads(PRIOR.read_text())
    cases = []
    for old in prior["cases"]:
        name = old["fixture"]["id"].removesuffix("-descriptive")
        if name not in ("portal_attempt", "portal_closed", "portal_left"):
            continue
        source = copy.deepcopy(old["request"])
        source.update(model="deepseek-v4-flash", max_tokens=8192, thinking={"type": "disabled"})
        source.pop("reasoning_effort", None)
        english = copy.deepcopy(source)
        for msg in english["messages"]:
            for pt, en in TRANSLATIONS.items():
                msg["content"] = msg["content"].replace(pt, en)
        reverse = copy.deepcopy(english)
        for msg in reverse["messages"]:
            for pt, en in reversed(list(TRANSLATIONS.items())):
                msg["content"] = msg["content"].replace(en, pt)
        assert reverse == source, "Only reversible translations may differ"
        for language, request in (("pt", source), ("en", english)):
            guard(request)
            cases.append(
                {
                    "case": name,
                    "language": language,
                    "request": request,
                    "schema": old["schema"],
                    "expected": old["fixture"]["required_act_completed"],
                }
            )
    assert len(cases) == 6
    write(HERE / "manifest.json", {"hashes": hashes(), "cases": cases, "repeats": 4})
    print("Frozen 24 direct Flash-only calls: three cases × two languages × four draws")


async def run():
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert manifest["hashes"] == hashes()
    stored = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    adapter = DeepSeekAdapter()
    adapter.validate_api_base(stored["api_base"])
    assert stored["api_key"]
    endpoint = stored["api_base"].rstrip("/") + "/chat/completions"
    runs = HERE / "runs"
    runs.mkdir()
    jobs = [(c, r) for c in manifest["cases"] for r in range(1, 5)]
    random.Random(691006).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)
    blocked = asyncio.Event()

    async def call(case, repeat):
        async with semaphore:
            stem = f"{case['case']}-{case['language']}-{repeat}"
            result = {
                "case": case["case"],
                "language": case["language"],
                "repeat": repeat,
                "valid": False,
                "correct": False,
                "session_id": str(uuid4()),
                "agent": "next_beat_language_replay",
                "turn_number": 3,
            }
            if blocked.is_set():
                result["skipped"] = "Unsent after credential/balance rejection"
                write(runs / f"{stem}.result.json", result)
                return
            body = case["request"]
            guard(body)
            path = runs / f"{stem}.request.json"
            write(path, body)
            config = (
                "\n".join(
                    [
                        "silent",
                        "show-error",
                        "request = POST",
                        "max-time = 180",
                        "url = " + json.dumps(endpoint),
                        "header = " + json.dumps("Content-Type: application/json"),
                        "header = " + json.dumps("Authorization: Bearer " + stored["api_key"]),
                        "data-binary = " + json.dumps("@" + str(path)),
                        'write-out = "\\n%{http_code}"',
                    ]
                )
                + "\n"
            )
            start = time.monotonic()
            process = await asyncio.create_subprocess_exec(
                "curl",
                "--config",
                "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate(config.encode())
            raw, _, status = stdout.rpartition(b"\n")
            (runs / f"{stem}.raw.json").write_bytes(raw)
            write(
                runs / f"{stem}.transport.json",
                {
                    "exit_code": process.returncode,
                    "http_status": status.decode(),
                    "stderr": stderr.decode(),
                },
            )
            if status in (b"401", b"402"):
                blocked.set()
            try:
                assert process.returncode == 0 and status == b"200", "HTTP/transport failure"
                envelope = json.loads(raw)
                message = envelope["choices"][0]["message"]
                output = json.loads(message["content"])
                validate_json_schema(output, case["schema"])
                result.update(
                    valid=True,
                    output=output,
                    correct=output["act_completed"] is case["expected"],
                    response_id=envelope.get("id"),
                    usage=envelope.get("usage"),
                    finish_reason=envelope["choices"][0].get("finish_reason"),
                    reasoning_chars=len(message.get("reasoning_content") or ""),
                )
            except Exception as error:
                result["error"] = f"{type(error).__name__}: {error}"
            result["wall_seconds"] = round(time.monotonic() - start, 3)
            write(runs / f"{stem}.result.json", result)
            (runs / f"{stem}.debug.jsonl").write_text(
                json.dumps({**result, "request": body}, ensure_ascii=False) + "\n"
            )
            print(
                stem,
                "valid",
                result["valid"],
                "correct",
                result["correct"],
                "flag",
                result.get("output", {}).get("act_completed"),
                flush=True,
            )

    await asyncio.gather(*(call(c, r) for c, r in jobs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    if parser.parse_args().command == "prepare":
        prepare()
    else:
        asyncio.run(run())
