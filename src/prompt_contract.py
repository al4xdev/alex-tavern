"""The one rule that says whether a prompt leaked the operator's existence.

`AGENTS.md` §3: no agent — Director, Character, Prose, Perspective, Historian
or Architect — may learn that a human drives one of the characters, or which
character that is. The lock is deterministic and lives in the Runner; the
prompts must not restate it, because restating it is what tells the model the
protected identity exists.

Two consumers share this module so the guarantee has exactly one definition:
`tests/` asserts that shipped builders emit nothing matching it, and
`tools/playtest_harness.py` counts hits over the prompts of a real run.

Deliberately phrase-based, not word-based. "human" can be a species and
"protagonist" can be ordinary craft talk; what is forbidden is the *operational*
frame — an outside person who controls a character. A bare word search would
both miss `(controlled by the player)` written as `(player-controlled)` and
reject a legitimate line about a human character in a world of elves.
"""

from __future__ import annotations

import re

# Each pattern names an operational relationship, never a bare noun.
OPERATOR_ONTOLOGY_PATTERNS: tuple[str, ...] = (
    r"\bthe player\b",
    r"\bplayer'?s\b",
    r"\bplayer[-\s]controlled\b",
    r"\bcontrolled by (?:the |a |an )?(?:player|human|user|operator)\b",
    r"\bhuman[-\s]controlled\b",
    r"\bthe human\b",
    r"\bthe user\b",
    r"\bthe operator\b",
    r"\bo jogador\b",
    r"\ba jogadora\b",
    r"\bdo jogador\b",
    r"\bagência humana\b",
    r"\bcontrolado pel[oa] (?:jogador|usuári[oa]|humano)\b",
    r"\bo usuári[oa]\b",
    r"\bo operador\b",
    # Structural markers: a role the system attaches to exactly one character
    # identifies that character even when it avoids the word "player".
    r"PROTAGONIST\s*[—-]",
    r"\bnever an expected actor\b",
    # --- Added 2026-07-27, after this list missed a shipped built-in scenario ---
    #
    # Every pattern above names the operator with a NOUN. The leaks below name
    # the same relationship with a VERB, or by negating the agents, and the whole
    # list was blind to them: the scenario said Link's choices "pertencem sempre
    # ao humano" and that "nenhum agente escolhe fala, pensamento [...] por ele",
    # and not one pattern fired. Written against the vocabulary the leak actually
    # used, not the vocabulary I expected it to use.
    #
    # Belonging: someone outside owns a character's inner life.
    r"\bpertencem?\s+(?:sempre\s+)?(?:ao|à|a)\s+(?:humano|humana|jogador|jogadora|usuári[oa]|operador)\b",
    r"\bbelongs?\s+(?:always\s+)?to\s+the\s+(?:human|player|user|operator)\b",
    # Negated agency: no agent may choose FOR this character. Naming the
    # exception is naming the protected identity.
    r"\bnenhum agente\b[^.]{0,80}\b(?:escolhe|decide|controla)\b",
    r"\bno agent\b[^.]{0,80}\b(?:chooses|decides|controls)\b",
    r"\bnão decida\b[^.]{0,60}\bescolhas de\b",
    r"\bdo not decide\b[^.]{0,60}\bchoices of\b",
    # Control handover: "input" and "control" have no referent inside the story.
    r"\breturn(?:ing)?\s+control\b",
    r"\bdevolver o controle\b",
    r"\blast input\b",
    r"\búltima entrada\b",
    # Outside-the-fiction framing.
    r"\bfora da ficção\b",
    r"\boutside the fiction\b",
    r"\bhuman operator\b",
    r"\boperador humano\b",
)

_COMPILED = tuple(re.compile(pattern, re.IGNORECASE) for pattern in OPERATOR_ONTOLOGY_PATTERNS)


def operator_ontology_hits(text: str) -> list[str]:
    """Every operational-ontology phrase found in one prompt, in order."""
    return [match.group(0) for pattern in _COMPILED for match in pattern.finditer(text)]


def leaks_operator_ontology(text: str) -> bool:
    """True when a prompt tells the model an outside operator exists."""
    return any(pattern.search(text) for pattern in _COMPILED)


_SPEAKER_LABEL_RE = re.compile(r"^\s*([^:\n]{1,60}?):", re.MULTILINE)


