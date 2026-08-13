# Handoff: generalising `narrator_hint` with an LLM

**Date:** 2026-07-18  
**Model tested:** DeepSeek V4 Flash, `thinking=disabled`, `temperature=0.1`  
**Method:** real calls through a `curl` wrapper in `/tmp`, with no change to the runtime  
**Result:** convergence across four cases from different domains after 55 valid calls

> The prompt blocks and the compiled hints below are kept **verbatim in
> Portuguese**. They are the exact strings that were measured; translating them
> would make the numbers in this document claims about text that was never sent.

## Executive summary

A single "creative" call did not generalise. It:

- repeated facts as if they were new;
- confused a profile with an event;
- controlled the character behind the final input;
- invented objects, extras and physics;
- suppressed the institutional agenda whenever a social reaction was more salient;
- ignored quantity limits written into the prompt.

The architecture that did generalise was:

```text
                         ┌─ Reaction Scout ────┐
lean canonical snapshot │                     ├─ Judge ── scalar fields
                         └─ Continuity Scout ──┘              │
                                                              ▼
                                                deterministic compiler
                                                              │
                                                              ▼
                                                     narrator_hint | null
```

Reaction Scout and Continuity Scout are independent and can run in parallel. The
Judge runs afterwards. Invalid responses are repaired by a retry carrying
`VALIDATION_ERROR`.

Do not use the `hint` string written by the LLM. The program must compile it from
the selected fields:

```text
{reaction_seed.actor} {reaction_seed.delta};
{reaction_followup.actor} {reaction_followup.delta};
{continuity.actor} {continuity.delta}.
```

Null fields are omitted. That removes style variation and abstract labels.

## The real cases used

| Case | Source in the project | Domain | Stimulus | Convergent result |
|---|---|---|---|---|
| Academy | `src/scenarios/turma-dos-portais-pt.json` + session `e5a0ca6a` | social tension + institutional duty | Link gives an embarrassing excuse after arriving late in public | Riven laughs; the nobles propagate murmurs; Maelis starts the selection |
| Thorn/Lyra | `src/scenarios/thorn-lyra.json`, characters `thorn-lyra-c1`/`thorn-lyra-c2` | fantasy, an arcane object, divergent dispositions | Edda puts an arcane medallion on the table and asks Lyra | Lyra leans in to examine it; Thorn stays guarded, as an unchosen candidate |
| Party | `.data/scenarios/tony_house.json`, presets `alex`/`sofia` | modern romantic tension + private knowledge | Alex greets his ex, Fernanda, in front of Sofia | Fernanda blushes / looks away / closes her posture; Sofia stays neutral |
| Mill | `.data/scenarios/presence-e2e-test.json` | space, presence and ambiguous physical risk | a beam above Aria cracks; Bron is absent | Aria looks up and stiffens; no collapse; Bron does not react |

## The experimental series

The rows below are this round's 55 valid calls. Timeouts with no response are not
numbered.

