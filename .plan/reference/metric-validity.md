# Which metrics this project trusts, and why — 2026-08-06

**The register. Look up the instrument you are holding; do not read this end to
end.** The rules it applies are one page, read once, in
[`.plan/guides/MEASURING.md`](../guides/MEASURING.md).

One page, because the same failure keeps recurring in different clothes: **a
metric passes review, ranks sessions, and then a read of the actual text says it
measured the wrong thing.** It happened three times on 2026-08-06 alone, to three
different instruments, two of which were written that same day.

Standing rule this page exists to enforce:

> **Never accept a metric on the strength of its numbers. Read the records it
> flagged and the records it cleared.** A clean band, a clean count and a clean
> rate are all reproducible under a broken ruler.



## The register

| metric | status | why |
|---|---|---|
| `director_authored` (task 68) | **trusted** | separates on an empty band, 0.827 against 0.857, over 3,936 records; independently re-derived off a second implementation |
| `_foreign_language` (task 65) | **trusted** | 0.012 against 1.000, nothing between, over all 3,936 records |
| `_leaks_internal_id` (task 65) | **trusted** | membership not shape; refuses to fire on `C4` where C4 is an explosive |
| `clamp_lost_half` (task 67) | **superseded** | replaces emptiness-only counting, but measures Director-vs-engine disagreement, not graph damage. Use `clamp_lost_half_unsealed` |
| `clamp_lost_half_unsealed` (task 67) | **REPORT, DO NOT GATE** | needed three repairs in one day, each found by reading a flagged case and never by the number looking wrong. Reads 5 / 0,0,0,0 / 0,4,0,0 / 2,0,0 across twelve cells |
| `named_exclusions` (task 70) | **fixed same day** | shipped with a false positive; see below |
| event-recurrence detector, `sim >= 0.6` (task 69) | **REPORT, DO NOT GATE** | unregistered until 2026-08-13 and never read. Proper sample read the same day: **2 false positives in 20 (10%)**, both *same phrasing, different content* — a different fissure swallowing different people. Fine as description, not as a guard. **43.4% of its hits are `audible_speech`**, so task 69 owns only about half of its own headline |
| `scene_clusters` / `scan_scene_splits` (task 71) | **trusted** | validated by reproducing all six of task 71's archived figures to every digit |
| `scan_cross_cluster_leak` (task 71) | **trusted, corrected twice** | scored per reader cluster, strict name matching, prose separated from speech reports on a measured empty band |
| `_strip_offstage_actors` (task 71) | **trusted, second version** | 3 fires, 0 false positives over 42 live narrations; the first version had 3 of each |
| `_carries_intent` (task 65) | **weak, kept permissive** | does not separate on real data; see below |
| `empty_audience` (task 67) | **REPORT, DO NOT GATE** | also cannot tell a DECLARED seal from graph damage: it filed seven turns of a man on a deliberately sealed pulpit as `graph_isolated` |
| Director-proposed `witness_ids`, as a scoping signal | **MEASURED AND REJECTED** | median `|witness_ids|`/cast = **0.95** (quartiles 0.86/0.95/1.00, n=4,843 events). The Director lists nearly the whole cast as witnesses of nearly everything, so the field carries no perception judgement. Corroborates task 67 from the other side: **the engine's clamp does all the narrowing**, and every audience number here is a property of the graph, not of the Director's intent |
| blind read of narration for room-vs-position (task 79) | **valid, and its answer is "cannot tell"** | 40 stratified blind reads: **35 "not determinable" (88%)**. Reported as the result, not as a failure of the judge - the prose does not carry the distinction. n=5 determinable is quoted as n=5 |
| positional `zone_moves` string rule (task 79) | **REPORT, DO NOT GATE — not a rate** | corrected from 37.6% to 16.7% after a building-level prefix bug; then its ACCEPTED set was read for the first time on 2026-08-14: **~60-80% precise**, two failure modes (origin==destination no-ops; room changes matched by a stray preposition), and **92 positives from 15 sessions with single turns contributing 5 and 4**. Median 5.6%, 12 of 27 sessions at zero. Zero-inflated and clustered |
| `Scene.positions` novelty signal (task 79) | **MEASURED AND REJECTED** | "destination newly minted and unoccupied at T-1" — set membership only, no string matching. **Passes its validity check** (fires on 73.2% of 512 moves, not degenerate) and **fails on reading**: a genuinely new ROOM is also newly minted and empty, so it separates novel destinations, not rooms from positions. Agreement with the string rule 35.4%. Tried because a critic noticed rule 5's own corollary names it and it had never been run |
| `NSR` | **report, never gate** | ranks sessions OPPOSITE to a blind reader, Spearman +0.923 |
| `SIL` | **report, never gate** | 0.0 in 18 of 18 runs; structurally impossible, see below |
| `deaf_occupied`, `unreciprocated`, `edges_lost` | **REJECTED** | measured, do not predict damage; see below |

