# Two-channel closure checker: frozen before calls

The prior [context A/B](CHECKER-CONTEXT-AB-RESULT.md) was technically incomplete
and exposed a contract flaw: one `support` field could not distinguish a quote
that proves the offered positive claim from a quote in the full source that
corrects it. This local candidate gives those judgments separate output fields
in **one** checker call. It is not a producer or a repair of extractor identity.

Input: named gate in ordinary prose, positive claim, `offered_support` passages,
and complete ordered `perception_events` plus `time_skip_summary`. The checker
returns:

- `offer_verdict: entailed|insufficient|contradicted` judging whether **offered
  passages alone** identify the gate and assert completed closure in the beat;
- `offer_quote: string`, literal substring of the offered passages for an
  `entailed` verdict, empty for non-entailed;
- `source_conflict: boolean`, true only if an explicit correction in the
  complete accepted beat **denies that the offered closure occurred**. A later
  reopening is a separate legitimate event, not a denial of earlier closure;
- `conflict_quote: string`, literal substring of complete events that states
  that correction when `source_conflict=true`, empty when false.

Admission would require `offer_verdict=entailed` and `source_conflict=false`.
This tests **proposal assertions**, before the private durable-state comparison.
T38's second closure therefore can be textually admitted here yet be rejected
as a repeated closed-to-closed transition later. A static closed gate is not a
new closure assertion. The model sees no current state, `scene_update`, internal
IDs or expected labels. The full source may disprove the offered claim, but it
may not fill missing identity or action in `offered_support`.

Freeze these eight bundles from the prior manifests/results; all source-derived
quotes remain unchanged and synthetic cases are explicitly marked:

| Case | Offered evidence | Expected offer entailment | Expected source conflict |
| --- | --- | --- | --- |
| `t38_explicit` | archived explicit blue closure | yes | no |
| `t38_weak` | archived static green-gate sentence for blue claim | no | no |
| `t37_generic_3` | archived short `o portão se fecha` without blue identity | no | no |
| `wrong_target` | archived blue closure for green claim | no | no |
| `minimal_future` | synthetic future warning | no | no |
| `minimal_complete` | synthetic explicit completed closure | yes | no |
| `synthetic_correction` | synthetic explicit blue closure followed in complete events by an explicit correction that no closure occurred | yes | yes |
| `synthetic_reopen` | synthetic explicit blue closure followed by later reopening in the same beat | yes | no |

For offer negatives, either `insufficient` or `contradicted` counts as no
admission; the reason is still saved. The correction control must have
`source_conflict=true` with a literal quote of the correction, while its
`offer_verdict` remains `entailed` because the offered sentence alone asserts
closure. The positives without corrections prevent a constant rejection
strategy; the reopening control prevents treating every later state reversal
as a factual correction.

Freeze exact eight requests, schema, source/script/preregistration hashes and
configured model settings in a manifest before the first call. Use direct curl
to configured DeepSeek V4 Flash with `json_object`, thinking disabled and no
temperature/top-p/seed override. Four independent calls per case, 32 total;
no replacement or retry. Save requests, raw envelopes, provider IDs, HTTP and
transport status and individual grades. The validator checks exact JSON schema,
positive `offer_quote` literal membership in offered passages, and true
`conflict_quote` literal membership in the complete source. A non-entailed
offer requires an empty `offer_quote`; no source conflict requires an empty
`conflict_quote`. A quote from the
complete source cannot serve as `offer_quote`; a correction quote is allowed in
`conflict_quote`. Secrets enter curl-config stdin only.

All 32 calls must pass HTTP, schema, quote and distinct-ID checks before any
aggregate semantic score. Then all four responses per case must match both
frozen expected columns. An isolated content reader, blinded to expected
labels, inspects complete text and outputs for specific unsupported positive
claims or fake conflicts and records any objection with a passage. Any
technical failure marks the screen incomplete; any semantic mismatch stops
this exact candidate. A local pass would justify testing a separate extractor
that consistently supplies enough identity evidence and then a real
proposal-repair-to-renderer boundary. It would not justify runtime wiring or
claim broad reliability.
