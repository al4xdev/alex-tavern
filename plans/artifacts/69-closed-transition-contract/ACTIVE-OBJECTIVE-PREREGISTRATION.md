# Active-objective catalogue diagnostic preregistration

Date registered: 2026-09-21, before any call in this diagnostic

## Question and scope

Two questions are kept separate: (1) does the active-only G boundary avoid
premature artifact-test material before selection while still selecting and
planning the active objective in the multi-turn test beat, and (2) does the
prior full-catalogue F prompt block reproduce intrusion while the active-only G
block avoids it?

This tests one hypothesis raised by the failed full-catalogue screen: the prior
full-catalogue prompt block may have contributed to the future objective's
appearance before the corresponding act. F and G also differ in catalogue
heading and closing guidance, so their contrast cannot isolate the future entry
as a cause. The diagnostic is limited to two frozen payloads from one session
and cannot estimate general model reliability.

The same production records are frozen from
`.data/sessions/20d4cdb3/debug.jsonl`:

- **C1, before selection:** `roteiro:compile`, turn 1. The scene is inside the
  Salão dos Quatro Arcos, teams are not announced and no mana-test artifact is
  in play.
- **C2, artifact test beginning:** `roteiro:replan`, turn 9. The scene is still
  inside the Salão dos Quatro Arcos; provisional groups are forming and Maelis
  has announced that the test will be in the courtyard. Act A2 has just become
  current and its exit requires one test artifact to break or be lost. A beat
  may move the scene toward the courtyard before conducting the test. An
  Architect beat is a 2-10-turn plan, not an immediate narration event; its
  intent and exit may sequence that movement before later artifact damage
  inside the same beat horizon.

## Arms

- **A, baseline:** provider-bound recorded request with no physical-objective
  catalogue or output field.
- **F, full catalogue, C1 only:** the rejected prior shape exposes `none` and
  `test_artifact_damaged`, including the future artifact description.
- **G, active-only catalogue:** C1 exposes only `none`, in instructions and
  schema; C2 exposes `none` and `test_artifact_damaged`, because the artifact
  objective is active in that frozen context.

C2-F is omitted because the full-vs-active contrast tests premature intrusion
in C1 before selection; in C2 the courtyard-test objective is already current.
Four fresh calls are made per included context/arm: C1-A/F/G and C2-A/G, for 20
calls total. Earlier outputs are not reused.

The public target text remains:

- `none`: this beat does not complete an authorized physical objective;
- `test_artifact_damaged`: one mana-test artifact is physically damaged during
  the courtyard test.

The private proposed mapping remains
`test_artifact_damaged -> (turma-test-artifact, integrity, damaged)`. It never
enters a payload and is not implemented by this diagnostic.

In candidate responses the selected label is the required string property
`physical_objective` inside `first_beat` for C1 and inside `beat` for C2. Its
schema is `{"type": "string", "enum": ["none"]}` for C1-G and
`{"type": "string", "enum": ["none", "test_artifact_damaged"]}` for
C1-F and C2-G. Conditions below extract the selected label only from that path.

## Payload fidelity

The generator copies every recorded request field except internal
`provider_options`, adds the separately logged model, and materializes the
recorded DeepSeek option as `thinking: {"type": "disabled"}`. It does not add
temperature, top-p or penalty settings. Candidate instructions occupy the same
production-builder position as the prior screen, immediately before the shared
language, punctuation and technical-schema instructions. The embedded schema
and any native API schema receive the same enum.

The exact inserted block for C1-F is:

```text
PHYSICAL OBJECTIVE CATALOGUE (scenario-authorized; choose exactly one label for this beat):
- none: this beat does not complete an authorized physical objective.
- test_artifact_damaged: one mana-test artifact is physically damaged during the courtyard test.
Set physical_objective to the matching label. A label is a planning target, not permission to
claim it already happened before the beat, and never requires a character decision.
```

The exact inserted block for C2-G is:

```text
PHYSICAL OBJECTIVE CATALOGUE (active entries for this beat; choose exactly one label):
- none: this beat does not complete an authorized physical objective.
- test_artifact_damaged: one mana-test artifact is physically damaged during the courtyard test.
Set physical_objective to the matching label. A label is a planning target, not permission to
claim it already happened before the beat, and never requires a character decision.
```

The exact inserted block for C1-G is:

```text
PHYSICAL OBJECTIVE CATALOGUE (active entries for this beat; choose exactly one label):
- none: this beat does not complete an authorized physical objective.
Set physical_objective to the matching label.
```

The generator preserves one blank line before and after each block.

Run four independent `curl` calls per included arm against the configured
DeepSeek V4 Flash endpoint. Preserve raw envelopes and extracted JSON. Do not
retry any HTTP-successful response because of its content or schema validity.
The shell may retry a transport failure, HTTP 429 or HTTP 5xx at most twice;
the final envelope remains the observation. Parse `choices[0].message.content`
after stripping surrounding whitespace and at most one surrounding Markdown
JSON fence; no other repair is applied.

