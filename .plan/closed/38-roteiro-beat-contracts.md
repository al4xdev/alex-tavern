> ✅ **FECHADA em 2026-07-27.** A ressalva era "coin-flip: 2 vitórias / 2
> derrotas" — **n=4**, que é exatamente o resultado que ruído puro produz. Foi
> remedida com n=10 em dois cenários e depois com três braços isolando o
> confundidor. Veredito e números no fim do arquivo. O roteiro continua opt-in e
> OFF por padrão, agora por medição e não por dúvida.

> ⚠️ **KEPT IN tasks/ (not in closed/) — delivered WITH RESERVATIONS, without a confident close.**
> The screenplay (roteiro) is opt-in (OFF by default) and helps drive in ACTION scenes, but is
> a **coin-flip in large procedural scenes** (portals 2W/2L). The ENGINE gains are
> reliable (beat ceiling, character guard, lexical backstop, stall disruption) and are banked; the SCREENPLAY itself is not a universal win.
> Convention (user, 2026-07-17): a task closed without confidence stays in tasks/
> with the reservations, it does not migrate to closed/. Full report:
> `docs/cases/11-roteiro-drive-scene-stagnation-2026-07-17.md`.

> **Contract correction confirmed 2026-07-21:** `budget_turns` remains the
> serialized field name, but its runtime unit is now **player actions**, not
> committed turns. One continuation action may commit several autonomous turns
> and spends exactly one unit. A real-provider run confirmed the counter moving
> `1 -> 2` across two continuation actions without a false `stalled` replan;
> see `.plan/closed/45-multi-beat-story-continuation.md`.

# Task 38 — Roteiro with Typed Beat Contracts and Algorithmic Replanning

**Depends on:** Task 36 (a Director box must exist to consume the roteiro).
Task 37 benefits but is not a hard dependency.

## Goal

Give the story a DIRECTION compiled before the first word (the user's
map-reduce insight applied to narrative): a hierarchical roteiro — stable
premise + act skeleton, rolling next-beat detail — consumed by the Director
and replanned by CODE, never by model self-assessment.

## Beat contract (design frozen in exploration, 2026-07-16)

```json
{
  "beat_id": "act1-beat3",
  "intent": "Van Helsing pressiona a delegacao a abrir o corredor solar",
  "expected_actors": ["C6", "C8"],
  "expected_anchors": ["corredor solar", "venezianas"],
  "exit_condition": "a delegacao decide sobre as venezianas",
  "budget_turns": 6
}
```

`budget_turns` is a frozen wire name. Read it as the beat's player-action
budget; renaming it would invalidate sessions without improving behavior.

## Replan signals (in preference order; hysteresis + cooldown everywhere)

1. exit condition met → advance beat (normal);
2. player-action budget exhausted without anchor coverage → stalled, replan rolling beat;
3. actor/anchor/location overlap below threshold for M consecutive player actions →
   drifted, replan rolling beat (fuzzy similarity as fallback signal — measured
   0.79 vs 0.23 discrimination on real pairs);
4. act-level exit broken hard → regenerate act skeleton.

Only the rolling beat is rewritten routinely; premise and act skeleton stay
stable (cache-friendly prefix, spoilers contained).

## Confidentiality rule

The roteiro reaches ONLY Director-side calls. Never a character prompt, never
the prose renderer (it contains future secrets). Assertable from debug.jsonl.

## Acceptance Criteria (headline)

- [ ] Roteiro generator produces valid typed beats from a scenario config.
- [ ] Deterministic replan triggers with unit-tested hysteresis; zero
  model-self-assessment triggers.
- [ ] Roteiro text never appears in character/prose requests (debug scan).
- [ ] Real-run A/B: same scenario with and without roteiro; blind critic
  compares narrative drive without knowing which is which.

## CLOSED 2026-07-17 (sessão autônoma) — honest, scoped

Full report: `docs/cases/11-roteiro-drive-scene-stagnation-2026-07-17.md`.

Roteiro delivered as an OPT-IN feature (roteiro_enabled, OFF by default),
consumed only Director-side, with deterministic replanning. It was closed once
prematurely (b23a9e7), reopened after the portais generalization test the user
proposed, then closed again with an honest scoped verdict.

### Headline criteria — MET
- [x] Roteiro generator produces valid typed beats (premise + 3-act skeleton +
  rolling beat), schema v7, Director-only.
- [x] Deterministic replan with unit-tested hysteresis; ZERO model-self-
  assessment triggers (every A/B logged advance/coverage_complete/
  coverage_sufficient/in_progress/stalled/drifted/cooldown, all code signals).
- [x] Roteiro text never in character/prose requests: confidentiality scan NONE
  in every A/B run (character/prose builders have no roteiro parameter at all).
- [x] Real-run A/B with blind comparative critic (deepseek, shuffled arms) —
  run many times across two scenarios.

