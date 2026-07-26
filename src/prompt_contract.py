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
)

_COMPILED = tuple(re.compile(pattern, re.IGNORECASE) for pattern in OPERATOR_ONTOLOGY_PATTERNS)


def operator_ontology_hits(text: str) -> list[str]:
    """Every operational-ontology phrase found in one prompt, in order."""
    return [match.group(0) for pattern in _COMPILED for match in pattern.finditer(text)]


def leaks_operator_ontology(text: str) -> bool:
    """True when a prompt tells the model an outside operator exists."""
    return any(pattern.search(text) for pattern in _COMPILED)
