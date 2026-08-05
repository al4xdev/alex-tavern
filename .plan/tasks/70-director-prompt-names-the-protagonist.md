# Task 70 — The Director prompt names the protagonist

> **Status:** open. **Wave 1.** Found by a blind evidence audit of the roadmap;
> no previous case, task or metric in this project had seen it.
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

## Closure evidence required

- [ ] no Director prompt contains a rule naming exactly one character id;
- [ ] `prompt_contract` gains a check that catches **this shape** — a constraint
      clause referencing a single cast id — and it fails against the current
      prompt before the fix and passes after;
- [ ] the scanner runs over the archived P1 and P2 prompts, before/after counts
      recorded (before: 100% of P2 turns);
- [ ] Task 45's requirement still holds: a test that the controlled character is
      not routed on the first beats of a burst, expressed without a named
      exclusion in the prompt;
- [ ] `return_control` and PC-routing rates re-measured on one cell afterwards,
      and the result written into task 64 before 64 is designed.

**The measurement that would falsify this task:** none. This is an invariant
under `AGENTS.md` §3; measurement chooses the fix, not whether to fix.
