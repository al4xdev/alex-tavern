# Checker context A/B: one request-field difference, frozen before calls

The previous [support-only candidate](SUPPORT-ONLY-CHECKER-RESULT.md) changed
both source availability and prompt wording, so it cannot identify why the
checker rejected T38's explicit present-tense closure. This experiment isolates
**source availability**. Both arms use byte-identical system instructions,
claim, subject, offered passages, schema, model settings and support rule. Arm
`offered_only` omits `complete_events` from the user JSON; arm `full_source`
adds the complete ordered Director `perception_events[].content` and
`time_skip_summary`. The same system prompt tells both arms that offered
passages alone must support identity and completed action; optional complete
events may reveal contradiction but may not supply missing proof.

Freeze six case inputs from the previous admission manifest/results, including
the exact support strings and complete source texts, plus one synthetic
correction control. Subjects are ordinary `O portão azul` or `O portão verde`.
Synthetic cases stay labeled synthetic. The archived T38 event list contains
the crossing, an explicit blue closure and a static green-gate observation,
without reopening or correcting the blue closure.

| Case | Offered passages | `offered_only` | `full_source` |
| --- | --- | --- | --- |
| `t38_explicit` | archived T38 explicit blue closure | `entailed` | `entailed` |
| `t38_weak` | archived T38 static green-gate sentence offered for blue claim | not entailed | not entailed |
| `t37_generic_3` | archived T37 extractor's short `o portão se fecha` quote with no identity | not entailed | not entailed |
| `wrong_target` | archived T38 blue closure offered for green claim | not entailed | not entailed |
| `minimal_future` | synthetic future blue-gate warning | not entailed | not entailed |
| `minimal_complete` | synthetic completed blue-gate closure | `entailed` | `entailed` |
| `synthetic_correction` | synthetic closure assertion later explicitly corrected as false in complete events | `entailed` | not entailed |

For `not entailed`, either `insufficient` or `contradicted` rejects admission;
the test does not validate which rejection reason is better. The positives
prevent a constant `insufficient` strategy from passing. The correction
control tests whether optional full context can overturn a quote explicitly
superseded later in the same synthetic beat; it is not archived evidence.
Each arm gets four fresh curl calls per case, 56 total, without replacement or retry, with
configured DeepSeek V4 Flash, `json_object`, thinking disabled and no sampling
override. Freeze source/script/preregistration hashes and all 14 exact request
bodies before calls. Save every raw envelope, HTTP/transport status, response
ID, parsed output and literal-support check. A positive verdict must cite a
nonempty literal substring of the **offered passages**. A quote copied only
from `complete_events` is invalid, even in the full-source arm. Secrets enter
curl-config stdin and no internal IDs enter requests.

All 56 calls must be HTTP 200, distinct-ID, schema-valid and literal-support
valid before semantic scoring. If that technical gate passes, report each case
and arm separately; an arm locally matches only if all four verdicts match
frozen labels. A content-only reader then examines the offered passage and
returned positive verdicts, blinded to expected labels, reporting any concrete
counterexample separately. Do not change labels or replace failed calls.
Even both arms matching would validate only these seven support bundles, not a
producer or general contradiction detection. If one arm differs, source
availability is the isolated request difference, but do not infer a general
mechanism or prevalence from this sample.