## Blind content read

Immediately after collection, evaluate condition 1 below. If it fails, terminate
the diagnostic as a failed boundary without constructing or executing the blind
read. Evaluate the C1-F technical precondition separately. If all four F calls
meet it, include F and set `N = 20`; otherwise mark the full-vs-active contrast
undiagnosed, omit all four F calls from the blind read and set `N = 16`. An F
failure does not remove any A or G observation.

Sort the N included outputs lexicographically by `(context, arm,
run_index)`, where context is `c1` or `c2`, arm is `a`, `f` or `g`, and
`run_index` is the integer 1 through 4. Shuffle that list in place with Python
`random.Random(70).shuffle()`, then assign opaque IDs `item_01` through
`item_N` in shuffled order. Each call produces one
extracted beat (`first_beat` for C1, `beat` for C2), so call output and beat are
the same unit. Before sorting, each observation is represented as
`{"context": "c1"|"c2", "arm": "a"|"f"|"g", "run_index": 1..4,
"beat": object}` and sorted with
`key=lambda x: (x["context"], x["arm"], x["run_index"])`. Each opaque item
includes its `item_id`, the precise public
context description above, the candidate names Link, Asword, Mirella Valecourt,
Seraphine Alvor, Nix Pata-Ligeira, Doran Pedra-Rúnica, Liora Celestria, Bruna
Ferrugem, Noa Véu, Cael Vesper, Bram Muralha, Lucan Morcant, Riven Draven,
Ysara Lua-Parda, Oriana Cantabile and Téo Ventobravo, and only that beat's
generated `intent`, `expected_anchors` and `exit_condition`;
these three fields are the beat prose, and there is no separate narration field
in these contracts. Remove arm, run, selected label and private mapping. One
fresh isolated server-configured Gemini reader receives this exact instruction.
The server exposes no model or temperature override to this client; the run ID
and response are saved, and the reader is never retried because its verdict is
inconvenient. The reader user prompt is the exact instruction below followed by
`\n\n## Items to evaluate\n\n` and a compact JSON array. Every array item has
exactly `item_id` (string), `context` (string), `candidate_names` (array of
strings), `intent` (string), `expected_anchors` (array of strings) and
`exit_condition` (string).

The exact `context` value for every C1 item is:

```text
C1, before selection: roteiro:compile, turn 1. The scene is inside the Salão dos Quatro Arcos, teams are not announced and no mana-test artifact is in play.
```

The exact `context` value for every C2 item is:

```text
C2, artifact test beginning: roteiro:replan, turn 9. The scene is still inside the Salão dos Quatro Arcos; provisional groups are forming and Maelis has announced that the test will be in the courtyard. Act A2 has just become current and its exit requires one test artifact to break or be lost. A beat may move the scene toward the courtyard before conducting the test. An Architect beat is a 2-10-turn plan, not an immediate narration event; its intent and exit may sequence that movement before later artifact damage inside the same beat horizon.
```

> You are reading opaque proposed story beats for a school-fantasy roleplay.
> Return a JSON list with exactly one object per item and no aggregate verdict.
> Each object has `item_id`, `objective_fit`, `future_test_intrusion`,
> `future_test_intrusion_reason`, `context_contradiction`,
> `context_contradiction_reason`, `agency_violation`,
> `agency_violation_reason`, `physical_sequence_defect` and
> `physical_sequence_defect_reason`. Preserve each supplied `item_id` exactly.
> `objective_fit` is `test_artifact_damaged` when the multi-turn beat's `intent`,
> `expected_anchors` or `exit_condition` plans physical damage to a mana-test
> artifact, regardless of whether that plan belongs in the supplied context;
> otherwise it is `none`.
> `future_test_intrusion` is true for any C1 (before selection) item whose beat
> introduces, deploys, conducts or plans a mana-test artifact, because every
> test-artifact event belongs to a later act. It is always false for C2 (artifact
> test beginning).
> `context_contradiction` is true when the beat asserts a phase, location or
> physical state directly incompatible with its supplied context, excluding
> test-artifact presence governed by `future_test_intrusion`.
> `agency_violation` is true when the beat settles a named candidate's voluntary
> choice, movement, speech, internal emotion or injury instead of leaving their
> response open.
> `physical_sequence_defect` is true when an effect precedes or lacks its stated
> physical cause, a character relocates incompatibly without elapsed movement,
> or the same beat places an entity in contradictory positions. A C2 beat may
> coherently plan movement from the hall to the courtyard before later test
> events within its 2-10-turn horizon.
> For each boolean, give a short string reason when true and the empty JSON
> string `""` when false. Judge only the supplied context and beat fields; do
> not infer an arm.

It returns exactly these fields per item:

- `objective_fit`: `none` or `test_artifact_damaged` from the prose;
- `future_test_intrusion`: boolean plus one short reason; for C1, true if the
  beat introduces, deploys, conducts or plans a mana-test artifact; always false
  for C2, where the test act is current;
- `context_contradiction`: boolean plus one short reason;
- `agency_violation`: boolean plus one short reason;
- `physical_sequence_defect`: boolean plus one short reason.

Each candidate output contributes at most once to any given defect category;
multiple defective clauses or bullets within one beat are not pooled. Each beat
is binary zero or one in each category, yielding zero through four affected
beats per arm/category cell. Save the response before unblinding.

The blind read is one judgement batch, not N statistically independent reader
observations; no p-value or population estimate is derived from it. If the
response, after removing one surrounding JSON markdown fence if present, is not
valid JSON, remove a conversational prefix/suffix by first trying the slice from
the first `[` through the last `]`; if that slice does not parse, try the slice
from the first `{` through the last `}`. No JSON syntax repair is applied. The
parsed root must be a list, or an
object with exactly one `items` property whose value is a list; otherwise the
blind read is invalid and the boundary does not advance. The resulting list
must contain exactly N objects with the supplied item IDs once each. Each object
must contain exactly the ten fields named in the instruction; `objective_fit`,
after ASCII whitespace stripping and lowercasing, must equal one of its two
allowed values; the four flags must be JSON booleans; and the four reasons must
be JSON strings, except that a null reason is normalized to `""` only when its
corresponding flag is false. A true flag requires a reason that remains nonempty
after whitespace stripping. No other field or envelope normalization is
performed. A reader
transport failure, HTTP 429 or HTTP 5xx may be retried at most twice with the
identical prompt in a fresh run; content or schema invalidity is never retried.

## Decision rules fixed before calls

The **active-only boundary** may advance only to design of a deterministic
activation resolver if every condition holds:

1. all 16 responses across A and G are HTTP-successful, parse and satisfy their
   complete arm schemas; all eight G responses return an allowed label;
2. the blind reader classifies at least 3/4 C1-G beat prose items as `none`;
3. C2-G selects `test_artifact_damaged` in at least 3/4 calls, the blind reader
   classifies at least 3/4 C2-G prose items as that objective, and selection
   agrees with the reader in at least 3/4 paired calls, where agreement means
   that call's `beat.physical_objective` exactly equals its blind
   `objective_fit` after the preregistered normalization;
4. `future_test_intrusion` affects at most 1/4 C1-G outputs and no more C1-G
   outputs than C1-A outputs;
5. within each context, G has no more beats affected by context contradiction,
   agency violation or physical-sequencing defect than A in any category.

Condition 2 checks absence of artifact damage in the beat prose. Premature test
setup, deployment or conduct without damage is governed separately by condition
4.

The separate **full-vs-active prompt contrast** can be evaluated only if all
four C1-F responses are HTTP-successful, parse, satisfy the complete F schema
and return an allowed label. Given that technical precondition, it is supported
only if the blind reader sets `future_test_intrusion` true for at least 3/4 C1-F
outputs, at most 1/4 C1-G outputs and at most 1/4 C1-A outputs. F's selected
`physical_objective` is recorded but is not part of this contrast rule. Any
other pattern leaves the difference undiagnosed, and even a supported contrast
does not attribute causality to the future entry alone. The F arm does not gate
the separate G-boundary decision: a safe G may advance to activation-resolver
design while the reason it differs from the prior full catalogue remains
undiagnosed.

Condition 5 is deliberately conservative across its six context/category
comparisons. A single category regression may reject a viable candidate; that
false-rejection cost is accepted because this screen is a permission gate, not
an estimate of comparative effect or model reliability. There is no noise-floor
allowance or pooling across categories: if A has zero and G has one affected
beat in a cell, that cell fails. Such a failure is a valid conservative result,
not a reason to reinterpret the threshold.

Failure of any boundary condition means no schema or resolver implementation.
Passing does not validate how code knows which objective is active, a transition
producer, narration correction or Task 69 closure. It only permits design and a
later deterministic test of an activation resolver.

## Reproduction

`build_active_objective_payloads.py` creates the five request bodies.
`run_active_objective_diagnostic.py collect` reads the API base and key from the
runtime config, passes curl configuration through standard input, makes the 20
calls and preserves their HTTP metadata and raw envelopes without exposing the
key in an artifact, command argument or output file. Its `prepare-reader`
command validates the DeepSeek envelopes, applies the condition-1 short circuit,
creates the seeded blind items/key and writes the exact Gemini reader prompt.
The prompt is sent once through `mcp__agy_scout__agy_scout`; its run ID and
verbatim response are saved. Finally, the script's `evaluate-reader` command
parses that saved response, joins the hidden key and emits each fixed count and
boundary verdict. The script and generated payloads are frozen before
`collect` begins.
