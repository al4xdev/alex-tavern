# Checker context A/B: technical gate failed; local outputs differ by arm

The [frozen A/B](CHECKER-CONTEXT-AB-PREREGISTRATION.md) used identical system
text, claim, subject and offered passages in each pair; only the
`complete_events` request field differed. A prepare-time assertion compared the
two request bodies after deleting that field. All **56** direct curl calls were
dispatched once, with distinct provider IDs; **53/56** passed HTTP, schema and
literal-support validation. One response echoed the JSON schema. One
`t38_weak/full_source` response returned `entailed` while citing a blue-gate
sentence present only in the complete source, correctly failing the frozen
offered-support validator. One `synthetic_correction/full_source` response
returned `contradicted` and cited the explicit correction present only in the
complete source, but the same validator rejected it. That last rejection
exposes a **contract defect in this experiment**: it forbids a legitimate
full-source contradiction quote even though the prompt and synthetic control
ask the checker to detect one. The formal technical gate failed. No aggregate
semantic pass, reliability estimate or approved checker follows.

| Case | `offered_only`, four calls | `full_source`, four calls |
| --- | --- | --- |
| T38 explicit blue closure | insufficient ×4 | entailed ×3; insufficient ×1 |
| T38 weak green quote for blue claim | insufficient ×4 | insufficient ×2; contradicted ×1; invalid positive quote ×1 |
| T37 generic gate fragment | insufficient ×4 | entailed ×2; insufficient ×2 |
| Wrong-target blue quote for green claim | insufficient ×4 | insufficient ×3; contradicted ×1 |
| Synthetic future warning | insufficient ×4 | insufficient ×3; contradicted ×1 |
| Synthetic completed closure | entailed ×4 | entailed ×2; insufficient ×1; schema-invalid ×1 |
| Synthetic correction | insufficient ×4 | contradicted ×3; invalid contradiction quote ×1 |

The valid individual responses give a narrower observation. With the explicit
archived T38 passage offered, `offered_only` returned `insufficient` in **4/4**
calls; `full_source` returned `entailed` in **3/4** and `insufficient` in one.
With the generic T37 `o portão se fecha` fragment offered for the blue gate,
`offered_only` returned `insufficient` in **4/4**, while `full_source` returned
`entailed` in **2/4** despite the offered fragment lacking gate identity. The
weak-support full-source case additionally produced one invalid positive that
borrowed the blue closure from outside the offered passage. In the synthetic
correction control, full-source calls recognized the explicit correction, but
one correct contradiction was invalidated by the experiment's quote rule.
An isolated [content-only reader](CHECKER-CONTEXT-AB-CONTENT-PACKET.txt)
confirmed that T38's offered sentence states completed blue-gate closure,
T37's short fragment lacks identity, and the synthetic correction negates its
offered closure assertion. The reader also identified the distinction between
illicit **positive** support imported from complete events and legitimate
**negative** correction evidence found there.

These paired observations are consistent with source context helping the model
recognize a completed event while also tempting it to fill gaps in offered
support. They do not prove a general causal effect: the sample is small,
stochastic and formally incomplete. A corrected future contract would need
separate evidence channels for offered positive support and full-source
contradiction, with validation rules appropriate to each. Neither arm is
admitted for Task 69; no private state comparison or renderer repair was run.
