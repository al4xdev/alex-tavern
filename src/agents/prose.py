"""Blind prose renderer (Task 36): confirmed public facts -> reader narration.

The renderer is the LAST box in the decision pipeline and the most restricted:
it receives ONLY what a reader is entitled to see — the public scene, the
reader-visible transcript so far, and the validated perception events of this
beat. It never receives personalities, knowledge sheets, private thoughts,
internal IDs in narrative position, world directives' secret canon, or any
unspoken reply. Prose leaks end structurally because there is nothing loaded
to leak (selection before the call, the principle measured at 0/13 vs 7/13).
"""

from __future__ import annotations

import difflib
import json
import re
from typing import Any

import httpx

from src.llm.client import call_agent, normalize_generated_text
from src.models import (
    Character,
    Scene,
    TurnRecord,
    display_name,
    record_visible_to,
    trim_history_by_tokens,
)

PROSE_SYSTEM = (
    "You are the prose narrator of a roleplay story. You receive the CONFIRMED\n"
    "events of the current beat and render them as immersive reader-facing\n"
    "narration.\n"
    "\n"
    "RULES:\n"
    "- Narrate ONLY the confirmed events and the visible scene. Never invent\n"
    "  outcomes, arrivals, discoveries, or reactions that are not in the events.\n"
    "- Ground the prose in the senses: name the concrete physical details a\n"
    "  witness would perceive. Third person, present tense, vivid but economical.\n"
    "- Never state anyone's thoughts, intentions, or emotions as fact; describe\n"
    "  observable evidence only.\n"
    "- Never write dialogue lines for anyone. If an event says someone spoke,\n"
    "  reference the act of speaking without inventing or repeating the words\n"
    "  beyond what the event states.\n"
    "- Do not repeat a sentence from the transcript.\n"
    "- LEXICAL VARIATION IS MANDATORY. Each beat must use fresh vocabulary, a\n"
    "  new sentence opening, and a different sensory angle than any earlier\n"
    "  narration. Never reuse a distinctive noun-phrase or clause you already\n"
    "  wrote (if a prior beat said 'the fire almost out', do not write it again;\n"
    "  find another image or drop it). Reusing prior phrasing is a failure.\n"
    "- Never reference unspecified speech (no 'says something', 'exchanges\n"
    "  words'); dialogue renders separately. Never narrate anyone's silence,\n"
    "  hesitation to answer, or non-response — and never present someone's\n"
    "  stillness or not-moving as an event. Omit anyone the events give\n"
    "  nothing new to do.\n"
    "- Characters in zones that cannot perceive each other must NEVER be staged\n"
    "  as sharing space, hearing one another, or being 'a few meters' apart —\n"
    "  cut between separated spaces explicitly.\n"
    "- You are omniscient for identities: always name characters by their\n"
    "  canonical names and never describe anyone as unknown or unidentified.\n"
    # Verbosity floor (Task 42): measured on real payloads, deepseek renders
    # ~120-270 chars without it; this single line at the END of the prompt
    # (position matters) lifted narration to ~570-1250 chars, 3/3 on two
    # scenes. A floor, never a cap - small beats still come out shorter.
    "- Narrate at least 150 words; a beat deserves full paragraphs.\n"
)


def _canonical_name(cid: str, characters: dict[str, Character], controlled_id: str) -> str:
    """Reader-facing name for a character id ('Player' resolves to the controlled one)."""
    return display_name(cid, characters, controlled_id)


def _transcript_content(
    record: TurnRecord, characters: dict[str, Character], controlled_id: str
) -> str:
    """Content shown to the blind renderer for one reader-transcript record.

    Speech content is structurally withheld (Task 36 hardening): the renderer
    receives a content-free 'someone spoke' marker, so it can NEVER re-voice a
    line in narration — the words are simply not loaded. Narration keeps its
    full content (the renderer's own prior prose, needed for continuity and
    anti-repetition) and actions keep theirs (physical, reader-visible).
    """
    if record.content_type != "speech":
        return record.content
    label = _canonical_name(record.speaker, characters, controlled_id)
    if record.audience is None:
        return f"{label} fala"
    audience = ", ".join(_canonical_name(cid, characters, controlled_id) for cid in record.audience)
    return f"{label} fala baixo (só {audience} percebem)"


