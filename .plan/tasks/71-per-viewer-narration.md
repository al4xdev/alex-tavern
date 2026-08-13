# Task 71 — Per-viewer narration

> **Status:** ✅ **CLOSED 2026-08-12.** Narration renders per perception cluster.
> Every closure item below is discharged, the last of them on a live cell.
>
> **The number, restated per session** after the unit-of-analysis error was
> found (see `.plan/reference/metric-validity.md`): a split narration naming
> someone its reader cannot perceive runs at **70% and 22%** in the two
> informative pre-71 sessions, and **0%, 9%, 0%, 0%** in the four post-71 ones.
> Clean separation, and every post session at or below every pre session.
>
> ⚠ **The p = 9.8e-09 this file used to quote was pooled over turns and is
> withdrawn.** With two informative sessions against four, the best an exact
> session-level test can produce is **p = 0.13**. What supports this task is the
> separation plus a mechanism that is unit-tested, not a significance level.
>
> Cost is **1.278x** prose calls per narrated turn, concurrent, so latency does
> not multiply.
>
> Two things a later reader should not have to rediscover. The singleton
> population is **not** empty — but the case that proved it is a Director-declared
> seal, **not** task 76's sibling defect, which is a correction made after
> implementing 76 and checking. And the deterministic backstop has never fired in
> production; its evidence is an offline replay over the sessions that did leak.
>
> ## ✅ THE RE-MEASUREMENT HAS RUN — 2026-08-12, the task stands
>
> Split rate 53.7% → **27.8%** (p=1.7e-4), cost multiplier **1.28x**, and no
> singleton clusters in the four post-67 sessions scored that day - a fifth
> session later found them, see the correction under "The singleton question".
> See "The re-measurement" below. The pre-67 figures further down this file are superseded; they are
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

  > ✅ **Confirmed 2026-08-12: it shrank, hard.** Zero singleton clusters across
  > the first four post-67 sessions, against 0.740 per turn before. The
  > prediction in this paragraph was right.
  >
  > **It did not vanish, and I said so for a few hours before a fifth session
  > proved otherwise.** `21f7c4e1` carries a singleton on all ten of its split
  > turns, and `54bcdace` on all fourteen of its. So the population is rare but
  > real, and the fold rule is doing work rather than guarding an empty case.
  >
  > ⚠ **I then blamed the wrong cause.** The pulpit singleton is not task 76's
  > sibling defect: the zone was created correctly linked at T10 and the Director
  > sealed it outright at T23 with `zone_link_updates: {"púlpito central": []}`.
  > The engine honoured a declared seal. So the fold is hiding a **Director
  > decision**, not a graph bug — a weaker complaint than the one I made, and
  > still worth someone's attention, because a lone character receiving no
  > narration at all is invisible until you go looking.
  >
  > **Nobody should cite 1.21x again** — the multiplier is 1.28x, measured, and
  > folding can only ever reduce it.

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

~~Fisher exact, 58/108 against 30/108: **p = 1.7e-4**.~~ **Withdrawn
2026-08-12**: that pooled turns across sessions. Per session the pre-67 rates are
**72.4%, 17.9%, 75.0%** and the post-67 rates are **52.6%, 29.4%, 0%** - the
ranges **overlap**, and with three sessions a side no test is meaningful. The
means moved the right way and that is all this evidence supports.

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

**There are no singletons to fold** *(in these four sessions - see the
correction below)*. `mean_clusters_ge2` equals `mean_clusters` to three decimals
in all three cells, and in the P2 post-67 cell `d0cc98e5` (37 narrated turns,
37.8% split, `singleton_turns` **0**) as well. Four post-fix sessions, not one
singleton cluster among them. Pre-fix there were 0.740 per turn.

