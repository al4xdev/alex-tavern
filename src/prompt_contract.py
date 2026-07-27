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