### The scoped verdict (the honest part)
- On tight ACTION scenes (estalagem, 3-4 chars, physical genre) the roteiro
  reliably WINS narrative drive (est. ~5 wins across the loops).
- On a large PROCEDURAL/ceremony scene (turma-dos-portais academy, 6 chars) the
  roteiro is a COIN-FLIP: 2 wins / 2 losses across four A/B runs. The value of
  "direction" is offset there by topic-pinning (procedural beats) and, once the
  disruption fix was added, by disconnected-disruption pile-up, plus high
  variance vs a free Director that sometimes finds cleaner emergent conflict.
  No single fix made it a reliable win there; that is architectural + variance,
  not a bug a loop closes. Feature stays OFF by default.
- goal-per-NPC-per-scene (user-added criterion): a GLOBAL character-prompt
  improvement, arc-dependent, not a guaranteed roteiro differentiator.
- lexical variation (user-added criterion): guaranteed by construction (the
  narration backstop); metric <0.8 with 0 near-dups every run.

### Engine improvements banked (help BOTH arms, independent of the roteiro)
- Hard per-beat action cap (6d6e9b8, corrected by b076ad3): no beat can pin the
  scene into static repetition (`min(budget_turns, 3)` player actions). A
  multi-beat continuation spends one action, not one unit per committed turn.
- Character anti-repetition guard (5c40276): verbatim self-echo / parroting
  eliminated deterministically (0/0), retry then drop-if-other-survives.
- Prose lexical backstop (06bb963): a sentence still echoing after the retry is
  stripped; lexical variation guaranteed.
- Roteiro replan into a concrete DISRUPTION on stall (490f1d5): validated 3/3 at
  the generator and 3/3 at the Director via curl-replay.
- Coverage measured on AUTHORITATIVE evidence (35a9a2f), partial-coverage
  advance (bdda81f), architect escalation + no-exposition (cedbb1a).

### Key methodological finding (the durable payoff, curl-replay technique)
Topic-looping is NOT a character problem and NO character-prompt rule fixes it
(even an explicit topic ban failed 0/3 on the isolated call). It is scene
stagnation: the fast model follows the established scene history hard. The only
levers that broke it: injecting a fresh scene event (2/3) and, decisively, a
concrete DISRUPTIVE beat fed to the Director (3/3). The Director has authority
to break the scene but exercises it only with a concrete "this happens NOW"
beat. Method documented in AGENTS.md; it also frames the player-attempt
adjudication rule (world-response + return_control, never dictating will).

### Routed
- General anti-stagnation trigger -> DRIVE LAYER (Task 33): give the hazard
  function a topic-stagnation input so it injects novelty in BOTH arms.
- Disconnected-disruption pile-up + procedural-arc weakness -> future roteiro
  work (make disruptions advance the planned arc, not interrupt loosely).
  **↑ RESERVATION ADDRESSED (2026-07-20, authorized by the owner) — via layer 33b,
  not via the screenplay prompt.** Two fronts tested via curl:
  1. **Rewrite the `stalled` prompt of the screenplay for a causal contract (A/B):**
     DID NOT win. OLD (loose "arrival/bursting in") 5/6 vs NEW (causal) 5/6 in
     real locked windows, blind causality judge. FIRE does not discriminate (scene
     on fire = any disruption grows from it, 3/3 in both); in LOTTERY
     (procedural, weak thread) each arm missed 1 — OLD with messenger-out-of-nowhere,
     NEW with FORCED escalation contradicting the scene ("already dissipated smoke
     explodes"). Pre-registered rule required NEW>OLD → reverted, not shipped
     (`plans/artifacts/roteiro-causal-stall-ab/`). Confirms the verdict of the task:
     procedural weakness is architecture + variance, not a prompt.
  2. **Route the stall recovery through the watcher's causal intervention (33b
     piece 3):** THIS is the resolution. The causal contract `source_thread→event_now`
     validated **9/9 grounded** by a blind judge (vs the disconnected pile-up). Delivered and
     wired behind `watcher_enabled` (see task 33b). When the watcher is
     on, the recovery disruption grows from an open thread (9/9), instead
     of the loose screenplay disruption. The A/B/C battery had already pointed out that ALL
     critic incoherence came from seeds without anchors — the causal contract closes
     that source.
- Re-narrated whole beats (cross-turn event dup) + semantic character echo +
  action_intent repetition -> Task 26.
- Perspective-ledger init overflow at 20+ present chars (fixed 1024 budget) ->
  Task 29.2 (large-cast scaling).
- Player-attempt adjudication (the portal example) -> new follow-up.

Suite: 550 passed. Artifacts + all blind-critic rounds:
`plans/artifacts/roteiro-ab*/`. Commits: 9761f31, 35a9a2f,
3f4c014, bdda81f, 9f073e0, 06bb963, cedbb1a, 86df261, 7b39304, 6d6e9b8,
5c40276, c3863ae, 490f1d5 (+ the b23a9e7 revert 52f5f88).