def singled_out_speakers(text: str, characters: dict) -> list[str]:
    """Characters formatted unlike the rest of the cast in the same block.

    The patterns above are lexical: they catch a prompt that NAMES the operator.
    This catches a prompt that POINTS at one character without naming anything —
    the leak found on 2026-07-27, where `recent_event_lines` rendered the
    human-controlled character by name and every other character by internal id:

        Thorn: Who runs this inn?
        C2: Hm, that depends...

    No word search can see that. The protected identity is encoded in the
    formatting, and the set of names was exactly the controlled character.

    Returns the labels that are the minority form when a block mixes canonical
    names with internal ids. An empty list means every speaker is written the
    same way, which is the property AGENTS.md section 3 actually needs: not
    "names are nicer", but "nobody is marked".
    """
    labels = [match.group(1).strip() for match in _SPEAKER_LABEL_RE.finditer(text)]
    if not labels:
        return []
    names = {character.mind.name for character in characters.values()}
    as_name = [label for label in labels if label in names]
    as_id = [label for label in labels if label in characters]
    if not as_name or not as_id:
        return []
    minority = as_name if len(set(as_name)) <= len(set(as_id)) else as_id
    return sorted(set(minority))


# A rule that steers AWAY from one named character. AGENTS.md section 3 lists
# this shape by name - "Rotulo, ordem, campo extra, exclusao nomeada" - because
# the engine only ever excludes one character systematically, so the clause
# encodes controlled_character_id however dramatic its stated reason is.
_EXCLUSION_LEADS: tuple[str, ...] = (
    r"\b(?:someone|somebody|anyone|anybody|something)\s+other\s+than\b",
    r"\bother\s+than\b",
    r"\banyone\s+but\b",
    r"\bexcept(?:ing)?\b",
    r"\bexclud(?:e|es|ed|ing)\b",
    r"\brather\s+than\b",
    r"\binstead\s+of\b",
    r"\boutr[oa]s?\s+que\s+n[aã]o\b",
    r"\bqu(?:e|em)\s+n[aã]o\s+seja\b",
    r"\balgu[eé]m\s+al[eé]m\s+de\b",
    r"\bexceto\b",
    r"\bmenos\b",
    r"\bevit(?:e|ar)\b",
)

_COMPILED_EXCLUSION_LEADS = tuple(
    re.compile(pattern, re.IGNORECASE) for pattern in _EXCLUSION_LEADS
)

# How far past the phrase the excluded party may be named. Long enough for
# "someone other than the young apprentice C4", short enough that the next
# sentence's cast mentions do not get attributed to this clause.
_EXCLUSION_WINDOW = 48

# The excluded party is named in the SAME clause as the phrase that excludes
# them. Without this, "he arrived rather than waited, and C2 followed" reads as
# an exclusion of C2, who is merely the subject of the next clause.
_CLAUSE_END_RE = re.compile(r"[,;:.\n]")


def named_exclusions(text: str, characters: dict) -> list[str]:
    """Cast members a prompt rule steers the model away from, by name or id.

    The two checks above cannot see this one. `operator_ontology_hits` is
    phrase-based and this clause contains none of its vocabulary; the shipped
    example read "Let someone other than C1 carry this beat; the scene is more
    interesting when attention moves", whose stated reason is pure craft.
    `singled_out_speakers` inspects speaker-label formatting, and this is a
    routing instruction in a different block entirely.

    Membership, not shape, decides - the same rule the internal-id guard in task
    65 was built on. `\\b[A-Z]\\d+\\b` only nominates a candidate; it counts only
    if it is a real cast id or name. "Take any road other than R4" in a scenario
    where R4 is a highway must not be read as excluding a character.
    """
    if not characters:
        return []
    tokens: dict[str, str] = {}
    for cid, character in characters.items():
        tokens[cid] = cid
        name = getattr(getattr(character, "mind", None), "name", None)
        if isinstance(name, str) and name.strip():
            tokens[name] = cid
    found: set[str] = set()
    for pattern in _COMPILED_EXCLUSION_LEADS:
        for match in pattern.finditer(text):
            window = text[match.end() : match.end() + _EXCLUSION_WINDOW]
            boundary = _CLAUSE_END_RE.search(window)
            if boundary is not None:
                window = window[: boundary.start()]
            for token, cid in tokens.items():
                if re.search(rf"\b{re.escape(token)}\b", window):
                    found.add(cid)
    return sorted(found)
