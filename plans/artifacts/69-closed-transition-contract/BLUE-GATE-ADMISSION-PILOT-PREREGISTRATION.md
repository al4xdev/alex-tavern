# Blue-gate single-effect admission pilot: frozen registration

This is an offline, source-bound screen for one narrow admission question: can a
text-only reader distinguish a **completed closure** of the named subject from a
future warning, narrowing, static sealed state, another gate, or unresolved
reference? It is not a runtime producer, a physical-state transition, a repair,
or an estimate of model reliability. No application source or runtime path is
in scope.

## Source packet and blindness boundary

The source is the accepted first-attempt Director response for T36--T39 in
`plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl`. Each
model request contains precisely a public subject, one question, every
`perception_events[].content` in source order, and `time_skip_summary` as the
last source field. It contains no turn label, current state, `scene_update`,
persisted narration, expected outcome, machine/internal identifiers, source
line, or other Director fields.

The public subject for the archive cases is `O portão azul que dá acesso ao
túnel da equipe azul`. The extractor receives no target-state or repair
question. It answers only whether that subject's completed closure is asserted
by the supplied source. Its literal support passages must be copied from that
packet. A blank summary remains `time_skip_summary: ""` so the input shape is
fixed.

## Frozen cases and labels

| Case | Source construction | Expected extractor label | Purpose |
| --- | --- | --- | --- |
| `t36_future_narrowing` | T36 | `no` | Future warning and narrowing remain incomplete. |
| `t37_time_skip_closure` | T37 | `yes` | Final time-skip summary explicitly closes the blue gate. |
| `t38_explicit_closure` | T38 | `yes` | A perception event explicitly closes the blue gate. |
| `t39_static_sealed` | T39 | `no` | Sealed gates are observed, without a new closure. |
| `t38_green_target` | T38, green-gate subject | `no` | The source closes blue, while the named target is green. |
| `synthetic_t38_green_swap` | T38 with blue/green references consistently swapped | `yes` | Same completed action under a changed target. |
| `synthetic_future_warning` | Minimal synthetic future statement | `no` | Future tense alone is not completion. |
| `synthetic_completed_closure` | The same minimal statement, completed | `yes` | Minimal completed counterpart. |
| `synthetic_two_gate_pronoun` | Blue and green gates followed by `Ele se fecha...` | `ambiguous` | Pronoun does not resolve to blue. |

The synthetic minimal pair contains only its stated event, an empty summary,
and the same subject/question shape. The two-gate case names both gates before
the unresolved pronoun. These are synthetic controls, not archival observations.

## Two independent calls

The extractor returns exactly:

```json
{"completed_closure":"yes|no|ambiguous","support_passages":["literal source passage"]}
```

It must provide at least one nonempty literal support passage. `yes` requires a
completed closure of the exact named subject. `no` means the supplied source
does not assert one. `ambiguous` is required when target or completion remains
unresolved.

The admission checker is separate and does not receive extractor output. It
receives the same whole source packet plus a pre-frozen proposed **positive**
claim and literal proposed support, and returns exactly:

```json
{"admission":"entailed|contradicted|insufficient","support_passages":["literal source passage"]}
```

For expected-positive cases its proposed support is an explicit completion
passage. Every expected-negative or ambiguous case receives a seeded wrong
positive and a literal but non-entailing support passage. These controls are
independent of extractor output. The checker should entail the source-positive
claims and reject every seeded wrong positive. Proposed support is evidence to
audit, never an instruction to accept the claim.

## Execution and frozen decision rule

`blue_gate_admission_pilot.py prepare` will make one manifest before provider
calls. It freezes SHA-256 hashes of source, script, registration, and every
extractor/checker request, with the nine case packets and 18 request templates.
`run` rechecks hashes and reconstructs each request byte-for-byte before
dispatch. It makes four calls for each extractor request and four for each
checker request, 72 calls total, with no retries, replacements, prompt changes,
or fixture changes. Secrets reach curl only through `--config -` stdin and never
an artifact or command argument. Every call stores its request, raw HTTP body,
parsed output, HTTP status, curl status, duration, and provider response id.

The technical gate requires all 72 calls to be HTTP 200, transport-successful,
schema-valid, and to contain nonempty literal support passages occurring in the
respective full source packet. A technical failure is `incomplete`, with no
semantic score.

If technical validity holds, the candidate passes only if every extractor call
matches its frozen label; every positive checker call is `entailed`; and every
seeded-wrong-positive checker call is `contradicted` or `insufficient`. Any
extractor false positive, wrong-target/future/static/unresolved-pronoun
admission, missed T37 or T38 positive, failure to reject a seeded wrong
positive, or failure to entail a source-positive claim stops the candidate. A
pass would only show this selected text-only shape survived these controls. It
does not authorize a producer, runtime change, or Task 69 closure.