| # | Case | Variant changed | Result | Reading |
|---:|---|---|---|---|
| 1 | Thorn/Lyra | The earlier general generator | Repeated the aura; "awaits an answer" | Novelty failure and no reaction |
| 2 | Thorn/Lyra | Strict novelty + micro-reactions | Found Thorn/Lyra; invented a leak, a drunk and an action by Edda | The generator needs a judge |
| 3 | Thorn/Lyra | Conservative judge | Chose the Thorn/Lyra reaction; rejected the noises and ACTOR_FINAL | Passed |
| 4 | Party | Same generator | Sofia tries to mediate; the agenda decides for Alex | The direct target was ignored |
| 5 | Party | `DIRECT_TARGET` first | Identified Fernanda; repeated the interruption | Right target, incomplete novelty |
| 6 | Party | `already_true` + `novel_delta` | Fernanda's reaction; invented a glass, an extra and music | Useful atoms mixed with inventions |
| 7 | Party | Ordinary conservative judge | Accepted a glass that does not exist | A textual prohibition is not enough |
| 8 | Party | Closed-world judge with claims | Rejected the glass/extra/music; kept Fernanda | Passed |
| 9 | Mill | Initial generator | The beam "might fall", Milo warns, the wheel "might be affected" | Modal, ACTOR_FINAL and invented physics |
| 10 | Mill | Affirmative event + NPC target | Found Aria; still invented a fall and a vibration | Right reaction, wrong physics |
| 11 | Mill | Closed-world judge | Rejected the collapse/vibration; chose Aria | Passed |
| 12 | Mill | Entity gate | Rejected the gears, but accepted the beam shifting | An entity does not settle the predicate |
| 13 | Mill | Derivation types | `world_inference` rejected; Aria accepted | Passed |
| 14 | Thorn/Lyra | Frozen universal generator v1 | Lyra leans in; the other lenses null | Passed |
| 15 | Thorn/Lyra | Universal judge v1 | Chose Lyra | Passed |
| 16 | Party | Same universal generator | Fernanda guarded | Passed |
| 17 | Party | Same universal judge | Chose Fernanda | Passed |
| 18 | Mill | Same universal generator | Aria + invented physics/environment | The generator stays deliberately broad |
| 19 | Mill | Universal judge v1 | Rejected the beam; accepted the gears/dust | Closed-world still loose |
| 20 | Mill | Typed derivation | Only Aria accepted | Passed |
| 21 | Academy | Composite universal generator | Riven/Liora valid but mixed with speech; agenda suppressed | Composite atom and salience |
| 22 | Academy | Independent atoms | Produced six reactions; agenda still suppressed | Separation improves filtering, not the agenda |
| 23 | Academy | Separate Continuity Scout | Found the start of the selection; also attempted a social reaction | The scouts need strict ownership |
| 24 | Academy | Judge with phases and a textual limit | Accepted everything and ignored the limit | Do not trust a textual `max 3` |
| 25 | Academy | Reaction Scout with classification | Nix classified hostile for being "merciless" | Compressed profile is ambiguous |
| 26 | Academy | Rule "pragmatism ≠ hostility" + canonical profile | Correct classification; emitted six atoms | Relationships correct |
| 27 | Academy | Judge with five slots | Selected four and returned a null hint | The schema allowed too much combining |
| 28 | Academy | Judge with three scalar fields | Riven + nobles + selection | Passed |
| 29 | Thorn/Lyra | Reaction Scout | Thorn guarded, Lyra approach | Passed |
| 30 | Thorn/Lyra | Scalar judge with no direct target | Chose Thorn; the hint lost its subject | `DIRECT_TARGET` and `actor` were missing from the schema |
| 31 | Party | Reaction Scout | Fernanda guarded, but an abstract delta | Require camera-observable |
| 32 | Party | Observable gate | Repeated the interruption | Require novelty against HISTORY |
| 33 | Party | Novelty + PENDING | Fernanda blushes / looks away / closes her posture | Passed |
| 34 | Mill | Reaction Scout | Aria guarded, Bron absent | Passed |
| 35 | Thorn/Lyra | Updated Reaction Scout | Thorn guarded, Lyra approach | Passed |
| 36 | Thorn/Lyra | Judge with `DIRECT_TARGET` and actor | Chose Lyra; subject preserved | Passed |
| 37 | Party | Same final judge | Chose Fernanda | Passed |
| 38 | Mill | Same final judge | Chose Aria | Passed |
| 39 | Thorn/Lyra | Permissive Continuity Scout | Invented a duty for Lyra | Knowledge is not authorisation |
| 40 | Thorn/Lyra | Require an explicit duty in the prompt | Still fabricated a duty for Edda | A prompt does not close the set |
| 41 | Thorn/Lyra | Closed `AUTHORIZATIONS=[]` | Candidate `null` | Passed |
| 42 | Academy | Structured authorisation from Maelis | The selection begins | Passed |
| 43 | Academy | Combined judge, repeat 1 | Riven + nobles + selection | Correct |
| 44 | Academy | Combined judge, repeat 2 | Same trio | Correct |
| 45 | Academy | Combined judge, repeat 3 | Same trio; abstract hint string | Structure 3/3; do not use the LLM's string |
| 46 | Thorn/Lyra | Reaction Scout, stability 2 | Same tendencies | Correct |
| 47 | Thorn/Lyra | Reaction Scout, stability 3 | Same tendencies | 3/3 |
| 48 | Party | Reaction Scout, stability 2 | Fernanda guarded | Correct |
| 49 | Party | Reaction Scout, stability 3 | Fernanda guarded, Sofia neutral | 3/3 |
| 50 | Mill | Reaction Scout, repeat | Aria approach | approach/guarded ambiguity |
| 51 | Mill | Reaction Scout, repeat | Aria approach | Same direction |
| 52 | Mill | Reaction Scout, repeat | Aria guarded | No directional convergence |
| 53 | Mill | Least-commitment tie-break, repeat 1 | Aria guarded, looks without moving | Correct |
| 54 | Mill | Tie-break, repeat 2 | Aria's relation; the atom attributed to Milo | A detectable structural error |
| 55 | Mill | Retry with `VALIDATION_ERROR` | Fixed only the actor, Milo → Aria | Recovery passed |

## The final prompts

Kept verbatim, as sent.

### 1. Reaction Scout