def _stage_event_content(
    event: dict[str, Any], characters: dict[str, Character], controlled_id: str
) -> str:
    """Event content as the blind renderer may see it.

    An ``audible_speech`` event carries the spoken words in ``content``; the
    renderer gets a deterministic content-free staging line instead (who spoke,
    to whom), so no spoken words can reach the prose prompt through the events
    channel either. Non-speech events keep their content.
    """
    if event.get("event_kind") != "audible_speech":
        return str(event["content"])
    subject = _canonical_name(str(event.get("subject_id", "")), characters, controlled_id)
    witnesses = [
        _canonical_name(str(cid), characters, controlled_id)
        for cid in event.get("witness_ids") or []
    ]
    audience = ", ".join(witnesses) if witnesses else "os presentes"
    return f"{subject} diz algo audível para {audience}"


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_MIN_SENTENCE_CHARS = 25
_SIMILARITY_THRESHOLD = 0.85
# A single near-verbatim sentence echo (the fire "goes out" rendered twice) is
# a lexical-variation failure even when the rest of the beat is fresh; the
# >half-of-sentences rule missed it. Fire the retry on any one qualifying
# sentence at or above this bar, tuned to catch near-verbatim reuse without
# tripping on ordinary thematic callbacks.
_PER_SENTENCE_ECHO_THRESHOLD = 0.8

REPETITION_CORRECTION = (
    "CORRECTION: your previous draft repeated earlier narration nearly "
    "verbatim. Write this beat fresh: new sentence structures, new observed "
    "details, no reuse of prior phrasing."
)


def _normalize_sentence(text: str) -> str:
    return " ".join(text.lower().split())


def _qualifying_sentences(text: str) -> list[str]:
    sentences = (_normalize_sentence(s) for s in _SENTENCE_SPLIT.split(text))
    return [s for s in sentences if len(s) >= _MIN_SENTENCE_CHARS]


def _repeats_prior_narration(new_text: str, history: list[TurnRecord]) -> bool:
    """True when the new narration is a near-verbatim echo of prior narration.

    Deterministic guard for the measured failure modes: the whole text is
    above 0.85 similar to a prior narration (identical paragraphs on
    consecutive turns), OR even a single qualifying sentence near-verbatim
    echoes a prior narration sentence (the fire "goes out" rendered twice) —
    lexical variation is a first-class acceptance criterion (Task 38).
    """
    prior_texts = [r.content for r in history if r.content_type == "narration"]
    if not prior_texts:
        return False
    whole_new = _normalize_sentence(new_text)
    for prior in prior_texts:
        ratio = difflib.SequenceMatcher(None, whole_new, _normalize_sentence(prior)).ratio()
        if ratio > _SIMILARITY_THRESHOLD:
            return True
    new_sentences = _qualifying_sentences(new_text)
    if not new_sentences:
        return False
    prior_sentences = [s for text in prior_texts for s in _qualifying_sentences(text)]
    if not prior_sentences:
        return False
    return any(
        difflib.SequenceMatcher(None, sentence, prior).ratio() >= _PER_SENTENCE_ECHO_THRESHOLD
        for sentence in new_sentences
        for prior in prior_sentences
    )


def _strip_echoed_sentences(new_text: str, history: list[TurnRecord]) -> str:
    """Drop sentences that near-verbatim echo prior narration; keep the rest.

    Final deterministic backstop when the retry still repeats: splits on
    sentence boundaries (keeping the delimiters) and removes any qualifying
    sentence at/above the per-sentence echo bar. Returns the surviving prose,
    or "" if nothing survives (the caller then keeps the model's draft).
    """
    prior_sentences = [
        s
        for record in history
        if record.content_type == "narration"
        for s in _qualifying_sentences(record.content)
    ]
    if not prior_sentences:
        return new_text
    parts = re.split(r"(?<=[.!?…])\s+", new_text)
    kept: list[str] = []
    for part in parts:
        norm = _normalize_sentence(part)
        if len(norm) >= _MIN_SENTENCE_CHARS and any(
            difflib.SequenceMatcher(None, norm, prior).ratio() >= _PER_SENTENCE_ECHO_THRESHOLD
            for prior in prior_sentences
        ):
            continue
        kept.append(part)
    return " ".join(p.strip() for p in kept if p.strip()).strip()


