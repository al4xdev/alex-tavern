# Two-channel checker: technically valid, semantic gate failed

The [pre-registered eight-case screen](TWO-CHANNEL-CHECKER-PREREGISTRATION.md)
separated `offer_verdict` and its literal `offer_quote` from
`source_conflict` and its independently validated `conflict_quote`. All **32**
direct curl calls returned HTTP 200, distinct provider IDs, schema-valid JSON
and field-appropriate literal quotes. No call was replaced. The technical gate
passed, so the frozen semantic rule applies: all four outputs per case had to
match both expected columns. It **failed**.

Six cases, including the archived T38 explicit blue closure, static green
gate offered for blue, short identity-free T37 quote, wrong target, synthetic
future warning and synthetic completed closure, matched both columns in 4/4
calls each. The two cases with a second event did not. In
`synthetic_correction`, the offered sentence alone says `O portão azul se fecha
com um baque`, while a later source sentence explicitly corrects it: the gate
remained open and never closed. All four calls correctly set
`source_conflict=true` yet incorrectly set `offer_verdict=insufficient` instead
of judging the offer on its own. In `synthetic_reopen`, the same offered
sentence is followed by a genuine reopening. All four calls correctly set
`source_conflict=false`, since reopening does not erase the earlier closure,
but again set `offer_verdict=insufficient`. An isolated [content-only
reader](TWO-CHANNEL-CONTENT-PACKET.txt) confirmed both offered sentences
assert closure, the first complete source corrects it, and the second merely
reverses state later.

This exact one-call checker shape does not keep the offered-evidence judgment
separate when the complete source contains a subsequent correction or reopening.
The result does not prove that all one-call contracts fail or identify an
internal model mechanism. The six matching cases are local controls, not a
reliability estimate. No checker, physical producer, state comparison or
renderer repair is admitted from this screen. A next candidate should isolate
the offered-evidence judgment before showing the model later events, then
validate correction separately while preserving sequential reopening as a
legitimate second event. That proposal needs a new pre-registered source test.