## The three that failed a read on 2026-08-06

### 1. `_INTENT_CARRIED_RATIO` — a band that was an artifact of the sample

A two-arm replay of 20 synthetic replies on one scene produced mandated
`0.39-0.79` against unmandated `0.00-0.29`: an empty band, and 0.34 shipped at
its midpoint with a confident write-up.

A 40-turn live cell flagged 9 of 42 case-C events, and **a read of all 9 found
every one compliant**, several nearly verbatim. The cause was Portuguese
morphology — reported form says *"ordena que todos formarem"*, the character says
*"formem"* — which exact token matching cannot pair, plus the subject's own name,
which reported form always states and direct speech never does.

Pooled real and synthetic compliant replies span `0.15-0.79` against the same
control's `0.00-0.29`: **the clouds overlap and no threshold separates them.**
Stem-prefix matching was tried and made the overlap worse, because it lifts the
control too. Now 0.15, chosen by which error is affordable rather than by a band,
and the constant says so at length.

**Transferable:** twenty samples from one scene is not a distribution. A band
that appears at n=20 and vanishes at n=42 was never there.

### 2. `named_exclusions` — a false positive the archive could not show

Shipped with `\bmenos\b` in its exclusion-lead list. In Portuguese `menos` is
ordinarily the comparative, so narration like *"despenca a menos de dois metros
de Link"* read as excluding Link. It fired **15 times in one fresh session and
zero times across all 631 archived prompts**, which is exactly how it passed
review: the corpus it was validated on happened not to contain the shape.

Now requires a universal (`todos menos`). The archived before-number was
re-checked and is unaffected — all 371 hits were real.

**Transferable:** validating a guard against one corpus proves it works on that
corpus. Run it on fresh output before trusting the rate.

### 3. `empty_audience` — the right defect, counted at the wrong threshold

Reported **2** on the fresh cell, which reads as nearly clean. The transcript:

> **Garran**: *"Todos para o corredor lateral agora!"* — audience **1**
> **Nix**: *"Todo mundo pro corredor novo, agora!"* — audience **1**

**19 of 72 scoped records reached two or fewer witnesses with 21 characters
present.** Two were empty; the metric saw those and missed seventeen. Worse, a
zone-graph fix could drive it to zero and leave all seventeen — the
reclassification trap task 67 already warned about, through a door the warning
did not cover.

`clamp_lost_half` replaces the emptiness test with proposed-against-persisted,
which is non-circular for the same reason the existing classification is: it
never asks the suspect graph whether an audience was right.

**Transferable:** when a metric counts an extreme, ask what the near-miss
population looks like. It is usually larger and usually the same defect.

### …and then over-counted, corrected 2026-08-12

Widening the metric gave it a floor problem at the other end. On the verification
cell (`d0cc98e5`) it reported two residual losses, 19 → 18 and 20 → 19. Reading
them: in both, the Director had listed **the speaker inside their own
`witness_ids`**, the clamp dropped them correctly, and the counter scored that
as a lost witness.

Both counters now subtract the subject and de-duplicate. The threshold was never
affected — one in twenty is far from 0.5 — but `clamp_worst_loss` and
`clamp_evidence` are the fields a human reads to find a real graph bug, and they
were pointing at a non-bug. After the correction the cell has **no losses of any
size**, and the pre-fix baseline still has its six.

**Transferable:** a metric's evidence field has to survive being read even when
its headline count is already below threshold. The count was right both times;
the pointer was wrong.

### …and then measured the wrong thing, split 2026-08-12

