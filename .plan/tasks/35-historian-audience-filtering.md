# Task 35 — Historian Audience Filtering (29.2 increment 3)

## Goal

Close the single confidentiality root the 29.3 comparison quantified: the
private Historian ignores `record_visible_to`, so whispered content enters
every character's private-memory prompt at compaction and cascades from there.

## Current Problem (measured, `output29/comparison-29.3.md`)

Five-stage cascade from one defect (`src/agents/summarizer.py`,
`build_private_memory_messages` filters only foreign thoughts, never audience):
whisper → 7 private-summarizer prompts at both compactions → poisoned
`character_notes` feed "What you remember" → Van Helsing (T19) and Watson
(T22) SPOKE the secret publicly → public records propagate it to everyone,
including perspective updaters. The character output guard cannot catch stage
3: it only protects secrets the speaker legitimately witnessed; a note-smuggled
secret is invisible to it. 26 classified instances in the post-29.2 full run,
all from this root.

## Direction

- `build_private_memory_messages`: include a speech/action record only when
  `record_visible_to(record, character_id)` (audience covers zone-scoped
  records too, since increment 2 computes effective audiences from zones).
- Decide (staged, not now): whether `character_notes` survive at all once the
  perspective ledger grows a memory dimension (29.2 doc §8 "remove private
  compaction"). This task does NOT remove notes; it makes them honest.
- Re-run the xfailed3 full tier: expected `GLOBAL-secret-in-unauthorized-prompt`
  26 → 0 and `SEC-01-watson-unauthorized` → 0 in one change.

## Acceptance Criteria

- [ ] Unit test: a whispered record outside X's audience never appears in X's
  private-summarizer prompt; the confidant's prompt keeps it.
- [ ] Unit test: zone-scoped records respect the same boundary.
- [ ] xfailed3 full tier re-run: secret family at 0; identity rules stay green;
  delta appended to `output29/comparison-29.3.md`.
- [ ] Existing summarizer tests stay green (world summary is narrator-side and
  keeps seeing every non-thought record — unchanged by design).
