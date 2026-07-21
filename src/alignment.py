"""Character alignment (Task 44 Toggle 2): the transient dramatic impulse.

When `character_roteiro_alignment_enabled` is on, an expected actor of the current
beat receives a TRANSIENT inner impulse that tilts their CHOICE toward the beat —
never dictating the action, never leaking the plot. This is NOT the disposition
substrate (Task 43): no scalar, no persistence. The curl gate (arm C,
plans/artifacts/roteiro-alignment/VALIDATION.md) proved that injecting such an
impulse flips a coherent character to serve a withheld-information beat with zero
leak and preserved voice.

LEAK-SAFE BY CONSTRUCTION. The deriver (Director-side, blind, sees the private beat)
outputs ONLY an enum key — it never writes free text — and the code renders that key
into a fixed-vocabulary line. So the character prompt can carry no premise, no future
anchor, no metalanguage: the impulse is one of a small closed set of feelings.
"""

from __future__ import annotations

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import Character

# The closed impulse vocabulary. Each key renders to a fixed first-person feeling —
# a disposition-flavored nudge, never plot content. `none` means no push this beat.
IMPULSES: dict[str, str] = {
    "bold": (
        "temerário — sinta um chamado a arriscar, a avançar sem hesitar, a confiar "
        "que a audácia resolve mais que a cautela"
    ),
    "cautious": (
        "cauteloso — sinta o peso do risco e a vontade de proteger, de não se "
        "precipitar nem arrastar os outros ao perigo"
    ),
    "warm": ("acolhedor — sinta abertura e generosidade para com quem está diante de você"),
    "hostile": (
        "hostil — sinta a guarda erguida, desconfiança e frieza para com quem está diante de você"
    ),
    "urgent": (
        "premido pelo tempo — sinta que hesitar custa caro, que o momento exige ação "
        "agora, não deliberação"
    ),
    "defiant": (
        "desafiador — sinta o impulso de contrariar, de romper a ordem ou a "
        "expectativa imposta sobre você"
    ),
}
IMPULSE_KEYS: tuple[str, ...] = (*IMPULSES.keys(), "none")


def render_impulse(key: str) -> str:
    """Render an impulse enum key into the fixed character-facing line (or '')."""
    feeling = IMPULSES.get(key)
    if not feeling:
        return ""
    return (
        "SEU ÍMPETO INTERNO AGORA (deixe colorir sua escolha; não anuncie nem "
        f"explique isto): {feeling}."
    )


def build_alignment_messages(beat_intent: str, character: Character) -> list[dict]:
    """Frame the private beat + a character for a blind, Director-side impulse pick.

    The beat is Director-only; it goes IN. Only an enum key comes OUT, so nothing
    plot-specific can reach the character through this call.
    """
    system = (
        "You silently read a PRIVATE dramatic beat and one character. Pick the single "
        "inner impulse that would make THIS character CHOOSE to serve the beat on "
        "their own — an impulse that redirects a coherent person toward the dramatic "
        "need without anyone dictating their action. Output ONLY one enum key; never "
        "quote or describe the beat.\n"
        "Impulses: bold (dare, take the risk), cautious (protect, hold back), warm "
        "(open up, help), hostile (guard up, cold), urgent (act now, no deliberation), "
        "defiant (break the imposed order). Use `none` if this character needs no push.\n"
        "Guidance: Focus on the core dramatic ACTION required by the beat (e.g., splitting, "
        "exploring, risking) rather than passive threats mentioned in the text. Beats that "
        "require proactive risk-taking or splitting should favor `bold` or `urgent` "
        "over `cautious`.\n"
        'Return json: {"impulse": <key>}.'
    )
    user = (
        f"PRIVATE BEAT (never reveal): {beat_intent}\n"
        f"CHARACTER: {character.mind.name} — {character.mind.personality}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_alignment_schema() -> dict:
    return {
        "name": "alignment_impulse",
        "schema": {
            "type": "object",
            "properties": {"impulse": {"type": "string", "enum": list(IMPULSE_KEYS)}},
            "required": ["impulse"],
            "additionalProperties": False,
        },
    }


async def derive_alignment_impulse(
    client: httpx.AsyncClient,
    beat_intent: str,
    character: Character,
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
) -> str:
    """Return the rendered transient impulse line for a character (or '').

    The model only picks an enum key; the returned string is always from the fixed
    IMPULSES vocabulary, so it is leak-safe by construction.
    """
    if not beat_intent.strip():
        return ""
    result = await chat_completion_json(
        client,
        build_alignment_messages(beat_intent, character),
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=64,
        json_schema=build_alignment_schema(),
        timeout=resolve_llm_timeout(config),
        session_id=session_id,
        turn_number=turn_number,
        agent="alignment:impulse",
        **llm_request_options(config),
    )
    key = str(result.get("impulse", "none")).strip()
    return render_impulse(key)
