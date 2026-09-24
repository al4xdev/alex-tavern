from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = [
    "77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl",
    "repetition-battery/base-P3-r2/sessions/d5a2ccf0/debug.jsonl",
    "repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl",
]


def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def main() -> None:
    os.environ["ROLEPLAY_DATA_DIR"] = tempfile.mkdtemp(prefix="tavern-intake-read-")
    sys.path.insert(0, str(ROOT))
    from src.runner import _fact_key_admissible

    cases = []
    manifest = []
    for relative in SOURCES:
        path = ROOT / "plans/artifacts" / relative
        raw = path.read_bytes()
        selected = 0
        for number, line in enumerate(raw.splitlines(), 1):
            row = json.loads(line)
            if row.get("agent") != "director" or row.get("error") is not None:
                continue
            request = row["request"]["messages"][1]["content"]
            marker = "  Physical facts: "
            assert request.count(marker) == 1
            facts = json.JSONDecoder().raw_decode(request.split(marker, 1)[1])[0]
            response = json.loads(row["response"])
            delta = response["scene_update"] or {}
            rejected = {
                key: value
                for key, value in delta.items()
                if key not in ("location", "time_of_day")
                and value is not None
                and not _fact_key_admissible(key, facts)
            }
            if not rejected:
                continue
            cases.append(
                {
                    "source": relative,
                    "line": number,
                    "turn": row["turn_number"],
                    "prior_facts": facts,
                    "events": response["perception_events"],
                    "elapsed_events": response.get("time_skip_summary", ""),
                    "proposed_delta": delta,
                    "rejected_by_current_key_check_against_input": rejected,
                }
            )
            selected += 1
            if selected == 4:
                break
        manifest.append(
            {
                "source": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "selected_calls": selected,
            }
        )
    lines = [
        "# Leitura de propostas de estado",
        "Seleção fixa: até as primeiras quatro chamadas aceitas com chaves recusadas em cada "
        "uma das três fontes declaradas. Não é amostra de frequência de erro. As recusas "
        "abaixo são uma inspeção da função atual sobre o estado do pedido; não comprovam, "
        "sozinhas, o estado historicamente persistido.",
        "Julgue o conteúdo de cada proposta recusada contra os fatos e eventos apresentados: "
        "contém mudança sustentada, repetição, conflito, ou falta contexto? Avalie também "
        "se simplesmente acrescentá-la conservaria afirmações contraditórias. Ordens não "
        "são execução. Eventos novos não precisam já existir no estado anterior.",
    ]
    for number, case in enumerate(cases, 1):
        lines += [f"## Caso {number}", dump(case)]
    with (OUT / "reader.md").open("x") as stream:
        stream.write("\n\n".join(lines) + "\n")
    (OUT / "cases.json").write_text(dump(cases))
    (OUT / "manifest.json").write_text(
        dump(
            {
                "sources": manifest,
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            }
        )
    )
    print(dump(manifest))


if __name__ == "__main__":
    main()