def _staging_lines(
    scene: Scene,
    characters: dict[str, Character],
    controlled_id: str,
    viewers: set[str] | None = None,
) -> list[str]:
    """STAGING block lines for the zone graph (empty when the scene is flat).

    Each zone lists which other zones it can hear, which it is acoustically
    isolated from, and who is inside (canonical names) — so the renderer can
    cut between separated spaces instead of collapsing them into one room.

    With ``viewers`` (task 71) only the zones that cluster stands in are staged.
    Naming a zone the audience cannot perceive is what made the rule at the top
    of `PROSE_SYSTEM` unfollowable: the renderer was told to cut between spaces
    and simultaneously handed both of them with nowhere else to put the second.
    """
    if not scene.zones:
        return []
    zones = scene.zones
    if viewers is not None:
        occupied = {
            position for cid, position in scene.positions.items() if cid in viewers
        }
        zones = {zone: audible for zone, audible in zones.items() if zone in occupied}
        if not zones:
            return []
    lines = ["STAGING (zone graph; audibility is one-way as listed):"]
    for zone, audible in zones.items():
        # An edge LEAVING the staged set names a place this audience cannot
        # perceive, which is the same leak one level down from the zone list.
        audible = [other for other in audible if other in zones]
        isolated = [z for z in zones if z != zone and z not in audible]
        occupants = [
            _canonical_name(cid, characters, controlled_id)
            for cid, position in scene.positions.items()
            if position == zone and (viewers is None or cid in viewers)
        ]
        hears = ", ".join(audible) if audible else "nothing outside itself (acoustically isolated)"
        iso = ", ".join(isolated) if isolated else "none"
        who = ", ".join(occupants) if occupants else "nobody"
        lines.append(f"  {zone}: hears {hears} | isolated from: {iso} | inside: {who}")
    return lines


def _blocking_lines(
    blocking: dict[str, str],
    characters: dict[str, Character],
    controlled_id: str,
    viewers: set[str] | None = None,
) -> list[str]:
    """BLOCKING block: where each person stands INSIDE the place they occupy.

    Task 79. The Director writes this on every call and `narrate()` used to throw
    it away, so the renderer staged people by zone NAME - a string no instrument
    in this project can interpret (five registered false positives). This hands it
    the Director's own words instead: "junto à saída lateral" rather than
    "Salão dos Quatro Arcos".

    ``viewers`` scoping is not cosmetic. ``character_zones`` covers EVERY present
    character, so handing it over whole would put cluster B's positions in cluster
    A's prompt - the cross-cluster leak task 71 closed from 16/29 to 3/78, coming
    back through a new door. It is filtered by the same set that scopes the cast.
    """
    if not blocking:
        return []
    lines = []
    for cid, where in blocking.items():
        if viewers is not None and cid not in viewers:
            continue
        if cid not in characters:
            continue
        lines.append(f"  {_canonical_name(cid, characters, controlled_id)}: {where}")
    if not lines:
        return []
    return [
        "BLOCKING (where each person is standing right now; narrate from it, "
        "do not contradict it):",
        *lines,
    ]


