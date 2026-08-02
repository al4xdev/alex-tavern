# benchmarks/

Archived acceptance batteries. One directory per battery:

```
<date>-<engine-fingerprint>-<label>/
  manifest.json    provenance: engine, models, per-run config
  metrics.json     every metric for every run
  transcripts/     one readable transcript per run
```

## What makes a benchmark valid, and what kills it

A number here is only meaningful next to the two things that produced it, and in
this project **both move underneath you**:

**The engine.** Keyed by `engine.fingerprint`, a hash of `src/**/*.py` — not a
commit. Batteries are routinely run from a dirty tree, and a commit hash would
claim a precision the run did not have. The commit and a `dirty` flag are
recorded alongside it, for humans.

**The provider's weights.** DeepSeek updated `deepseek-v4-flash` **in place** on
2026-07-31. Same model id in every single log line, different model. That
silently confounded a before/after comparison until a control cell was added that
re-ran the *old engine* on the *new weights* — see
`docs/cases/20-repetition-baseline-2026-08-01.md`. A model id is therefore not
enough to establish comparability; the archive date is part of the key.

**Rule: two batteries are comparable only if they share an engine fingerprint or
were run in the same weights window.** Anything else is a difference of unknown
composition. When in doubt, re-run the control cell rather than assume.

## The most current battery

The newest directory by date, whose `engine.fingerprint` matches
`tools/acceptance/archive_benchmark.py::engine_fingerprint` run against the
current tree. If they differ, the archive predates the engine and its absolute
numbers are stale — its *within-battery* contrasts (cell vs cell) usually survive,
because those shared an engine with each other.

## Reading them

Start with `transcripts/`, not `metrics.json`. Every defect that mattered in the
repetition investigation was found by reading output — the same event staged
seven times, an act clock re-issuing one order twelve times — and several
metrics turned out to be measuring their own fixture. The metrics are there to
make a found defect countable and to keep it from coming back, not to find it.

## Archiving a new one

```bash
uv run python -m tools.acceptance.archive_benchmark <artifact-dir> --label <what-it-answered>
```

Raw sessions are deliberately not archived: one is ~14MB and a battery is
~500MB. They stay in `plans/artifacts/` (gitignored) for as long as the disk
allows; what is kept here is what can still be read or re-checked a month later.
