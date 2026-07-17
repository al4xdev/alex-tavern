"""Deterministic confidentiality primitives for whispered history records.

Shared by the Narrator context guard (``redact_whisper_leaks``) and the Character
output guard: secrets are always derived from the history itself, never hardcoded.

A "secret token" is a rare token (4+ characters, or containing a digit) that belongs
to the INFORMATIONAL PAYLOAD of a whispered record (see ``payload_tokens``) and does
not appear in what the exposed party can legitimately know: speech/action records
visible to them, their own thoughts, character names/ids, and current scene facts.
Narration is excluded from that known set on purpose — characters never receive
Narrator prose, so a narration leak cannot launder a whispered secret into "known".

Payload, not phrasing: a whisper mixes casual conversational words ("alto", "sabe",
"negócio") with the actual secret (codes, numbers, proper nouns and the words that
locate or qualify them). Only the latter is guarded. Treating every rare word of a
whisper as secret poisons the speaker's ordinary vocabulary — after one whispered
exchange, innocent public speech triggers retries and gets garbled by redaction.
"""

from __future__ import annotations

import re

from src.models import Character, Scene, TurnRecord, record_visible_to

_WORD_RE = re.compile(r"\w+")

# Marker substituted for whispered-only content that would otherwise reach someone
# outside the whisper's audience. Reads as diegetic sensory failure.
REDACTION_MARKER = "[indistinct]"


def tokens(text: str) -> set[str]:
    """Casefolded word tokens of ``text``."""
    return {token.casefold() for token in _WORD_RE.findall(text)}


def _is_rare(token: str) -> bool:
    """Common short words never qualify as secrets; numeric fragments always do."""
    return len(token) >= 4 or any(ch.isdigit() for ch in token)


# How many word positions around an informational anchor still count as payload.
# Calibrated on real leak transcripts: the words that locate or qualify a secret
# ("ponte", "terceiro pilar", "margem norte", "cartas") sit within a few words of
# the code or number they describe, while the casual framing of the whisper
# ("assunto de trabalho", "só tu sabes disso") sits outside that neighborhood.
PAYLOAD_WINDOW = 7

# Characters that end a sentence for anchor detection purposes. A colon is
# deliberately NOT a boundary: a capitalized word right after a colon ("o código
# é: Girassol") is far more likely to be the secret itself than a sentence start.
_SENTENCE_END = frozenset(".!?\n…")
_SKIP_BEFORE = frozenset(" \t\r\"'“”‘’«»()[]")


def _sentence_initial(text: str, start: int) -> bool:
    """Whether the token beginning at ``start`` opens the text or a sentence."""
    index = start - 1
    while index >= 0 and text[index] in _SKIP_BEFORE:
        index -= 1
    return index < 0 or text[index] in _SENTENCE_END


def _is_anchor(token: str, sentence_initial: bool) -> bool:
    """High-signal informational cores: digits, code-style caps, proper nouns.

    Ordinary sentence-initial capitalization never counts; an all-caps token
    (code word) counts even at the start of a sentence.
    """
    if any(ch.isdigit() for ch in token):
        return True
    if len(token) >= 2 and token.isupper():
        return True
    return token[:1].isupper() and not sentence_initial


def payload_tokens(text: str) -> set[str]:
    """Casefolded informational-payload tokens of a whispered ``text``.

    Anchors are the high-signal cores of a secret (tokens with digits, code-style
    all-caps tokens, proper nouns capitalized mid sentence). The payload is every
    rare token within ``PAYLOAD_WINDOW`` word positions of an anchor, anchors
    included. A whispered text without any anchor has no guardable payload: its
    rare words are ordinary conversation, not secrets (the prompt-side whisper
    discipline still applies to the model; this function only feeds the
    deterministic guards).
    """
    matches = list(_WORD_RE.finditer(text))
    anchor_positions = [
        position
        for position, match in enumerate(matches)
        if _is_anchor(match.group(), _sentence_initial(text, match.start()))
    ]
    if not anchor_positions:
        return set()
    payload: set[str] = set()
    for position, match in enumerate(matches):
        token = match.group()
        if not _is_rare(token):
            continue
        if any(abs(position - anchor) <= PAYLOAD_WINDOW for anchor in anchor_positions):
            payload.add(token.casefold())
    return payload


