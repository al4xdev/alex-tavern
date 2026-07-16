# Roadmap — execution sequence (2026-07-16)

Single source of truth for WHAT COMES NEXT. Architecture reference:
`tasks/explore-29.2-architecture-map.md`. Update this file whenever a task
closes or the sequence changes.

## Done (closed, evidence committed)

| #           | Task                                            | Delivered                                                        |
| ----------- | ----------------------------------------------- | ---------------------------------------------------------------- |
| 31          | Unified retry policy                            | zero runs lost to JSON flakes since                              |
| 34          | Sequential multi-speech (`next_speakers` queue) | routed [C3,C2,C4] live                                           |
| 29.1        | xfailed3 baseline                               | 8/25 violations recorded, `output29/`                            |
| 29.2 inc. 1 | Perspective ledger + viewer projection          | identity leaks 7/13 → 0/13                                       |
| 29.2 inc. 2 | Typed perception events + zone graph            | partition structural 2/2                                         |
| 29.3 r.1    | Before/after comparison                         | identity family → 0; Historian cascade quantified                |
| 35          | Historian perception boundary (3 layers)        | secret family 26 → 0; full tier at 2 stochastic                  |
| 33          | Drive hazard scheduler + skip turns no harness  | A/B: cena travada ganha eventos externos; OFF permanece circular |

## Main sequence (strict order)

| Ordem | Task                                                         | Why this position                                                                                                  | Depends on                 |
| ----- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | -------------------------- |
| **3** | **36 — Decision/Prose split + action_intent + Resolver**     | the architecture core (Director/Resolver); supertask, full critic protocol; zone movement lands here               | 29.2 inc. 1-2 (done)       |
| **4** | **37 — Bounded autonomous loop**                             | needs the Director/Resolver boxes; owns undo/transaction/latency decisions                                         | 36                         |
| **5** | **38 — Roteiro + typed beat contracts + algorithmic replan** | consumed by the Director; replanning is code, never model self-assessment                                          | 36 (37 helps)              |
| **6** | **39 — Ledger memory dimension (remove character_notes)**    | one memory authority; fixes the no-rapport gap and the 35 trade-off                                                | 35 (done); better after 36 |
| **7** | **29.3 exit rounds**                                         | after 35 and each of 36-38: re-run xfailed3, append delta; strict xfail removed only per §15 repeated-run criteria | each increment             |

## Parallel lane (independent, any time)

| Task                                        | Nature                                                                   |
| ------------------------------------------- | ------------------------------------------------------------------------ |
| 28 — Force speaker regression               | bug, user-reported, reproduces with plugin                               |
| 30 — Whisper/audience UI                    | frontend exposure of existing kernel feature                             |
| 32 — Harness cost×quality + routing metrics | needed to judge the WT-08 routing signal from 29.3 r.1                   |
| 23 — Trim/compaction gap                    | 2 strict xfails as acceptance; partially reshaped by 35/ledger decisions |
| 26 — Narrator prose quality                 | evidence accumulator; much of it dissolves structurally in 36            |

## Deferred decisions (owned by a task, not open-ended)

- Remove `character_notes`/private compaction → now owned by Task 39.
- K-speakers as core vs plugin boundary → 36.
- Undo across autonomous bursts → 37.
- Multi-model benchmarking → explicitly excluded (user, 2026-07-15).

ROADMAP.md — fonte única de "o que vem depois", com três blocos:

- Feito (31, 34, 29.1, 29.2 inc. 1-2, 29.3 r.1, cada um com sua evidência);
- Sequência principal: 35 → 33 → 36 → 37 → 38, com rodada 29.3 após cada
  incremento;
- Lane paralela (28, 30, 32, 23, 26 — independentes, qualquer momento) e
  decisões diferidas com dono (remoção de character_notes → pós-35; undo em
  rajada → 37; etc.).

