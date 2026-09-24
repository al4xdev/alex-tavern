# Deterministic durable-state bootstrap result

Date: 2026-09-21

## Outcome

Scenario definitions may now declare a provenance-free `physical_entities`
manifest. Session creation converts that manifest into validated turn-zero
`GameState.durable_state` before the initial commit. This makes the storage
foundation consumable by deterministic code; it does not make durable state
visible to a model or establish a narrative improvement.

The built-in `thorn-lyra` scenario supplies one passage fixture for the tavern
door with `aperture: closed`. No actor vitality was added: actor entries have no
consumer yet, and the validator requires them to be all-or-none across the
canonical character IDs so the controlled character cannot be structurally
singled out.

## Boundary implemented

The authored manifest carries only entity ID, logical key, kind, optional
static scene-partition label and initial dimension values. Bootstrap owns all
provenance: registration and initial values use turn 0, no transition ID, and a
deterministic `scenario-bootstrap:<entity_id>` update ID. Input list order has
no physical meaning, so bootstrap sorts by entity ID; duplicate IDs and logical
keys remain errors.

`scene_key` remains a static scenario label. Schema 16 still has no active-scene
ID or scene registry, so bootstrap neither compares it with `Scene.location`
nor uses it for visibility or co-presence.

The same ingestion path serves HTTP starts, default `Runner.start_session()`
calls and explicit direct-runner manifests. A partially custom direct session
does not inherit fixtures from the default scenario merely because it borrowed
the default cast or scene. Missing manifests intentionally produce an empty
physical store.

The setup UI carries a loaded manifest through populate, collect, start and
scenario save without exposing an unfinished editor. When an active session is
saved as a new scenario, its current durable values are deliberately exported
as the new initial values and runtime provenance is removed, matching the
existing snapshot semantics for its scene and characters.

After extension hooks return, the durable store's shape, vocabulary,
provenance consistency and actor references are revalidated just before
session-start, turn and undo commits. An invalid plugin draft therefore cannot
persist a malformed store that only fails on the next load. This pass does not
reconstruct transition history: a trusted plugin that mutates values directly
can bypass graph-edge enforcement, so transition writers must still use the
domain API.

## Deterministic evidence

The focused durable-state module has 38 passing cases. They include:

- canonical bootstrap ordering and generated turn-zero provenance;
- malformed, dangling and partial-actor manifests rejected atomically;
- no accidental default-manifest inheritance for either kind of partial custom
  session;
- invalid `session.before_commit`, `narrator.result` and `undo.before_commit`
  drafts, plus the downstream `turn.before_commit` path, rejected without
  persisting partial state or history;
- a hardcoded `narrator.result` test hook applying `closed -> open` at the real
  Runner turn-1 commit boundary, followed by persistence and exact undo back to
  the bootstrapped `closed` value.

Separate integration coverage materializes the built-in fixture through the
FastAPI boundary. A frontend module test proves that a loaded manifest is
defensively cloned and that saving an active durable snapshot emits canonical
initial values while stripping runtime provenance.

Repository validation after the final corrections:

- `uv run pytest -q`: 1,182 passed, 2 deselected, 1 unrelated deprecation
  warning. The deselected tests are the two `llm`-marked xfailed3 tiers excluded
  by project pytest configuration;
- `uvx ruff check .`: clean;
- every module in `src/static/*.js` and `src/static/adapters/*.js` passes
  `node --check`;
- `uvx mypy src/durable_state.py src/models.py`: clean. The standard full mypy
  command retains the same three pre-existing `src/runner.py` errors, now at
  lines 883, 1301 and 1974.

An independent architecture review found the default-manifest inheritance and
post-hook validation gaps described above. Both were corrected and the final
review returned `CLEAR`. The independent content-contract review is agy run
`268621be13e0`; it selected fixture-only bootstrap, all-or-none actor coverage,
normalized order and the static-label interpretation of `scene_key`.

## Evidence boundary and next step

This increment adds no model-authored transition, prompt projection, dynamic
entity registration, spatial handoff, causal or witness inference, roteiro
target, or reader-visible prose. The hardcoded hook is test evidence for the
transaction boundary, not a shipped transition producer. Task 69 remains open,
and no live recurrence or narrative-quality claim follows.

The earlier proposal to let a model-authored roteiro emit raw
`(entity_id, dimension, target_state)` triples is withdrawn. Physical entity
IDs have no permitted prompt projection, and exact equality would validate
satisfaction without validating the model's target selection. The next design
step is a scenario-owned catalogue of prompt-safe natural-language objectives
mapped privately to validated triples. The Architect would see only an
enum-constrained objective label; code would resolve it and exact equality
could then contribute to beat completion. This is still a model-selection
boundary and requires a pre-registered real-payload screen before any roteiro
schema change. The dormant watcher rung remains unwired until it has a concrete
deterministic action.