def known_tokens(
    history: list[TurnRecord],
    viewer_id: str,
    characters: dict[str, Character],
    scene: Scene,
) -> set[str]:
    """Everything ``viewer_id`` can legitimately know, as a casefolded token set.

    Visible speech/action records, the viewer's own thoughts, character names and
    ids, and current scene facts. Narration is deliberately excluded (see module
    docstring).
    """
    known: set[str] = set()
    for rec in history:
        if rec.content_type == "narration":
            continue
        if rec.content_type == "thought" and rec.speaker != viewer_id:
            continue
        if rec.audience is not None and not record_visible_to(rec, viewer_id):
            continue
        known |= tokens(rec.content)
    for cid, character in characters.items():
        known |= tokens(cid)
        known |= tokens(character.mind.name)
    known |= tokens(scene.location)
    known |= tokens(scene.time_of_day)
    for key, value in scene.physical_facts.items():
        known |= tokens(str(key))
        known |= tokens(str(value))
    return known


def hidden_whisper_tokens(
    history: list[TurnRecord],
    viewer_id: str,
    characters: dict[str, Character],
    scene: Scene,
) -> set[str]:
    """Secret tokens of whispered records that ``viewer_id`` did NOT perceive.

    Used by the Narrator guard: nothing from these records may reach that viewer.
    """
    hidden = [
        rec
        for rec in history
        if rec.audience is not None
        and getattr(rec, "audience_origin", "whisper") == "whisper"
        and rec.content_type != "thought"
        and not record_visible_to(rec, viewer_id)
    ]
    if not hidden:
        return set()
    known = known_tokens(history, viewer_id, characters, scene)
    secret: set[str] = set()
    for rec in hidden:
        secret |= {token for token in payload_tokens(rec.content) if token not in known}
    return secret


def secret_tokens_exposed_to(
    history: list[TurnRecord],
    speaker_id: str,
    exposed_ids: set[str],
    characters: dict[str, Character],
    scene: Scene,
    controlled_id: str | None = None,
) -> set[str]:
    """Secret tokens ``speaker_id`` knows that must not reach ``exposed_ids``.

    Used by the Character output guard: whispered records the speaker DID perceive,
    whose audience does not cover every exposed listener. A token every exposed
    listener could already know legitimately (e.g. the secret was later said in
    public: earned knowledge) is not a secret anymore. The internal "Player"
    speaker marker counts as ``controlled_id`` for audience-coverage purposes.
    """

    def cover(rec: TurnRecord) -> set[str]:
        speaker = controlled_id if rec.speaker == "Player" and controlled_id else rec.speaker
        return set(rec.audience or []) | {speaker}

    # Only INTENTIONAL whispers are confidences. A zone-computed audience is
    # physics (who could hear), not secrecy: repeating what you said in one
    # room in front of a newcomer is not leaking a confidence.
    confidential = [
        rec
        for rec in history
        if rec.audience is not None
        and getattr(rec, "audience_origin", "whisper") == "whisper"
        and rec.content_type != "thought"
        and record_visible_to(rec, speaker_id)
        and not exposed_ids <= cover(rec)
    ]
    if not confidential:
        return set()
    outsider_known: set[str] | None = None
    for exposed_id in exposed_ids:
        listener_known = known_tokens(history, exposed_id, characters, scene)
        outsider_known = (
            listener_known if outsider_known is None else outsider_known & listener_known
        )
    known = outsider_known or set()
    secret: set[str] = set()
    for rec in confidential:
        secret |= {token for token in payload_tokens(rec.content) if token not in known}
    return secret


def redact_tokens(text: str, secret: set[str]) -> str:
    """Replace every secret token with the neutral marker, collapsing runs."""
    if not text or not secret:
        return text
    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(token) for token in sorted(secret)) + r")\b",
        re.IGNORECASE,
    )
    redacted = pattern.sub(REDACTION_MARKER, text)
    marker = re.escape(REDACTION_MARKER)
    return re.sub(rf"{marker}(?:[\s\-,;:/.]*{marker})+", REDACTION_MARKER, redacted)
