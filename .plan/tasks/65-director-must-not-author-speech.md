# Task 65 — The Director must not author speech

> **Status:** open, **BLOCKED ON A SCOPE DECISION as of 2026-08-05.** Still wave
> 1, still the largest measured defect in the archive; two blind reviewers with
> different framings — one auditing logs, one reading transcripts as fiction —
> independently concluded it should be the first cut of the phase, and that
> stands.
>
> **What does not stand is the 65a/65b split.** It was drawn on the assumption
> that 64% of the channel duplicates a line that already exists. Verified against
> the archive before implementation, the real figure is **21–42%**; the majority
> of this channel is dialogue that exists nowhere else, and the prose renderer is
> structurally forbidden from carrying it. See "⚠ 65a's premise did not survive
> verification" below.
>
> Shipping 65a as originally written would delete **264–362 dialogue records**,
> not the ~18% the note below estimated — which is what Case 20's rule against
> buying quiet instead of movement exists to prevent.

## Problem

`Runner._persist_audible_speech` (`src/runner.py:1404`) takes the Director's
`audible_speech` perception events and persists `event["content"]` — **text the
Director just wrote** — as a spoken record attributed to a character.

That makes the Director a second speaker. `AGENTS.md` §3 says it is not one:

| Papel | Responsabilidade |
|---|---|
| Narrador | Mundo físico, consequência, transição, cena, humor e próximo falante |
| Personagem | **Somente fala** e pensamento subjetivo em primeira pessoa |

The Director's own prompt forbids it too — *"DIALOGUE OWNERSHIP: never invent new
dialogue… Record only the stimulus or words already spoken in HISTORY"*. It is a
prompt promise, and prompt promises lose; this one loses 28% of the time.

## Scale

Measured over the twelve P1 sessions, matching each persisted `speech` record
against the Director's `audible_speech` event texts (`SequenceMatcher > 0.85`):

**467 of 1,649 speech records — 28.3% — were authored by the Director.**
Present in **12 of 12** sessions, in every cell, on both engines, on both input
profiles. Per-session it ranges 21%–40%.

Nothing else in this phase is close. For comparison: the redaction marker appears
in 11 of 12 sessions and 69 times total; the internal-id leak is n=1.

## What it produces

- **Duplication.** A character speaks, then the Director restates it in the third
  person in the same turn. `oldcode-P1-r1` T4 stacks **three** — *"Garran anuncia
  em voz alta…"*, *"Riven questiona em voz alta…"*, *"Lorde Cassian propõe…"* —
  so the last beat of the turn is a summary of the turn.
- **Self-narration.** `null-P1-r1` T26-T28: *"Téo, da arquibancada, comenta em voz
  alta que a decisão de desqualificar Link foi dura demais…"* — Téo speaking
  about Téo.
- **The player's own words read back.** `base-P2-r1` T2. The human typed
  *"Continuo aqui."* The turn ends:
  > **Link:** Link responde, em tom neutro, que continua aqui.
  > **Link:** Link acrescenta que sim, concorda em continuar ali.
- **The internal-id leak.** `oldcode-P1-r1` T39, *"C17 ordena que C20 permaneça
  com os estilhaços e que C18 a acompanhe"* — one record, three ids, and it came
  through this channel. n=1 in the corpus.
- **The language flip.** `null-P1-r2` T2 has **four** Director `audible_speech`
  events in English under a pinned Brazilian Portuguese — *"Asword said that
  Link's portal showed precise control…"* — two of which persisted. **Zero**
  narration records in the corpus are English. This was filed against the prose
  renderer; it belongs here.
- **42 of the 43** persisted records carrying `[indistinct]` are on this channel.
  Task 63's target population is almost entirely this task's population.

The existing guard cannot catch any of it. `_echoes_recent_speech` compares
against `voices = {subject}` only — by design, *"another speaker saying the same
thing is not an echo"* (`tests/test_audible_speech_echo.py`). Paraphrase in the
third person by a different producer is exactly what it is built not to flag.

## Why the channel exists (do not delete the requirement)

