# Task 64 return-control wording screen: preregistration

## Question and boundary

Can a more operational definition of `return_control` correct one recorded false
negative without turning ongoing physical action into a handoff?

`return_control` is chosen inside the Director response. Character-agent speech
generated later in the turn is outside this decision boundary and cannot be used
to classify the Director's boolean. This screen therefore uses only the request
available to the Director and the events the Director itself returns.

This is a prompt screen over selected cases, not evidence that sessions improve
or that handoff opportunities are frequent. Passing it permits the exact
candidate wording to enter the production builder only for a live-cell test; the
task remains open until that check. Failing it changes no runtime code.

## Frozen wording

Arm A is the exact archived production wording:

> `- "return_control": true ONLY when this beat ends on a decision, danger,`
> `or direct question aimed at ONE named person, which that person alone`
> `can answer; false while the scene can keep moving on its own.`

Arm B replaces exactly that three-line block, in the same position, with:

> `- "return_control": true when, after this beat's events, one named person's`
> `answer or voluntary action is the next causal step. This includes an invitation,`
> `request, order, direct question, or immediate danger aimed at that person, even`
> `when other characters also spoke in this beat. Set false when a physical`
> `consequence or another person's already-started action should occur first.`

The candidate names no character and gives every named person the same rule. The
messages, schema, model, response format, disabled-thinking setting and every
other byte stay fixed per payload.

## Frozen real payloads

Each source is a committed post-task-70 turn from
`plans/artifacts/repetition-battery/`:

1. **T, target:** `b11b38dc` T13. The Director's own last speech event says
   Asword would join Link's team `se Link aceitasse`; it nevertheless returned
   `false`. The answer is the next causal step and no action has started.
2. **P, positive control:** `54bcdace` T11. The creature advances with its eyes
   fixed on Asword while the room waits; the archived response returned `true`.
3. **N1, negative control:** `00997daa` T33. The ceiling is failing, Garran chooses
   the side passage, and Doran has already begun bracing it; the archived response
   returned `false`. The physical action should continue before a handoff.
4. **N2, negative control:** `09aabf25` T30. Maelis orders the group through the
   north gate and Asword, supported by Link, has already started moving toward it;
   the archived response returned `false`.
5. **N3, negative control:** `21f7c4e1` T26. A beam is about to fall, but Marta has
   already pulled a tow cable and begun organizing the rescue; the archived
   response returned `false`.

The archived output is evidence for selecting the payload, never one of the four
new observations.

## Execution

- Build ten request bodies: both A and B for T, P, N1, N2 and N3.
- Assert that A is byte-identical to the archived request body reconstructed from
  its debug record and that B differs only by the frozen three-line replacement.
- Run four fresh calls per body, 40 calls total, shuffled with a recorded seed and
  at most four concurrent calls.
- Use direct `curl` to the configured DeepSeek chat-completions endpoint. Pass the
  key only through curl config on stdin. Save exact requests, raw envelopes, HTTP
  metadata and parsed responses. Retry only transport failures, HTTP 429 and all
  HTTP 5xx, at most three attempts. Never replace a schema-invalid HTTP 200.
- Validate each parsed response against the exact JSON Schema embedded in that
  request's system message.
- For the mechanical count, use the production normalisation:
  `bool(response.get("return_control", False))`. Report field presence separately;
  a schema-valid omission therefore counts as `false`, not as a technical error.

## Technical gate

All four scheduled calls for every payload/arm must be HTTP-successful,
parseable and schema-valid. An invalid HTTP 200 counts as invalid and is not
retried. If any of the 40 observations is invalid, the screen is technically
incomplete and no behavioural conclusion follows.

## Mechanical decision rule

The recorded classifications must first reproduce in arm A:

- T-A: `return_control=false` in at least 3/4 responses;
- P-A: `return_control=true` in at least 3/4 responses;
- each of N1-A, N2-A and N3-A: `return_control=false` in at least 3/4 responses.

If any baseline condition fails, the frozen cases are not stable enough to test
the wording and the screen stops without adoption.

If all baseline conditions pass, arm B passes mechanically only if:

- T-B: `return_control=true` in at least 3/4 responses;
- P-B: `return_control=true` in at least 3/4 responses;
- each of N1-B, N2-B and N3-B: `return_control=false` in at least 3/4 responses.

All thresholds are per payload. Calls are repeated observations within one
payload, not independent session-level estimates; no pooled percentage or
significance test will be reported.

## Blind content check

Before collection, derive and save one reader-context file per payload from its
archived final user message: take the exact substring from `HISTORY:` up to, but
not including, `ROTEIRO (`. This includes history, current scene and current moods
but excludes private future direction. Hash those files into the manifest before
any call. No reader context may be written or changed after collection starts.

After collection, shuffle all 40 responses under opaque item IDs. Give a clean
reader the frozen context and the complete parsed response with only
`return_control` removed. Do not reveal arm, expected label, source label or the
model's boolean. For every item the reader returns exactly one
`expected_return_control` boolean and a short reason, using this precedence:

1. `false` if an already-started action by another person or an immediate physical
   consequence must occur before anyone can answer;
2. otherwise `true` if a named person's answer or voluntary action is the next
   causal step;
3. otherwise `false`.

The reader must not infer which character is controlled. Baseline A is
semantically stable only if the reader expects `true` in at least 3/4 T-A and P-A
items and `false` in at least 3/4 items for each negative-control A payload. Arm B
passes only if model and reader agree pairwise in at least 3/4 items for every
payload, with the expected direction (true for T and P; false for N1, N2 and N3).
Reader disagreement stops adoption even if the mechanical gate passes.

The reader mechanism is frozen before collection: one native subagent using
`gpt-5.6-terra`, effort `medium`, `fork_turns="none"`, with no conversation
history. This fallback is used because three parallel `mcp__agy_scout__agy_scout`
calls on these session reads produced no result and were terminated on 2026-09-22.
The subagent receives only the generated blind prompt, not repository paths or
the hidden key. Its instruction is exactly the precedence and field definition
above followed by: `Return only a JSON array with exactly 40 objects. Each object
has exactly item_id, expected_return_control, and reason. Preserve every item_id
exactly; expected_return_control is a JSON boolean and reason is a non-empty
string.` One invocation is allowed. Anything other than parseable JSON with the
exact 40 IDs and exact fields makes the content screen incomplete; no replacement
reader or repaired response is allowed.

## Outcomes

- **All technical, baseline, mechanical and content conditions pass:** replace the
  production text with the exact B wording only to perform the existing live-cell
  check, and add a prompt-contract regression that the wording identifies no
  character. Do not claim general improvement from this screen.
- **Technical gate fails:** report incomplete; do not adopt.
- **Baseline gate fails:** report payload variance; do not adopt or infer that the
  current wording is adequate.
- **Candidate mechanical or content gate fails:** record measured-and-rejected;
  do not try a third wording on these frozen payloads.

This screen confirms or rejects one selected false-negative case, one retained
positive and three already-started-action controls. It makes no claim about other
classes of excessive handoff, the frequency of handoff opportunities or the
archived 314-turn cohort. Its falsifier is any failed condition above.
