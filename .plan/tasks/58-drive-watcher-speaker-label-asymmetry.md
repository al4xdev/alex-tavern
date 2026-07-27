# Task 58 — Speaker-label asymmetry in the drive and watcher context

> **Status:** open. Observation confirmed in code and in real prompts; the
> decision is deliberately NOT made here.
>
> **Note on framing.** The previous session found this, ran one measurement on
> it, and did form a preference about the outcome. That preference is
> deliberately left out of this document so the analysis can start clean; the
> owner has it and can introduce it after you have formed your own. Treat every
> section below as evidence, not as argument.

## Observation

`recent_event_lines` (`src/prompting.py:41`) takes `resolve_names: bool = False`.
With the default, a character is labelled by whatever `speaker_label`
(`src/models.py:444`) returns, and `speaker_label` translates only the internal
`Player` marker. The result is that the human-controlled character is rendered
by NAME and every other character by internal ID, in the same list.

Real prompt, `drive:event_seed`, unmodified:

```
RECENT EVENTS (oldest to newest):
  Thorn: Who runs this inn?
  Narrator: The tavern's dim candlelight flickers across scarred oak tables...
  C2: Hm, that depends. Do you mean the official owner on the charter...
```

`Thorn` is the controlled character (`C1`). `C2` is not.

Two consumers use the default: `stalled_scene_context` (`src/prompting.py:83`),
which feeds `drive.build_event_seed_messages` (`src/drive.py:61`) and
`watcher` (`src/watcher.py:324`). The third caller, `roteiro`
(`src/roteiro.py:380`), passes `resolve_names=True` and does not have the
asymmetry.

Measured on one real session: 3 lines carrying a name, 3 carrying an ID, in a
single context block.

## Why this may or may not matter — both readings, stated plainly

**Reading A — it is an ID hygiene problem.** The concern is that a model reads
`C2` as a proper noun. There is precedent: the summarizer, given `SPEAKER=C2`
with no roster, invented a third cast member ("a group (Thorn, Lyra, and a
talkative companion called C2)") and collapsed two people into one token, in 11
of 15 real story summaries (fixed in `33648e0`). The `event` returned by the
drive becomes the Director's `narrator_hint`, which the Director is instructed
to materialise, so an ID inside it is text the system pushes toward narration.

**Reading B — it is an agency-lock problem.** `AGENTS.md` §3 says no agent may
learn that a human drives one of the characters, or which one. The asymmetry
marks exactly one character differently from every other, in every drive and
watcher prompt. Compare the Director's routing constraint fixed in `5002f11`,
where singling out one ID was itself treated as the leak, independent of any
word like "player" appearing.

The two readings imply different bars. Under A this is a quality trade-off and a
measurement decides. Under B it is an invariant and a measurement does not apply.
**Deciding which reading governs is the substance of this task.**

## The measurement that already exists, and its limits

`tools/acceptance/drive_label_ab.py`, run 2026-07-27, n=80 per arm, real
provider, 4 real game states. Rule fixed before the run: the names arm wins only
if it (1) yields strictly fewer seeds containing a raw id AND (2) does not lose
grounding, where grounding = `source_thread` quoting something literally present
in the supplied context.

| arm | seeds with a raw id | grounded |
|---|---|---|
| ids (current default) | 5/80 | 74/80 (92%) |
| names (`resolve_names=True`) | **0/80** | 70/80 (88%) |

Criterion 1 passed decisively. Criterion 2 failed. By that rule the change was
not adopted.

Run the significance, because the previous session did not: grounding is
**p = 0.43** and the raw-id difference is **p = 0.059 two-sided / 0.029
one-sided**. The criterion that vetoed the change is noise; the one that approved
it is signal. The rule was also badly formed - "must not drop", strict, over a
stochastic binary rate with no noise floor, rejects about half the time on
identical arms, which is readable in its text before any run.

**Three limits of that measurement, all of which you should weigh yourself:**