def build_prose_messages(
    scene: Scene,
    characters: dict[str, Character],
    controlled_id: str,
    history: list[TurnRecord],
    events: list[dict[str, Any]],
    context_max: int | None = None,
    max_tokens: int = 1024,
    viewers: set[str] | None = None,
    blocking: dict[str, str] | None = None,
) -> list[dict]:
    """Reader-entitled inputs only.

    Appearance and outfit are included (the reader sees bodies); minds are not.
    History is the READER transcript: narration plus public speech/actions —
    thoughts and whispered actions stay out. Spoken WORDS never enter at all:
    every speech record is reduced to a content-free marker (who spoke, and for
    whispers, who perceived it), so the renderer cannot re-voice dialogue in
    narration — there is nothing loaded to re-voice. The same holds for
    ``audible_speech`` events, staged as content-free lines.

    ``viewers`` (task 71) scopes every block to one perception cluster: the
    cast, the staging, the transcript and the events. Left at ``None`` the
    output is byte-identical to the pre-71 prompt, which is what keeps the
    unsplit turns - the majority - on exactly the path they were on.

    Scoping the TRANSCRIPT matters as much as scoping the events. A record
    carries the audience the engine computed for it, so a line spoken in the
    other half of a split scene is already marked unreachable; passing it in
    anyway would let the renderer allude to it even with the events clean.
    """
    cast_lines = [
        f"  {character.mind.name}: {character.body.physical_description[:200]} | "
        f"wearing: {character.body.outfit[:120]}"
        for cid, character in characters.items()
        if viewers is None or cid in viewers
    ]
    visible = [
        record
        for record in history
        if record.content_type in ("narration", "speech")
        or (record.content_type == "action" and record.audience is None)
    ]
    if viewers is not None:
        visible = [
            record
            for record in visible
            if any(record_visible_to(record, viewer) for viewer in viewers)
        ]
    if context_max is not None:
        visible = trim_history_by_tokens(visible, context_max, max_tokens)
    transcript = [
        f"  {display_name(r.speaker, characters, controlled_id)} "
        f"[{r.content_type}]: {_transcript_content(r, characters, controlled_id)}"
        for r in visible
    ] or ["  (story opening)"]
    # Dialogue shows itself as dialogue lines; staging "someone says something"
    # in prose produced phantom unspecified speech ("Bento diz algo para Rui")
    # and narrated the protagonist's silence. The renderer only narrates
    # NON-SPEECH events.
    scoped_events = events
    if viewers is not None:
        scoped_events = [
            event
            for event in events
            if viewers & (set(event.get("witness_ids") or []) | {event.get("subject_id")})
        ]
    event_lines = [
        f"  - ({event['event_kind']}) {_stage_event_content(event, characters, controlled_id)}"
        for event in scoped_events
        if event.get("event_kind") != "audible_speech"
    ] or ["  - Nothing new happens; render a short atmospheric beat."]
    staging = _staging_lines(scene, characters, controlled_id, viewers)
    staging_block = "\n".join(staging) + "\n\n" if staging else ""
    # Left at None the prompt is byte-identical to the pre-79 one, which is what
    # keeps every existing renderer and every archived comparison on their own
    # path — the same guarantee task 71 made for `viewers`.
    blocking_lines = _blocking_lines(blocking or {}, characters, controlled_id, viewers)
    blocking_block = "\n".join(blocking_lines) + "\n\n" if blocking_lines else ""
    # Measured leak, session `c76037ff` 2026-08-12: scoping the cast, staging and
    # events is not enough, because the TRANSCRIPT reintroduces the other half.
    # Narration rendered while the scene was still whole is `audience=None` and
    # therefore visible to every cluster forever - correctly, the reader did see
    # it happen. The renderer then continued that thread into the PRESENT, giving
    # Marta Ferrolume kneeling at a lock in three consecutive turns to a group
    # that could no longer perceive her, with no event of this beat mentioning
    # her at all. Remembering her is right; narrating what she is doing now is
    # not, and the roster is the line that says which is which.
    roster_block = ""
    if viewers is not None:
        roster = ", ".join(
            sorted(_canonical_name(cid, characters, controlled_id) for cid in viewers)
        )
        roster_block = (
            "IN THIS VIEW (the only people whose PRESENT actions you may narrate; "
            "others may be remembered as past events, never shown acting now):\n"
            f"  {roster}\n\n"
        )
    user = (
        f"SCENE: {scene.location} | {scene.time_of_day}\n"
        f"PHYSICAL FACTS: {json.dumps(scene.physical_facts, ensure_ascii=False)}\n"
        "CAST (visible appearance only):\n"
        + "\n".join(cast_lines)
        + "\n\n"
        + roster_block
        + staging_block
        + blocking_block
        + "READER TRANSCRIPT (oldest to newest):\n"
        + "\n".join(transcript)
        + "\n\n"
        "CONFIRMED EVENTS OF THIS BEAT (narrate exactly these):\n" + "\n".join(event_lines)
    )
    return [
        {"role": "system", "content": PROSE_SYSTEM},
        {"role": "user", "content": user},
    ]


def _offstage_name_patterns(
    scene: Scene,
    characters: dict[str, Character],
    controlled_id: str,
    viewers: set[str],
) -> list[re.Pattern[str]]:
    """Patterns matching ONLY present characters outside this cluster.

    **A surname can be an ordinary noun.** The first version of this guard
    matched any name token case-insensitively and deleted three atmospheric
    sentences from `c76037ff` for containing *"véu"* — Portuguese for veil, and
    also the surname of Noa Véu, who was not in them. That is the `menos` bug of
    task 70 in a new costume: a guard validated on the corpus that happens not
    to contain its own counter-example.

    So a multi-token name must match in FULL and adjacent, which no ordinary
    noun does, and a single-token name must match with its capital, which an
    ordinary noun in mid-sentence does not. Measured on the split narrations of
    both post-71 sessions: fires on all three known leaks, and on none of the
    other thirty-nine.

    A pattern that would also match somebody IN the cluster is dropped: a false
    negative costs one stray sentence, a false positive deletes prose the reader
    is entitled to.
    """
    on_stage = [_canonical_name(cid, characters, controlled_id) for cid in viewers]
    patterns: list[re.Pattern[str]] = []
    for cid in scene.present_characters:
        if cid in viewers or cid not in characters:
            continue
        name = _canonical_name(cid, characters, controlled_id).strip()
        tokens = name.split()
        if not tokens or len(name) < 3:
            continue
        if len(tokens) > 1:
            body = r"\s+".join(re.escape(token) for token in tokens)
            pattern = re.compile(rf"\b{body}\b", re.IGNORECASE)
        else:
            pattern = re.compile(rf"\b{re.escape(tokens[0])}\b")
        if any(pattern.search(other) for other in on_stage):
            continue
        patterns.append(pattern)
    return patterns


