# Source-inspired pillar-pair storage fixture

Date: 2026-09-21

## Result

**Source-boundary correction, 2026-09-24.** The earlier result treated T29's
fully sealed rubble gap as an unambiguous part of the accepted Director
proposal. It is not. The accepted T29 output's `scene_blocking` says the
collapsed pillar "deixa uma fresta estreita na base", but that field is a
**pre-decision spatial draft**, not a post-event state. A subsequent event says
blocks "bloqueiam a fresta", and an observation places Liora's calls
"através da fresta". Only the later prose response says the blocks bury the
remaining gap, "vedando por completo o acesso ao corredor interno". Audible
calls do not by themselves prove a traversable opening, but the proposal does
not unambiguously specify a complete seal. The fixture's `ajar -> closed`
**aperture** label was inspired by the later prose's claim that access was
sealed. Access and aperture are different dimensions: neither source boundary
establishes the fixture's aperture transition as a historical fact.

The deterministic fixture still verifies a narrow storage behavior: after a
held `destroyed` pillar value, a repeated `destroyed` transition is rejected
without corrupting its provenance, and an independently submitted gap
`ajar -> closed` transition can be applied. It does not verify that a model
producer would emit either transition, that a mixed batch is separated, or
that the renderer corrects a physical discrepancy before prose is persisted.

The focused durable-state suite passed 46 tests at that checkpoint. Together
with the existing synthetic `intact -> damaged -> destroyed` test, this covers
the chosen storage transitions. It does not complete source-grounded producer
coverage for the recorded pair.

## Source decomposition

The source is
`plans/artifacts/p1-archive/base-P1-r2/sessions/8bd4d0f1/`.

- T27 describes a cracking pillar and a narrowing gap through rubble. The test
  maps these to pillar integrity `damaged` and rubble-gap aperture `ajar`.
- T28 says the pillar splits and collapses. It also says weak calls still pass
  through a gap among the stones. The test advances only pillar integrity to
  `destroyed`; the rubble gap remains `ajar`.
- T29's accepted Director `perception_events` says the pillar "desaba em blocos
  que bloqueiam a fresta" after T28's collapse. Its `scene_update` retains
  `pilar_rachado: desabado`; the text does not settle whether a whole pillar
  collapses twice or remnants move. The same accepted output explicitly says
  the collapsed pillar leaves a narrow basal gap in pre-decision
  `scene_blocking`, and a later observation routes calls through it. The
  pre-decision gap can be blocked by the later event without contradiction;
  the event does not specify whether passage is completely sealed. Its
  `scene_update` has no gap-closure field. The **prose** response, a separate
  call, says the remaining gap is buried and access completely sealed. The test
  models a repeated `destroyed` value and a **synthetic** `ajar -> closed`
  aperture change as a chosen pair of independent transitions. It does not
  validate those as a single unambiguous Director proposal.

The earlier content critic read the narrated gap closure without this
proposal/prose separation, so its agreement cannot validate a pre-render
transition label. It did reject a binary duct transition: T28 calls the duct
partly obstructed but accessible, while T29 says the stair is cleared nearly
to the first landing. The fixture excludes the duct because no existing
binary edge is fixed by those words.

`damaged`, `destroyed`, `ajar` and `closed` are interpretations into the current
closed vocabulary, not fields present in the archived session. Complete
closure of **access** is explicit in persisted prose, while closure of the
named gap's **aperture** is not settled by either boundary. No automatic
extractor exists.

## What the test establishes

`test_source_inspired_pillar_duplicate_and_independent_gap_transition` starts
both entities at their T27 fixture states. It applies the T28 pillar collapse,
then submits a repeated `destroyed -> destroyed` transition and observes
`PhysicalTransitionRejectionError`. It next applies a synthetic independent
gap closure, selected to test storage separation. The final assertions require:

- pillar integrity remains `destroyed` with turn 28 and the T28 transition ID;
- the rejected T29 pillar proposal changes no pillar provenance;
- rubble-gap aperture is `closed` with turn 29 and the fixture transition ID.

The earlier synthetic test separately accepts integrity
`intact -> damaged -> destroyed`. Together they cover a synthetic integrity
sequence and a source-inspired, manually chosen duplicate-plus-independent
transition fixture.

## Producer constraint exposed by the fixture

The fixture processes the rejected and legal *chosen T29 transitions*
separately. The existing batch API is intentionally atomic: if a future
producer puts the duplicate pillar transition and the legal gap transition in
one unchecked batch, the rejection rolls back the whole batch. A future
producer must ensure that rejected proposals are not included in the same atomic batch as
independent legal transitions it intends to preserve. Pre-validation, splitting
or a corrected retry remain design options; this result does not select one.
Whether rejected physical events are omitted or corrected before prose is
rendered remains open producer work, not a reason to weaken batch atomicity.
The accepted T29 proposal versus persisted T29 prose is also a separate
proposal-to-renderer fidelity question; this fixture does not answer it.

The test does not prove that this pre-render separation works in a real turn.
Cross-submission producer coverage, input reconciliation and live narrative
measurement remain open under their own Task 69 criteria.

## Validation

- `uv run pytest -q tests/test_durable_state.py`: 46 passed;
- `uv run pytest -q`: 1,190 passed, 2 LLM tests deselected and the existing
  FastAPI `TestClient` deprecation warning;
- targeted Ruff check and format check: passed;
- targeted mypy for the diagnostic scripts: passed;
- mypy over the test module still reports its existing intentional malformed
  dataclass arguments and monkeypatch assignments, in addition to the three
  previously recorded `src/runner.py` errors; this test added no new reported
  mypy line.
