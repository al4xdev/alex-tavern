# Task 71 — Per-viewer narration

> **Status:** open, **UNSCHEDULED — blocked on a product decision.** Found by a
> blind narrative reviewer reading the transcripts as fiction; no metric, case or
> task in this project had raised it.
>
> This is a leak — the owner's immersion-breaker #2 — in its purest form: the
> player is handed the god's-eye view of a scene their character is not in.
>
> ---
>
> **Removed from wave 2 on 2026-08-05.** Not because it is wrong — the defect is
> real and the diagnosis (`runner.py:1323`, `audience=None`) is verified. Because
> **it is not an engineering decision and it was sitting in a wave as though it
> were.** The §"Note the product question underneath" below says this task changes
> what the game *is*, and its own first closure item is *"the product question
> answered and recorded here before implementation"* — so it was already blocked;
> the wave placement just hid that.
>
> It also changes the API contract (`narration` is currently a single string) and
> depends on task 67's graph being correct, which puts it structurally after the
> checkpoint regardless.
>
> **To unblock: answer the question in §"Note the product question underneath",
> in writing, here.** If the answer is *"narration stays omniscient"*, this task
> closes unbuilt and the leak becomes a documented product property. That is a
> legitimate outcome and costs nothing to reach.

## Problem

Narration has no per-viewer projection anywhere in the engine.

Every other channel does. Speech and action records get a zone-computed audience
(`_append_history`, `runner.py:2632-2636`: *"a speech/action record's effective
audience is computed from who can physically perceive the speaker's zone"*).
Perception events are clamped per witness (`perception.validate_perception_events`)
and redacted per viewer (`runner.py:1445`). Whispers are projected per confidant.

Narration is appended with no audience at all:

```python
self._append_history(game, "Narrator", narration, "narration", step)
```

`runner.py:1323` — `audience` defaults to `None`, which means "public record,
visible to everyone" (`record_visible_to`). One narration string is produced per
turn and handed to every reader.

## What it produces

`base-P1-r1` T25–T29. Link and Elowen are underground behind a total collapse;
the rest of the cast is in the hall. Every italic paragraph covers both, sometimes
in one sentence:

> T28: *"…soterrando metade do corredor sob uma pilha de pedras. **No salão
> distante**, o toque grave do sino ecoa pelas arquibancadas."*

The player, controlling a character sealed underground, is reading Seraphine's
argument with the Director in another building. Nothing in the fiction gives them
that knowledge.

## Why this is a data problem, not a prompt problem

The prose renderer is **already instructed not to do this** (`src/agents/prose.py:50-52`):

> - Characters in zones that cannot perceive each other must NEVER be staged as
>   sharing space, hearing one another, or being 'a few meters' apart — cut
>   between separated spaces explicitly.

The renderer holds the rule and breaks it, because there is exactly one narration
output slot and the scene has two halves that both need narrating. It has no way
to comply: cutting between spaces is the best it can do inside one paragraph, and
that still delivers both halves to both readers.

This is the recurring pattern of the phase — **a prompt promise with no structure
behind it loses.** It is the same finding recorded as #1 in task 59.

## Direction

The hard question is not the guard, it is the shape of the output. Options, none
chosen:

- **Render per zone-cluster.** One narration per set of mutually-perceiving
  zones, each with its own audience list, merged for the reader according to
  which character they control. Most correct, most expensive — it multiplies
  prose calls when the scene splits.
- **Render once, project by filtering.** Keep one call, tag sentences or
  paragraphs with the zone they describe, and drop what the viewer cannot
  perceive. Cheaper; risks incoherent prose after filtering.
- **Render once for the player's zone only**, and let the rest of the world reach
  other characters through the channels that are already per-viewer (perception
  events, memory). Cheapest; loses the omniscient-narrator quality the project
  currently has, which may be a deliberate product choice.

**Note the product question underneath.** This engine's narration is currently
omniscient by design, and a session is read by one human. Making narration
per-viewer changes what the game *is* — from "a story about a cast, in which you
act" to "your character's experience". That is the owner's call, not an
engineering one, and this task should not pick it silently.

## Interaction with other tasks

- **Task 67** fixes the zone graph. This task depends on that graph being
  correct: projecting narration through a graph that wrongly severs a sub-zone
  would hide narration from people who should see it.
- **Task 63** is about redaction reaching persisted records. If narration becomes
  per-viewer, the redaction question changes shape — a projected narration can be
  redacted per viewer without mutilating a shared record.

## Closure evidence required

- [ ] the product question answered and recorded here before implementation;
- [ ] a test with a split scene: a character in zone A does not receive narration
      describing zone B, asserted against the real builders;
- [ ] `prose.py:50-52`'s rule becomes enforceable — a test that the renderer is
      never asked to stage two mutually-imperceptible zones in one output;
- [ ] the API contract change documented (`narration` is currently a single
      string in the turn response);
- [ ] cost measured: prose calls per turn before and after, on a session that
      splits;
- [ ] narration must not get thinner, only correctly scoped — judged by a blind
      read, since `NSR` cannot see this (it counts stimuli, not narration, and is
      not a gate: `.plan/ROADMAP.md`).

**The measurement that would falsify this task:** if scenes essentially never
split in real play, the defect is rare enough to live with and this drops below
task 66.
