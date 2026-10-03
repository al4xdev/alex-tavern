# Runner authority slice: preregistration draft

Scope: an isolated candidate subclass of the actual Runner, using its existing
session lock, current GameState persistence, per-viewer render orchestration and
undo. It is not enabled in application construction. This slice investigates
state authority separately from the fidelity of generated language. No claim
about model behaviour is made by mocked tests.

The production Runner receives a behaviour-preserving extraction of its beat
coverage and planning-evaluation methods so these boundaries can be overridden
without replacing the commit transaction or replan application. The default
still consumes exactly the existing event text,
Character replies and accepted descriptive scene keys.

The candidate owns ONLY two explicitly registered portals' aperture and declared
crossings through them. Public entity keys resolve to private IDs in code. It
uses the existing physical transition validator, applying ordered proposed steps
to a draft before ordinary canon reconciliation. A crossing requires a declared
attempt, an open portal at that step, and the actor at its declared origin.
Blocked attempts retain the actor's position. A missing or malformed typed
step list fails the whole turn; an empty list is a valid physical hold when
there are no declared attempts. Any conflicting descriptive field also aborts
the whole turn atomically; no keys or events are pruned. Invalid typed proposals
fail the turn; repeated closing/opening steps are rejected rather than silently repaired.

Descriptive updates of owned portal keys and zone moves of tracked actors are
accepted only when they agree exactly with the computed typed outcome. The
candidate also rejects removal of tracked actors, whole-scene relocation and
replacement of the tracked zone graph. These are explicit bounded safeguards,
not a general physical-world parser. Other scene facts retain existing semantics.

Two synthetic physical goals are explicitly fixture-bound: blue aperture open
and Téo in the tunnel after crossing blue. Physical goals are evaluated from
accepted typed operations and committed state, never from event text, Character
speech/actions or descriptive keys. The candidate also requests authoritative coverage during planner evaluation:
history text cannot prove these physical anchors. Other anchors keep the
production coverage method; existing actor coverage and pacing remain active. This fixture binding does not prove automatic planner goal extraction.
Both portals and the entire cast use the same formatting in added Director
context; nothing identifies the controlled character. Subsequent actual Director
requests must reflect the state and goal coverage loaded from disk.

Deterministic checks before fresh provider calls:
- baseline Runner: retain both the initial noncontiguous wording that does not
  match and the explicit contiguous-anchor wording that does match; the latter
  covers anchors while durable aperture and actor position stay unchanged;
- candidate with reviewer forced to accept everything: the same free text in
  event content or a transition cause cannot change aperture, actor position,
  or complete the two bound physical goals;
- contradictory parallel scene updates/moves fail with persisted state, history,
  revision and coverage unchanged; valid typed operations combined with an
  invalid movement must not leave any partial physical commit;
- actual consecutive player_turn calls close/block, retain/block, reopen/cross,
  then retain the already-open/already-crossed world, with intervening reload;
  allow the real hard-cap replan before turn 3, answered by a deterministic
  planner double that retains the two physical goals and unrelated lamp anchor;
  keep an unfulfilled Bento speech/action objective so turn 4 still has a beat;
- reject a missing step list, non-array steps and an unknown target through the
  existing three-attempt JSON/schema client policy, leaving saved state intact;
- reject omission of a declared attempt even when the step list is empty;
- reject a repeated transition and a crossing without an attempt, preserve an
  unrelated lamp event/fact, and restore state, positions and goals on undo;
- scoped events retain their original audiences through render and persistence;
- forced acceptance of a contradictory final prose can still persist that prose.
  This last check MUST expose the remaining narrative-fidelity gap, not be
  counted as successful narrative admission.

Passing requires every stated deterministic assertion, the existing coverage
checks and relevant Runner regression checks. A failure blocks the candidate;
no fixture expected-state substitution or weakening assertions after results.
Record exact commands and observed boundaries. No LLM reliability rate, general
physical-family coverage, or task/roadmap completion follows from these tests.

Next provider boundary, separately frozen before calls: actual production
Director and renderer builders, both complete-source and final-viewer audits,
explicitly named causes, independently persisted chains plus controls and
known contradictions inserted at event/cause/prose boundaries. Freeze initial
fixtures and builder rules; future accepted history is generated, retained and
reconstructed, never substituted with expected history. Chain counts, stop conditions and independent controls require a separate
preregistration before any provider call. No fresh provider calls belong to this
deterministic stage.

Protocol revisions during deterministic implementation, before any provider
calls: the initial prose canary did not contain contiguous anchor phrases, so
its expected lexical coverage failed. Keep that exact wording as a negative
control and add a distinct literal-anchor canary, rather than rescore it. The
first chain attempt also encountered the real three-action cap; include its
actual replan call and preserve its reset of current-beat coverage. Inspection
and tests revealed that planner evaluation also proves coverage from historical
text; protecting only the commit collector is insufficient. The candidate now
requests authoritative anchors at this second boundary as well. These changes
revise the candidate and its deterministic test scope, not an LLM experiment.

Before the final deterministic run, content review raised the untested schema
boundary; add the three schema controls and missing-attempt control above. All
rejection checks assert the whole persisted GameState is unchanged. Exceptions
are returned to the caller; there is no semantic retry, automatic repair or
partial-event salvage in this candidate. The final per-viewer reviewer receives
only the events eligible for that viewer group (using production projection),
though it is a Director-side validator with canonical world-state access.
