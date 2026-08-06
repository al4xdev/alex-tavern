# Task 70 — The Director prompt names the protagonist

> **Status:** DELIVERED 2026-08-06, bar the task-64 re-measurement. **Wave 1.**
> Found by a blind evidence audit of the roadmap; no previous case, task or
> metric in this project had seen it.
>
> **The sections below are left as they were written**, including the line
> numbers and the suggested Direction, because the Direction turned out to be
> already-rejected in this repo and that is worth seeing. What shipped is in
> "✅ DELIVERED" at the end.
>
> This is the one task in the phase whose **existence is not negotiable by
> measurement**. `AGENTS.md` §3 says so explicitly, and says why.

## Problem

`src/agents/narrator.py:531-534` appends to the Director prompt:

```python
lines.append(
    f"  Let someone other than {exclude_speaker} carry this beat; the "
    "scene is more interesting when attention moves."
)
```

`exclude_speaker` is always the human's character: `runner.py:2409` passes
`game.player.controlled_character_id`, and `exclude_controlled` **defaults to
`True`** (`runner.py:2401`), overridden only inside the burst loop
(`runner.py:1150`) for beats beyond `BURST_PROTAGONIST_EXCLUDE_BEATS`.

So on most turns, the Director is handed one character id, by name, with an
instruction that applies to that id and no other.

`AGENTS.md` §3, *Agência e imersão*:

> **marcador estrutural também é vazamento.** Um prompt que formata o personagem
> controlado de maneira diferente de todos os outros o identifica sem nomear
> nada — e isso viola esta seção do mesmo jeito que a palavra "jogador"
> violaria. Rótulo, ordem, campo extra, **exclusão nomeada**: se a regra de
> formatação separa exatamente um personagem, ela codifica
> `controlled_character_id` no texto. Encontrado duas vezes em 2026-07-27: a
> constraint de routing do Diretor (corrigida em `5002f11`) e o contexto de
> drive/watcher (task 58).

The rule names this exact construct, and cites the commit that was supposed to
have fixed it. **`5002f11` changed the justification, not the naming.** The
comment above the code says as much (`narrator.py:526-530`): the old wording
*"they just spoke or passed"* was false on the second beat of a burst, so the
reason was rewritten to a dramatic one that holds on every beat. The id is still
in the string.

## Scale

Counted from the archived prompts:

| cells | turns carrying the named exclusion |
|---|---|
| P2 (`base`, `oldcode`) | **41/41, 41/41, 44/44 — 100%** |
| P1 | 16/39, 16/40, 17/51 — **33–41%** |

P2 is every turn because the exclusion only lifts inside a multi-beat burst, and
the P2 profile has no bursts at all.

## Why no guard caught it

`src/prompt_contract.py` has two checks. `operator_ontology_hits` is lexical —
"player", "user", "operator" — and the string contains none of them.
`singled_out_speakers` inspects **speaker-label formatting** in the rendered
cast/history, and this line is not a speaker label; it is a routing instruction
in a different block. The invariant has a scanner and the scanner is structurally
blind to this shape of violation.

## Why it may also be a mechanism, not only a leak

`AGENTS.md` §3 also states the designed path for handing control back:

> quando o Narrador escolhe o personagem controlado como próximo falante, o
> Runner devolve o controle ao humano e não gera sua fala

That is the engine's primary control-return mechanism, and this block instructs
the Director against taking it. Measured corpus-wide: `return_control=True` fired
**5 times in 482 Director turns (1%)**, the controlled character was routed as a
speaker **11 times (2.3%)**, and in **5 of 12 sessions control never returned by
either path**.

So this task may partly or wholly resolve **task 64**. That is a hypothesis, not
a claim — 64 says to re-measure after this lands rather than design against a
number taken while this was in the prompt.

## Direction

The requirement behind the line is real: on the first beats of an autonomous
burst the world should react before the story pulls the human back in (Task 45).
The requirement can be met without naming anyone — express the constraint as
**structure the model cannot resolve to an identity**, e.g. constrain the
candidate set the model chooses from rather than describing an exclusion in
prose, so the prompt never contains a rule that separates exactly one character.

Per `AGENTS.md` §3, the experiment decides the **form** of the correction, never
whether to make it:

> Uma invariante que aceita reprovação por métrica de qualidade não é invariante.

If removing the instruction costs narrative quality, the answer is a different
formulation, not keeping this one.

## Counter-argument, recorded