def _strip_offstage_actors(
    text: str,
    scene: Scene,
    characters: dict[str, Character],
    controlled_id: str,
    viewers: set[str],
) -> str:
    """Drop sentences that stage someone this cluster cannot perceive.

    The measured residual of task 71 (session `c76037ff`): scoping the cast,
    staging and events still leaked, because past PUBLIC narration stays in the
    reader transcript forever - correctly, that reader watched it happen - and
    the renderer carried the thread into the present, giving Marta Ferrolume
    kneeling at a lock across three consecutive turns to a group that could no
    longer perceive her, with no event of the beat naming her.

    The `IN THIS VIEW` roster asks the model not to. This makes it true whatever
    the model does, which is the difference the project keeps re-learning: a
    prompt promise with no structure behind it loses (task 59, finding 1).

    Mirrors `_strip_echoed_sentences` deliberately, including returning "" when
    nothing survives so the caller keeps the draft: a leaking paragraph is worse
    than no paragraph only if there IS another paragraph.
    """
    patterns = _offstage_name_patterns(scene, characters, controlled_id, viewers)
    if not patterns:
        return text
    parts = re.split(r"(?<=[.!?…])\s+", text)
    kept = [part for part in parts if not any(p.search(part) for p in patterns)]
    # Returning the ORIGINAL when nothing was dropped, rather than a rejoined
    # copy: the rejoin normalizes whitespace, which made 5 of 32 untouched
    # narrations look modified by one or two characters the first time this was
    # measured. A guard that reports work it did not do cannot be audited.
    if len(kept) == len(parts):
        return text
    return " ".join(part.strip() for part in kept if part.strip()).strip()


def build_prose_schema() -> dict:
    return {
        "name": "prose_narration",
        "schema": {
            "type": "object",
            "properties": {"narration": {"type": "string"}},
            "required": ["narration"],
            "additionalProperties": False,
        },
    }


async def render_narration(
    client: httpx.AsyncClient,
    scene: Scene,
    characters: dict[str, Character],
    controlled_id: str,
    history: list[TurnRecord],
    events: list[dict[str, Any]],
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
    viewers: set[str] | None = None,
    blocking: dict[str, str] | None = None,
) -> str:
    max_tokens = int(config.get("max_tokens_narrator", 2048))
    messages = build_prose_messages(
        scene,
        characters,
        controlled_id,
        history,
        events,
        context_max=config.get("context_max"),
        max_tokens=max_tokens,
        viewers=viewers,
        blocking=blocking,
    )
    # Shared by the first attempt and the anti-repetition retry below.
    request_kwargs: dict[str, Any] = {
        "agent": "prose",
        "json_schema": build_prose_schema(),
        "max_tokens": max_tokens,
        "session_id": session_id,
        "turn_number": turn_number,
    }
    result = await call_agent(client, config, messages, **request_kwargs)
    narration = str(result.get("narration", "")).strip()
    if _repeats_prior_narration(narration, history):
        # Deterministic anti-repetition guard (measured failure: the same
        # paragraph rendered on consecutive turns). Retry ONCE with an explicit
        # correction. deepseek sometimes reproduces the offending sentence even
        # after the retry (a persistent world state re-narrated verbatim), so a
        # final deterministic backstop strips any sentence that still echoes
        # prior narration — dropping a verbatim repeat loses nothing the reader
        # has not already read, and guarantees the lexical-variation invariant
        # by construction rather than by instruction.
        retry_messages = messages + [{"role": "user", "content": REPETITION_CORRECTION}]
        result = await call_agent(
            client, config, retry_messages, guard_retry="repetition", **request_kwargs
        )
        narration = str(result.get("narration", "")).strip()
        if _repeats_prior_narration(narration, history):
            narration = _strip_echoed_sentences(narration, history) or narration
    if viewers is not None:
        # Structural half of the cross-cluster guard; the roster block is the
        # instruction half. Measured 3 leaks in 32 split narrations with only
        # the instruction, all of them a remembered character shown acting in
        # the present.
        narration = _strip_offstage_actors(
            narration, scene, characters, controlled_id, viewers
        ) or narration
    return normalize_generated_text(narration)
