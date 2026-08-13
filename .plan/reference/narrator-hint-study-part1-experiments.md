# Explore: autonomous generation of `narrator_hint`

**Date**: 2026-07-18  
**Scope**: open experiment with DeepSeek V4 Flash over `curl`, using the state as
it stood before the human hint on turn 10 of session `e5a0ca6a`.

## Goal and criterion

The reference human hint was kept out of the prompts (quoted verbatim, as typed):

> todo nobres riem de link, devido a cena e a sujeira dele

An output counted as close when it discovered, on its own, the social consequence
that had been set up: a hostile rival starts the mockery, status-aligned
characters propagate a restrained public reaction, and a protective character may
react to the excess. Repeating Maelis's interrogation, controlling Link, inventing
danger, or merely prolonging the silence counted as a failure.

The calls made before the explicit request to "start over from scratch", and three
smoke tests of the wrapper, are not part of the series. A timeout with no response
was not counted as a valid call either.

## Calls

| # | Input data | Prompt/role | Output contract | Result in brief | Assessment and next hypothesis |
|---:|---|---|---|---|---|
| 1 | Scene and minimal history, no profiles | Direct generator of the next event | `{hint, motivo}` | Murmurs in the audience, but Maelis goes back to suspecting and interrogating | Partial. The public situation is enough to suggest a murmur, but relationship and saturation are missing |
| 2 | Four contrasting profiles + participation | Simulation of the next five seconds | Pressure ranking + hint | Identified Riven=laughter and Liora=contempt; the hint incorrectly claimed they had already taken over | Ranking beats free-form synthesis |
| 3 | Same input | Calculator; an event only at pressure >=70 | Scores + composite event | Riven and Liora start the mockery, others follow, Asword objects; escalated into jeering | Very close, intensity excessive |
| 4 | Same input | Explicit 1–5 scale and a cost for formality | Scores + event + hint | Riven/Liora out loud, murmurs, Asword; invented a reaction from the headmistress and treated Nix as hostile | Personality prose is ambiguous |
| 5 | Structured relational ledger | Social propagation: hostile, aligned, protective, pragmatic | Seed + followers + counter + hint | Riven starts; Liora and the nobles propagate; Asword pushes back | Correct and close to the human hint |
| 6 | Identical to #5 | Stability repeat | Same | Same chain, with surface variation | Correct |
| 7 | Identical to #5 | Stability repeat | Same | Returned `seed=null`, claiming no designated initiator | Conservative failure; stability 2/3 |
| 8 | Ledger; temperature 0.1 | The model must select the initiator, `null` only with no trigger | Same | Riven → laughter from the nobles/Liora → Asword's discomfort | Correct |
| 9 | Identical to #8 | Repeat | Same | Same chain | Correct |
| 10 | Identical to #8 | Repeat | Same | Same chain | Correct; 3/3 |
| 11 | Canonical profiles in prose instead of the ledger | Same social mechanism | Same | Nix was aligned with the bullying because she "uses jokes"; Asword duplicated | Raw prose is not safe without prior classification |
| 12 | Canonical profiles in prose | Strict order: classify the relationship, then simulate | Relations + seed/followers/counter + hint | Classified Riven/Liora hostile, Nix neutral, Asword protective; event correct | One call can build an ephemeral ledger |
| 13 | Identical to #12 | Repeat | Same | Nix `pragmatic_positive`; event correct | Correct |
| 14 | Identical to #12 | Repeat | Same | Nix neutral; event correct | Correct; 3/3 |
| 15 | Control: private conversation, Link/Maelis only | Staged classification | Same | Maelis pragmatic; `hint=null` | Negative control passed |
| 16 | Control: public scene, allies/neutrals only | Staged classification | Same | Everyone protective/neutral; `hint=null` | An audience and embarrassment alone do not force bullying |
| 17 | Transfer: an artisan spills wine; a rival, a status guardian and a friend | Staged classification | Same | The rival starts the laughter, guardian/audience follow, the friend pushes back | Generalised, but classified the status guardian as protective |
| 18 | Same transferred control | Taxonomy includes `status_aligned` | Same | Fixed the guardian; rival → audience → friend | A social-alignment category is necessary |
| 19 | Full real scene, summarised | An "auction" of physical/social/institutional/agenda lenses | Scored candidates + winner | Produced a cough for Link, an absurd postponement and valid sarcasm; got the arithmetic wrong and truncated | One creative call plus an internal arbiter is unstable |
| 20 | The bad and good candidates from #19 | Conservative judge | Verdicts + winner + hint | Rejected the cough, the postponement and the expulsion; chose Riven's sarcasm | Separating generation from judgement works |
| 21 | Real scene | Pure generator across five lenses, with no power to choose | Candidate list with support | Produced a sensation imposed on Link, Riven, Maelis, Liora and a noble | Useful diversity, still with invalid candidates |
| 22 | The exact output of #21 | Conservative judge | Verdicts + winner + hint | Rejected Link's action/sensation; chose Riven | The full pipeline reached the social hint |
| 23 | Institutional transfer: a stalled selection | Permissive lens generator | Candidate list | Invented a tablet, a light, a ritual and supporting facts; did not start the announcement | The generator needs near-literal support and explicit pending state |
| 24 | Same institutional control | Strict generator; the agenda lens looks for pending state | Each lens returns a candidate or `null` | Physical/social/environment `null`; duty and agenda start the announcement | Correct, nothing invented |
| 25 | The candidates from #24 | Judge of the smallest transition | Verdicts + winner + hint | *"Inicie o anúncio das equipes e ranks em cena, sem definir escolhas do protagonista"* | The institutional transfer passed |

