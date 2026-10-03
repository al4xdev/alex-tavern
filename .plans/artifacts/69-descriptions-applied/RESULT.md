# Applied roteiro descriptions, 2026-10-03

Applied at the owner's explicit request: concise descriptions by field type,
quoted exact sibling/parent references, both Boolean values, number units and
ranges. Removed corresponding field prose from the general system prompt.
The compiler uses 'first_beat'; replanning uses 'beat' and references
'act_completed'. Budget is actions, deadline is narrative-clock ticks, zero
disables the deadline. No intensity field exists in these schemas. No persisted
field, schema version, controller, provider config or input label changed.

This is an applied instruction change, not a demonstrated quality improvement.
The roadmap goal remains paused and Task 69 remains open.

## Next-beat curl comparison

24 fresh curls: four per controlled fixture per arm, old frozen production
REQUESTS versus actual applied production-builder requests. No response reuse,
retry or replacement. Same story input, structural schemas and body settings;
the combined wording/placement change cannot isolate a location effect.

Each row has four calls per arm. Flag errors count only schema-valid responses.

| Fixture / confirmed source | Prior valid | Prior flag errors | Descriptive valid | Descriptive flag errors |
| --- | --- | --- | --- | --- |
| portal_attempt: failed closing attempt, portal open | 4 | 3 | 4 | 0 |
| portal_closed: portal closed, people in hall | 4 | 0 | 3 | 2 |
| portal_left: portal closed, people in canyon | 4 | 0 | 4 | 2 |

Expected flags false/true/true. All calls returned HTTP200 with distinct nonempty
IDs per cell, but portal_closed-descriptive-3 added 'expected_anchors_note',
which additionalProperties=false rejects. It remains preserved, not retried.
The comparison fails its all-valid prerequisite; valid semantic/flag failures
remain observed counterexamples. No pooled rate or general efficacy claim.
In this screen the applied version produced more errors on the already-closed
fixtures than the prior request. Its clean failed-attempt cell does not offset
those failures or establish overall improvement.

Source says the portal closed completely and no return passage is open.
portal_left-descriptive-1 nonetheless says 'fechamento incompleto' and returns
false. portal_left-descriptive-3 describes a widening passage emitting material
into the camp, also false. portal_closed-descriptive-1 explicitly says
'O portal sumiu' but returns false: text recognition and structured flag can
disagree. These do not establish the model's internal reason for either error.

An isolated blind reader examined all 23 schema-valid outputs (scout
1de7770b5519), not just candidate failures. Source verification supports the
flag mismatches and incomplete-closure assertions. Its future-reopening-loop
concern is retained as an interpretation, not an automatic contradiction:
new explicitly caused reversals and repeated future targets are allowed.
Prospective closure alone is not proof of retroactive realization; the Boolean
is independently checked against already confirmed events.

## Compiler boundary

Four extra curls used the actual generate_roteiro captured payload and final
compiler schema, separately preregistered. All four HTTP200 responses had
distinct IDs and passed schema validation. All returned three acts, budgets
5 or 6 actions and act durations between 2 and 5 narrative ticks.
This is boundary evidence, not quality acceptance or a controlled gain.

One output (compile_closed-3) used character names ['Iara', 'Bento'] in
'first_beat.expected_actors' despite the source roster IDs C1/C2. The current
normalizer drops unknown actor references; replaying this saved first_beat
through the real normalizer yielded an empty expected_actors list. This loses
the actor hints; it is not a mitigation or a successful semantic validation.
No downstream full-turn effect was tested. The isolated reader (073d72bfe929) also identified
character-action scripting and unestablished map placement. Do not automatically
promote future planned action to fabricated historical action, or infer that
absence of a map-position fact explicitly disproves every possible placement.
Those role/source questions remain open; no full-turn compliance was tested.

The compiler parent reference was corrected after the next-beat screen; a
typing annotation was corrected after compiler capture. Final actual requests
were re-captured and matched both tested payloads exactly. Frozen source hashes
describe capture-time source; final request parity verifies delivered prompts
and schemas, not full downstream behavioral equivalence.

## Validation and limits

Final pytest: 1204 passed, two deselected. Ruff lint passes; mypy passes all
61 checked source files. Changed Python files pass format checks and git diff
passes whitespace checks. Repository-wide format check reports 42 unrelated
pre-existing unformatted files; these were not bulk changed.

README documents field-local guidance and its distinction from semantic
validation. Runtime config stayed unchanged; requests/results are ignored local
JSON artifacts. No commit or remote operation was performed. The owner-requested
change remains applied, with its failures disclosed rather than treated as a
fix for beat transitions. No candidate tuning occurred within either screen.

Result-critic disposition (9bee8684ab2b): accept splitting ambiguous table
notation, mapping fixture IDs, stating the observed closed-case deterioration,
and limiting the request-parity claim. Reject its purported 2/8 accuracy:
there are three valid correct descriptive replies across the two positive
cells, not two. Reject converting these selected calls into population
reliability or calling schema rejection a demonstrated runtime crash. Reader
claims still need source verification; the preregistration explicitly allowed
new caused reversals and future targets, so disagreement with a reader is not
itself proof of selective acceptance. No statistical or causal claim follows
from the critic's proposed pooled test.
