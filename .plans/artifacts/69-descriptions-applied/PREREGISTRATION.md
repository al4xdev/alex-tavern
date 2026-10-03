# Applied concise field descriptions, 2026-10-03

Owner explicitly requested applying concise type-specific descriptions with
quoted exact field references, and then testing the applied JSON via curl.
The change affects roteiro compile and next-beat schemas; no persisted fields,
sampling/provider settings or controller decisions change. Shared field rules
move out of the system prose into descriptions. Booleans explain both values;
numbers explain units and useful range rather than inventing an intensity scale.

Three controlled problem fixtures: failed closure, closed portal with people in
hall, and closed portal after departure. Exclude owner sessions. Four fresh
calls per fixture/arm: frozen prior production request versus exact current
production-builder request, 24 total. Reusing the old REQUEST as comparator is
intentional; do not reuse old RESPONSES. Capture through actual provider adapter.
Assert unchanged story-input messages, sampler/body settings and schema structure
after stripping descriptions. New descriptions are concise and use exact quoted
field names; this comparison tests the applied combined wording/placement change,
not an isolated scientific effect of description length or serialization.

Freeze hashes and all requests before calls, shuffle with four concurrent curls,
read-only config and secret via stdin, preserve all envelopes/IDs/status/timing.
No retry or replacement. Require four HTTP200 schema-valid distinct nonempty IDs
per cell for complete comparison. Inspect act_completed against confirmed old-act
exit: false for failed attempt, true for closed and departed cases. Read all
proposal content separately against its source. Neither gate alone establishes
quality; boolean errors, repeated settled transitions, invented prior actions or
unresolved material source ambiguity remain failures. Newly caused reversals,
new independent pressures and future targets are allowed. Transport failure is
incompleteness, not proof of narrative failure. An isolated text reader sees all
valid results with shuffled labels and source facts; verify its claims manually.

Owner authorization to apply wording is not evidence of improvement. Record each
case/arm outcome and any failures even if all Python checks pass. No roadmap task
closure, model-change assurance, population rate or causal attribution follows.
Preserve this applied user-requested change and report its observed limits rather
than silently reverting it. Any further semantic intervention requires a distinct
experiment; do not tune within this run.