```text
Você é REACTION SCOUT universal de roleplay POV.

1. Classifique NPC PRESENTE como approach, avoid, attack_status,
   defend_target, guarded, align_status ou neutral.
   attack_status exige hostilidade explícita; humor, pragmatismo, utilidade
   e ausência de pena não bastam.
2. Em conflito entre approach e avoid/guarded, ou diante de risco físico não
   verificado, use guarded e a MENOR reação não comprometida: orientar
   olhar/postura sem aproximar, afastar, tocar ou agir sobre o risco.
3. Descarte neutral e quem não percebe.
4. Gere átomos novos ligados a PENDING, nunca repetindo HISTORY.
   Apenas olhar, expressão, postura, gesto ou distância física;
   sem estado abstrato, fala, objeto novo ou ACTOR_FINAL.
   align_status só acompanha attack_status;
   defend_target só reage a attack_status.

Retorne JSON:
{
  "relations": [
    {"actor": "...", "tendency": "...", "evidence": "..."}
  ],
  "atoms": [
    {
      "atom_id": "...",
      "actor": "...",
      "tendency": "...",
      "delta": "...",
      "support": ["..."]
    }
  ]
}
```

### 2. Continuity Scout

```text
Você é CONTINUITY SCOUT de narrator_hint.
Ignore reações, atmosfera e física.

Para cada PENDING, owner e autorização DEVEM copiar uma entrada de
AUTHORIZATIONS. Se nenhuma entrada combina exatamente com pending e owner
presente, candidate=null; lista vazia obriga todos null.

Nunca derive autorização de conhecimento, pergunta, capacidade, relação ou
plausibilidade.

Com autorização válida, proponha a menor ação externa que inicia avanço, sem
completar decisão nem inventar conteúdo de fala. owner=ACTOR_FINAL ou
sobreposição com reação => null.

Retorne JSON:
{
  "pending_reviews": [
    {
      "pending": "...",
      "matched_authorization_id": "... | null",
      "owner": "... | null",
      "candidate": {
        "atom_id": "...",
        "actor": "...",
        "tendency": "duty_transition",
        "delta": "...",
        "support": ["..."]
      } | null
    }
  ]
}
```

### 3. Judge

```text
Você é JUIZ FINAL CLOSED-WORLD de narrator_hint.

Valide tendência, entidade, novidade e grounding.
Rejeite ACTOR_FINAL, ausente, conteúdo de fala inventado, objeto novo,
segredo transferido, repetição, estado abstrato, detalhe excessivo e
world_inference.

A saída possui SOMENTE três seleções escalares:

- reaction_seed:
  - se houver attack_status, escolha o mais específico;
  - sem ataque, prefira actor=DIRECT_TARGET;
  - depois, a reação mais diretamente causal.
- reaction_followup:
  - somente com attack_status;
  - escolha UM entre propagação attack_status/align_status ou counter
    defend_target;
  - prefira propagação se o ataque ainda não ocorreu;
  - prefira counter se o ataque já ocorreu.
- continuity:
  - duty_transition com authorization_id e pending;
  - somente se compatível com as reações.

Cada seleção inclui actor e delta.

Retorne JSON:
{
  "reaction_seed": {"atom_id": "...", "actor": "...", "delta": "..."} | null,
  "reaction_followup": {"atom_id": "...", "actor": "...", "delta": "..."} | null,
  "continuity": {"atom_id": "...", "actor": "...", "delta": "..."} | null,
  "reason": "..."
}
```

Do not ask the Judge for a `hint` in production. Compile it deterministically.

### 4. Validation retry

```text
Você é REACTION SCOUT universal.
Corrija sua resposta anterior quando receber VALIDATION_ERROR.
Preserve relações e semântica válidas; altere somente campos inválidos.
ACTOR_FINAL nunca pode aparecer em atoms.
Todo atom.actor deve existir em relations e atom.tendency deve ser idêntica
à relation correspondente.
Retorne somente JSON corrigido.
```

The same pattern serves errors from the Continuity Scout and the Judge: send the
previous response plus a precise list of violations, without re-running the whole
creation step.

## The recommended input contract

```json
{
  "actor_final": "character_id",
  "direct_target": "character_id|null",
  "present": ["character_id"],
  "absent": ["character_id"],
  "perception": {
    "character_id": ["event_id"]
  },
  "stimulus": "the last public event, normalised",
  "history_predicates": [
    "recent actions/predicates already performed"
  ],
  "pending": [
    {"id": "pending_id", "description": "..."}
  ],
  "authorizations": [
    {
      "id": "authorization_id",
      "owner": "character_id",
      "scope": "which pending/duty it may start"
    }
  ],
  "participation": {
    "character_id": 0
  },
  "profiles": {
    "character_id": {
      "personality": "...",
      "knowledge_relevant": ["..."]
    }
  },
  "allowed_entities": ["..."]
}
```

