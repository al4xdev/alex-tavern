# Task 65 — live validation of the Director prompt variant, 2026-08-06

The obligation `AGENTS.md` §6 leaves open when a prompt ships: the validated
variant has to be the shipped variant. Task 65 changed the DIALOGUE OWNERSHIP
rule and the `"content":` clause on 2026-08-06 and shipped them unvalidated,
because the old text (*"never invent new dialogue… record only words already
spoken in HISTORY"*) contradicts the engine that replaced it, so leaving it was
not an option. This is the replay that closes that gap.

> **The evidence corpus this ran against no longer exists on disk.**
> `plans/artifacts/p1-archive/` was emptied at 11:47 on 2026-08-06, during this
> session, between the runs and the write-up. `plans/` is gitignored, so git
> cannot restore it. Everything below was extracted before it went, and the
> numbers are recorded here rather than left as a pointer for that reason. The
> outstanding control arm needs the corpus back.

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

### But 0.5 is not in an empty band, and saying so is the point

The language guard in this same task earned its threshold: 0.012 against 1.000,
an empty band, nothing in between. **This one has no such band.** The
distribution above is continuous from 0.39 to 0.79 with no gap, so 0.5 is a
cost/benefit cut through a dense cluster, not a separation. It should never be
quoted with the language guard's confidence.

The single sub-threshold case is a **false positive** — a fully compliant reply
scored below the line:

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

**This is measured but NOT shipped**, deliberately. Removing tokens that cannot
be matched makes the *measurement* honest, but it also strictly raises every
ratio, which moves the operating point — and the cost of moving it is a
false-negative rate this experiment cannot see, because all ten replies
complied. Changing a discriminator while only one of its two error rates is
observable is the move §6 exists to prevent.

### What is missing: the negative control

The control arm — the identical character payloads fired **without** the
mandate, scoring whatever overlap topicality alone produces — was written and
was blocked by the corpus loss above. Its pre-registered reading:

> If the no-mandate ratios sit clearly below the mandated ones with a gap, the
> ratio discriminates and the threshold belongs in that gap. If the two clouds
> overlap substantially, the ratio cannot separate *"voiced the fact"* from
> *"happened to be talking about it"*, and no threshold rescues it — a finding
> about the instrument, not a reason to pick a nicer number.

Until it runs, `_INTENT_CARRIED_RATIO` stays at 0.5 with a **measured 10%
false-positive rate on compliant case-C replies** and a known structural bias in
its denominator. That is a great deal more than was known this morning, and less
than a closed calibration.

It needs `plans/artifacts/p1-archive/` restored from the other machine, or any
real session carrying character calls in the same scene as the intents.
