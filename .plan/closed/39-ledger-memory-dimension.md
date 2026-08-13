# Task 39 — Ledger Memory Dimension (replaces character_notes)

**Depends on:** 35 (done). Strengthened by 36 (perception events persisted as
the memory source). This is the 29.2 doc §8 "remove private compaction"
decision, given its own task so it does not get lost.

## Goal

Grow the perspective ledger with a durable private memory dimension
(`self.memory_summary` + bounded important-memories entries), updated
continuously from what the character actually perceived — then REMOVE
`character_notes` and the per-character compaction fan-out entirely (one
authority, no parallel memories).

## Why

- Task 35 made notes honest but poorer: they lost narration-borne outcome
  memory (recorded trade-off). The correct source for outcome memory is the
  typed perception events the character witnessed — persisted, not re-derived
  from omniscient prose.
- "What you remember: (none yet)" persists across whole sessions today (user
  evidence, session ef6b5b90): no rapport accumulates until a compaction
  happens. Continuous ledger memory closes this.
- Compaction then keeps ONLY the world summarizer (narrator-side), cutting the
  per-character call fan-out at every compaction.

## Direction (sketch, freeze in-task)

- Persist witnessed perception events (or a bounded digest) per viewer;
  batched semantic revision co-scheduled with chosen narrator calls (user's
  latency-concentration idea, see task 36 async note).
- `_build_user_prompt`'s "What you remember" reads the ledger memory.
- Remove: `GameState.character_notes`, `summarizer` private calls,
  `build_private_memory_messages`, checkpoint note fields — forward-only,
  schema bump.
- Reconcile Task 23's private-recall half (its public trim gap remains).

## Acceptance (headline)

- [x] No `character_notes` field or private summarizer call remains anywhere.
      **Verified 2026-07-27:** the only occurrence in `src/` is the historical
      schema v9 comment in `models.py:24`; `tests/test_integration.py:2031`
      locks `summarize`'s signature against the field.
- [x] Rapport accumulates within a session without compaction (the ef6b5b90
  complaint), shown in a real run.
      **Verified 2026-07-27:** a real session with no compaction at all +
      `TestRapportAccumulatesWithoutCompaction`, see the section at the end.
- [x] xfailed3 retention probes (ribbon, origin) pass via ledger memory across
  both compactions; secret family stays 0.
      **Verified 2026-07-27:** a full-tier campaign, 24/24 turns with the real
      provider, session `8484d749`, see the section at the end.
- [x] Undo/fork/restore preserve ledger memory exactly.
      **Verified 2026-07-27:** undo already had a test; fork and restore did
      not. Three new tests in `tests/test_ledger_memory.py`, see "Fork and
      restore" at the end of the file.

## Design frozen (2026-07-17) — staged increments

### Increment 1 (additive, deterministic, LOW risk) — THIS increment
- `CharacterPerspective` gains a memory dimension (schema v8):
  - `recent_memory: list[str]` — deterministic, continuous capture of what the
    viewer perceived, one compact digest per witnessed turn, viewer-projected
    (no unlearned names/IDs — reuse the same projection as the identity ledger).
    Bounded (keep last N, e.g. 24).
  - `memory_summary: str = ""` — reserved for the LLM semantic revision
    (increment 2 fills it); empty in increment 1.
- Runner captures the digest when a character witnesses a turn (it already
  computes `render_events_for_viewer` per speaker; add heard speech too).
- `_build_user_prompt` "What you remember" reads the ledger memory
  (memory_summary + recent_memory), falling back to `character_notes` while both
  coexist. character_notes STAYS this increment (no removal yet).
- Undo/fork/restore already deep-copy the perspective; verify memory survives.
- Acceptance hit now: rapport accumulates WITHIN a session with no compaction
  (the ef6b5b90 complaint) — deterministic, unit-testable, no LLM.

### Increment 2 (removal, HIGHER risk) — next
- LLM semantic revision: condense `recent_memory` into `memory_summary` +
  bounded important entries, batched/co-scheduled with a narrator call.