A second post-fix cell (`00997daa`) came back with `clamp_lost_half` = **2**
where the first had 0. On the pre-registered criterion that is a partial
regression, and the honest reading of one cell at 0 and another at 2 is that
n=1 had closed the task too early.

Reading the two: both are a character **behind an explicitly sealed zone** —
Garran on the far side of the collapse the narration describes — with the
Director proposing nineteen courtyard witnesses across the seal and the clamp
correctly cutting it to one. The engine is right. The Director over-proposed.

So the metric never measured graph damage. It measures **disagreement between
the Director and the engine**, and that has two causes:

1. the graph is wrong — 67's actual defect;
2. the Director ignores a correct seal — a prompt-side issue, arguably not a
   defect at all.

`clamp_lost_half_unsealed` counts only cause 1, and across three cells reads
**6 → 0 → 0** with no crossover: every pre-fix loss unsealed, both post-fix
losses sealed. Sealing is detected by **asymmetry, not emptiness** —
`zones[Z] == []` while another zone still lists Z, which is the residue a
`zone_link_updates` seal leaves. A zone *born* isolated is empty both ways and
keeps counting, because that is damage.

**Transferable, and the sharpest one about THRESHOLDS on this page:** a metric that compares two
components attributes the gap to whichever component you already suspect. It
took a cell where the *other* component was at fault to notice. Two cells is the
minimum for any metric defined as a disagreement.

## ⚠ READ THIS FIRST: the session is the unit, and almost every p-value here ignored that

Added 2026-08-12 after measuring session-to-session variance under **identical
code**, four sessions per group:

| metric | mean | sd | range | sessions needed to see a 10-point change |
|---|---|---|---|---|
| **split rate** | 49.1% | **17.9** | 28.6 - 67.3 | **~51 per arm** |
| frozen-position rate | 88.3% | 6.1 | 81.0 - 95.5 | ~6 per arm |
| `return_control` rate | 2.7% | 3.9 | 0.0 - 8.3 | ~3 per arm |
| `empty_audience` | — | — | **0 or 7** | bimodal, one decision drives all 7 |

**The split rate swings by a factor of two on identical code**, and every
comparison this project has made on it used three or four sessions.

### The error underneath it

Nearly every test in these files - including most of the ones written on
2026-08-12 - was a Fisher exact on **pooled turns or pooled records**:
`16/29 vs 3/78`, `58/108 vs 30/108`, `168/610`. That treats each turn as an
independent draw. **It is not.** One Director decision - sealing a pulpit -
produces seven empty-audience records in one session. One graph shape produces
thirty split narrations. The correlated unit is the **session**, and pooling
turns inside it inflates the effective n by roughly an order of magnitude, which
makes p-values look far stronger than the evidence is.

**What this does and does not invalidate:**

- **Sound:** tests whose unit already IS the session. Task 64's *"control never
  returned in 5 of 12 sessions versus 0 of 9"*, p=0.045, is a real test.
- **Direction probably right, confidence overstated:** task 71's leak
  (16/29 → 3/78) and task 67's split-rate change. The effects are large and
  visible per session, but the quoted p-values are not defensible.
- **Never trust at n≤4:** anything built on the split rate.

**The rule going forward:** count the metric per session, then compare
sessions. If that leaves too few points to test, say so instead of pooling turns
to manufacture significance.

## The sharpest case on this page: 0.02 similarity, and a reader sees one paragraph

Found 2026-08-12 by reading `c76037ff`, after task 71 shipped that morning.

Its five-person cluster got sixteen narrations, eight of them with no events at
all, so the renderer described the room instead. Consecutive pairs score **0.02**
on sequence similarity. Every repetition instrument in this project reads that
as two unrelated paragraphs, and every one of them is wrong: the imagery is the
same every time.

| word | small cluster | main cluster |
|---|---|---|
| `quietude` | **44%** | 3% |
| `penumbra` | **50%** | 0% |
| `halos` | **19%** | 0% |
| `colunas` | **19%** | 0% |

A stillness vocabulary the busy half of the scene never touches. The model
varies its wording enough to defeat sequence similarity while saying the same
thing, which is exactly the failure mode a language model should be expected to
have and exactly the one `SequenceMatcher` cannot see.

