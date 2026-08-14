"""Negative control for _INTENT_CARRIED_RATIO: the same calls WITHOUT the mandate.

WHY. The mandate arm produced ten replies and a reader calls all ten compliant,
so it measures only the false-positive side of the threshold. A threshold needs
both sides. This fires the identical character payloads with the mandate REMOVED
and scores the reply against the same intent. That is the "mandate ignored"
population, built rather than assumed: the character was never told, so whatever
overlap appears is the overlap topicality alone produces.

PRE-REGISTERED READING, written before the control ran:

  - If the no-mandate ratios sit clearly BELOW the mandate ratios with a gap
    between the two clouds, the ratio discriminates and the threshold belongs in
    that gap, sized like the language guard in this same task.
  - If the two clouds OVERLAP substantially, the ratio cannot separate "voiced
    the fact" from "happened to be talking about it", and no threshold rescues
    it. That is a finding about the instrument, not a reason to pick a nicer
    number.

Both arms are scored with the subject's own name excluded from the denominator
and with it included, because that bias was measured at 10/10 in the mandate arm
and the control has to be read under the same rule as any change it motivates.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

import httpx  # noqa: E402

from src.runner import _intent_words  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from calibrate_intent_ratio import (  # noqa: E402
    TAIL,
    character_payloads,
    collect_intents,
)

ROOT = pathlib.Path("/home/alex/git/my/alex-tavern")
OUT = pathlib.Path(__file__).parent / "control"


def ratios(intent: str, spoken: str, name: str) -> tuple[float, float]:
    wanted = _intent_words(intent)
    said = _intent_words(spoken)
    with_name = len(wanted & said) / len(wanted) if wanted else 1.0
    bare = wanted - _intent_words(name)
    without_name = len(bare & said) / len(bare) if bare else 1.0
    return with_name, without_name


async def main() -> None:
    cfg = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
        "deepseek"
    ]
    payloads = character_payloads()
    intents = [i for i in collect_intents() if i.name in payloads]
    print(f"firing {len(intents)} UNMANDATED control calls", flush=True)

    async def one(client: httpx.AsyncClient, intent) -> dict:
        request = payloads[intent.name]
        body = {
            "model": cfg["model"],
            "messages": [dict(m) for m in request["messages"]],  # untouched: no mandate
            "max_tokens": request.get("max_tokens", 12288),
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
            raw = response.json()["choices"][0]["message"]["content"]
            spoken = str(json.loads(raw).get("speech") or "")
        except Exception as exc:  # noqa: BLE001
            return {"name": intent.name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
        with_name, without_name = ratios(intent.text, spoken, intent.name)
        print(
            f"  ok  {intent.name:<24} with_name={with_name:.2f} without_name={without_name:.2f}",
            flush=True,
        )
        return {
            "name": intent.name,
            "ok": True,
            "intent": intent.text,
            "spoken": spoken,
            "with_name": with_name,
            "without_name": without_name,
        }

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(4)

        async def guarded(i):
            async with semaphore:
                return await one(client, i)

        rows = await asyncio.gather(*(guarded(i) for i in intents))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report(rows)


def report(rows: list[dict]) -> None:
    good = [r for r in rows if r["ok"]]
    mand = json.loads(
        (pathlib.Path(__file__).parent / "calibration" / "results.json").read_text(encoding="utf-8")
    )
    mand_rows = [r for r in mand if r["ok"]]

    print("\n" + "=" * 72)
    for label, key in (("own name IN denominator", "with_name"), ("own name EXCLUDED", "without_name")):
        ctrl = sorted(r[key] for r in good)
        if key == "with_name":
            treat = sorted(r["ratio"] for r in mand_rows)
        else:
            treat = sorted(
                ratios(r["intent"], r["spoken"], r["name"])[1] for r in mand_rows
            )
        print(f"\n{label}")
        print(f"  MANDATED  : {' '.join(f'{x:.2f}' for x in treat)}")
        print(f"  CONTROL   : {' '.join(f'{x:.2f}' for x in ctrl)}")
        print(f"  mandated min={min(treat):.2f}   control max={max(ctrl):.2f}")
        gap = min(treat) - max(ctrl)
        print(f"  separation: {'GAP of %.2f' % gap if gap > 0 else 'OVERLAP of %.2f' % -gap}")
        print("  threshold sweep (carried / false-positive-on-control):")
        for t in (0.3, 0.4, 0.5, 0.6, 0.7):
            tp = sum(1 for x in treat if x >= t)
            fp = sum(1 for x in ctrl if x >= t)
            print(f"    {t:.1f} -> mandated kept {tp}/{len(treat)}, control wrongly kept {fp}/{len(ctrl)}")

    print("\n  control replies:")
    for r in sorted(good, key=lambda r: r["without_name"]):
        print(f"    {r['without_name']:.2f}  {r['name']}: {r['spoken'][:110]}")


if __name__ == "__main__":
    asyncio.run(main())
