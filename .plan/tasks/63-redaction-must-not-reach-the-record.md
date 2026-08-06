# Task 63 — Redaction must not reach the persisted record

> **Status:** open. **Wave 1**, but sequenced **after 68 and 65**: 68's scanner
> decides which fix is correct, and 65 removes 42 of this task's 43 cases.
>
> An earlier draft proposed a fix that a blind reviewer argued would make the
> reading *worse*. That objection is recorded below and is the reason this task
> does not prescribe a single solution.

## Problem

`src/agents/narrator.py:783-788` redacts the content of **every**
`perception_event` against `hidden_thought_tokens`:

```python
thought_secret = hidden_thought_tokens(history, characters, scene)
for event in result["perception_events"]:
    content = normalize_generated_text(event["content"])
    if thought_secret:
        content = redact_tokens(content, thought_secret)
    event["content"] = content
```

Two properties make this over-fire, and they compound:

**The set is global.** Compare the signatures in `src/confidentiality.py`:

```python
def hidden_whisper_tokens(history, viewer_id, characters, scene)  # per viewer
def hidden_thought_tokens(history, characters, scene)             # no viewer
```

A token is "thought-only" if it appears in *any* character's private thought and
in no non-thought record. With 21 characters thinking every turn, that set is
large and it is applied to everybody.

**The payload window is wide, and narration does not count as known.**
`payload_tokens` (`confidentiality.py:78-104`) marks any rare token within
`PAYLOAD_WINDOW = 7` word positions of an anchor, where an anchor is a
mid-sentence capital, a digit or a CAPS token. With 21 proper names on stage,
nearly every sentence has an anchor and fourteen words around it are eligible.
And `hidden_thought_tokens` deliberately excludes narration from the "known" set
(module docstring), so an ordinary word the prose uses but nobody has literally
*said* stays eligible.

The result is that ordinary vocabulary is censored out of public dialogue.

## Evidence

**69 occurrences of `REDACTION_MARKER` across 15 of 16 transcripts** (49 in P1
alone; `base-P1-r2` is the only session with zero). The captured words are not
secrets:

- `base-P1-r3` T21 — *"Maelis ordena, com a **[indistinct]** erguida"* — the
  word is `bengala`, her cane, described in her own body sheet.
- *"Nix… grita: 'Tem algo vivo aí dentro! Eu **[indistinct]** cheiro!'"* — `sinto`.
- `base-P1-r3` T7 — *"As segundas portas **[indistinct]** abertas"* — `estão`.
- `null-P1-r2` — *"a masmorra não **[indistinct]** quem **[indistinct]** sem
  ordem"*.
- `base-P1-r3` line 633 — inside the **italic narration**, not dialogue.

This is the owner's immersion-breaker #2 in its plainest form: the machinery
becoming visible in the fiction. No metric in the project looked at it.

**It also reaches the memory ledger.** In `oldcode-P1-r1`'s `state.json`, 1,714
marker occurrences total: **1,699 in per-turn `perspective_snapshot`s** and
**6 in the live `character_perspectives` ledger**. The 1,699 are snapshot history
of the same memories, so the honest figure is *six corrupted live memory entries
in one session* — smaller than it first looks, and still a different class of
damage from a mangled transcript line: it is what a character will recall next
turn. This is where the task touches **task 59**, which is about who may know
what.

## Direction — and why this task does not prescribe one

The obvious fix is: redact only in the **per-viewer projection**, as
`runner.py:1445` already does with `hidden_whisper_tokens`, and on the persisted
path **fail closed** — drop an event that cannot be safely published rather than
publish mutilated text.

**A blind reviewer's objection, which stands:** that converts 69 mutilated words
into 69 *dropped events*. Dropping *"Maelis raises her cane and orders everyone
back"* because `bengala` is thought-tainted removes a decision from the story
silently. Against a phase whose headline complaint is *the scene does not move*,
trading visible garbage for invisible absence is not self-evidently better.

So the options to weigh, with the scanner's numbers in hand:

1. **Per-viewer projection only**, no drop — the guard still protects the viewer
   who must not know, and the persisted record keeps its words.