**Transferable, and it generalises past repetition:** lexical distance measures
whether the WORDS changed. Nothing on this page measures whether anything
HAPPENED. When those two come apart, the reader tracks the second one, and every
instrument here tracks the first.

## The recurrence detector that carried a whole task, unread

Task 69's headline symptom - the Director re-proposing events it already
resolved - was **9.8% of events, 97 of 987**, produced by `sim(a,b) >= 0.6` over
events within three turns. The threshold had **no derivation, no empty band, no
false-positive population and no entry on this page**, and nobody had read its
hits until 2026-08-13.

Read, five flagged pairs from `55d03896`:

| sim | verdict on reading |
|---|---|
| 0.80 | ✅ genuine: *"A mesa central desaba parcialmente na fenda, revelando um duto"* twice |
| 0.70 | ✅ genuine: the same rune re-applied, restated |
| 0.68 | ~ the second EXTENDS the first (adds a screech) |
| 0.66 | ~ a progression: the rune is *started*, then *completed* |
| **0.62** | ❌ **false positive**: *"O clarão verde **continua** pulsando"* against *"O clarão verde **cessa de repente**"* - opposite events sharing vocabulary |

And the 0.4-0.6 band it clears contains at least one plausible repeat (a creature
crossing a wall, described twice at 0.41).

**So the 9.8% is not a rate.** It is the output of an instrument with roughly
half precision on a read of five, in the band where this project has already been
burned twice. Task 69's symptom is **OBSERVED, not MEASURED**, until someone
reads a proper sample.

**One thing that partly survives**: a biased instrument applied to both halves of
the same session can still detect a *difference*, provided the bias is constant.
It is not quite constant - baseline similarity between unrelated events (>=10
turns apart, so they cannot be repeats) drifts **+0.013** upward from first half
to second, rising in 14 of 19 sessions. That is small against the 0.29-to-0.60
gap, so it cannot manufacture the whole effect, but it is the right size to
inflate it.

**Transferable:** an instrument nobody has read is not a weaker instrument, it is
an unknown one, and a task can be built on it for weeks. This one was found by a
critic that had never seen the code, asking why a similarity score was standing
in for whether anything happened.

### The proper sample was read, same day — 2 false positives in 20 (10%)

Systematic sample (every 35th) of all **703** flagged pairs across the **33
distinct** sessions, each read individually:

| | |
|---|---|
| genuine re-proposals | **18 of 20** |
| false positives | **2 of 20 = 10%** |

Better than the *"roughly half precision"* the read of five suggested, and the
five-case estimate above is superseded rather than deleted — it was right that
the instrument needed reading and wrong about how badly it performs.

**Both misses share one shape: same phrasing, different content.**

- a fissure swallows **Mirella, Liora and Lucan**; one turn later a *new* fissure
  swallows **Cael, Ysara, Oriana and Téo** (`d0cc98e5` T28→T29);
- **Nix** shouts to back off the fissure edge, **Bruna** shouts to fall back to
  the arches because the fire will surround them (`5d60575d` T20→T22).

Neither is a repeat. Both score high because Portuguese emergency-shouting has a
small vocabulary. **A lexical detector cannot see that the people are different**,
which is the same blindness as *"opposite events sharing vocabulary"*, one level
up: it is not the words that changed, it is who they happened to.

**Verdict unchanged: REPORT, DO NOT GATE.** 10% is fine for describing a corpus
and not fine for blocking a Director's output.

**And the population is not what the task using it assumed.** Of the 703 pairs,
**43.4% are `audible_speech`** — the Director re-summarising speech — against
24.3% `physical_outcome` and 28.6% `observation`. Task 69 is about physical
events, so slightly more than half of its own headline number is somebody else's
defect. Pooled recurrence over the full archive is **703/5,064 = 13.9%**, per
session **median 12.5%, sd 5.2pts, range 4.6-24.9%** (n=31) — which is, unusually
for this page, a spread that does **not** destroy the pooled figure.

## An agreement figure needs chance agreement as its control

Recorded 2026-08-13, found by a critic given the numbers with the prose removed.

