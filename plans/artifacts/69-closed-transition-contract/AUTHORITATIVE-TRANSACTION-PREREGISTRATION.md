# Frozen-screen protocol: typed gate events as the physical source of truth

This is an isolated **counterfactual fixture** screen, not a replay of an
archived Director call and not a production-schema test. It asks only whether
a model can emit a coherent ordered gate event sequence under a restricted
contract, then whether the production prose-message builder can render those
confirmed events without adding or removing a physical outcome. The earlier
same-generation annotation and full-draft reporter variants failed; this
changes what owns the physical event, rather than asking for a second label.

Four prewritten cases in `AUTHORITATIVE-TRANSACTION-CASES.json` use one uniquely
named blue gate, salon/tunnel sides and public names only. The beat request
explicitly supplies the intended causal outcome so an empty list cannot pass
by avoiding the beat:

1. `closed_blocked`: gate closed, Liora attempts crossing and remains in salon;
   expected physical operation sequence `[]` and at least one observation of
   the attempted, blocked action.
2. `open_cross`: gate open, Liora completes crossing into tunnel; expected
   `[cross]`.
3. `reopen_cross`: gate closed, Garran releases its mechanism so it opens, then
   Liora crosses; expected `[open, cross]`.
4. `seal_maintenance`: gate closed and already ice-sealed, Mirella checks the
   unchanged seal, nobody crosses; expected `[]` and at least one observation
   of the check.

Every fixture explicitly lists all four public actors' initial positions and
whether an ice seal is present. The request describes the fictional outcome
without telling the model which schema kind to use. The expected operation
objects bind kind, gate public name and crossing subject; validation does not
score only a list of kind strings. These choices were tightened after an
independent pre-dispatch content review found that empty event lists could
otherwise satisfy two mechanical cases. The first prepared manifest was
moved to `/tmp/` before **any** provider call; only the revised protocol and
manifest are eligible for execution.

The Director's experimental JSON schema contains only `ordered_events`.
Physical event kinds are `open`, `close`, `cross`; their `content` must be
empty, and code renders their fixed public event sentence. `observation`
events retain free content but may not assert an untyped physical change. The
gate name and crossing subject are public names; no internal ID reaches the
Director request. The harness validates the ordered physical operations
against initial aperture/position, derives final state, and builds the prose
request using `src.agents.prose.build_prose_messages` with a minimal fixture
scene and the salon perception cluster after the derived move. This uses the production prose builder but
does not reproduce all Runner projection, retries or plugin hooks. The
renderer receives the canonical confirmed events and the derived scene; it
does not receive a separate model-authored `zone_moves`.

Freeze this protocol, exact cases, script, JSON schema and all 16 Director
requests before any curl call. Direct DeepSeek V4 Flash, `json_object`,
thinking disabled, no sampling override, four fresh Director calls per case.
For every technically valid Director output, run one subsequent real-provider
prose call using the production builder; no replacement on any failure. Store
request bodies, raw envelopes, provider IDs, HTTP status, parsed outputs,
derived state and prompt hashes. Pass the secret via curl-config stdin only.

**Technical prerequisite:** all 16 Director outputs and all 16 corresponding
prose outputs return HTTP 200 with distinct IDs and pass their frozen JSON
schemas; every Director sequence is mechanically legal and its physical kinds
match the case's expected sequence in order. If any fail, aggregate screen is
incomplete or failed and no semantic pass is scored. Then a content-only
reader receives shuffled complete Director event sequences, derived initial
and final state, and full prose, without the expected labels. For each, read
whether a required outcome was omitted, whether an observation or final prose
adds an unauthorized opening/closing/crossing, whether a blocked attempt is
mistaken for a passage, and whether a sealing observation is mistaken for an
aperture transition. A single contradiction stops this exact candidate.

A clean selected-fixture result is **only a local contract signal**. The
fixture states the outcome in its request, has one gate and no open-ended
multi-character topology; it does not estimate reliability or authorize a
runtime change. A subsequent frozen archived-payload test must cover messy
real context, multiple entities, per-viewer projection and renderer retries
before any production producer is considered.