WT-09, documented in the docstring at `runner.py:1407-1425`: a fact voiced to the
room must reach the memory of **every witness**, not just whoever happened to
reply that turn. Before this channel, events were rendered to the turn's repliers
and then discarded, so a silent witness never got the fact and memory — which
reads history — never had it. That need is real and stays.

**Only the producer of the text changes.**

## ⚠ 65a's premise did not survive verification — 2026-08-05

**The version below claimed a pure win with zero content loss. It is wrong, and
implementing it would delete between 264 and 362 lines of dialogue that exist
nowhere else in the session.** Read this section before the next one.

### What the 64% actually counts

*"64% of Director `audible_speech` events are for a character who was routed that
same turn, **so a persisted record already exists**"* — the first clause is right
(the scanner measures 66%), the second does not follow. "The character also spoke
this turn" is a proxy for "the Director restated the line they spoke", and the
proxy fails: the Director usually re-voices **something else**.

Measured over all 458 Director-authored records in P1, against every line the
same character spoke in the same turn **and the four before it** — the window the
existing echo guard uses — scored by shared content words, which is far more
forgiving of third-person paraphrase than the lexical ratio that found them:

| "restates a recent line" at overlap ≥ | restatements | **new content** |
|---|---|---|
| 0.3 — barely more than sharing a topic | 194 (42%) | **264 (58%)** |
| 0.4 | 135 (30%) | **323 (71%)** |
| **0.5** — a defensible reading | **96 (21%)** | **362 (79%)** |
| 0.8 — near-verbatim | 14 (3%) | **444 (97%)** |

**The conclusion is robust across the whole threshold range**: even at the most
generous setting, where "restatement" means little more than talking about the
same subject, the majority of this channel is new dialogue. Only **19 of 458**
are close paraphrases of the character's own line *in the same turn*, which is
the case the original text described.

### And the prose renderer cannot carry the content

This is what makes the cut expensive rather than merely debatable. The prose
prompt **never receives `audible_speech` content** — the event is filtered out of
`event_lines` entirely and `_stage_event_content` reduces it to *"X diz algo
audível para Y"* (`prose.py:98-107`, `:262`). That is a deliberate leak guard:
the renderer must not be able to re-voice dialogue.

So the persisted speech record is the **only** path by which those words reach
the reader. Dropping it does not move the line into narration; it removes it from
the story. Case 20's pre-registered rule binds directly: *a cut that buys quiet
instead of movement is a failure, not a fix.*

### What survives, and what this does to the 65a/65b split

The channel is still a role-boundary violation and still owns the duplication,
the self-narration, the player's words read back, the id leak, the language flip
and 40 of the redaction markers. **None of that is retracted.** What changes is
the shape of the fix:

- the population that can be dropped or referenced with no content loss is
  **21–42%**, not 64%;
- the population that needs a *producer*, not a deletion, is **58–79%** — it is
  the majority of the channel, and it was scoped as 65b's minority case;
- so **65b option 1 — route the character for a real line — stops being one of
  three alternatives for a corner and becomes the primary mechanism.** Costed
  against the archive it is roughly **+38 character calls per session (~+33%)**,
  which is the number that has to be decided before anything ships.

**Nothing is implemented against the section below until that fork is chosen.**

## 65a — the half with no design risk (wave 1) — SUPERSEDED, see above

Measured by the audit: **64%** of Director `audible_speech` events are for a
character who **was routed that same turn**, i.e. the character agent produced a
real line and the Director restated it. For these, a persisted record already
exists.

Direction: persist a **reference** to the existing record, never the Director's
text. Where the referenced line already exists in history, the Director's version
is dropped with zero content loss — it was duplication.

~~This is the pure win.~~ It kills all the duplication, the self-narration, the
player-words-read-back, and the id leak; it takes most of `[indistinct]` with it
— **and it deletes the majority of the channel's content along with them.**

## 65b — the open question (wave 3)

The other **36%** are for a character who was **not routed that turn**. There is
no agent output to reference. Referencing-only deletes them — roughly **18% of
all dialogue in the corpus**.

Case 20's pre-registered rule binds here: *a cut that buys quiet instead of
movement is a failure, not a fix.* So 65b is a design question, not a cut:

- have the Runner route the character for a real line when the Director wants one
  voiced (costs a call, keeps the role boundary); or
- let the Director emit a *stimulus* (not dialogue) that a later turn's character
  agent may voice; or
- accept a narrated, unattributed record — audible to witnesses, owned by no
  speaker.

**Ship 65a, then measure at the checkpoint before choosing.**

> **Corrected 2026-08-05.** This line used to read *"ship 65a with an `NSR`/`SIL`
> interlock"*. That interlock does not work: `NSR` measures event volume and runs
> **anti**-correlated with read quality on this corpus (ρ = +0.923), `SIL` is
> `0.0` in 16/16 runs, and `base`'s own within-cell `NSR` spread (1.12) is 7× the
> effect 65a could produce. Derivation in `.plan/ROADMAP.md`.
>
> The question 65b needs answered is *"did removing 18% of the dialogue thin the
> fiction?"* — which is a reading question. **The blind read answers it**; a
> volume counter cannot. Re-run it at the checkpoint against the pre-65a
> transcripts.

## Counter-argument, recorded

*"28% is inflated — some of those matches are the Director faithfully echoing a
line, which is the WT-09 feature working."* Correct, and that is precisely the
64/36 split. The 64% is duplication because the original record is already there;
the echo adds a second copy. The 36% is the feature. The number that decides 65a
is not the 28% — it is that in the 64% case a persisted original **already
exists**, which is parameter-free.

> **This paragraph is the error, and it is left standing so the shape of it is
> visible.** It says the deciding number is "parameter-free", and it is: *whether
> the character was routed*. The mistake is that the parameter-free number
> **answers a different question** than the one the design needs. Routing tells
> you an agent ran; it does not tell you the Director restated what came out of
> it. Measuring the second question directly (above) moves the safe population
> from 64% to 21–42%. A number being clean and cheap is not evidence that it is
> the right number.

## The scanner exists, and this is its "before" — 2026-08-05

`tools/acceptance/immersion_scanners.py`, archived at
`benchmarks/*/immersion-scan.json` and defined in `benchmarks/README.md` §8. It
matches each persisted speech record back to the Director event in `debug.jsonl`
that produced it, because nothing in `state.json` distinguishes the two producers
— a re-voiced line carries `audience_origin='zone'` exactly like an ordinary one.

| | P1 (12 sessions) | P2 (4) |
|---|---|---|
| Director-authored speech records | **458 of 1,601 (28.6%)** | **181 of 618 (29.3%)** |
| sessions affected | **12 of 12** (21.3–40.6%) | **4 of 4** (24.5–33.1%) |
| …for a character routed that same turn | **303 (66%)** | **132 (73%)** |
| …carrying a redaction marker | 40 | 15 |

An independent re-derivation of this task's headline number, off a second
implementation. The threshold that separates the two producers is not a judgement
call: matched pairs score 0.857–1.000 (median 1.000) and the nearest non-match in
the whole archive is 0.827, an empty band the scanner's constant sits inside. One
record scores above the line unmatched, so **458 is conservative by one**.

## Closure evidence required

- [ ] no persisted speech record's text originates from a Director-authored
      `audible_speech` payload — the scanner from task 68, at zero
      (`director_speech.director_authored`, **458** in P1 today);
- [ ] WT-09 preserved: a test where a witness who did not reply can still recall
      a fact voiced to the room on a later turn;
- [ ] `oldcode-P1-r1` T39's id leak cannot recur — a test asserting no `C\d+`
      reaches a persisted record;
- [ ] a test that the player's own submitted line is never re-voiced back;
- [ ] the language-flip case: a Director event in the wrong language cannot
      become a persisted record;
- [ ] a blind read of the post-65a cell against the archived pre-65a transcripts,
      same protocol, judging whether the fiction thinned;
- [ ] 65b written up as its own decision with the three options costed, whichever
      is chosen.

**The measurement that would falsify this task:** if the blind read says the
post-65a sessions read thinner — fewer voices, flatter rooms — the duplication was
carrying narrative load and the reference-only direction is wrong. `NSR` is
reported alongside but decides nothing (see the correction above).
