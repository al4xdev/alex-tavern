# Manually bound closure admission: frozen decision rule before calls

This is an offline diagnostic for Task 69, not an approved producer. Two earlier
blue-gate prompt shapes failed local semantic gates despite valid JSON. This test
separates (1) reading whether a named gate completed closure in a Director beat,
(2) independently admitting a proposed positive claim, and (3) the private,
deterministic comparison with stored aperture. Only the first two are model
calls here. The subject-to-fixture association is manual and private to this
harness; schema 16 has no validated prompt-safe label or automatic binder.

## Source and projected input

Archived source: `plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl`,
final successful Director first attempts at T36 line 334, T37 line 344, T38
line 350, T39 line 352. Give the model the **full ordered**
`perception_events[].content` list and `time_skip_summary` from each selected
response. T37's time-skip summary is part of the accepted event, not context to
discard. Withhold `scene_update`, state, internal IDs, expected labels, future
turns and persisted narration. The bound subject uses ordinary world language:
`O portão azul que dá acesso ao túnel da equipe azul` (T38 identifies the gate
and tunnel). This is a manually supplied target, not a persisted `public_label`.

The extractor returns `completed_closure: yes|no|ambiguous` and literal
`support` passages. `yes` requires that the **named subject** finishes closing
in this beat. Narrowing, warnings about future closure, and a static sealed
gate do not qualify. `ambiguous` means a closure is asserted but its target
cannot be determined. Passage membership is checked mechanically; whether the
passage entails the claim is a semantic judgment.

A separate checker request receives the same complete source, subject, a fixed
positive claim that this subject completed closure in this beat, and a literal
source passage offered as support. It does not receive the extractor's verdict
or reasoning. It returns `entailed|contradicted|insufficient` and literal support.
It runs on **every** case, including seeded wrong positives where the extractor
may correctly say no. Only `extractor=yes` plus `checker=entailed` would admit a
physical closure for a later deterministic comparison; the checker alone never
commits a transition.

## Frozen cases and labels

| Case | Origin | Extractor | Checker | Why |
| --- | --- | --- | --- | --- |
| `t36_blue` | archived T36 | no | not entailed | Future five-second warning and narrowing to usable gap. |
| `t37_blue` | archived T37 | yes | entailed | Time-skip summary closes the contextually identified blue gate. |
| `t38_blue` | archived T38 | yes | entailed | Explicit blue-gate closure assertion; private prior `closed` makes it a repetition later. |
| `t39_blue` | archived T39 | no | not entailed | Already sealed gates, no new closure. |
| `t38_green` | archived T38, different subject | no | not entailed | Blue-gate closure is not green-gate closure. |
| `swap_t38_green` | **synthetic** T38 with blue/green exchanged consistently in all events | yes | entailed | Closure now belongs to green subject. |
| `swap_t38_blue` | same **synthetic** passage, blue subject | no | not entailed | Reverses the target test. |
| `minimal_future` | **synthetic** future warning | no | not entailed | Explicit five-second prediction. |
| `minimal_complete` | **synthetic** completed closure | yes | entailed | Same object and vocabulary, completed tense. |
| `ambiguous_two_gates` | **synthetic** two-gate unresolved pronoun | ambiguous | insufficient | Closure asserted, target unresolved. |

The seeded checker claim is deliberately positive even on negative cases. For
`t36_blue` it quotes the warning; for `t39_blue` it quotes the static sealed-gate
observation; for wrong-target cases it quotes closure of the other gate. Thus a
checker that accepts all literal quotes fails. Synthetic cases are controls,
never described as archived behaviour. Case text, expected labels, support
seeds, both exact request bodies, source/script/preregistration hashes and model
settings are frozen in a manifest **before** the first provider call.

## Calls, validation, stopping rule

Use configured DeepSeek V4 Flash via direct curl, `json_object`, thinking
disabled, no temperature/top-p/seed override. Four independent calls for each
of two roles in ten cases: 80 total, no replacement or retry. Save each exact
request, HTTP status, raw response envelope, provider response ID, parsed JSON,
schema verdict and literal-support verdict. Secrets enter curl through config
stdin, not arguments or artifacts. No call receives a private entity ID.

Technical prerequisite: all 80 calls return HTTP 200, distinct response IDs,
schema-valid JSON and valid literal support (empty support permitted only for
extractor `no`/`ambiguous` and checker `insufficient`/`contradicted`). Otherwise
the screen is **incomplete** and receives no semantic pass. If technically
complete, pass only if all four outputs of **both** roles match every frozen
case label (`not entailed` allows `contradicted` or `insufficient`) and a
content-only reader finds no supported label contradicted by the complete
source text. Any future/static/wrong-target positive admitted, any missed T37
or T38 positive, or unresolved-pronoun target assigned stops this candidate.
Save failures as failures without rerunning or changing the rule.

A pass supports only this manually bound admission boundary. It would permit a
separate offline proposal-repair-to-production-renderer test, with its own
registration. It would not validate automatic identity binding, runtime
entities, schema 17, a live producer, or overall model reliability.
