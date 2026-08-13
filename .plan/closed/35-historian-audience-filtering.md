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

- [~] Unit test: a whispered record outside X's audience never appears in X's
  private-summarizer prompt; the confidant's prompt keeps it.
  **SUPERSEDED** — see the 2026-07-27 note.
- [~] Unit test: zone-scoped records respect the same boundary.
  **SUPERSEDED** — same note.
- [x] xfailed3 full tier re-run: secret family at 0; identity rules stay green;
  delta appended to `output29/comparison-29.3.md`. — redone on 2026-07-27
  (session `8484d749`, 24/24 turns, real provider): **secret family = 0**;
  see `.plan/closed/39-ledger-memory-dimension.md`.
- [x] Existing summarizer tests stay green (world summary is narrator-side and
  keeps seeing every non-thought record — unchanged by design). — the world
  summary stays narrator-side; `tests/test_ledger_memory.py` and
  `tests/test_thought_containment.py` cover the boundary today.

> **CLOSED 2026-07-16.** Three-layer fix in `build_private_memory_messages`:
> record visibility (`record_visible_to` + Player→controlled ownership),
> narration exclusion (narrator prose retold the whisper at T21), and
> world-directives exclusion (the canon bible defines the secret as WT-11).
> Benchmark cascade: 26 → 17 → 13 → **0** secret instances across three
> full-tier re-runs; final state 25 (baseline) → 2 violations, both stochastic
> semantic probes. 7 unit tests in `tests/test_historian_audience.py`. Suite:
> 433 passed. Note-quality trade-off recorded: notes lose narration-borne
> outcome memory; the proper future source is persisted perception events
> (ledger memory dimension, 29.2 §8).


---

# Note of 2026-07-27: two criteria were superseded, not met

The first two unit tests demanded proof about the **private summarizer's prompt**.
That component no longer exists: task 39 replaced private notes with deterministic
ledger memory and removed the call. Marking them done would be a lie; leaving them
open would suggest pending work that does not exist. They stay as
`[~] SUPERSEDED`.

What remains of the criterion did not vanish with it — it moved, and got stronger:

| 35's guarantee | where it lives today |
|---|---|
| a whisper outside the audience does not enter X's prompt | `tests/test_thought_containment.py` (nothing but the Director reads thought) + `record_visible_to` in `_format_history_for_character` |
| zone boundaries respected | `tests/test_zone_audibility_default.py`, `TestRunnerZoneMaterialization` |
| the component does not come back | `tests/test_integration.py:2035` locks the signature against `build_private_memory_messages` |

That last row is the part that matters in review: when a component is removed for
being the source of a leak class, the surviving test should not be about how it
filtered — it should be about it **not existing**. That is what is there.

The third box was measurable and was measured that day, not inherited: a full-tier
campaign of 24 turns with the real provider, secret family at 0.

> **Reproducibility caveat (2026-07-27).** The sessions cited in this section were
> generated in a temporary directory and **are not in the repository**: the numbers
> are not auditable by a third party or by a future session. I checked them at the
> time of execution and the method is described above in enough detail to be
> redone, but whoever re-reads this should treat them as an *account*, not as
> verifiable evidence. Measurements that need to count as proof have to write their
> artifacts into `docs/` or `.plan/`, or the criterion must require an acceptance
> script in `tools/acceptance/` that anyone can run.
