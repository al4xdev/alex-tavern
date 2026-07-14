# Explore: automatic compaction and measured progress

**Date**: 2026-07-13
**Scope**: Tasks 04 and 05, including configuration, Runner transaction boundaries, Historian
calls, HTTP/UI consumers, observability, and tests.

## Findings

### One synchronous compaction transaction owns every mutation

- `Runner.compact_session` acquires the shared per-session lock, loads current state, selects the
  cutoff from distinct turn numbers, calls the Historian, updates the state, saves it atomically,
  and logs completion (`src/runner.py:501`).
- Turn, manual compaction, restore, undo, state reads, history reads, fork, and delete use the same
  process-local session lock (`src/store/sessions.py:19`, `src/runner.py:194`).
- Calling the public `compact_session` method from inside `player_turn` would reacquire the same
  non-reentrant `asyncio.Lock`; an automatic call site therefore needs one lock-owning entry point
  and one internal operation that assumes the lock is already held.
- The current backup is created before the Historian calls finish (`src/runner.py:535`). An LLM
  error or request cancellation can consequently leave a backup even though no compacted state was
  committed.

### Context pressure is estimated before generation and measured after it

- Narrator and Character history are trimmed with a deterministic `len(text) // 4` estimate and a
  history budget of 70% of `context_max` minus reserved output tokens (`src/models.py:86`).
- The Narrator message builder can render either full history (`context_max=None`) or the trimmed
  history used by a real call (`src/agents/narrator.py:199`). Thoughts are removed before either
  path (`src/agents/narrator.py:149`).
- Provider token usage is available only after a response and is written to the append-only debug
  log together with `prompt_estimated_tokens` (`src/llm/client.py:126`,
  `src/llm/debug_log.py:109`). The log is observability evidence, not canonical session state.
- The current compaction eligibility rule is independent of tokens: it requires more distinct
  turns than `compaction_keep_recent_turns` and always retains exactly that recent window
  (`src/runner.py:523`).

### Historian work has observable, finite lifecycle units

- One world-summary request runs first. Relevant character IDs are then derived, and all private
  memory requests run concurrently through `asyncio.gather` (`src/agents/summarizer.py:200`,
  `src/agents/summarizer.py:215`, `src/agents/summarizer.py:252`).
- Every request is non-streaming structured JSON (`stream: false`) and may retry inside the shared
  client (`src/llm/client.py:100`, `src/llm/client.py:195`). No provider-neutral incremental token
  callback currently exists.
- Actual lifecycle progress can be measured as preparation, completion of the world request,
  completion of each relevant private request, pre-commit, and durable commit. Token-level
  generation progress would require changing the provider/client structured-output contract.

### HTTP and browser expose only a final result today

- `POST /session/{id}/compact` awaits the complete Runner operation and returns one
  `CompactResponse` JSON object (`src/main.py:185`, `src/main.py:312`).
- The browser estimates duration from rendered DOM message count, animates to 90%, and jumps to
  100% on the JSON response (`src/static/app.js:804`). It does not reflect backend work.
- `src/static/api.js`, the debug MCP client, and `tools/replay_session.py` all consume the same JSON
  endpoint. HTTP content negotiation can add an event-stream representation for the browser while
  retaining JSON as the intentional machine-client representation of the same operation.

### Configuration and user notification have explicit owners

- Common compaction configuration belongs to the top-level canonical config and is rendered by
  `runtime-config.js`; provider adapters own only provider fields (`src/config.py:19`,
  `src/static/runtime-config.js:7`, `src/static/adapters/base.js:23`).
- `PlayerTurnResponse` is the existing atomic response boundary for a turn. It can report the final
  outcome of an automatic pre-turn compaction without exposing `Player` identity to any model.
- The debug log already has a `compact` operation marker, but it records only successful completion
  and has no trigger, threshold, skipped, or failure fields (`src/llm/debug_log.py:184`).

### Existing tests cover the core mutation but not the deferred behavior

- Integration tests cover no-op compaction, successful backup/save, summary and note propagation,
  undo after compaction, restore safety, and missing sessions (`tests/test_integration.py:736`).
- Session-lock tests prove that other operations wait for active mutations, but there are no tests
  for an automatic call from a turn or for client disconnect during a streamed compaction.
- Frontend tests validate module structure and localization, not the compaction progress behavior.

### The real compaction case separates an initial correlation from later evidence

- The original 20-turn playtest observed Narrator prompt growth from 1,416 to 26,443 characters
  and first-attempt failures on turns 14 through 20, but explicitly classified this as correlation,
  not proof that context growth caused the failures (`docs/cases/report.md:144`).
- The remediated 20-turn playtest reached a larger 32,550-character prompt with 40 successful LLM
  calls, no retry, and a maximum call duration of 10.6 seconds
  (`docs/cases/explore-live-playtest-2026-07-12.md:18`). The remediation report therefore found no
  evidence for changing timeout or introducing automatic compaction from latency/retry behavior
  alone (`docs/cases/report-remediation-final.md:50`).
- Both playtests verified the compaction cutoff: the original removed 45 records and retained the
  configured last eight turns; the later playtest additionally verified post-compaction summary
  and private-note use, restore, re-compaction, and undo
  (`docs/cases/report.md:253`, `docs/cases/explore-live-playtest-2026-07-12.md:180`).
- The original Historian promoted an unsupported Character claim into the world summary. After
  provenance rules were added, the repeated unsupported ruin claim was not promoted in either
  compaction (`docs/cases/report.md:182`,
  `docs/cases/explore-live-playtest-2026-07-12.md:147`). The remediation remains explicitly a
  probabilistic mitigation, not proof that semantic errors are impossible
  (`docs/cases/report-remediation-final.md:21`).
- Compacting, restoring, and compacting the identical state produced semantically similar but
  non-identical summaries and notes. The case attributes this to model generation at temperature
  1.0 and records that compaction is not semantically idempotent
  (`docs/cases/explore-live-playtest-2026-07-12.md:200`).
- The case predates the current partitioned Historian flow. It reports two Historian calls, while
  current source performs one world call followed by concurrent calls for every relevant character
  (`src/agents/summarizer.py:177`). Current source and tests are the active contract.

## Open Questions Carried Into Planning

- The product has not previously selected an automatic threshold, default enabled state, or
  hysteresis policy.
- The existing recent-turn window can make compaction ineligible even when estimated context is
  above the threshold.
- A streamed HTTP response cannot change its status code after headers are sent, so operational
  failures need an explicit terminal event contract.