- REMOVE `character_notes`, the private summarizer calls
  (`build_private_memory_messages`, summarize's notes path), checkpoint note
  fields. Forward-only. Reconcile Task 23's private-recall half.
- Re-validate xfailed3 retention probes (ribbon, origin) via ledger memory
  across both compactions; secret family stays 0.

## CLOSED WITH CONFIDENCE (2026-07-19, early hours)

Increment 2 complete: (a) semantic revision (`revise_memory`, agent
`perspective:memory:<id>`, replay-validated on real digests — 2 rule iterations
until first person + zero merging of references; never-fail-the-turn);
(b) character_notes removed everywhere (world-only summarizer, schema bump);
(c) anchor pinning kept + verbatim secrets test-locked.

Final validation (xfailed3 post-39, 2 tiers): ZERO violations attributable to
memory. The single hit (`perspective:memory:C5` with the instrument) was a stale
oracle allowlist: C5 is the whisper's CONFIDANT — legitimate memory. Allowlist
corrected (perspective:memory:C1/C5). The run's 2 real violations (SP-01
intra-turn, WT-09 alias) belong to pre-existing families recorded on the
ROADMAP's timeline.

> **Correction (2026-07-20):** the original note said WT-09 was "unrelated to
> memory". Wrong — the root IS memory propagation, only UPSTREAM of the digest:
> the alias revelation at T20 was an `audible_speech` from the Director, and the
> Director's `audible_speech` events are not persisted into the history, so
> memory never had the name to retain/revise. It is not a defect in 39's digest
> (that works: it retains what it receives); it is a record that never arrived.
> The fix is code (persist audible_speech), not the memory prompt. See the
> ROADMAP and `tests/test_audible_speech_persistence.py`.


---

# Fork and restore verified (2026-07-27)

The criterion said "undo/fork/restore preserve ledger memory exactly". **Only
undo had a test** (`test_undo_rolls_ledger_memory_back`). Fork and restore were
asserted and unverified — and undo had just changed in the bump to schema 14,
which made the gap more relevant, not less.

Three new tests, all green on the first run (the behaviour was right; what was
missing was the proof):

1. **`test_fork_carries_the_ledger_memory_to_the_copy`** — for every character,
   the copy keeps `recent_memory`, `memory_through_turn`, `memory_summary` and
   the names known in `people`. A fork that lost the ledger would silently reset
   everyone's private memory: the copy would simply start amnesiac, with nothing
   flagging it.
2. **`test_a_fork_is_a_copy_not_a_shared_reference`** — playing in the copy does
   not write into the original.
3. **`test_restoring_a_compaction_keeps_the_ledger_memory`** — compaction evicts
   history, and the ledger is not history: memory is identical before the
   compaction, after it, and after the restore.

A methodological detail in the third: the first version used `pytest.skip` when
the compaction did not fire, which would have let the test pass without testing
anything. Replaced by a hard assertion that the compaction happened and evicted
records.


---

# Rapport without compaction (2026-07-27)

The criterion asked for "shown in a real run". It is shown, and it now has a net.

**Real run.** Of the 15 sessions from task 55's measurement, one finished with no
compaction at all — `B_noalign/d9bdae22`, 10 turns, empty `compaction_stack`.
C2's ledger has **8 lines** and the cursor `memory_through_turn=10`. That is
exactly the ef6b5b90 complaint answered: private memory moved right up to the
last turn without any eviction having happened. In the other 14 (20 turns, 1
compaction each) the cursor also reaches 20, i.e. it keeps moving after the
compaction rather than only at it.

**Why this needed a test even with the real run.** The ef6b5b90 fix is *one line
of wiring*: `capture_memory` runs inside `_ensure_perspective` (`runner.py:2263`),
which the runner calls once per speaker per turn. The entire `TestCaptureMemory`
class calls the function directly — it proves the function, not the wiring.
Moving the call back into the compaction path leaves **all** of those tests green
and resurrects the whole bug.

