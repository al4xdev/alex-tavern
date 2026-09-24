# Task 69 durable-state foundation result

Date: 2026-09-20

## Result

The deterministic storage foundation exists, but Task 69 is not closed. The
runtime still has no scenario bootstrap, roteiro targets or accepted transition
producer, so no claim about live narrative recurrence follows from this change.

`GameState.durable_state` now persists closed physical-world entities under
session schema 16, including an optional vitality component for actors whose IDs
must already exist in `GameState.characters`. Each entity has independent
dimensions instead of one family enum: vitality, aperture, security, integrity,
traversability and consumable resource. Kinds declare which dimensions they
allow and require; missing optional dimensions stay absent rather than receiving
loader defaults.

The first implementation draft used exclusive families such as container
`locked | unlocked | open | empty | broken`. An isolated content critic rejected
that shape: a chest can be open and empty simultaneously, a door can be open and
damaged, and an incapacitated actor can remain present. It also identified
`used`, `impact`, `empty` and `present/gone` as events or derived relations rather
than intrinsic state. That draft was replaced before integration. The foundation
interface keeps those axes separate and leaves containment, custody and position
with their owning domains.

## Enforced behavior

- registrations require stable nonempty IDs/keys, a valid kind/dimension shape,
  valid directed states and consistent provenance;
- the store keeps defensive copies and rejects duplicate IDs or logical keys;
- transitions address a dimension registered on the entity instance, require an
  exact current source, a different target and a permitted directed edge;
- the public APIs require the caller's expected Runner turn, reject mismatched or
  non-monotonic provenance and allow at most one change per dimension per beat;
- a batch may change several independent dimensions in one beat and commits none
  if any registration or transition fails;
- current state stores only last provenance per dimension, avoiding a cumulative
  log copied into every undo snapshot;
- serialization uses direct field access and validates actor entities against
  canonical `GameState.characters` IDs;
- the Runner's shared pre-beat undo anchor snapshots durable state alongside the
  roteiro and clock; a regression test mutates durable state after the anchor and
  proves the stamped record still holds the pre-beat value.

Tests cover every dimension's same-state rejection, directed escalation and
terminal edges, stale replay after reversal, expected-turn mismatch, independent
same-beat dimension changes, duplicate same-dimension changes, doorless passages,
invalid kinds/scopes/provenance, defensive copies, batch rollback, persistence,
corrupt actor IDs, pre-beat stamping and end-to-end undo.

## Internal review passes

The isolated text-only architecture critic (`agy` run `f5cafa68dbd0`) returned
`CLEAR` for the foundation contract after three passes. Earlier passes caused
material changes: removal of the cumulative transition history, explicit root
ownership, separation of actor and physical IDs, scene ownership, replacement
of collapsed state families, accurate anti-replay wording and a
bootstrap-before-roteiro order. This verdict does not cover Task 69 closure or
runtime narrative behavior.

The isolated native code reviewer (`/root/durable_state_review`) returned `CLEAR`
for the store, serialization and undo changes after finding and retesting mutable
registration references, replay after reversal, missing pre-beat durable anchors,
empty persisted IDs and a transition turn that was merely monotonic rather than
checked against the producer's supplied beat. This verdict excludes the deferred
bootstrap, roteiro consumer and transition producer.

## Validation

- `uvx ruff check .`: passes;
- `uvx ruff format --check` on the changed Python files: passes;
- `uvx mypy src/durable_state.py src/models.py`: passes;
- `uv run pytest -q tests/test_durable_state.py
  tests/test_session_schema_version.py tests/test_autonomous_burst.py`: 47 passed;
- full pytest suite: 1,167 passed, 2 deselected, 1 dependency warning.

The two deselected tests are the provider-backed strict-xfail tiers
`test_xfailed3_reduced_tier` and `test_xfailed3_full_tier`; project pytest config
excludes the `llm` marker. The repository-wide format check still reports
pre-existing formatting drift in unrelated files. The standard repository-wide
mypy command still reports three pre-existing `src/runner.py` errors outside the
changed anchor lines; the new durable module and model serialization are clean.

## Remaining boundary

The next step is deterministic bootstrap, not a model call. Scenario definitions
need a manifest that registers stable fixture/object entities and any declared
actor vitality entries at turn 0. A deterministic integration test can then use
the domain API as a hardcoded transition producer at a known Runner step and
prove that roteiro target equality removes a satisfied target from the pending
prompt. That test does not authorize a runtime model producer. Dynamic entity
creation, model-authored transitions, causal/witness validation, prompt
projection and reader-visible prose remain deferred. The archived V1-V5 provider
screens in `REPORT.md` provide no basis to ship any of them yet.