2. **Count narration as known**, closing the laundering asymmetry that makes
   prose vocabulary eligible in the first place.
3. **Require the anchor inside the event itself**, not anywhere in history —
   narrows the payload set enormously.
4. **Fail closed with a drop**, as originally proposed — only if the scanner says
   the drop count is small.

~~**Run 68's scanner first.** If the answer is "five events per session would be
dropped", option 4 ships. If it is twenty, it does not.~~

> ## ✅ Decided 2026-08-05 — option 1, and the drop path is dead
>
> The paragraph above chooses an architecture by counting how much content the
> cheap version destroys. Under `AGENTS.md` §2 there is nothing to shop for:
> **redaction moves to the per-viewer projection and the persisted record keeps
> its words.** More work and possibly more calls; neither is a reason.
>
> **Option 4 (fail closed with a drop) is rejected outright**, not deferred. A
> dropped event is a decision removed from the story to make a guard's life
> easier — Case 20's rule against buying quiet instead of movement, and the exact
> shape the withdrawn `NSR` gate would have scored as an improvement.
>
> **Option 2 (count narration as known) still ships alongside**, because the
> laundering asymmetry is a real defect independent of where redaction runs.
> **Option 3 (anchor inside the event)** is now optional: it narrowed the payload
> set to make dropping survivable, and nothing is being dropped.
>
> 68's scanner is still run before and after — not to choose the fix, but as the
> before/after evidence. The numbers are in the section above.

### 68's scanner has run — the numbers, 2026-08-05

`benchmarks/*/immersion-scan.json`, defined in `benchmarks/README.md` §8.

| channel | P1 (12 sessions) | P2 (4) |
|---|---|---|
| persisted **speech/action** records carrying a marker | **42** | **15** |
| **narration** records carrying one | 7 | 4 |
| **ledger** entries carrying one | **33** | **6** |
| total occurrences | **87** | **28** |

**The ledger is the part this task was under-counting.** The 49 P1 markers this
file was written against are the ones visible in a transcript. The scanner finds
**87**, because 38 more sit in `character_perspectives` — and not in the identity
ledger (`people`, **zero** occurrences in the whole archive) but in
`recent_memory` and `memory_summary`: what a character *remembers being said*.
One mutilated public line propagates into every witness's durable memory, so the
persisted-record count understates the reach by roughly a factor of two, and it
survives the compaction window through `memory_summary`.

That does not change which option is right, but it raises the cost of getting it
wrong, and it adds a closure item: the ledger channels have to be re-scanned
after the fix, not just the transcript. The drop-count question option 4 turns on
is still unanswered — it needs a live cell, which is post-65 work by the
sequencing above.

## Dependency on task 65

**42 of the 43** persisted records carrying the marker fuzzy-match a Director
`audible_speech` event; the 43rd is a narration record echoing one. Task 65
removes that channel. These are not two overlapping tasks — they are one
population, and measuring them as independent wave-1 cuts would have them fight
over the same counterfactual. Ship 65 first, re-scan, then size this.

## Closure evidence required

- [x] 68's channel-split scanner run over the archive **before** the fix is
      chosen (numbers above); the chosen option still has to be justified against
      them in this file;
- [ ] zero `REDACTION_MARKER` in any persisted speech record and in prose;
- [ ] zero in the live `character_perspectives` ledger — **all three sub-channels**
      (`recent_memory`, `memory_summary`, `people`), not only the identity one;
- [ ] the guard still works: a seeded whisper with a rare token does not reach a
      non-hearer's prompt, and a seeded thought-only token does not surface as a
      perception event — both asserted against the real builders;
- [ ] no event silently disappears without a counted, logged reason;
- [ ] if a drop path ships, the drop count is measured on one live cell — and the
      question *"did dropping remove decisions from the story?"* is answered by
      the blind read, not by `NSR` (see `.plan/ROADMAP.md` on the inverted gate;
      a dropped event is exactly the shape `NSR` would score as an improvement).

**The measurement that would falsify this task:** if the scanner shows the marker
never reaches a persisted record or the ledger after task 65 lands, this is a
prose-rendering cosmetic issue and drops out of wave 1.