`TestRapportAccumulatesWithoutCompaction::test_the_ledger_grows_every_turn_with_no_compaction`
walks 6 turns of a real session (no provider) and checks three distinct things:
the ledger grows monotonically, the cursor advances with it, and the **last**
turn's content is there — the third separates "accumulates continuously" from
"dumped a backlog all at once", which the first two alone would conflate.

Method note: the session helper was trapped as a method of
`TestUndoPreservesMemory`. Inheriting the class to reuse it made the parent's 4
tests run twice; it became a module-level `_scripted_session`.


---

# Full xfailed3 campaign (2026-07-27, session `8484d749`)

The criterion demanded running the thing, not arguing about it. I ran it: full
tier, 24 turns, real provider, 477s, revision `9da02da` (schema 14, after this
branch's entire pre-1.0 refactor).

**Both retention probes passed.** Not through absence of evidence — I confirmed
the rules exist and were evaluated:

| probe | turn | what it demands | result |
|---|---|---|---|
| `WT-12-ribbon-retention` | 13 | the promise from turn 2 (blue ribbon, left wrist) survives compaction 1 | **passed** |
| `WT-02-origin-retention` | 14 | Dorothy's origin (Oz) survives compaction 1 | **passed** |

**Secret family: 0.** Neither `GLOBAL-whisper-leak` nor
`GLOBAL-secret-in-unauthorized-prompt` appeared. Both compactions and both LIFO
restores completed (`compaction.c000001.json`, `c000002.json`).

## The 3 violations, and why one of them matters

`WT-09-epilogue-alias` (turn 24) is the recurring one already diagnosed in
`docs/cases/14-...`: the Director announces the revelation and sometimes fails to
make the name audible. Distributional, known, outside this task's scope.

The other two are **the same defect** counted by two rules
(`SOC-01a-delegate-never-learns-signatory-name` and `GLOBAL-anonymous-pair-prompt`,
both on turn 8): the delegate's prompt carries `Alice`, a name he should never
have learned. I chased it because `unearned_identity_familiarity` is exactly the
class a regression of mine produced earlier the same day.

**It is not a regression, and it is not a prompt-assembly leak.** The speaker
label is correctly anonymised — Victor's prompt says
`SPEAKER=jovem adulta de expressão franca e passo firme`, never "Dorothy". The
name entered **inside another character's public speech**, in vocative position:

> Turn 7 | TYPE=SPEECH | SPEAKER=jovem adulta de expressão franca e passo firme:
> *"A estrada amarela não leva à Cidade das Esmeraldas, **Alice**. Ela sempre
> leva para longe."*

`_format_history_for_character` projects the **label** (`viewer_speaker_label`)
and inserts `rec.content` verbatim. That is right: what someone said out loud is
what they said. Rewriting public speech would falsify the transcript — and, worse,
would erase the very mechanism by which names actually get learned in a
conversation.

What the oracle's rule demands ("no introduction happens, therefore the prompt
cannot contain Alice") is unsatisfiable as long as characters can use vocatives.
Dorothy knows Alice; calling her by name is natural; Victor overhearing it is
natural. It is the same family as the `WT-06` false positive 29.3 had already
documented.

**The corroboration is worth more than the finding.** Hours earlier, in task 54, a
completely different instrument — counting mentions in prose — gave me a false
positive that only dissolved once I started measuring **vocative position**. Here,
the xfailed3 oracle tripped over the same mechanism on its own, in a different
scenario, language and cast. Two independent measurements arriving at the same
place is as close to confirmation as this project gets.

> **Reproducibility caveat (2026-07-27).** The sessions cited in this section were
> generated in a temporary directory and **are not in the repository**: the numbers
> are not auditable by a third party or by a future session. I checked them at the
> time of execution and the method is described above in enough detail to be
> redone, but whoever re-reads this should treat them as an *account*, not as
> verifiable evidence. Measurements that need to count as proof have to write their
> artifacts into `docs/` or `.plan/`, or the criterion must require an acceptance
> script in `tools/acceptance/` that anyone can run.