### Operational occurrences outside the count

| Occurrence | Result |
|---|---|
| Private control #15, first attempt | HTTP timeout after 45 s, no response; repeated without altering the variant |
| Initial wrapper smoke test | HTTP 400, because DeepSeek requires the word "JSON" when `json_object` is used |
| Initial wrapper | A non-recursive substitution left `$DEEPSEEK_MODEL` in the body; fixed in `/tmp` |

## Findings

### The data that actually changed the outcome

1. **A recent public stimulus**, without long prose: who did what, in front of
   whom, and which consequence has not appeared yet.
2. **Recent participation per character**: Maelis had spoken three times and the
   rivals zero. That reduces repetition and reveals accumulated pressure.
3. **Profiles/relationships of the relevant people present**: hostility,
   protection, pragmatic humour and status alignment.
4. **Explicitly pending state**: "teams and ranks not announced yet". Without that
   declarative form, the agenda lens invented a wait and a ritual.
5. **Agency and canon constraints**: do not extend the action, speech, thought or
   sensation of whoever wrote the last input; do not invent objects or support.

The complete physical state, every personality and the long history were not
needed to discover the target hint. Irrelevant facts raised the chance of a
spurious association.

### The social contract of a single call

This contract scored 3/3 on the target scene and passed two negative controls:

```json
{
  "relations": [
    {"actor": "id", "polarity": "hostile|status_aligned|protective|pragmatic_positive|neutral", "evidence": "..."}
  ],
  "seed": {"actor": "id", "reaction": "..."} ,
  "followers": [{"actor_or_group": "id|group", "reaction": "..."}],
  "counter": {"actor": "id", "reaction": "..."},
  "hint": "..."
}
```

The order that produced stability:

1. classify the relationships;
2. choose the initiator only among the hostile;
3. propagate only to the hostile or the status-aligned;
4. select the opposition only among the protective/pragmatic;
5. compose the hint from the previous fields only.

That contract is efficient, but specialised in social dynamics.

### The general two-call pipeline

The design that transferred both to the public humiliation and to the advance of
the selection was:

```text
lean snapshot
    → lens generator, with no power to choose
    → conservative judge of least consequence
    → narrator_hint or null
```

Useful lenses:

- `physical_consequence`
- `social_reaction`
- `institutional_duty`
- `ongoing_agenda`
- `environmental_change`

The generator must return `null` per lens when there is no support, and must
quote facts almost literally. The judge rejects:

- control over whoever authored the final input;
- invented support;
- repetition by a saturated agent;
- disproportionate escalation;
- an agenda delay with no cause;
- an event that only dramatises appearance without moving the situation.

Among valid candidates, the judge picks the smallest observable transition that
releases a prepared consequence not yet expressed.

### Result for the real scene

Without receiving the human hint, the stable variants converged on:

> Riven opens with restrained laughter or sarcasm; Liora and the noble
> representatives propagate glances, whispers or stifled laughs; Asword shows
> opposition without taking control of Link.

That is semantically equivalent to the human impulse, but it preserves the hall's
formality better and differentiates the characters instead of making literally
"all the nobles" react alike.

## Conclusion

An LLM can simulate `narrator_hint`, but "ask for a good next idea" is not stable.
The result depends far more on the **representation of the state** and on the
**separation between generation and judgement** than on one more prohibition in
the current Director's prompt.

The single-call option is enough for a specialised social module. For a general
hint, the generator + judge pipeline was more robust: it tolerates creativity in
the first call and stops invalid candidates from contaminating the Director.
