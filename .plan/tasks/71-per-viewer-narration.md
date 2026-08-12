# Task 71 — Per-viewer narration

> **Status:** open and **UNBLOCKED 2026-08-12.** The product question was
> answered 2026-08-05 (below); the post-67 re-measurement that gated design has
> now run and the task stands. Ready to design. It is wave 3.
>
> ## ✅ THE RE-MEASUREMENT HAS RUN — 2026-08-12, the task stands
>
> Split rate 53.7% → **27.8%** (p=1.7e-4), cost multiplier **1.28x**, and zero
> singleton clusters across four post-67 sessions. See "The re-measurement"
> below. The pre-67 figures further down this file are superseded; they are
> kept because the reasoning around them is still the reasoning.
>
> ## The original blocker, kept for the record
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

  > ✅ **Confirmed 2026-08-12, and it did not shrink — it vanished.** Zero
  > singleton clusters across four post-67 sessions, against 0.740 per turn
  > before. The prediction in this paragraph was exactly right, and it leaves
  > nothing to decide: there is no singleton population to fold or render. The
  > fold rule stays in as a guard against the case recurring, and the
  > redundancy argument is the only thing holding it up, which is the footing
  > the re-framing above asked for. **Nobody should cite 1.21x again** — the
  > multiplier is 1.28x and it is the same number either way.

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

## The re-measurement — decision rule, pre-registered 2026-08-12

Written before any post-67 cell was scored. The cells were already running when
this was written, and no result had been read.

**Instrument.** `scan_scene_splits` / `scene_clusters` in
`tools/acceptance/immersion_scanners.py`, checked in on 2026-08-12 specifically
so the before and the after come from the same code. The ad-hoc script that
produced the table above no longer exists. Validation: run over the 16 archived
sessions it returns **610 narrated turns, 168 split, 1.562 clusters per turn,
1.202 holding 2+, 8 of 16 never splitting, worst session 3.625, max 5** — every
figure in the table above, to every digit the table reports. Pinned by
`tests/test_scene_clusters.py`.

**Comparison.** `base` / `P1` post-67 against the archived `base-P1-r1..r3`,
which is the same cell and profile. Pre-67 baseline for that cell alone:
**58 of 108 narrated turns split (53.7%)**, per-session 21/29, 7/39, 30/40.
Pooling across cells is not the test, because the population is bimodal and
pooling hides it; per-session split shares are reported alongside.

**Decision rule.**

| post-67 `base-P1` split share | verdict |
|---|---|
| **< 5%**, and mean clusters/turn < 1.05 | the falsifier at the bottom of this task FIRES. Scenes essentially never split once the graph is right; 71 closes unbuilt and the leak becomes a documented product property |
| **5% to 20%** | 71 shrinks. The defect is real but rare; the singleton-fold question is decided on cost alone and the task drops below the checkpoint |
| **> 20%** | 71 stands as written. Re-derive the cost multiplier from the post-67 mean and proceed to design |

**⚠ Amendment, same day, still before scoring: a confound survives 67.** Task 76
was found while measuring 67's last closure item: sibling sub-zones minted from
the same origin are never linked to each other, so two flanks of one hall are
mutually deaf. 67 did not touch this, so **the post-67 split rate is still an
upper bound**, and reading the zone names of the archive puts the inflation at
roughly **17 of 168 splits (10%)**. If the post-67 rate lands near a boundary in
the table above, that is not a decision — it is a signal to do 76 first and
measure again. Only a result clear of the boundaries by more than 10% decides
anything today.

**Not a count-only decision.** Whatever the number, the split turns get read:
for a sample of them, does the narration actually describe two separated groups,
and is the separation one a reader would accept as real? A split rate that
survives the graph fix but is made of separations the fiction does not support
is still an artifact, just a subtler one. This clause exists because the case-C
falsifier in task 65 fired with a diagnosis that reading the flagged replies
showed to be wrong.

## ✅ The re-measurement — 2026-08-12. The task STANDS.

Three post-67 `base-P1` replicates against the three archived pre-67 ones. The
two groups land on **exactly 108 narrated turns each**, which is luck, but it
makes the comparison as close to paired as this instrument gets.

| | narrated | split | mean clusters | clusters ≥2 | **singletons/turn** |
|---|---|---|---|---|---|
| **pre-67** pooled | 108 | **58 (53.7%)** | 2.352 | 1.611 | **0.740** |
| **post-67** pooled | 108 | **30 (27.8%)** | 1.278 | 1.278 | **0.000** |

Per session, post-67: 20/38 (52.6%), 10/34 (29.4%), 0/36 (0%). Bimodality
survives the fix — one session never splits at all.

Fisher exact, 58/108 against 30/108: **p = 1.7e-4**. The split rate genuinely
halved.

**Verdict against the pre-registered rule: 27.8% is above the 20% line, so the
task stands as written.** The amendment required a result clear of the
boundary by more than the sibling confound, and that check was run rather than
argued: recomputing the post-67 cells with sibling zones made mutually audible
changes the split count **not at all** (30 → 30). Task 76's confound is real in
the archive and absent from this sample, so it does not touch this decision.

### The singleton question is answered, and it dissolves

The single biggest cost lever in this task was *"1.56x prose calls per turn if
every cluster renders, 1.21x if singletons fold"*, and the open closure item
below asked for the fold decision to be made against post-67 numbers.

**There are no singletons to fold.** `mean_clusters_ge2` equals `mean_clusters`
to three decimals in all three cells, and in the P2 post-67 cell `d0cc98e5`
(37 narrated turns, 37.8% split, `singleton_turns` **0**) as well. Four post-fix
sessions, not one singleton cluster among them. Pre-fix there were 0.740 per
turn.

That is the spurious singleton task 71 predicted the broken graph was
manufacturing, and 67 removed all of it. So:

- **the cost multiplier is 1.28x**, and it is 1.28x under either policy;
- **the fold-or-render decision no longer has a population to decide about.**
  Keep the fold rule anyway as a cheap guard, but it is not a cost lever and
  must not be sold as one.

### The splits that remain are real

Required by the rule above, and not skippable. Read across the three cells:

> **r1 T16-T20** — 19 in `pátio central`, 2 in `corredor da ala norte`. The T16
> narration describes a mass of stone burying the return corridor. The split is
> stable for five turns.
> **r2 T24-T25** — 19 in the hall, 2 in `corredor da masmorra`. Garran drives
> his shoulder into the dungeon door and it seals with a final click.

Both are separations the fiction states outright, in the sentence that creates
them. And in both, the two people on the far side are handed narration
describing the room they cannot see — which is the leak this task exists to
close, alive in the post-67 graph.

**The falsifier at the bottom of this file does not fire.**

## Closure evidence required

- [x] the product question answered and recorded here before implementation —
      **per zone-cluster, 2026-08-05**, see the decision block at the top;
- [x] **⛔ BLOCKING, do this first:** the split rate and cluster count
      **re-measured on the post-67 graph**. Every figure in this file is a
      pre-67 upper bound. If the rate collapses, re-size or close the task
      instead of building it; *(2026-08-12: 53.7% → **27.8%**, p=1.7e-4. It
      halved but did not collapse, and stays above the 20% line the rule was
      registered against)*;
- [x] the singleton-cluster question decided against those numbers — the leaning
      is **fold**, and it needs the post-67 population to be confirmed;
      *(2026-08-12: **the population is empty.** Zero singleton clusters across
      four post-67 sessions, against 0.740 per turn pre-fix. Keep the fold rule
      as a cheap guard; it is not a cost lever)*;
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