*"The model cannot tell that this id is the human's — it just sees a routing
preference for one character."* That is the argument `5002f11` already rejected,
and §3 rejects it in general: the rule is about what the formatting **encodes**,
not about what the model is proven to infer. A rule that separates exactly one
character encodes `controlled_character_id` whether or not this week's model
acts on it.

## ✅ DELIVERED — 2026-08-06

**The block is gone, not reworded.** `_build_user_prompt` no longer takes
`exclude_speaker` at all, so the exclusion is not expressible in the Director
prompt any more — it is enforced only where it always actually was, in
`narrate`'s normalization (`narrator.py:750`, `entry != exclude_speaker`, with
`["Narrator"]` as the fallback when that empties the queue).

### The task's own suggested fix was already dead, with a measurement

The Direction section proposes *"constrain the candidate set the model chooses
from"*. That is exactly what `narrator.py:298-303` records as rejected: a
narrowed enum made the provider-side validator reject responses the lenient
normalization was built to absorb, **3 straight schema failures on a stalled
skip turn**. So the schema was never available and the real choice was between
prompt formulations, with code enforcing either way.

### The form was chosen by measurement, per §3

Decision rule pre-registered before any call. Two archived P2 payloads
(`base-P2-r1` T13, `oldcode-P2-r1` T13), 4 runs each, three arms — **A** the
recorded named exclusion (baseline, ineligible to ship), **B** the block
deleted, **C** the block kept with the id removed.

| variant | PC routed (raw) | Narrator-only | mean queue |
|---|---|---|---|
| A named exclusion | **0/8** | 0/8 | 2.75 |
| B deleted | **0/8** | 0/8 | 2.88 |
| C id-free block | **0/8** | 0/8 | 2.88 |

**The clause was buying nothing measurable.** The Director never routed the
controlled character even with no instruction at all, and no arm ever collapsed
a beat to Narrator-only. Both id-free arms passed, so the pre-registered
tie-break applied and **B shipped**, chosen by the owner.

*Recorded so it is not mistaken for evidence:* arm C looked like it spread the
cast wider on one payload (10 distinct characters against B's 4) and narrower on
the other (4 against 5). It does not replicate at n=4 per cell, it was not
pre-registered, and it decided nothing.

### Closure evidence

- [x] no Director prompt contains a rule naming exactly one character id
      *(builder emits none on any routing path: `forced_speaker` unset, set to a
      character, and set to `Narrator`)*;
- [x] `prompt_contract` gains a check that catches **this shape** —
      `named_exclusions()`, membership-not-shape like task 65's id guard, and a
      test asserts the two older checks are **blind** to the shipped clause;
- [x] the scanner runs over the archived P1 and P2 prompts, before/after counts
      recorded — **before: 371/631 (58.8%)**, 100% of every P2 cell and 40–55%
      of every P1 cell; **after: 0**;
- [x] Task 45's requirement still holds — `narrate` is driven with a Director
      that routes the controlled character anyway and the id is dropped, plus
      the negative half (without an exclusion the same response routes everyone,
      so the drop is the exclusion working and not normalization eating the
      first entry);
- [x] `return_control` and PC-routing rates re-measured on one cell afterwards
      *(2026-08-06, session `34390b86`, 40-turn P2 base)*:

| | archive, WITH the exclusion | fresh cell, WITHOUT it |
|---|---|---|
| `return_control=True` | 5 of 482 Director turns (**1.0%**) | 2 of 40 (**5.0%**) |
| controlled character routed | 11 of 482 (**2.3%**) | 1 of 40 (**2.5%**) |

**`return_control` rose about fivefold; PC routing did not move.** Both samples
are small — 2 events against 5 — so this is a direction, not a rate. What it
does establish is that task 64 must not be designed against the archive's 1%,
which is the reason this item existed.

The controlled character still never reaches a persisted record as a speaker
(`pc_records_in_history` = 0): the one raw routing was dropped by normalization,
which is the mechanism working with nothing in the prompt to help it.

**Handed to task 64.** The archive's "control never returned in 5 of 12
sessions" is the number that most needs re-taking, and one cell cannot.

`named_exclusions` is also swept per call by `tools/playtest_harness.py`
alongside the other two contract checks, under the same
`None`-means-not-swept contract.

**The measurement that would falsify this task:** none. This is an invariant
under `AGENTS.md` §3; measurement chooses the fix, not whether to fix.