> ⚠ **Corrected 2026-08-12 by the fifth session.** `21f7c4e1` has a singleton on
> every one of its ten split turns - a man sealed on a pulpit by task 76's
> sibling defect. The population is not zero, it is rare and graph-shaped. The
> cost conclusion below is unaffected (1.278x was measured on the cells that
> have no singletons, and folding only ever reduces calls), but **"there are no
> singletons" is not a fact about the engine**, and the fold rule is doing real
> work rather than standing guard over an empty case.

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
- [x] a test with a split scene: a character in zone A does not receive narration
      describing zone B, asserted against the real builders;
      *(`tests/test_per_viewer_narration.py`, 21 tests. Both halves verified
      non-vacuous by simulating the regression: un-scoping the events fails 2,
      collapsing the cluster split fails 6)*;
- [x] `prose.py:50-52`'s rule becomes enforceable — a test that the renderer is
      never asked to stage two mutually-imperceptible zones in one output;
      *(`test_staging_names_only_the_zones_this_cluster_stands_in`. The STAGING
      block now lists only the zones the cluster occupies, and edges LEAVING
      that set are dropped so the prompt cannot name an unreachable place)*;
- [x] the API contract change documented (`narration` is currently a single
      string in the turn response); *(there is no shape change: it stays a
      single string and now carries the controlled character's cluster. The
      other clusters are real history records with their own `audience`.
      Documented on `PlayerTurnResponse` in `src/main.py`)*;
- [x] cost measured: prose calls per turn before and after, on a session that
      splits; *(over the three post-67 cells: 138 prose calls across 108
      narrated turns = **1.278x**, per session 1.526x / 1.294x / 1.000x. Equal
      to the cluster mean, which confirms the singleton fold saves nothing
      because there are no singletons. Clusters render concurrently in the
      existing `asyncio.gather`, so wall-clock latency does not multiply)*;
