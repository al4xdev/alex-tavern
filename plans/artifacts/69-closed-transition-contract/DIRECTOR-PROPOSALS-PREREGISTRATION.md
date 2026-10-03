# Director-authored gate transition proposals, bounded screen

Task 69 has a durable physical-state store but no reliable producer. The
independent whole-draft reporter missed material contradictions in two archived
scenes. This screen asks whether the **Director's own generation** can expose
the gate actions it narrates in a structured side channel. It is an annotation
fidelity experiment, not a runtime guard or proof of consistency.

Replay the real accepted Director requests at archived blue-gate T38
(`null-P1-r1/7fd84e9a`, debug line 350) and kennel-gate T34
(`oldcode-P1-r2/a3e1ceda`, debug line 398). Keep their original messages,
including T34's final correction, model settings and embedded schema. Extend
the embedded schema with a required `physical_proposals` array. Each item has
a public gate name (`portão azul` or `portão do canil`), `operation` (`close`,
`open`, `cross`), public actor text (empty for an inanimate gate), and a
literal quote from `perception_events` or `time_skip_summary`. Add one short
instruction before the schema and a final user reminder naming the tracked
gate and its committed `closed` aperture. No new internal entity ID is sent.
The historical requests already contain character IDs; this experiment does
not endorse adding such leakage to production.

Freeze script, source hashes, this protocol, schema and exact requests before
calling the provider. Run four fresh direct DeepSeek V4 Flash curl calls per
case, thinking disabled, `json_object`, no sampling override, no retries or
replacements. Keep raw envelopes, request hashes, response IDs and all errors.
The API key travels only through curl-config stdin.

Technical prerequisite: eight distinct HTTP-200 response IDs, parseable JSON
valid against the amended archived schema, and every proposal quote is a
literal substring of an event or time-skip summary. Any failure makes the
aggregate screen incomplete. Then a content-only reader, blind to experiment
expectations where possible, compares the **whole draft** to its proposals:
every narrated new gate closure, opening or crossing of the tracked gate must
have a matching proposal with the right public target and operation; every
proposal must represent a narrated action. A static closed observation,
attempted crossing without passage, or echo of an earlier impact is not a new
transition. The reader separately checks blocking, zone moves and scene update
for unannotated completed passage. The committed state is `closed` in both
cases; an ordered close on closed or cross before an explicit open is a
mechanical violation. A narrated explicit open followed by crossing is legal.

**Decision rule, fixed before calls:** if no draft narrates any tracked-gate
action, this screen is unexercised. If a single draft omits, misidentifies or
hallucinates a proposal, or narrates a completed passage only outside its event
text, annotation fidelity fails and no deterministic runtime guard follows.
If all eight are technically valid and all exercised drafts have complete,
accurate proposals, this establishes only a local producer signal. A separate
frozen screen must still show legal reopening/crossing and whole-draft retry
without contradictory prose before runtime integration. There is no population
reliability estimate from eight calls.
