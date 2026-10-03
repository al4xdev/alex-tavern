# Support-only checker ablation: frozen before provider calls

The preceding [admission pilot](CLOSURE-ADMISSION-RESULT.md) was formally
incomplete (86/88 valid) but exposed a concrete checker behaviour: when offered
only a static green-gate sentence for a blue-closure claim, four checkers used
a different sentence from the complete source and returned `entailed`. Two
T37 positive extractor supports contained only generic `o portão se fecha`,
yet full-source checkers approved them. This ablation changes **only the
checker's visible context**: it sees the subject, positive claim and offered
passages, with no full Director event list. It tests whether the support boundary
can be enforced locally, not whether complete-source contradiction checks can
be omitted from a future producer.

Freeze seven support bundles from the existing archived/synthetic admission
manifest and recorded extractor outputs, all unmodified and labeled by origin.
The subject is `O portão azul` or `O portão verde`. Each request uses the same
DeepSeek V4 Flash settings as the prior pilot: direct curl, `json_object`,
thinking disabled, no sampling override. The checker answers
`entailed|contradicted|insufficient` and literal supporting passages. `entailed`
requires the offered passages themselves to establish both the specified gate
and completed closure in the interval. A generic `o portão` without identifying
context, future warning, static state or different-color gate does not suffice.

| Case | Offered support | Expected |
| --- | --- | --- |
| `t37_generic_1` | actual T37 extractor repetition 1: generic `o portão se fecha` fragment | not entailed |
| `t37_generic_3` | actual T37 extractor repetition 3: shorter generic fragment | not entailed |
| `t38_explicit` | actual T38 extractor repetition 1: explicit blue-gate closure | entailed |
| `t38_weak` | seeded T38 weak control: static green gate; blue subject | not entailed |
| `wrong_target` | T38 explicit blue closure; green subject | not entailed |
| `minimal_future` | synthetic five-second warning | not entailed |
| `minimal_complete` | synthetic explicit blue closure | entailed |

`not entailed` permits either `contradicted` or `insufficient`; the local
question is binary admission, not calibration among rejection reasons. The two positives prevent an
always-insufficient checker from passing. The source provenance and full
original text remain in the hash-pinned prior artifacts for audit but are
**not** sent to the checker. The frozen manifest stores all exact requests, expected labels,
source/script/preregistration hashes and settings before the first call. Run
four independent calls per case, 28 total, with no replacement or retry. Save
requests, raw envelopes, HTTP and transport statuses, IDs, parsed outputs and
literal-support validation. Secrets travel only in curl-config stdin.

Technical gate: all 28 calls must be HTTP 200, schema-valid with literal
support and distinct provider IDs. `entailed` requires nonempty literal
support. Any technical failure makes the result incomplete. If all valid,
local semantic match requires all four verdicts per case match the frozen
expectation. An isolated content-only reader will also inspect the offered
passages and returned verdicts, blinded to expected labels, to identify any
positive approval unsupported by its offered text; every disagreement must
name the deficient passage and is reported separately, never used to replace
a failed call or change a frozen label. Any mechanical mismatch stops this
exact checker shape. Even a local match with no reader objection
permits only a separate full-source contradiction check and an extractor support
repair experiment before any producer or renderer integration; it does not
repair the wrong-target extractor result from the earlier pilot.