Two instruments were compared: one calling 16.7% of moves a reposition, the other
calling 93.2%. The reported agreement was **24.5%** — and with those two marginals
the arithmetic **ceiling** is 23.4% and the chance floor is 21.2%. The reported
figure exceeded its own ceiling (so a denominator was inconsistent somewhere), and
the entire feasible range corresponds to **kappa between 0 and 0.03**.

**An agreement percentage between two classifiers with lopsided base rates is
pinned by those base rates and carries almost no information.** It looked like
evidence and was arithmetic.

**Transferable, and it is rule 3 applied to a shape nobody thinks of as a metric:**
*the control for an agreement figure is chance agreement.* Compute it before
quoting the raw percentage, and if one classifier is near-degenerate — 93.2% one
way — say so instead, because that fact explains the agreement entirely.

## Matching a NAME: the failure that keeps recurring

### ⚠ It recurred again on 2026-08-13, in a NEW instrument, written after this page

**The fifth.** Task 79's hierarchical detector asked whether a destination's first
comma-segment was a **substring of** the origin. Every zone in the scenario is
named `Academia Real do Primeiro Sino, <somewhere>`, so it scored **every move
anywhere inside the academy** as *"repositioning inside a space they never left"*:
hall to outer courtyard, hall to meeting hall, meeting hall to east gardens. One
turn of `17ec48d5` scored 21 such moves and all 21 were the cast walking outdoors.

| | pooled | per session |
|---|---|---|
| the inflated rule | **37.6%** (228/606) | — |
| **corrected** (full origin plus a comma) | **16.7%** (101/606) | median **5.6%**, sd 22.0pts, range 0-79.3%, **12 of 27 sessions at zero** |

**The number that justified a task was about 2x too high, for three weeks.**

What makes this one worth its own entry rather than a tally mark: **it is the same
failure as task 76's two shipped false positives — a wing and a building read as
rooms — reproduced by an author who had read that lesson, written it into this
page, and cited it in the very file the new detector lived in.** Knowing the rule
did not prevent it. The pattern is not ignorance, it is that *prefix containment
looks like hierarchy* and hierarchy is what these names accidentally encode.

**The only defence that has ever worked here is reading the disagreement set.**
This was caught by printing 15 of the 127 entries the corrected rule rejects and
looking at them, not by either number seeming wrong. Both numbers looked fine.

**Transferable rule, stronger than the old one:** *never match a name with a
string heuristic* was not enough, because it reads as advice about proper nouns.
The operative version is: **any test of the form "is A part of B" over
model-authored place names is measuring a naming convention until you have read
the set it separates.** Substring, prefix, suffix and token overlap are all the
same trap.


Three times this month, in three different components, a guard matched a proper
name against Portuguese prose and fired on an ordinary word. It is the single
most repeated mistake in this register, so it gets a rule rather than a third
war story.

| where | matched | actually |
|---|---|---|
| `named_exclusions` (task 70) | `\bmenos\b` | *"despenca **a menos de** dois metros"* — a distance |
| `_strip_offstage_actors` (task 71) | any name token, case-insensitive | *"um **véu** opaco"* — Portuguese for veil, and Noa **Véu**'s surname |
| `scan_cross_cluster_leak` (task 71) | first names | inflated the pre-71 leak rate from 55% to 72% |

Every one passed review, and two passed a corpus. The corpus is the trap: a name
guard validated on 631 archived prompts fired 15 times on the first fresh
session, because the archive happened not to contain the shape.

**The rule.** A guard that matches a model-authored NAME must:

1. **require more than one token** where the name has more than one, matched
   adjacent — `Marta Ferrolume` is not a word anybody writes by accident, and
   `Marta` is;
2. **require the capital** where the name is a single token, since an ordinary
   noun mid-sentence does not carry one;
3. **drop any pattern that also matches something legitimate in scope** — a
   name shared with an on-stage character decides nothing;
4. **be replayed over real output including the sentences it should NOT touch.**
   The true-positive count is the cheap half. The false-positive population is
   the evidence.

Applied to `_strip_offstage_actors`, that took it from 6 fires with 3 false
positives to 3 fires with 0, over the same 42 narrations.

**And the asymmetry that decides the tuning:** for a guard that DELETES text, a
false positive destroys prose the reader is entitled to and a false negative
leaves one stray sentence. They are not the same cost, so when two variants
score equally on the true positives, take the stricter one.

