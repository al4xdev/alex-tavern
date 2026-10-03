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
`O portão azul` or `O portão verde`. This is a manually supplied target, not a
persisted `public_label`.

The extractor returns `completed_closure: yes|no|ambiguous` and literal
`support` passages. `yes` requires that the **proposal asserts** the named
subject finishes closing in this beat. Whether this is physically possible in
the prior world state is a separate deterministic question. Narrowing, warnings about future closure, and a static sealed
gate do not qualify. `ambiguous` means a closure is asserted but its target
cannot be determined. Passage membership is checked mechanically; whether the
passage entails the claim is a semantic judgment.

A separate checker request receives the same complete source, subject, a fixed
positive claim that this subject completed closure in this beat, and literal
source passages offered as support. For each ordinary repetition where the extractor says
`yes`, the offered passages are **that repetition's actual extractor output**;
otherwise they are a frozen seeded passage, including wrong positives on
negative cases. One explicit checker control (`t38_weak_support`) overrides
the extractor's passages with a weak frozen quote despite closure elsewhere in
the source. The checker must decide whether the **offered passages themselves**
support both target identity and completed action. It may inspect the full
source for contradiction but may not substitute other passages for absent
support. It does not receive the extractor's verdict or reasoning. It returns
`entailed|contradicted|insufficient` and literal support.
It runs on **every** case. Only `extractor=yes` plus `checker=entailed` would
admit a physical closure for a later deterministic comparison; the checker
alone never commits a transition. This tests actual positive handoff and also
tests seeded false claims when the extractor correctly declines one.

## Frozen cases and labels

| Case | Origin | Extractor | Checker | Why |
| --- | --- | --- | --- | --- |
| `t36_blue` | archived T36 | no | not entailed | Future five-second warning and narrowing to usable gap. |
| `t37_blue` | archived T37 | yes | entailed | Time-skip summary closes the contextually identified blue gate. |
| `t38_blue` | archived T38 | yes | entailed | Explicit blue-gate closure assertion; private prior `closed` makes it a repetition later. |
| `t39_blue` | archived T39 | no | not entailed | Already sealed gates, no new closure. |
| `t38_green` | archived T38, different subject | no | not entailed | Blue-gate closure is not green-gate closure. |
| `t38_weak_support` | archived T38, checker control | yes | insufficient | Offered passage mentions the green gate sealed in the hall, not the blue closure elsewhere. This pair must not be admitted. |
| `swap_t38_green` | **synthetic** T38 with blue/green exchanged consistently in all events | yes | entailed | Closure now belongs to green subject. |
| `swap_t38_blue` | same **synthetic** passage, blue subject | no | not entailed | Reverses the target test. |
| `minimal_future` | **synthetic** future warning | no | not entailed | Explicit five-second prediction. |
| `minimal_complete` | **synthetic** completed closure | yes | entailed | Same object and vocabulary, completed tense. |
| `ambiguous_two_gates` | **synthetic** two-gate unresolved pronoun | ambiguous | insufficient | Closure asserted, target unresolved. |

The seeded checker claim is deliberately positive even on negative cases. For
`t36_blue` it quotes the warning; for `t39_blue` it quotes the static sealed-gate
observation; for wrong-target cases it quotes closure of the other gate. Thus a
checker that accepts all literal quotes fails. Synthetic cases are controls,
never described as archived behaviour. T37's local referent chain is the
event `fresta do portão azul` followed by the time-skip `A equipe azul ... o
portão se fecha`; no earlier turn is supplied. Case text, expected labels,
support seeds, extractor request bodies, checker request **construction rule**,
source/script/preregistration hashes and model settings are frozen in a manifest
**before** the first provider call. Each actual checker body is derived only
from its frozen case and the paired extractor result, then saved verbatim.

## Calls, validation, stopping rule

Use configured DeepSeek V4 Flash via direct curl, `json_object`, thinking
disabled, no temperature/top-p/seed override. Four independent calls for each
of two roles in eleven cases: 88 total, no replacement or retry. Run all extractor
calls first, then pair each checker call to exactly one extractor output by case
and repetition. Save each exact request, HTTP status, raw response envelope,
provider response ID, parsed JSON, schema verdict and literal-support verdict.
Secrets enter curl through config stdin, not arguments or artifacts. No call
receives a private entity ID. Repetitions are deliberate probes of stochastic
behaviour, not a deterministic temperature-zero replay.

Technical prerequisite: all 88 calls return HTTP 200, distinct response IDs,
schema-valid JSON and valid literal support (empty support permitted only for
extractor `no`/`ambiguous` and checker `insufficient`/`contradicted`). Otherwise
the screen is **incomplete** and receives no semantic pass. If technically
complete, pass only if all four outputs of **both** roles match every frozen
case label (`not entailed` allows `contradicted` or `insufficient`) and an
isolated content-only reader, blinded to the expected labels, finds no specific
verdict contradicted by the complete case text or unsupported by the offered
passages. That reader examines each case/output pair, records the contradicting
or insufficient passage if vetoing a local pass,
and does not infer model mechanism. The semantic gate never depends solely on
literal quote membership. Any future/static/wrong-target positive admitted, any missed T37
or T38 positive, or unresolved-pronoun target assigned stops this candidate.
Save failures as failures without rerunning or changing the rule.

A pass supports only this manually bound admission boundary on these eleven cases.
It does not establish treatment of future warnings inside a time skip or
negated past-tense closure, which this fixture set does not cover. It would permit a
separate offline proposal-repair-to-production-renderer test, with its own
registration. It would not validate automatic identity binding, runtime
entities, schema 17, a live producer, or overall model reliability.
