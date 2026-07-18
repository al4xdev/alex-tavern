# Task 39 — Ledger Memory Dimension (replaces character_notes)

**Depends on:** 35 (done). Strengthened by 36 (perception events persisted as
the memory source). This is the 29.2 doc §8 "remove private compaction"
decision, given its own task so it does not get lost.

## Goal

Grow the perspective ledger with a durable private memory dimension
(`self.memory_summary` + bounded important-memories entries), updated
continuously from what the character actually perceived — then REMOVE
`character_notes` and the per-character compaction fan-out entirely (one
authority, no parallel memories).

## Why

- Task 35 made notes honest but poorer: they lost narration-borne outcome
  memory (recorded trade-off). The correct source for outcome memory is the
  typed perception events the character witnessed — persisted, not re-derived
  from omniscient prose.
- "What you remember: (none yet)" persists across whole sessions today (user
  evidence, session ef6b5b90): no rapport accumulates until a compaction
  happens. Continuous ledger memory closes this.
- Compaction then keeps ONLY the world summarizer (narrator-side), cutting the
  per-character call fan-out at every compaction.

## Direction (sketch, freeze in-task)

- Persist witnessed perception events (or a bounded digest) per viewer;
  batched semantic revision co-scheduled with chosen narrator calls (user's
  latency-concentration idea, see task 36 async note).
- `_build_user_prompt`'s "What you remember" reads the ledger memory.
- Remove: `GameState.character_notes`, `summarizer` private calls,
  `build_private_memory_messages`, checkpoint note fields — forward-only,
  schema bump.
- Reconcile Task 23's private-recall half (its public trim gap remains).

## Acceptance (headline)

- [ ] No `character_notes` field or private summarizer call remains anywhere.
- [ ] Rapport accumulates within a session without compaction (the ef6b5b90
  complaint), shown in a real run.
- [ ] xfailed3 retention probes (ribbon, origin) pass via ledger memory across
  both compactions; secret family stays 0.
- [ ] Undo/fork/restore preserve ledger memory exactly.

## Design frozen (2026-07-17, Opus) — staged increments

### Increment 1 (additive, deterministic, LOW risk) — THIS increment
- `CharacterPerspective` gains a memory dimension (schema v8):
  - `recent_memory: list[str]` — deterministic, continuous capture of what the
    viewer perceived, one compact digest per witnessed turn, viewer-projected
    (no unlearned names/IDs — reuse the same projection as the identity ledger).
    Bounded (keep last N, e.g. 24).
  - `memory_summary: str = ""` — reserved for the LLM semantic revision
    (increment 2 fills it); empty in increment 1.
- Runner captures the digest when a character witnesses a turn (it already
  computes `render_events_for_viewer` per speaker; add heard speech too).
- `_build_user_prompt` "What you remember" reads the ledger memory
  (memory_summary + recent_memory), falling back to `character_notes` while both
  coexist. character_notes STAYS this increment (no removal yet).
- Undo/fork/restore already deep-copy the perspective; verify memory survives.
- Acceptance hit now: rapport accumulates WITHIN a session with no compaction
  (the ef6b5b90 complaint) — deterministic, unit-testable, no LLM.

### Increment 2 (removal, HIGHER risk) — next
- LLM semantic revision: condense `recent_memory` into `memory_summary` +
  bounded important entries, batched/co-scheduled with a narrator call.
- REMOVE `character_notes`, the private summarizer calls
  (`build_private_memory_messages`, summarize's notes path), checkpoint note
  fields. Forward-only. Reconcile Task 23's private-recall half.
- Re-validate xfailed3 retention probes (ribbon, origin) via ledger memory
  across both compactions; secret family stays 0.
