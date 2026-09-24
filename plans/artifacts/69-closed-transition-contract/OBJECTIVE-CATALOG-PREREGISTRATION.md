# Objective-catalog screen preregistration

Date registered: 2026-09-21, before any candidate call

## Question and fixed payloads

Can the roteiro Architect select a scenario-authorized physical objective by a
prompt-safe enum label without seeing a physical entity ID, dimension or state
token, while keeping the selection responsive to the actual story context?

Two real production requests are frozen from
`.data/sessions/20d4cdb3/debug.jsonl`:

- **C1, before the selection:** `roteiro:compile`, turn 1. The teams have not
  been announced and no test artifact is in play. Correct label: `none`.
- **C2, artifact test beginning:** `roteiro:replan`, turn 9. The current act is
  the courtyard artifact test and its declared physical escalation is an
  artifact breaking. Correct label: `test_artifact_damaged`.

The catalogue has exactly two public entries in both contexts:

- `none`: this beat does not complete an authorized physical objective;
- `test_artifact_damaged`: one mana-test artifact is physically damaged during
  the courtyard test.

The private candidate mapping is fixed as
`test_artifact_damaged -> (turma-test-artifact, integrity, damaged)`, with the
experiment's source state `integrity: intact`. That triple never enters a
prompt. It is a proposed scenario mapping for the screen, not a shipped entity
or transition.

## Arms and payload fidelity

For each context:

- **A, baseline:** the provider-bound form of the recorded request;
- **B, objective catalogue:** the same request plus the catalogue instructions
  and a required enum field on the generated beat (`first_beat` for compile,
  `beat` for replan).

The generator copies every recorded request field except internal
`provider_options`, adds the separately logged model, and materializes the
recorded DeepSeek option as `thinking: {"type": "disabled"}`. The record has no
temperature, top-p or penalty field, so neither arm invents one. If a frozen
payload uses native `json_schema`, the candidate synchronizes that API-level
schema as well as the embedded technical schema.

Candidate instructions are placed at the end of the production builder's
Architect content, immediately before the shared language, punctuation and
technical schema instructions. Position is part of the variant.

## Calls

Run four independent `curl` calls for each context and arm, 16 calls total,
against the configured DeepSeek V4 Flash endpoint. Preserve the recorded
`max_tokens`, use thinking disabled, and keep raw envelopes and extracted JSON
separately. Do not retry a schema-valid response because its choice is
inconvenient.

## Fixed blind reading

After collection, build a deterministic shuffle with seed 69. For every output,
remove arm/context metadata and remove `physical_objective`; show only the beat's
`intent`, `expected_anchors` and `exit_condition`. Send all 16 opaque items in
one isolated `mcp__agy_scout__agy_scout` run using the server-configured Gemini
with this exact instruction:

> You are reading proposed story beats for a school-fantasy roleplay. For each
> opaque item, classify `objective_fit` as `none` or
> `test_artifact_damaged` from the prose alone. Then list concrete agency
> violations, contradictions with the supplied context, or impossible physical
> sequencing. Do not infer which experimental arm produced an item. Return one
> record per opaque label and no aggregate verdict.

The critic receives the two public context descriptions above, but no schemas,
private triple, selected labels or hypothesis. After its response is saved,
unblind the labels and compare its classification with B's hidden selection.
Baseline items contribute only the defect-rate control; they have no hidden
selection.

## Decision rule fixed before calls

The boundary advances to schema design only if all conditions hold:

1. all eight B responses are HTTP-successful, parse as JSON, satisfy their
   complete candidate schemas and return one of the two enum values;
2. at least three of four C1-B responses choose `none`, and at least three of
   four C2-B responses choose `test_artifact_damaged`;
3. in each context, at least three of four B selections agree with the blind
   critic's independent prose classification;
4. the candidate has no more concrete agency, contradiction or physical-
   sequencing defects than baseline within either context, and no candidate
   prose exposes an internal entity ID, dimension name or state token.

If condition 1 fails, the contract is mechanically unsuitable. If 2 or 3 fails,
the catalogue does not discriminate context reliably and remains unproven. If 4
fails, do not add roteiro target fields. Revise or remove the boundary and run a
newly registered screen. Passing does not validate a transition producer,
narrative improvement or Task 69 closure. It only permits implementation of
private target resolution and exact-equality consumption for a later
deterministic test.

## Reproduction

`build_objective_catalog_payloads.py` writes four request bodies from the two
frozen records. The API key is read only by the shell running `curl`; it is
never written to an artifact, command argument or output file.