### The indispensable data

- `actor_final`: not "Player"; only the character who produced the final input.
  It preserves immersion and prevents agency from being extended.
- presence, zones and perception, already computed;
- recent predicates, not long prose;
- canonical profiles of the relevant NPCs present;
- relevant individual knowledge;
- participation/saturation;
- explicitly pending states;
- closed authorisations;
- the allowed entity set.

### The real blocker: `AUTHORIZATIONS`

`AUTHORIZATIONS` cannot be freely inferred by the same LLM. In the tests it turned
curiosity and a question into an "explicit duty" for Lyra even after being
forbidden to.

Possible safe sources:

- a structured role/duty in the scenario;
- a beat/owner structured by the roteiro system;
- plugin state with an explicit owner;
- a typed institutional rule.

If the runtime has no structured source, send `AUTHORIZATIONS=[]`. Losing an
automatic advance is better than fabricating authority.

## Mandatory local validations

These invariants must not depend on the model:

```text
relation.actor ∈ present
relation.actor != actor_final
atom.actor ∈ relations.actor
atom.actor != actor_final
atom.tendency == relations[atom.actor].tendency
atom.delta not empty
continuity.authorization_id ∈ input.authorizations.id
continuity.actor == authorization.owner
the selected ids exist in the scouts' outputs
reaction_followup != null only if reaction_seed.tendency == attack_status
at most 1 seed + 1 followup + 1 continuity
```

Also validate locally against:

- missing IDs;
- entities not allowed, where extractable;
- Unicode dashes, per the global normalisation;
- a strict JSON schema;
- a maximum size for each `delta`.

A failure must trigger a corrective retry with a precise error. Call 55 showed
that this fixes an attribution error without recreating the beat.

## Stability results

| Component/case | Result |
|---|---|
| The Academy's combined judge | the same three fields 3/3 |
| Reaction Scout, Thorn/Lyra | the same `guarded/approach` tendencies 3/3 |
| Reaction Scout, Party | Fernanda `guarded`; Sofia `neutral/omitted` 3/3 |
| Reaction Scout, Mill, before the tie-break | 2 approach / 1 guarded |
| Reaction Scout, Mill, after the tie-break | minimal guarded semantics 3/3; 1 structural error recovered by retry |
| Continuity Scout with no authorisation | `null` when `AUTHORIZATIONS=[]` |
| Continuity Scout, Academy | the selection starts, on Maelis's authorisation |

## The final compiled hints

Verbatim, as produced.

```text
Academia:
Riven revira os olhos e solta uma risada sarcástica;
noble_audience troca murmúrios de desaprovação;
Maelis sinaliza o início da seleção.

Thorn/Lyra:
Lyra inclina-se e estende a mão em direção ao medalhão.

Festa:
Fernanda cora, desvia o olhar brevemente e fecha a postura.

Moinho:
Aria olha para cima e enrijece os ombros.
```

## Recommendation for Claude

1. Do not put this responsibility into the Director's current prompt.
2. Do not implement a single `generate_hint` call.
3. Build an isolated experimental contract with Reaction Scout and Continuity
   Scout in parallel, the Judge afterwards, and a deterministic compiler.
4. Start it behind a flag/plugin or in the harness, still outside the canonical
   turn.
5. Reuse the shared LLM client and the debug JSONL; every call needs a
   `session_id`, a `turn_number` and a distinct agent.
6. Only integrate it into the turn after replaying it across more real sessions
   and defining the canonical source of `AUTHORIZATIONS`.
7. If integrated, the result must enter the Director as a system hint, never as a
   fact that already happened. The Director keeps validating space, perception
   and routing.

## Limitations

- The tests measure DeepSeek V4 Flash; other providers need the same battery.
- The Reaction Scout still emits a variable quantity; the scalar Judge absorbs it.
- Exact gestures vary, although the tendency converges.
- The pipeline adds two latency phases (parallel scouts, then the Judge).
- There was no implementation and no HTTP test of the full turn.
- There was no test of compaction/long history.
- `allowed_entities` and `history_predicates` require a trustworthy input builder.

## The files of this research

- Earlier report:
  `.plan/explore-narrator-hint-llm-experiments.md`
- This handoff:
  `.plan/narrator-hint-generalization-handoff.md`
- Temporary wrapper, not versioned:
  `/tmp/curl_wrapper.py`
- Temporary request, not versioned:
  `/tmp/curl_request.json`
