# Roadmap — execution sequence (2026-07-16)

Single source of truth for WHAT COMES NEXT. Architecture reference:
`tasks/explore-29.2-architecture-map.md`. Update this file whenever a task
closes or the sequence changes.

## Done (closed, evidence committed)

| # | Task | Delivered |
|---|---|---|
| 31 | Unified retry policy | zero runs lost to JSON flakes since |
| 34 | Sequential multi-speech (`next_speakers` queue) | routed [C3,C2,C4] live |
| 29.1 | xfailed3 baseline | 8/25 violations recorded, `output29/` |
| 29.2 inc. 1 | Perspective ledger + viewer projection | identity leaks 7/13 → 0/13 |
| 29.2 inc. 2 | Typed perception events + zone graph | partition structural 2/2 |
| 29.3 r.1 | Before/after comparison | identity family → 0; Historian cascade quantified |
| 35 | Historian perception boundary (3 layers) | secret family 26 → 0; full tier at 2 stochastic |

## Main sequence (strict order)

| Ordem | Task | Why this position | Depends on |
|---|---|---|---|
| **2** | **33 — Auto-suggest hazard scheduler** | smallest Drive win, attacks measured passivity; independent of the split | — |
| **3** | **36 — Decision/Prose split + action_intent + Resolver** | the architecture core (Director/Resolver); supertask, full critic protocol; zone movement lands here | 29.2 inc. 1-2 (done) |
| **4** | **37 — Bounded autonomous loop** | needs the Director/Resolver boxes; owns undo/transaction/latency decisions | 36 |
| **5** | **38 — Roteiro + typed beat contracts + algorithmic replan** | consumed by the Director; replanning is code, never model self-assessment | 36 (37 helps) |
| **6** | **29.3 exit rounds** | after 35 and each of 36-38: re-run xfailed3, append delta; strict xfail removed only per §15 repeated-run criteria | each increment |

## Parallel lane (independent, any time)

| Task | Nature |
|---|---|
| 28 — Force speaker regression | bug, user-reported, reproduces with plugin |
| 30 — Whisper/audience UI | frontend exposure of existing kernel feature |
| 32 — Harness cost×quality + routing metrics | needed to judge the WT-08 routing signal from 29.3 r.1 |
| 23 — Trim/compaction gap | 2 strict xfails as acceptance; partially reshaped by 35/ledger decisions |
| 26 — Narrator prose quality | evidence accumulator; much of it dissolves structurally in 36 |

## Deferred decisions (owned by a task, not open-ended)

- Remove `character_notes`/private compaction entirely → decided inside 35's
  follow-up once the ledger grows a memory dimension (29.2 doc §8).
- K-speakers as core vs plugin boundary → 36.
- Undo across autonomous bursts → 37.
- Multi-model benchmarking → explicitly excluded (user, 2026-07-15).
