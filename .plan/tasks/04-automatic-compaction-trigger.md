# Task: Automatic compaction trigger

**Status:** Explicitly deferred from the first version  
**README evidence:** `README.md:333-334`, `README.md:378-383`, `README.md:499-505`

## Current behavior

- Compaction occurs only through `POST /session/{id}/compact` and its UI button.
- `Runner.compact_session` decides whether there is anything to compact from the number of
  distinct turns and `compaction_keep_recent_turns`.
- No token-usage threshold, background trigger, or automatic call site exists.

## Future behavior identified by the README

- Optionally trigger compaction from context usage instead of relying exclusively on the
  manual button.
- Preserve the project's deliberate difference from production server-side compaction
  unless that design decision is changed explicitly.

## Open questions

- No threshold, token estimator, trigger timing, failure behavior, user notification, or
  interaction with an in-progress turn is specified.
- The README calls manual triggering a conscious simplification, so automatic triggering
  is a deferred candidate rather than committed scope.
