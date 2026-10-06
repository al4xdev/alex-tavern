# Conversation boundaries

`src/engine_io.py` owns the narrative text boundary. `EngineInput` carries speech,
thought, action and manual event text alongside routing metadata. The `engine.input`
filter runs under the session lock before those texts enter canonical history.
Filters may replace text but cannot change routing, audiences, or whether a field
is empty. The former backend `turn.input` hook has been removed.

`engine.output` receives an `EngineOutput` with an operation, viewer and a mapping
of explicitly selected text leaves. Operations cover turn responses, state/history,
suggestions and opening suggestions. The host owns the response structure; plugins
cannot translate IDs, keys, audiences or routing metadata. Projection follows the
existing viewer visibility rules before filters run.

Canonical sessions remain JSON in `.data/sessions/{id}/state.json`. A translation
plugin stores derived text through `context.storage`, under its own namespace in
`.data/plugins/storage/`. The frontend continues reading the normal HTTP API and
does not read plugin files. Session export and fork retain canonical state; a fork
builds its own derived translations when first presented.

These two filters are required boundaries: failure returns HTTP 503 with
`engine_transform_failed` and retains the filter for retry. Input failure does not
advance the turn. Output failure can follow a durable commit; the response marks
`committed` and supplies a recovery operation ID when retention succeeded.
The Runner atomically retains the latest response per generated operation in
session-owned `presentation.json`. `GET /session/{id}/presentation/{operation}`
with `operation_id` retries presentation without generating fiction or suggestions.
The session lock and revision/viewer checks reject stale recovery with HTTP 409.
If retention itself fails, the UI reloads state without submitting another turn.

The curated `Conversation Translator` plugin translates Portuguese conversation
inputs to English and visible conversation output back to Portuguese. Configure
the engine's existing narrative language as English before enabling it. This first
version does not translate scenario descriptions, character sheets, directives,
configuration labels or the entire internal pipeline. Its model calls use the
active provider, including local llama.cpp, and are recorded with session, turn,
agent and operation identifiers.
