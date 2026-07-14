# Task 04: Automatic compaction trigger

**Status:** Planned; ready for implementation

**Updated:** 2026-07-13

**README evidence:** `README.md`, section `Context compaction`

**Exploration:** [`../explore-04-05-compaction.md`](../explore-04-05-compaction.md)

## Objective

Automatically compact eligible old history before a Narrator call when the complete, untrimmed
Narrator request is estimated to approach the active provider's context window. Keep manual
compaction available, preserve the per-session transaction boundary, and make automatic failure
non-destructive and visible without blocking the player's turn.

## Architecture decisions

### Trigger policy

- Add two common, server-owned config fields:
  - `automatic_compaction_enabled: bool`, default `false`;
  - `automatic_compaction_threshold_percent: int`, default `80`, valid range `1..100`.
- Estimate the next Narrator request from the same pure Narrator message builder with
  `context_max=None`, after `turn.input` plugins have produced the effective input. Add the
  Narrator output reservation before comparing it with the threshold:

  ```text
  estimated_context_tokens = estimated_untrimmed_prompt_tokens + max_tokens_narrator
  threshold_tokens = floor(context_max * automatic_compaction_threshold_percent / 100)
  ```

- Share one character-based prompt estimator with the debug logger so the trigger and
  `prompt_estimated_tokens` cannot drift. This remains explicitly an estimate; provider-reported
  usage arrives too late for a pre-call decision and the append-only debug log must not become
  canonical state.
- Evaluate only turns that will call the Narrator. A private-thought-only turn does not need
  compaction; the next narrating turn evaluates the accumulated state.
- Require both conditions before calling the Historian:
  1. estimated context is at or above the configured threshold;
  2. at least one complete turn lies before `compaction_keep_recent_turns`.
- Retain the existing exact recent-turn window. If context pressure is high but no turn is
  eligible, report `blocked_by_retention_window` and rely on the existing prompt trimming for the
  current call. Do not silently reduce the user's retention setting.
- No background job, polling registry, or second session lock is introduced. Automatic compaction
  runs synchronously under the same session transaction as the initiating turn.

### Transaction shape

- Split the current method into:
  - `compact_session(session_id, ...)`, which acquires the session lock for manual/tool callers;
  - one private `_compact_loaded_game(...)` operation that receives the already loaded
    `GameState`, assumes the caller owns the lock, and is reused by `player_turn`.
- In `player_turn`, compute the next `turn_number`, run `turn.input`, build a temporary probe state
  containing the effective speech/action, and evaluate pressure without mutating the live game.
  If triggered, compact the loaded pre-turn game first, then append the effective player input and
  continue through the normal Narrator/Character transaction.
- Prepare summaries and run `compaction.before_commit` against an isolated draft. Only after every
  fallible LLM/plugin step succeeds, create the backup from the still-current session bytes, save
  the compacted draft atomically, and emit `compaction.after_commit`. This prevents failed or
  cancelled attempts from leaving a restoreable backup for a state that was never compacted.
- The automatic compaction is a discrete committed revision before the turn revision. If the later
  Narrator call fails, the compaction remains valid and the player's unsaved draft input does not
  enter session state.
- Catch ordinary automatic-compaction errors, log them, and continue the turn through the existing
  token-trimmed prompt path. Do not catch cancellation or process-exit exceptions. Manual
  compaction continues to surface failures to its caller.

### Result and observability contract

- Define a typed compaction result shared by manual and automatic paths with:
  `status` (`not_needed`, `blocked`, `compacted`, `failed`), `trigger` (`manual`, `automatic`),
  `reason`, estimated/threshold/context tokens, cutoff, record counts, and backup path where
  applicable.
- Add optional `automatic_compaction` to `PlayerTurnResponse`. The field reports only the completed
  maintenance outcome and contains no prompt text or secret. The browser shows a localized success,
  blocked, or failure toast after the turn response and refreshes history when compaction committed.
- Extend debug markers to record automatic trigger decisions, the estimate and threshold, terminal
  status, cutoff/counts, and a sanitized error type/representation. Preserve all Historian LLM
  records with their existing `session_id`, `turn_number`, and `summarizer:*` agents.
- Keep the manual button and restore behavior. An automatic compaction creates the same backup and
  is restored by the same safety rule as a manual one.

## Implementation sequence

1. Add strict config defaults, validation, public serialization, active-config resolution, common
   settings controls, localization, and config round-trip tests.
2. Extract the shared prompt estimator and add pure tests proving parity with debug-log estimates
   and exclusion of private thoughts from the Narrator probe.
3. Refactor compaction into lock-owning and lock-held layers; move backup creation to the final
   commit boundary and keep plugin hooks on an isolated draft.
4. Add the pre-Narrator automatic policy to `player_turn`, including effective plugin-transformed
   input, private-thought exclusion, typed result metadata, and best-effort failure handling.
5. Extend debug logging, the HTTP response model, browser state refresh/toasts, README/config docs,
   and the compaction help pages.
6. Move this task to `.plan/closed/` only after all acceptance criteria and the real HTTP boundary
   test pass.

## Tests and acceptance criteria

- [ ] Canonical config accepts valid booleans/percentages, rejects missing/wrong/out-of-range
  values, redacts secrets unchanged, and round-trips through `GET/PUT /config` and the browser.
- [ ] A below-threshold narrating turn performs no Historian call, backup, compaction revision, or
  history rewrite.
- [ ] An above-threshold eligible turn compacts exactly once before the Narrator, keeps the
  configured recent window, and the Narrator sees the new summary plus effective current input.
- [ ] Plugin-transformed speech/action affect the estimate; private thoughts never enter the
  Narrator estimate or world summarizer.
- [ ] Private-thought-only turns defer automatic evaluation and remain one atomic persisted step.
- [ ] Above-threshold but ineligible history returns `blocked_by_retention_window`, creates no
  backup, and still completes through token trimming.
- [ ] Historian/plugin failure leaves state and backups unchanged, appends failure evidence, and
  does not prevent the player's normal turn.
- [ ] Concurrent turn, manual compaction, undo, restore, fork, read, and delete operations wait on
  the same session lock; no nested-lock deadlock occurs.
- [ ] Successful automatic compaction increments revision once, the subsequent successful turn
  increments it once, and restore refuses whenever restoring would erase that new turn.
- [ ] HTTP and browser tests prove localized notification and history refresh without exposing
  config secrets or the internal `Player` marker.
- [ ] Standard Python validation, frontend module parsing, adapter-registry loading, HTML parsing,
  and a real ASGI/HTTP smoke test pass.

## Non-goals

- Provider tokenization or exact preflight token counts.
- Reading debug logs to make runtime decisions.
- Background compaction, multi-process coordination, or a persistent job queue.
- Automatically overriding `compaction_keep_recent_turns`.
- Streaming automatic progress through the turn endpoint; Task 05 covers measured progress for
  the explicit compaction operation while turns retain their atomic JSON response.