## The three that were measured and rejected

`deaf_occupied` (an occupied zone that can hear nothing), `unreciprocated` (A
hears B, B does not hear A) and `edges_lost` (an edge present at turn N gone at
N+1), each computed per turn over all 16 archived sessions:

| session | `deaf`·turns | `unrecip`·turns | actual empty audiences |
|---|---|---|---|
| `oldcode-P1-r3` | 288 | **1764** | **0** |
| `drive-P1-r3` | 243 | 9 | **0** |
| `base-P1-r2` | **0** | 270 | **10** |
| `oldcode-P1-r1` | 0 | 0 | 2 |

**None predicts the damage.** Graph damage is *exposure*, not damage — a broken
edge costs nothing until someone speaks across it.

`deaf_occupied` was additionally just wrong: `zones[Z] = []` does not make Z
deaf, because same-zone perception is implicit. It was flagging ordinary closed
rooms, and 36 of 106 archived `zone_link_updates` deliberately create that state.

They remain useful as **diagnostics** — they are how the fresh cell's wiped hall
and `base-P1-r2`'s T20→T21 edge deletion were both located — and they are
recorded here as rejected so nobody re-derives them as dashboard numbers. Each
would look entirely plausible on a dashboard and rank sessions wrong.

## `SIL`, and why a constant is not always worthless

`SIL` is 0.0 in **18 of 18** runs including both 2026-08-06 cells.
`perception_events` requires one item and the prose floor is 150 words, so a
silent turn is structurally impossible. As a *guard* it is dead and must gate
nothing.

**It is not dropped**, because it is the standing evidence for **task 72**: the
engine cannot be still. A metric that always reads the same value still
documents a structural fact, as long as nobody mistakes it for a check that
passed.

## The critic subagent — first run, 2026-08-13

The instrument defined in `.plan/reference/critic-protocol.md`, measured for the
first time. It reviewed `.plan/CHECKPOINT-2026-08-13.md` in isolation: the
content and the critic prompt, no code, no task files, no history, no author.
27 claims extracted, 7 marked WORSE THAN ABSENT, 8 demoted, 2 promoted.

**It found two defects a human reader of the same document had missed.** Both are
verifiable in the text alone, which is the point:

1. **The phase's top-priority metric is stated twice, incompatibly.** The task-79
   row carries the post-audit figures (median 6.8%, sd 7.0pts, range 0.5-25.4%);
   the "standing numbers" table 111 lines later still carries the pre-audit ones
   (median 6%, sd 9.0pts, range 0-44%). Same metric, a range nearly twice as wide,
   no label saying which run is current — under a heading that invites quoting.
2. **A generalisation contradicted by the list it summarises.** *"Not one was
   caught by a number looking wrong... seven for seven, and it is the standing
   method"* sits four lines below a bullet reading *"Killed by a control that cost
   nothing, under a rule written before the number existed."* At least two of the
   seven were caught numerically. Promoted to "the standing method", that sentence
   reads as licence to skip controls — the opposite of what the same document
   demands elsewhere.

It also caught `"the mechanism is that settled state does not bind the output"`
sitting under a ✅ in a **mechanism** column with nothing behind it, and
`"every headline number carries its per-session spread"` asserted in a file where
four headline numbers do not.

### What it costs

**Isolation produces false alarms, and that is the design, not a defect.** The
critic called 76's *"firings track opportunity 6/6"* unsupported — *"the classic
shape of a detector that cannot see the negative case"*. The reasoning is sound
and the conclusion is wrong: that finding came from a cross-tabulation that did
include negative cases (a 53%-comma-named session with zero sibling pairs), which
is recorded elsewhere and was withheld from the critic on purpose. The verdict
still did its job — it is a ruling on whether *the text carries its own weight*,
and that text did not.

Budget for roughly one such alarm per document. The exchange is a good one.

### Status

**TRUSTED as a reader of documents. It gates nothing.** It cannot rule on the
world, only on whether a page supports what it says. When the critic and a reader
of the code disagree, the reader wins and the disagreement is recorded here — the
same rule that applies to every other instrument on this page.

n=1 document. Ask again after five.