- [x] narration must not get thinner, only correctly scoped — judged by a blind
      read, since `NSR` cannot see this (it counts stimuli, not narration, and is
      not a gate: `.plan/ROADMAP.md`); *(2026-08-12: control unmoved at +3%,
      split -11.9% inside the band, and the read finds concrete prose. See "The
      thinning check")*;
- [x] **the residual transcript leak re-scored on a fresh cell.**
      *(2026-08-12, two cells `09aabf25` and `54bcdace`: **0 of 36 split
      narrations**, both halves live. The task's headline is 16/29 (55%) →
      3/78 (3.8%) pooled, p=9.8e-09. The backstop removed nothing in either
      cell because the model did not leak in them, so its own evidence stays
      the offline replay: 3 fires, 0 false positives, over 42 narrations.)*

**The measurement that would falsify this task:** if scenes essentially never
split in real play, the defect is rare enough to live with and this drops below
task 66.

## The thinning check — decision rule, pre-registered 2026-08-12

Written before the post-71 cell was launched. The last closure item is *"narration
must not get thinner, only correctly scoped"*, and it is the one this
implementation could plausibly fail, because the scoping cuts four things out of
the prompt at once: cast, staging, transcript and events.

**The risk, stated as a mechanism.** A cluster of two gets a prompt naming two
characters, one zone, and only the events they witnessed. If that is too little
material, the renderer falls back on generic atmosphere — the
*"Nothing new happens; render a short atmospheric beat"* shape — and the reader
trades a leak for filler. That would be a worse product than the leak.

**Comparison.** A post-71 `base-P1` cell against the three post-67 pre-71 cells
already scored (`00997daa`, `b11b38dc`, `55d03896`). Same cell, same profile,
same graph — the ONLY difference is this task's code, which is what makes it a
clean read.

**Decision rule.**

| observation on split turns | verdict |
|---|---|
| median narration length within **25%** of pre-71, and a read finds the prose concrete | ship as is |
| length holds but the read finds generic atmosphere where the pre-71 turn was concrete | **relax the transcript scoping first**, not the events: the events are the leak, the transcript is context |
| median length drops **more than 25%** | the cluster prompt is under-fed; revisit before this task closes |

**Unsplit turns are the control.** They take the pre-71 path structurally, so
their narration length must be unchanged. If it moved, something leaked into the
majority path and that is the first thing to fix, ahead of any quality question.

**The read is not optional and not replaceable by the length number.** Length is
the cheap proxy; this project has now recorded four instruments that passed on
their numbers and failed on a read (`.plan/reference/metric-validity.md`).

### ✅ Result — session `21f7c4e1`, 2026-08-12

**Length.** Speech reports had to be excluded first; see the defect below.

| | pre-71 (3 cells) | post-71 |
|---|---|---|
| unsplit median chars *(the control)* | 1235 | 1275 (**+3%**) |
| split median chars | 1170 | 1031 (**-11.9%**) |

The control did not move, so nothing leaked into the majority path. The split
drop is inside the 25% band. **Ship-as-is branch of the rule.**

**The read.** Concrete, not atmospheric filler:

> **T25** the east arch gives way, a slab tearing loose and sealing the entrance,
> dust thick enough to hide the podium, fist-sized fragments hammering the floor.
> **T27** (the shortest, 431 chars) a steel beam on loose bolts swinging over
> crates and coiled rope — a specific hazard being set up, not a mood.
> **T31** Marta driving the last stake, the rope rectangle, dust in the folds of
> her leather apron.

**The leak, measured before and after** by `scan_cross_cluster_leak`, checked in
alongside the split scanner for the same reason the split scanner was: the first
version of this count was an ad-hoc script. A split narration leaks if it names a
character, or the zone a character stands in, that some reader of that record
cannot perceive - scored **per reader cluster**, because asking "can anybody
reach this" answers yes for each half of a split scene and finds nothing.

| | split narrations | leaking |
|---|---|---|
| pre-71 `00997daa` | 20 | **14** |
| pre-71 `b11b38dc` | 9 | **2** |
| pre-71 `55d03896` | 0 | 0 |
| post-71 `21f7c4e1` | 10 | **0** |
| post-71 `c76037ff` | 32 | **3** |

**16 of 29 (55%) → 3 of 42 (7.1%).**

> ⚠ **The 72% I first reported was too high.** The ad-hoc script matched first
> names, so it counted `b11b38dc` at 7 rather than 2. Strict matching - a
> multi-token name must appear in full and adjacent - is the same discipline the
> guard needed after `véu`, and it is the instrument's number that stands.

> ⚠ **And then replicate 2 found the residual, 2026-08-12.** `c76037ff`: **3
> leaks of 32 split narrations (9.4%)**. Not zero. n=1 was optimistic here
> exactly as it was for the clamp metric this morning.
>
> All three are the same character on consecutive turns. Marta Ferrolume is in
> `depósito de ferramentas`; the reader cluster is at `próximo à saída norte`;
> `can_perceive` is **False in both directions**, so these are real leaks and not
> a detector artifact. The prompt was checked directly: cast, staging and events
> were all scoped correctly and **no event of the beat names her**.
>
> The vector is the **reader transcript**. Narration rendered while the scene was
> still whole carries `audience=None` and stays visible to every cluster forever,
> which is correct - that reader did watch her come in. The renderer then carried
> the thread into the PRESENT and gave her current, invented action:
>
> > *"Marta Ferrolume, ainda de joelhos diante do corredor A, ergue a cabeça, a
> > chave de reserva pendendo frouxa na mão"* (T18)
>
> **Fixed in two halves, and the structural half is measured.** The residual is
> **3 of 42 split narrations (7.1%)** with the roster alone, down from 16 of 29
> (55%) before the task.
>
> The instruction half is a scoped `IN THIS VIEW` roster: the only people whose
> present actions may be narrated, others available as memory but never shown
> acting now. On its own that is a prompt promise, which this project has
> recorded more than once as the weak kind of fix.
>
> The structural half is `_strip_offstage_actors`, a deterministic backstop that
> drops any sentence naming a present character outside the cluster. It mirrors
> `_strip_echoed_sentences`, which already sits beside it in `prose.py` for
> exactly this reason, down to returning "" so the caller keeps the draft when
> nothing survives.
>
> **Replayed over both post-71 sessions: it fires on all 3 known leaks and on
> none of the other 39 split narrations.** The surviving prose stays substantial
> (1181 → 863, 1225 → 948, 1204 → 892 characters) and reads as complete, and the
> OTHER cluster's narration - the one Marta is actually in - is untouched at
> full length.
>
> ⚠ **The first version of this guard was wrong, and the corpus hid it.** It
> matched name tokens case-insensitively and deleted three atmospheric sentences
> for containing *"véu"* - Portuguese for veil, and also the surname of Noa Véu,
> who was not in them. A 9.4% false-positive rate against a 9.4% leak. That is
> the `menos` bug of task 70 in a new costume, and it is the second time this
> month a name guard has been validated on a corpus that did not contain its own
> counter-example. A multi-token name now must match in full and adjacent; a
> single-token name must match with its capital.
>
> **The end-to-end cell ran (`09aabf25`, 38 turns, both halves live: 26 of 46
> prose calls carried the roster, 22 records carry `audience_origin="cluster"`).
> Result: 22 split narrations, ZERO leaking.**
>
> ⚠ **It does not demonstrate the backstop.** Comparing every persisted
> narration against the model's raw prose in `debug.jsonl`, the backstop
> **removed nothing all session** — the model simply did not leak this time. So
> the cell confirms the pipeline and the roster; the backstop's evidence remains
> the offline replay against the sessions that *did* leak.
>
> And the honest statistics, since the temptation is to read 0/22 as the pair
> working:
>
> | variant | sessions | split narrations | leaking | |
> |---|---|---|---|---|
> | pre-71 | 2 | 29 | **16 (55%)** | |
> | roster only | 2 | 42 | **3 (7.1%)** | |
> | roster + backstop | 2 | 36 | **0** | vs roster only **p = 0.25** |
> | **all post-71** | 4 | 78 | **3 (3.8%)** | vs pre-71 **p = 9.8e-09** |
>
> The last row is the task's result and it is overwhelming. **The
> roster-versus-backstop comparison is not significant** and must not be quoted
> as if it were: 0 of 36 is an ordinary draw from a 7% rate.
>
> **The backstop has never fired in production.** Across both cells that carry
> it, 36 narrations, it removed nothing — checked by diffing every persisted
> narration against the model's raw prose in `debug.jsonl`. Its entire evidence
> is the offline replay over the sessions that did leak: 3 fires, 0 false
> positives, 42 narrations. That is real evidence and it is not the same thing
> as having watched it work.

### ⚠ Two things the live session corrected

**1. Singleton clusters are not extinct, and my "zero across four sessions" was
too strong.** Every one of this session's ten splits is 20 people in the
courtyard plus **one man alone on the `púlpito central`** — Lorde Cassian Aurel,
addressing an assembly he is acoustically sealed from:

```json
{"Salão dos Quatro Arcos": ["púlpito central", "Pátio norte da Academia"],
 "púlpito central": [], "Pátio norte da Academia": ["Salão dos Quatro Arcos"]}
```

The pulpit and the courtyard are both children of the hall, and **task 76 is
exactly that**: siblings are never linked, so the pulpit hears nothing. So the
singleton is a graph artifact, the fold rule fired ten times, and each time it
denied narration to a character who should have been in the main cluster.

Not a reason to drop the fold — the player is never folded and was in the
courtyard throughout — but it means **the fold is currently masking task 76**,
and 76 should land before anyone treats singleton folding as harmless. The
earlier claim that the post-67 singleton population is zero holds for those four
sessions and does not generalize.

**2. Cluster prose was indistinguishable from a speech report.** `_report_speech`
appends `content_type="narration"`, speaker `Narrator`, `audience=heard_by`,
`audience_origin="zone"` — the exact four values the first version of this task
wrote. The thinning measurement counted one-line speech reports as narration and
had to be redone against the `audible_speech_drop` log. Cluster prose now carries
`audience_origin="cluster"`, pinned by a test.