1. It measured the presence of a raw ID **in the output**, which is Reading A's
   variable. It did not measure the asymmetry itself, which is Reading B's.
   Under B there may be nothing to measure: an invariant either holds or it does
   not.
2. The grounding metric rewards verbatim quotation. The ID arm quotes more
   literally, because `C2:` reads as a record label and gets copied wholesale,
   while the names arm paraphrases more. The metric may therefore favour the
   current default by construction. A blind judge would settle this; a four-word
   window cannot.
3. n=4 game states is a thin population. Two of the four came from throwaway
   acceptance sessions.

Raw rows: re-run the script; it writes `drive_label_ab_result.json`. The original
run's artifacts are not in the repository.

## Options as they stand

**Option 1 — measure before changing.** Build a blind-judge instrument for
grounding (does the seed grow causally from something in the context?), re-run
both arms under it, and let a pre-registered rule decide. Cost: a new instrument
plus provider calls. Risk: if the judge also favours the current arm, the
asymmetry stays and the decision has to be made on other grounds anyway.

**Option 2 — change the default and treat the grounding cost as accepted.**
`resolve_names=True` in `stalled_scene_context` removes the asymmetry by
construction and, per the existing measurement, also eliminates the raw-ID leak.
Cost: an unquantified grounding effect, possibly zero if limit 2 above holds.
Risk: shipping a prompt change whose quality effect was never measured with a
sound instrument, which `AGENTS.md` §6 exists to prevent.

**Option 3 — anything you conclude that is not on this list.** The two above are
the ones already on the table, not an exhaustive set. A third path — for example
resolving names only for the controlled character's counterparts, or giving these
prompts a roster the way the Director has one — has not been examined.

## What is already true and needs no rediscovery

- `TestTheResidueThisFixDidNotCover` in `tests/test_internal_ids_in_prompts.py`
  pins the current behaviour, including the mixed labelling. It will fail when
  the default changes, which is intentional: it forces the change to be explicit.
- `src/prompt_contract.py` does NOT detect this. The asymmetry is structural, not
  lexical, and no pattern list can see it. If the conclusion is that structural
  markers belong under the same guarantee, the guard for it does not exist yet.
- The Director is a deliberate exception to ID-free prompts: its typed events
  reference `subject_id`/`witness_ids`, and its prompt ships an
  `ID=C2 | NAME=Marta` roster. Verified at 330/330 real calls. Do not "fix" it.

## Closure evidence required

- [ ] a stated decision on which reading governs (A, B, or a defended third), with
      the reasoning recorded in this file;
- [ ] if a measurement is used, its rule written down BEFORE the run and its
      artifacts committed under `tools/acceptance/` or `docs/`, not left in a
      temporary directory;
- [ ] `AGENTS.md` §3 amended or explicitly confirmed as-is on whether structural
      markers (one character labelled unlike the others) fall under the agency
      lock;
- [ ] whatever ships, the pinning test updated to match the new intent rather
      than deleted;
- [ ] suite, Ruff and mypy green; local commits only, no push.

## Out of scope

- The Director's roster (see above).
- The whisper-leak detector's false positives on common Portuguese words
  (`onde`, `cabeça`), recorded in `.plan/closed/31-harness-json-robustness.md`.
  Related in spirit, separate in substance.


## Two questions answered 2026-07-27 (facts, not conclusions)

**Does any path store the controlled character as `C1` rather than `Player`?**
No. Every human action is appended as `"Player"` (`src/runner.py:820,913`), and
in the sessions on disk it is 3/3. The asymmetry is therefore consistent, not an
inconsistent mapping bug.

**Is the asymmetry intermittent - only present when a `Player` record falls
inside the recent window?** The mechanism is real, but in practice the answer is
no: recutting the window at three points of one real session gave an asymmetric
block every time, because the human acts on essentially every turn. Caveat: that
is one session, and the population on disk is thin.