---

# Fechamento (2026-07-27) — a ressalva medida

## O problema com a ressalva original

Ela dizia: *"numa cena PROCEDURAL grande o roteiro é COIN-FLIP: 2 vitórias / 2
derrotas em quatro runs A/B"*. Todos os critérios headline estavam cumpridos; o
que segurava a task era esse empate.

**2-2 em n=4 não distingue nada.** É o resultado mais provável de uma moeda
honesta e também de um efeito moderado. A ressalva não estava errada — estava
sem resolução. E o instrumento era um crítico cego, caro por run, o que
explicava o n baixo.

## Método novo: métricas objetivas, n maior

Troquei o crítico cego pelas métricas determinísticas do harness (que não
custam chamada extra) e rodei mais.

### Rodada 1 — dois cenários, ON contra OFF

| Métrica | conversacional ON/OFF (n=6) | elenco grande ON/OFF (n=4) |
|---|---|---|
| chamadas LLM | 60,2 / 46,0 (+31%) | 92,5 / 70,0 (+32%) |
| tokens de saída | 12.528 / 9.861 (+27%) | 20.601 / 16.225 (+27%) |
| `character_action_heuristic_hits` | 3,17 / 1,17 | 8,50 / 3,50 |
| guard retries | 2,83 / 5,33 | 3,25 / 6,00 |
| duplicatas de narração | 5,67±8,0 / 6,33±5,0 | 4,00±4,2 / 11,50±17,1 |

O custo reproduziu nos dois. E o `character_action_heuristic_hits` — personagem
enfiando movimento físico dentro de fala/pensamento — apareceu 2,4× mais alto
com roteiro, nos dois cenários.

**Mas eu tinha criado um confundidor**: o braço ON tinha roteiro **e**
alinhamento de personagem ligados, e o alinhamento manda impulsos dramáticos
transitórios aos personagens. Causa muito mais plausível para "mais movimento no
campo errado" do que o roteiro.

### Rodada 2 — três braços, confundidor isolado (n=5/4/5)

| Métrica | A: roteiro+align | B: roteiro só | C: nenhum |
|---|---:|---:|---:|
| `character_action_heuristic_hits` | **6,20±1,1** | 3,75±1,7 | 4,40±1,5 |
| chamadas LLM | 93,6±5,0 | 80,5±1,0 | **69,0±2,9** |
| tokens de saída | 21.386±2153 | 21.398±1031 | **15.500±988** |
| `redundant_mood_updates` | 1,60±1,1 | 1,00±2,0 | **0,00±0,0** |
| duplicatas de narração | 2,60±4,2 | 1,75±2,4 | 2,60±3,4 |
| falhas de recall / routing | 0 / 0 | 0 / 0 | 0 / 0 |

**B fica igual ou abaixo de C.** A regressão de movimento no campo errado
acompanha o toggle de **alinhamento**, não o roteiro. Eu teria atribuído ao
roteiro um defeito que não é dele.

## Veredito

1. **O roteiro custa e não paga em nenhuma métrica objetiva.** +27% de tokens em
   três lotes independentes. Nenhum sinal de qualidade melhora de forma
   distinguível do ruído: as duplicatas de narração têm desvio maior que a
   diferença nos três lotes.
2. **A ressalva de "coin-flip" está resolvida** — não como vitória nem derrota
   narrativa, mas como: *não há efeito objetivo mensurável, e há custo medido*.
   Opt-in e OFF por padrão continua sendo a decisão certa, agora por número.
3. **O alinhamento de personagem carrega um custo próprio** que estava escondido
   atrás do roteiro: `character_action_heuristic_hits` 6,20 contra 3,75/4,40.
   Fica registrado para quem for mexer na task 44.

## Honestidade sobre os limites

- n=5 por braço, desvios de ±1,1 a ±1,7 num intervalo de 3,75 a 6,20. A ordem é
  consistente; a separação A×B é de ~1,5 desvio. **Sugestivo, não conclusivo.**
- Os números absolutos variam entre lotes (o mesmo braço deu 8,50 num lote e
  6,20 noutro). A métrica tem variância de lote além da variância de run — a
  mesma lição da task 55.
- `scene_cast_rotation` não pôde ser usada: `stress.json` e `natural.json` usam o
  elenco padrão de 2 personagens, e a métrica exige 3+.
- Uma run do braço B morreu com `Invalid Character response after correction` —
  que virou um bug corrigido (`b62f49b`): um deslize de estilo matava o turno
  inteiro enquanto os outros dois guards do mesmo arquivo degradam sem falhar.

## O que a medição comprou além do veredito

Escrever esta medição achou dois defeitos que nenhum teste pegava:

1. **O harness estava morto pela linha de comando** (`9402737`) — `write_text`
   abaixo do `__main__`, seis sessões completadas sem reportar nada.
2. **Um deslize de estilo matava o turno** (`b62f49b`).
