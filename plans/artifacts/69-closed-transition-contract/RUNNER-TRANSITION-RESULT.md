# Runner transition-boundary result

Date completed: 2026-09-21

## Outcome

`PhysicalTransitionRejectionError` is now raised on contract-level rejection,
allowing a producer that catches it to discard the proposal before the plugin
runtime sees an exception. It does not add a model-authored target, infer a
transition from prose or prevent narration from describing an event whose
transition was rejected.

A real producer may continue the turn after catching this error only if its
pre-render output path also omits or corrects the rejected event. Catching the
error after prose already claims the event would create a state/narration
contradiction.

## Contract coverage

The implementation provides typed validation cases for malformed transition
field types, non-integer and boolean turn numbers, unknown entities or
dimensions, stale provenance, empty or repeated IDs, a source state that is no
longer current, a target equal to the current state, invalid vocabulary and
illegal graph edges. Registration and complete-store validation retain their
existing validation error types. Producers are directed to catch only the
transition-specific type when discarding a routine proposal.

An automated batch rollback test registers a new entity and applies one valid
transition before a later invalid transition; the original store retains
neither the registration nor the earlier state change.

## Real Runner submissions

Two tests exercise the boundary through `narrator.result`, the hook that carries
the current Runner turn number:

1. Turn 1 changes the bootstrapped door from `closed` to `open`. Turn 2 proposes
   `open` again. The producer catches the typed repeated-state rejection, the
   story turn continues, and the stored physical value retains turn 1's state
   and provenance.
2. A custom bootstrapped roof changes from `intact` to `damaged` on turn 1 and
   from `damaged` to `destroyed` on turn 2. Both turns and the final turn-2
   provenance persist.

These are hardcoded producers. In these two synthetic scenarios, repeated state
change is rejected and legal escalation survives across submissions. They do
not show that a model can select the correct entity, dimension or target, and
they do not close the live narrative-repetition criterion.

## Validation

- `tests/test_durable_state.py`: 45 passed;
- full non-LLM suite: 1,189 passed, 2 deselected, with the existing FastAPI
  `TestClient` deprecation warning; the two deselections are the tests marked
  `llm` by the repository's default pytest configuration;
- `uvx mypy src/durable_state.py`: clean; the repository's standard mypy command
  retains its three pre-existing `src/runner.py` diagnostics at lines 883, 1301
  and 1974;
- independent code review: clear after adding transition type validation,
  registration-plus-transition batch rollback coverage, and narrowing the test
  name to repeated state-transition rejection.
