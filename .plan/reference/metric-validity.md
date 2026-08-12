# Which metrics this project trusts, and why — 2026-08-06

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
| `clamp_lost_half` (task 67) | **new, trusted** | replaces emptiness-only counting; recovers every case its task already cites. Corrected 2026-08-12: the subject is not their own witness |
| `named_exclusions` (task 70) | **fixed same day** | shipped with a false positive; see below |
| `_carries_intent` (task 65) | **weak, kept permissive** | does not separate on real data; see below |
| `empty_audience` (task 67) | **kept, but not sufficient alone** | true positives only, and it misses the near-miss population |
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
