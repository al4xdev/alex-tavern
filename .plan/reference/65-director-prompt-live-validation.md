# Task 65 — live validation of the Director prompt variant, 2026-08-06

The obligation `AGENTS.md` §6 leaves open when a prompt ships: the validated
variant has to be the shipped variant. Task 65 changed the DIALOGUE OWNERSHIP
rule and the `"content":` clause on 2026-08-06 and shipped them unvalidated,
because the old text (*"never invent new dialogue… record only words already
spoken in HISTORY"*) contradicts the engine that replaced it, so leaving it was
not an option. This is the replay that closes that gap.

> **The evidence corpus briefly vanished mid-experiment.**
> `plans/artifacts/p1-archive/` was emptied at 11:47 on 2026-08-06, between the
> Director runs and the control arm, by the SSH sync of a machine move. It was
> restored from the other machine the same afternoon, which is what let the
> control arm run. `plans/` is gitignored and git could not have restored it,
> which is why every number below is written out here rather than left as a
> pointer to a corpus that can disappear again.

## The decision rule, pre-registered before any call

> The NEW variant ships if, over 4 runs per payload on two real archived
> payloads:
>
> 1. **the defect rate falls** — on the payload where the old variant
>    demonstrably authors dialogue, the share of `audible_speech` events
>    carrying a quoted span is materially lower under NEW than under OLD;
> 2. **the channel does not collapse** — mean `audible_speech` events per call
>    under NEW stays above half the OLD mean. A Director that simply stops using
>    the channel has not fixed the defect, it has broken WT-09.
>
> Both must hold. Clause 2 is the one that matters: it is easy to win clause 1
> by making the Director abandon the channel, which silently deletes facts
> witnesses need.

Payloads were chosen from the **recorded** output only, before any new call:

| | why |
|---|---|
| **T10** | 2 `audible_speech`, **both quoted**. The defect is present, so the variant has something to fix. |
| **T23** | 4 `audible_speech`, **none quoted** (already reported form). The richest turn in the session, so the sharpest test of clause 2. |

Both from `base-P1-r2/sessions/8bd4d0f1`, `deepseek-v4-flash`, `thinking`
disabled, `response_format: json_object`.

**Method:** the two changed blocks were read out of the production builder and
**substituted into the recorded system prompt**, not rebuilt — position is part
of the variant (§6, measured 2026-07-18: the same rules at the END worked 3/3,
buried in the MIDDLE failed 3/3), and substitution preserves it exactly. Each
old block occurred exactly once in the recorded prompt, asserted before firing.

## Result — the variant passes both clauses

| payload | variant | audible/run | quoted | events/run |
|---|---|---|---|---|
| T10 | old | 1.00 (`0,2,1,1`) | **4/4 (100%)** | 5.50 |
| T10 | **new** | 1.00 (`0,1,1,2`) | **0/4 (0%)** | 5.75 |
| T23 | old | 1.00 (`0,2,1,1`) | **1/4 (25%)** | 5.25 |
| T23 | **new** | 1.75 (`3,2,2,0`) | **0/7 (0%)** | 5.00 |

**Pooled: 5/8 (62%) quoted under OLD, 0/11 (0%) under NEW.** Fisher exact
two-tailed **p = 0.0048**.

Clause 2 is satisfied with room to spare: the channel was used **more** under
the new variant, 1.38 `audible_speech` per call against 1.00, and total
`perception_events` per call is flat (5.4 vs 5.4). The variant did not buy
compliance by going quiet.

Runs with zero `audible_speech` occur under both variants (T10 old r1, T10 new
r1, T23 old r1, T23 new r4), so they are turn-level variance, not an artifact of
the new text.

**The quote detector was checked against ground truth first**: over all 41
recorded `audible_speech` events in the session it flagged 17 and missed none,
agreeing with a read of every one. That 17/41 is also the session-wide baseline
for the old prompt — **41% of the channel carried a quoted line.**

### The variant that was validated is not quite the variant that shipped

Two dropped words were found in the shipped text while reading it for this
replay, and **fixed before the replay ran**, so that the validated text is the
shipped text rather than an approximation of it:

- `"the fact that character makes public"` → `"the fact that **the** character
  makes public"`;
- `"engine hands that brief"` → `"**The** engine hands that brief"`.

## The `_INTENT_CARRIED_RATIO` calibration — one arm of two

`_INTENT_CARRIED_RATIO = 0.5` (`src/runner.py`) is the one threshold in task 65
that could not be sized against the archive, because it judges compliance with a
prompt that did not exist before 2026-08-06. The archive has no positives for
it, so this **built** them: each of the 11 intents the validated Director
produced was handed to the real character agent through the shipped
`_speech_mandate_note`, substituted into a recorded character payload
immediately before *"Return your audible speech and private thought…"*, which is
exactly where `_build_user_prompt` puts it. 10 of the 11 had an archived call
for that character to carry them.

### The falsifier does NOT fire — the mandate is a prompt promise that wins

**All 10 replies genuinely voiced the fact**, on a read of every one. Case C
stays as designed; it does not fall back to case A's dedicated call.

```
ratios, sorted:  0.39  0.53  0.55  0.57  0.60  0.64  0.67  0.69  0.73  0.79
carried at the shipped 0.5:  9/10        mandate_ignored: 1/10
```

### The negative control: there IS a band, and 0.5 was on the wrong side of it

The mandate arm alone shows only one of the two error rates, so it cannot size a
threshold. The control fired **the identical payloads with the mandate removed**
and scored the reply against the same intent — the overlap topicality alone
produces, since the character was never told.

| | mandated | unmandated control |
|---|---|---|
| ratios, sorted | `0.39 0.53 0.55 0.57 0.60 0.64 0.67 0.69 0.73 0.79` | `0.00 0.00 0.00 0.00 0.07 0.07 0.09 0.09 0.19 0.29` |
| range | **0.39 – 0.79** | **0.00 – 0.29** |

**The two clouds do not touch: an empty band from 0.29 to 0.39, 0.10 wide.** The
ratio discriminates cleanly, and the pre-registered reading applies — the
threshold belongs in the gap.

**0.5 was not in the gap. It was above it, inside the mandated cluster**, which
is precisely why it cost a compliant reply. Any threshold in `(0.29, 0.39]`
classifies this sample perfectly: **10/10 mandated kept, 0/10 control kept.**
Shipped at the midpoint, **0.34**.

| threshold | mandated kept | control wrongly kept |
|---|---|---|
| 0.3 | **10/10** | **0/10** |
| **0.34** (shipped) | **10/10** | **0/10** |
| 0.4 | 9/10 | 0/10 |
| 0.5 (was) | 9/10 | 0/10 |
| 0.6 | 6/10 | 0/10 |

**On the strength of this evidence:** n = 10 per arm, one scenario, one model,
one session. The language guard in this same task was sized over 3,936 records;
this is twenty. The band is real and the direction of the error is unambiguous,
but 0.34 is a first calibration, not a settled constant, and the next corpus of
real `mandate_ignored` records should re-derive it.

The control replies confirm the confound is doing its job rather than being
trivially separable — several are on the same topic and still land below the
band, e.g. Bruna at **0.31**, *"Diretora, a braçadeira quebrou! A carga vem do
piso, não da escada…"* against an intent about the mist's source under the
rubble. Talking about the same crisis is not carrying the fact, and the ratio
tells them apart.

### Why the old threshold's single miss was the expensive kind

The sub-threshold case under 0.5 was a **false positive** — a fully compliant
reply scored below the line:

> **intent:** *"A diretora Maelis, com a voz firme e cortante, ordena que todos
> os alunos formem fila e caminhem em direção ao corredor leste para evacuar, e
> que ninguém pare para recuperar pertences ou investigar selos."*
> **spoken:** *"Chega de hesitação! Todos os alunos, agora, em fila única para o
> corredor leste. Nada de voltar para buscar pertences ou investigar selos. Quem
> parar, fica para trás."*

That costs more than a wasted call. At `runner.py:1721-1726` a false
`_carries_intent` in case C emits a **Narrator report of the same fact beside
the character's own compliant line** — the room hears the beat twice, which is
the duplication task 65 exists to remove, wearing the degradation path's byline.
False positives are the expensive direction here.

### The measured cause: the denominator counts words the character cannot say

**10 of 10 intents name their own subject; 0 of 10 replies do.** The new prompt
*requires* reported form, and reported form always names the speaker, so
`diretora`/`maelis`, `bruna`, `riven`, `ysara`, `lucan` sit in the denominator
of every case-C event and can never be matched. The worst case above also spends
denominator on the Director's delivery notes (`firme`, `cortante`), which a
character embodies rather than utters.

Excluding only the subject's own name tokens from `wanted`:

| threshold | denominator as shipped | own name excluded |
|---|---|---|
| 0.4 | 9/10 | **10/10** |
| 0.5 | 9/10 | 9/10 |
| 0.6 | 6/10 | **9/10** |
| 0.7 | 2/10 | 4/10 |

Every ratio rises (mean +0.073, minimum +0.044); sorted, they become
`0.44 0.60 0.62 0.67 0.67 0.69 0.73 0.73 0.85 0.89`.

Scored under the control too, excluding the name widens the empty band from
**0.10 to 0.13** (control tops out at 0.31, mandated starts at 0.44):

| | mandated | control | band |
|---|---|---|---|
| denominator as shipped | 0.39 – 0.79 | 0.00 – 0.29 | **0.10** |
| own name excluded | 0.44 – 0.89 | 0.00 – 0.31 | **0.13** |

**Measured, and deliberately NOT shipped.** The shipped denominator already
separates the two arms perfectly, so the refinement buys 0.03 of band width at
the cost of plumbing the subject's name into the discriminator at both call
sites. The argument for doing it anyway is not this sample but generalisation:
the bias is *proportionally larger on short intents*, which have the smallest
denominators and therefore the noisiest ratios, and those are the ones a narrow
band will fail on first.

**If it is ever adopted, re-derive the threshold with it** — the two are
coupled, and the midpoint under that denominator is ≈0.375, not 0.34.

## ⚠ A real cell falsified the band — 2026-08-06, later the same day

Everything above about the threshold was derived from **20 synthetic replies on
one scene**. A fresh 40-turn P2 cell (`34390b86`, base, post-65 and post-70)
contradicts it, and the contradiction is the useful part.

Of **42 case-C events**, 9 were logged `mandate_ignored` at the 0.34 threshold.
**A read of all 9 finds every one compliant**, several nearly verbatim:

| | |
|---|---|
| intent | *"Garran … ordem para os alunos **formarem** equipes de quatro imediatamente e se **afastarem** da criatura"* |
| said | *"**Formem** equipes de quatro agora! **Afastem**-se da criatura, não encostem nos destroços!"* |
| score | **0.30** — below the line |

**The cause is Portuguese morphology.** Reported speech, which the new Director
prompt now requires, uses infinitive and subjunctive forms (`formarem`,
`afastarem`, `subam`); a character speaking uses the imperative (`formem`,
`afastem`). Exact token matching pairs none of them — nor the subject's own
name, the bias already recorded above, which reported form always states and
direct speech never does.

### The clouds overlap, so no threshold classifies both correctly

Pooling the **9 verified-compliant real replies** with the 10 synthetic mandated
ones, against the same unmandated control:

| | range |
|---|---|
| compliant (n=19) | **0.15 – 0.79** |
| unmandated control (n=10) | **0.00 – 0.29** |

**Overlap of 0.13**, not a band. The pre-registered reading applies exactly as
written: *"the ratio cannot separate 'voiced the fact' from 'happened to be
talking about it', and no threshold rescues it — a finding about the instrument,
not a reason to pick a nicer number."*

Stem-prefix matching was tried as a fix for the morphology and **made it worse**
(overlap 0.13 → 0.18), because it lifts the control's ceiling too.

### So the value is chosen by which error is affordable

| threshold | compliant kept | spurious duplications | control wrongly kept |
|---|---|---|---|
| 0.10 | 19/19 | **0** | 2/10 |
| **0.15** (shipped) | **19/19** | **0** | **2/10** |
| 0.20 | 16/19 | 3 | 1/10 |
| 0.30 | 14/19 | 5 | 0/10 |
| 0.34 (was) | 10/19 | **9** | 0/10 |

A false negative is the expensive error: `_resolve_speech_intents` then prints a
Narrator report **beside the character's own compliant line**, which is task
65's founding defect. At 0.34 that fired on 9 of 42 case-C events in a single
session. **Shipped at 0.15**, where 0.10-0.15 is a plateau rather than a
knife-edge, so it is not tuned to one sample's edge.

### What this says about the case-C falsifier

The falsifier's trigger fired — `mandate_ignored` on 21% of case C — **and its
diagnosis is wrong.** It reads that rate as "the mandate is a prompt promise
that loses", which would send case C back to a dedicated call. But the mandate
did not lose: **42 of 42 case-C events were compliant on reading.** The
measurement lost. Falling back to a dedicated call would have spent calls to fix
a defect that was in the ruler.

**Case C stays**, and the falsifier now reads: *if `mandate_ignored` fires on a
large share of case C **and a read of the flagged replies confirms they missed
the fact**, the mechanism is what failed.* The second clause was missing and is
the whole difference.

## Status

| | |
|---|---|
| Director prompt variant | **validated, shipped** |
| `_INTENT_CARRIED_RATIO` | **0.5 → 0.34 → 0.15**; the 0.34 band was a synthetic-sample artifact |
| the ratio as an instrument | **does not separate on real data**; kept permissive by design |
| own-name exclusion | measured, **not shipped**; would not fix the morphology half |
| case-C mandate mechanism | **survives** — 42/42 compliant on a real cell |
| 65's headline defect | **`director_authored` = 0 of 119 speech records**, from 29.3% in P2 |

`plans/artifacts/p1-archive/` was restored from the other machine after the loss
noted above, which is what let the control arm run. Raw outputs for every call
in both experiments, plus the three harness scripts, are in
`plans/artifacts/65-live-validation/` (gitignored, so they travel with the tree
and not with git).
