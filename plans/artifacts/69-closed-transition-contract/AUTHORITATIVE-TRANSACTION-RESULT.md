# Typed gate transaction screen: local Director signal, final-prose boundary fails

The [first frozen protocol](AUTHORITATIVE-TRANSACTION-PREREGISTRATION.md)
used four explicitly counterfactual gate scenes, four direct DeepSeek curl calls
each. The model returned schema-valid and mechanically expected ordered physical
events in all 16 Director calls on outcome-specified beats. All 16 prose requests then received HTTP 400:
the harness used the production `build_prose_messages` but omitted the
DeepSeek adapter's technical JSON Schema instruction, and the provider
requires the word `json` in a `json_object` prompt. This was a **harness
failure**, with no prose verdict. The first manifest,
requests, raw errors and [V1 script](authoritative_transaction_screen_v1.py)
are preserved. None of those calls was replaced within the first run.

The separately frozen [V2 protocol](AUTHORITATIVE-TRANSACTION-V2-PREREGISTRATION.md)
changed only prose request preparation: it invokes the actual
`DeepSeekAdapter.prepare_request` with `build_prose_schema()`. The four cases,
Director contract and decision rules remained fixed. V2 made 16 fresh
Director calls and the corresponding prose calls. All 16 Director outputs
passed local schema, expected operation order, bound public gate/subject and
simple aperture/crossing preconditions. Four calls per case repeatedly
followed beats that already specified their physical outcomes; this is a
**local format/transaction signal**, not autonomous narrative judgement or a
reliability estimate. Two prose outputs were schema-shaped objects, not
`{"narration": ...}`, leaving **14 of 16** technically valid end-to-end
outputs. The registered all-valid prerequisite failed; there is no aggregate
semantic pass and no runtime producer admitted. These are counts of calls on
four selected scenes, not estimates of response validity.

**Later request audit, 2026-09-25:** V2 called the adapter after
`build_prose_messages` but bypassed the shared LLM client's `language` and
no-dash instructions. It did not mirror a complete production prose request;
the prose observations below remain selected-fixture observations.

A separate content-only reader inspected the 14 valid complete prose outputs
shuffled, with initial state, beat request, typed Director events, canonical
confirmed events and transaction-derived final state. In one `open_cross`
output, the gate **began open** and the only physical operation was Liora's
`cross`, yet the prose says `as duas folhas pesadas giram para dentro` and a
corridor is revealed. That is a new, unconfirmed opening in reader-facing
text, not a static description of an open gate. In one `reopen_cross` output,
the prose says `Há pouco, uma camada de gelo selava a passagem` and describes
recent thaw, although the fixture supplies no such past event: its initial
ice seal was `absent` and neither the transaction nor confirmed events
introduced a seal or thaw. This is **unsupported backstory**, not proof that
the gate's current aperture differs from state. A focused second reader
confirmed the invented antecedent. The first reader also flagged Liora's
spatial origin and `O corredor fecha-se atrás dela` in that paragraph; the
second reader offered a plausible camera/metaphor reading, and the next
sentence says the passage remains open. **Those disputed readings are not
counted as physical violations.** The unconfirmed opening in `open_cross`
alone shows that this selected rendering can change the reader's physical
timeline beyond its confirmed transaction.

These observations separate boundaries. No selected Director output proposed
`close` on an already closed gate or `cross` before `open`; the scripted beats
and local validator were not compared to an untyped control, so no causal
improvement is claimed. In valid individual outputs, the downstream prose
model nevertheless narrated an extra aperture movement and unsupported earlier
seal. The test
uses one gate, outcome-specified beats, minimal cast and the production prose
builder; it does not exercise real Runner audience clustering, retries,
plugins or open-ended scene choice. No causal claim is made about why the two
prose responses echoed a schema or why the valid prose drifted. This exact
screen stops at the final-prose boundary; it does not establish that the
boundary is inherently unsolvable. The next design question is how accepted
physical transactions constrain or check final viewer prose without hiding
additions in a metric.
