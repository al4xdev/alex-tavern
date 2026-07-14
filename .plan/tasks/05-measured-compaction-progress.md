# Task 05: Measured compaction progress

**Status:** Planned; ready after Task 04's shared compaction refactor

**Updated:** 2026-07-13

**README evidence:** `README.md`, section `Context compaction`

**Exploration:** [`../explore-04-05-compaction.md`](../explore-04-05-compaction.md)

**Dependency:** Task 04 provides the single lock-held compaction operation and safe commit boundary.

## Objective

Replace the simulated browser animation with progress derived from completed backend lifecycle
units: eligibility/preparation, each Historian model job, plugin pre-commit, durable save, and the
terminal result. Stream those events for interactive clients without creating a background job or
changing the JSON representation intentionally used by replay and MCP clients.

## Progress definition

- Progress means completed, observable compaction work, not guessed elapsed time and not partial
  model tokens.
- Determine relevant private-memory characters before issuing requests. The measurable model-work
  denominator is `1 + relevant_character_count`: one world summary and one private-memory result
  per relevant character.
- Emit stable events with a monotonically increasing `sequence` and `completed_units/total_units`:

  | Event | Meaning | Progress |
  |---|---|---|
  | `checking` | Session loaded; cutoff and eligibility being determined | 0 |
  | `summarizing` | Eligible slice fixed; model-work total known | 0 model units |
  | `model_completed` | Named `summarizer:world` or private job completed successfully | measured completed model units |
  | `before_commit` | Every model job completed; plugin draft filter is running | all model units complete |
  | `committing` | Backup is complete and the atomic state save is starting | final non-durable stage |
  | `completed` | State is durable and after-commit/log actions finished | 100% plus final result |
  | `skipped` | Nothing eligible; no model call or backup occurred | terminal no-op |
  | `failed` | Operation ended before a durable commit | terminal sanitized error |

- The browser maps model-unit completion into the central portion of the bar and reserves fixed
  edges for preparation and commit. Percentages are derived only from these events; remove message
  count, elapsed-time estimation, `requestAnimationFrame`, and the artificial 90% ceiling.
- Do not claim token-level progress. Structured calls currently use `stream: false`, providers do
  not expose a common incremental JSON contract, and retries mean received bytes would not equal
  committed work.

## Backend contract

- Add a frozen `CompactionProgress` value object and a non-blocking progress sink accepted by the
  shared Runner operation and `agents.summarizer.summarize`.
- Compute relevant character IDs before starting model work. Run the independent world and private
  calls in one cancellation-safe task group and emit `model_completed` as each successful result
  arrives. Preserve deterministic final note ordering even when completion order differs.
- A failed task cancels its siblings, discards the compaction draft, creates no backup, and emits
  one terminal `failed` event. A caller cancellation follows the same cleanup path.
- Use HTTP content negotiation on the existing `POST /session/{id}/compact` endpoint:
  - `Accept: text/event-stream` returns UTF-8 SSE events with JSON `data` payloads;
  - the normal JSON accept path returns the final typed compaction result for MCP, replay, tests,
    and simple API callers.
- The SSE producer starts one Runner task and forwards its progress through a bounded in-memory
  queue. It sends a periodic SSE comment only to keep proxies from timing out; keepalives do not
  advance progress. On disconnect, cancel and await the Runner task so it cannot continue as an
  orphan.
- Once SSE headers are sent, operational errors use the terminal `failed` event rather than a
  fictitious late HTTP status. Validation that can finish before streaming still uses normal HTTP
  status codes. Every stream has exactly one terminal event.
- Add `Cache-Control: no-store`, `X-Accel-Buffering: no`, and the SSE media type. Do not persist
  transient progress state or add a polling endpoint.

## Browser and tool behavior

- Add a focused SSE parser to `src/static/api.js`; `api.compact` requests the event-stream
  representation, validates monotonic sequences and one terminal event, invokes an `onProgress`
  callback, and resolves to the final compaction result.
- `compactSession` renders the latest measured stage, updates the existing fill from backend units,
  disables only conflicting session actions, and uses an `aria-live` status label. On completion it
  refreshes canonical state/history exactly as today; on skipped or failed it clears the busy state
  and shows localized detail.
- `AbortController` cancels the stream when the active session changes or the page unloads. A
  network interruption without a terminal event is an error; the client does not invent completion
  or retry a destructive operation automatically.
- MCP and replay clients keep requesting JSON intentionally. Add an MCP-facing assertion that the
  endpoint still returns the final result under its normal Accept header; do not teach tools to
  parse browser progress they do not expose.

## Implementation sequence

1. Introduce the progress value/sink and instrument the shared Runner preparation, draft,
   pre-commit, atomic commit, skip, and failure boundaries.
2. Refactor Historian orchestration to know its total work before calls, use cancellation-safe
   concurrency, and emit one completion event per successful world/private result.
3. Add negotiated SSE delivery, queue/disconnect cleanup, no-buffer headers, terminal event
   encoding, and JSON-path parity at the FastAPI boundary.
4. Replace the browser estimate with the streaming parser, measured UI updates, cancellation,
   accessibility text, localization, and error handling.
5. Update README/help/tool documentation and capture one real HTTP stream showing multiple
   Historian completions and a durable final result.
6. Move this task to `.plan/closed/` after automated and real-boundary evidence is recorded.

## Tests and acceptance criteria

- [ ] Unit tests prove monotonic sequence numbers, stable total units, valid stage transitions, and
  exactly one terminal event for success, skip, model error, plugin error, and cancellation.
- [ ] Multiple relevant private memories complete concurrently; progress follows actual completion
  order while persisted `character_notes` remain deterministically ordered/scoped.
- [ ] No progress payload contains private thought text, character-note text, prompts, responses,
  API keys, or provider authorization data.
- [ ] SSE framing survives chunk boundaries, multiline JSON text, keepalive comments, and UTF-8;
  malformed/out-of-order/missing-terminal streams fail visibly in the browser client.
- [ ] Client disconnect cancels outstanding Historian calls, releases the session lock, leaves
  `state.json` and backups unchanged before commit, and permits the next session operation.
- [ ] Cancellation during the synchronous backup/save commit window yields either the complete old
  state with no new backup or the complete compacted state with its backup, never a partial file.
- [ ] SSE success ends at 100%, refreshes canonical history once, and leaves the compact/other
  session controls usable. Skip and failure never flash a false 100% completion.
- [ ] The same endpoint returns equivalent final result fields on SSE and JSON paths; MCP and replay
  smoke tests continue to pass through JSON content negotiation.
- [ ] Automatic compaction from Task 04 can use the same progress sink internally but its turn
  response exposes only terminal metadata; no second compaction engine appears.
- [ ] Standard Python validation, frontend module parsing, adapter-registry loading, HTML parsing,
  complete pytest suite, and a real Uvicorn/fetch streaming smoke test pass.

## Non-goals

- Streaming raw LLM tokens, partial JSON, prompts, responses, or private memories.
- Estimating remaining wall-clock time or completion ETA.
- Persisted progress, polling, resumable jobs, automatic destructive retries, or multi-process
  event distribution.
- Converting the normal player-turn endpoint to SSE.
- Android-specific progress behavior beyond consuming the same browser fetch stream where its
  current WebView supports it; the plugin platform remains unrelated.
