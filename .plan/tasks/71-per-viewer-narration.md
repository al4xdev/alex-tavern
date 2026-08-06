# Task 71 — Per-viewer narration

> **Status:** open. The product question is **ANSWERED** (2026-08-05, below), and
> the task is **PARKED until task 67 has shipped** — deliberately, by the owner,
> on the same day the answer was given. It is wave 3.
>
> ## ⛔ DO NOT DESIGN THIS TASK UNTIL THE RE-MEASUREMENT BELOW HAS RUN
>
> Every cost figure in this file was taken on the **pre-67 zone graph**, which is
> known to be broken in two ways that each **manufacture a spurious cluster**
> (`zone_moves` mints a sub-zone with no inbound edge; `zone_link_updates`
> replaces instead of merging). So the split rate, the cluster counts and the
> prose-call multiplier are all **upper bounds of unknown tightness**.
>
> **First action when 67 lands, before any design work:**
>
> ```
> # re-derive the split rate on the fixed graph, over a post-67 cell
> uv run python -m tools.acceptance.immersion_scanners --battery <artifact-dir>
> # plus the cluster count per narrated turn — the block in .plan/tasks/68
> ```
>
> If the split rate collapses once the graph is right, this task shrinks or
> disappears, and that is a legitimate outcome. Designing it against the numbers
> currently in this file is designing against a confounded baseline — the exact
> failure this phase has now recorded three times (`main_doors`,
> `perception_events`-in-`state.json`, the inverted `NSR` gate).
>
> ---
>
> Found by a blind narrative reviewer reading the transcripts as fiction; no
> metric, case or task in this project had raised it.
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

## ✅ The decision — 2026-08-05, by the owner

**Render per zone-cluster.** The first of the three options below: one narration
per set of mutually-perceiving zones, each with its own audience, and the reader
receives the cluster their controlled character is in.

Recorded verbatim, because the reasoning is the part that binds: *"vai ser uma
droga, vai dar trabalho, mas o alex tavern nunca foi feito pra ser fácil."*

What the decision settles, and what it does not:

- **Settled.** The game is *"your character's experience"* at the narration
  layer. The cast-story quality survives inside a cluster — everyone who can
  perceive each other still shares one omniscient paragraph — but a reader is no
  longer handed a scene their character cannot reach. The two cheaper options
  are rejected: filtering after one render risks incoherent prose, and rendering
  only the player's zone throws away the ensemble quality the project has.
- **Leaning, endorsed by the owner the same day, not yet a decision: fold the
  singleton clusters.** A cluster holding **one character who is not the player**
  probably does not need its own narration render — that character already learns
  their surroundings through perception events and memory, both of which are
  per-viewer today, and nobody is reading their paragraph.

  > **⟳ Re-framed 2026-08-05, and the reason matters more than the answer.** This
  > was recorded as *"the single biggest cost lever in this task — 1.56x prose
  > calls per turn if every cluster renders, 1.21x if singletons fold."* Under
  > `AGENTS.md` §2 **that is not a reason to decide anything.** Cost is cheap
  > here; quality is not.
  >
  > So the question has to be re-asked on the right axis: **does a lone
  > character's own experience need a narrated paragraph, when they already
  > receive perception events and memory?** The answer may well still be *fold* —
  > but for being **redundant**, not for being expensive. The difference decides
  > what happens the day someone asks to un-fold it: "it was redundant" survives
  > that conversation, "it was expensive" does not survive a faster model.
  >
  > The multiplier stays recorded as an observation. It is not the argument.

  It stays a leaning rather than a decision for one further reason: *those
  numbers are from the broken graph*, and the graph bugs specifically produce
  **isolated single characters**. After 67 the singleton population is expected to
  shrink. **Confirm against the post-67 measurement, then write the decision
  here — on the redundancy argument, not the call count.**

### Scenes do split, so the falsifier does not fire

The falsifier at the bottom of this task — *"if scenes essentially never split in
real play, the defect is rare enough to live with"* — was evaluated over the
whole 2026-08-02 archive (16 sessions, 610 narrated turns). Clusters computed
over each narration record's own `scene_snapshot`, under mutual perceivability.

| | |
|---|---|
| narrated turns whose scene is split (>1 cluster) | **168 of 610 (28%)** |
| sessions that never split | **8 of 16** |
| sessions that split on 42–78% of turns | **5 of 16** |
| mean clusters per narrated turn | **1.56** (worst session **3.62**, max **5**) |
| mean clusters holding **2+ characters** | **1.21** |

It is bimodal, not rare: half the sessions never split, and the ones that do,
split constantly. That is the shape that makes the defect worth fixing — when it
happens it happens for a third of a session, which is exactly the `base-P1-r1`
T25–T29 reading experience described above.

> ⚠ **These numbers are an upper bound, measured on the broken graph.** Task 67
> shows `zone_moves` minting sub-zones with no inbound edge and
> `zone_link_updates` wiping edges — and every such bug manufactures a spurious
> singleton cluster. `base-P1-r2` is the clearest case: 18% of turns split, and
> its splits are the same C13 sub-zone bug that produces its 10 empty-audience
> records. **Re-measure after 67 lands**; the true split rate and the true cost
> multiplier are both lower than the table above, by an unknown amount. This is
> the second reason the task sits after 67, alongside the correctness one.

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

The hard question is not the guard, it is the shape of the output. Options —
**the first one is the decision above**; the other two are kept because rejecting
them is part of the record:

- **Render per zone-cluster.** ← **CHOSEN.** One narration per set of mutually-perceiving
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

- [x] the product question answered and recorded here before implementation —
      **per zone-cluster, 2026-08-05**, see the decision block at the top;
- [ ] **⛔ BLOCKING, do this first:** the split rate and cluster count
      **re-measured on the post-67 graph**. Every figure in this file is a
      pre-67 upper bound. If the rate collapses, re-size or close the task
      instead of building it;
- [ ] the singleton-cluster question decided against those numbers — the leaning
      is **fold**, and it needs the post-67 population to be confirmed;
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
