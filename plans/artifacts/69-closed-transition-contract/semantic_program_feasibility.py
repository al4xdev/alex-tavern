"""Frozen, hand-bound closed-event realizer screen; never imported by runtime."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = {
    "T38": (
        "p1-archive/null-P1-r1/sessions/7fd84e9a",
        38,
        "03aef5776ce1565352f1c526ee4c7b17909b3f873ac57cda06704c2f68f1f187",
        "c66b438dfb62452153ea9b9c0c841baae366424245b07c7d85eb513caab06302",
    ),
    "T8": (
        "p1-archive/drive-P1-r1/sessions/5c994c42",
        8,
        "f958df9f12b6926344fbbddf9b1d57d6088442d0da71e35d555a33569fb561fd",
        "872ecab6dfd3ad324c15acaaa0a67adfc7d1087c7296f5ffdbcbc82b2488a187",
    ),
    "T6": (
        "repetition-battery/base-P3-r2/sessions/d5a2ccf0",
        6,
        "01cc4b84dd3f4b049e00e2fe3481630cc711a45de3b4ef2c9a69a2ce5873e931",
        "94727049f62ebb156ee7a5ffa7a55b9f4088a7b12e4b069da821f7f93fabc669",
    ),
    "T23": (
        "p1-archive/null-P1-r2/sessions/05e0dffc",
        23,
        "ea49f397cff98c81ac391d4e2d056b50bcdd795f3c114d1b874ef8602b84217c",
        "daf2afc504c9cd7262d0a7fa16e5bcaa5a7ca39c6cc6ccf62ca0f0e941bb3deb",
    ),
}

# Nominal glossary only. Event-bearing verbs and their consequences live in
# the closed renderer below, never in data fields or source-prose fragments.
NOUNS = {
    "teo": "Téo",
    "blue_gate": "o portão azul",
    "blue_gap": "a antiga fresta",
    "blue_team": "a equipe azul",
    "blue_tunnel": "o túnel azul",
    "main_gate": "os portões principais",
    "guard": "um guarda ensanguentado",
    "hall": "o salão",
    "outer_wall": "a muralha externa",
    "maelis": "Maelis",
    "garran": "Garran",
    "asword": "Asword",
    "students": "os alunos",
    "rear": "os fundos",
    "shield": "um escudo",
    "chest": "o baú",
    "smoke": "a fumaça",
    "bells": "os sinos",
    "breach": "a entrada",
    "gap": "o vão estreito",
    "far_corridor": "o corredor além",
    "rubble": "os blocos soltos",
    "elowen": "Elowen",
    "cael": "Cael",
    "cloth": "um pano limpo",
    "shoulder": "o ombro ferido",
    "infirmary": "a enfermaria",
    "floor": "o chão",
    "slabs": "as lajes",
    "block": "um bloco",
    "noa": "Noa",
    "bruna": "Bruna",
    "liora": "Liora",
    "mirrors": "os espelhos",
    "test": "a prova",
    "line": "a linha",
    "cane": "a bengala",
    "stone": "a pedra",
}


@dataclass(frozen=True)
class Event:
    op: str
    actor: str
    target: str = ""
    aux: str = ""
    audience: str = "hall"


PROGRAMS = {
    "T38": [
        Event("sealed", "blue_gate", "blue_team", "blue_tunnel"),
        Event("blocked_attempt", "teo", "blue_gap", "blue_gate"),
    ],
    "T8": [
        Event("forced_open", "main_gate"),
        Event("enter", "guard", "hall"),
        Event("report_breach", "guard", "outer_wall"),
        Event("collapse", "guard", "stone"),
        Event("speech_intent_evac", "maelis", "students", "rear"),
        Event("speech_intent_guard", "maelis", "garran", "breach"),
        Event("move", "garran", "main_gate"),
        Event("take", "garran", "shield", "chest"),
        Event("speech_intent_move", "garran", "students"),
        Event("sensory_smoke", "smoke", "main_gate"),
        Event("sensory_bells", "bells"),
    ],
    "T6": [
        Event("cross", "garran", "gap", "far_corridor", "origin"),
        Event("blocked_corridor", "far_corridor", "rubble", audience="origin"),
        Event("approach", "elowen", "cael", audience="origin"),
        Event("treat", "elowen", "shoulder", "cloth", "origin"),
        Event("pray", "elowen", "cael", audience="origin"),
        Event("speech_intent_care", "elowen", "cael", "infirmary", "origin"),
        Event("tremor", "floor", "slabs", audience="origin"),
        Event("roll", "block", "rubble", audience="origin"),
    ],
    "T23": [
        Event("waiting", "noa", "test"),
        Event("pressure", "bruna", "noa", "mirrors"),
        Event("mock", "liora", "noa"),
        Event("tap", "maelis", "cane", "stone"),
        Event("speech_intent_order", "maelis", "students"),
        Event("speech_intent_start", "maelis", "noa", "line"),
    ],
}


def render(event: Event) -> str:
    a = NOUNS[event.actor]
    t = NOUNS[event.target] if event.target else ""
    x = NOUNS[event.aux] if event.aux else ""
    match event.op:
        case "sealed":
            return f"{a.capitalize()} continua fechado; {t} já está no {x[2:]}."
        case "blocked_attempt":
            return f"{a} tenta avançar pela {t[2:]}, mas {x} não cede. Ele permanece deste lado."
        case "forced_open":
            return f"Um impacto do lado de fora força {a} a se abrir de vez."
        case "enter":
            return f"{a.capitalize()} cambaleia para dentro do {t[2:]}."
        case "report_breach":
            return f"Ele consegue avisar que criaturas romperam {t}."
        case "collapse":
            return f"Então {a} desaba sobre {t}."
        case "speech_intent_evac":
            return f"{a} orienta {t} a sair pelos {x[3:]}."
        case "speech_intent_guard":
            return f"Ela ordena a {t} que feche {x}."
        case "move":
            return f"{a} corre até {t}."
        case "take":
            return f"No caminho, {a} tira {t} do {x[2:]}."
        case "speech_intent_move":
            return f"{a} conclama {t} a não parar."
        case "sensory_smoke":
            return f"{a.capitalize()} entra pelos {t[3:]}."
        case "sensory_bells":
            return f"{a.capitalize()} soam cada vez mais alto."
        case "cross":
            return f"{a} atravessa {t} e desaparece do outro lado."
        case "blocked_corridor":
            return f"Do vão, {a} ainda aparece parcialmente obstruído pelos {t[3:]}."
        case "approach":
            return f"{a} se ajoelha ao lado de {t}."
        case "treat":
            return f"{a} pressiona {x} contra {t}."
        case "pray":
            return f"{a} começa uma oração de estabilização junto de {t}."
        case "speech_intent_care":
            return f"{a} considera a ferida de {t} superficial, mas pede que o levem à {x[2:]}."
        case "tremor":
            return f"Uma segunda vibração atravessa {a} e faz {t} estalar."
        case "roll":
            return f"{a.capitalize()} se solta dos {t[3:]}, rola alguns metros e para."
        case "waiting":
            return f"{a} ainda espera no centro para começar {t}."
        case "pressure":
            return f"{a} pressiona {t} a mostrar {x}."
        case "mock":
            return f"{a} ridiculariza a hesitação de {t}."
        case "tap":
            return f"{a} bate {t} contra {x}."
        case "speech_intent_order":
            return f"{a} exige silêncio de {t}."
        case "speech_intent_start":
            return f"Ela lembra que a prova de {t} só começa quando a jovem cruza {x}."
        case _:
            raise ValueError(f"unregistered operation: {event.op}")


def source_packet(case: str) -> tuple[list[str], dict[str, str]]:
    rel, turn, debug_hash, state_hash = SOURCES[case]
    base = ROOT / "plans/artifacts" / rel
    for name, expected in (("debug.jsonl", debug_hash), ("state.json", state_hash)):
        actual = hashlib.sha256((base / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"source hash mismatch: {case}/{name}")
    state = json.loads((base / "state.json").read_text())
    director = next(
        json.loads(row["response"])
        for line in (base / "debug.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("turn_number") == turn
        and row.get("agent") == "director"
        and row.get("response")
    )
    speakers = director["next_speakers"]
    speech = {
        speaker: next(
            item["content"]
            for item in state["history"]
            if item["turn_number"] == turn
            and item["speaker"] == speaker
            and item["content_type"] == "speech"
        )
        for speaker in speakers
    }
    return speakers, speech


def main() -> None:
    output = {}
    for case, events in PROGRAMS.items():
        speakers, speech = source_packet(case)
        # Group only by consecutive event-time audience. No case-specific prose.
        paragraphs: list[str] = []
        audience = ""
        for event in events:
            if event.audience != audience:
                paragraphs.append("")
                audience = event.audience
            paragraphs[-1] = f"{paragraphs[-1]} {render(event)}".strip()
        speaker_names = {
            "C17": "maelis",
            "C18": "garran",
            "C2": "asword",
            "C21": "elowen",
            "C8": "bruna",
            "C7": "liora",
        }
        words = "\n".join(
            f"{NOUNS[speaker_names[speaker]]}: {speech[speaker]}" for speaker in speakers
        )
        output[case] = {
            "events": [event.__dict__ for event in events],
            "narration": "\n\n".join(paragraphs),
            "character_speech": words,
        }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
