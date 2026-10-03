# Current-builder label-only curl screen, 2026-10-03

Owner requested a focused test of problematic cases. The earlier eight-call
screen used an experimental temporal/events-last payload and a label containing
an epistemic instruction; it was not this production-builder label-only test.

Use existing synthetic portal_attempt, portal_closed, portal_left fixtures;
owner-play sessions excluded. Capture today's actual production next-beat
builder through the provider adapter. Control unchanged; candidate replaces
only CURRENT BEAT with PREVIOUS BEAT PLAN, in place. No added instruction,
event reorder, schema, sampling, or provider-setting change. Status text still
exists unchanged: this screen tests one local label, not a full contract rewrite.

Four fresh curl calls per fixture per arm, 24 total, shuffled, at most four
concurrent. Read-only provider config, secret through curl stdin, no retries or
replacement calls. Hash protocol, script, production source and freeze requests
before executing; preserve every raw response, ID, HTTP status and duration.
All four HTTP200 schema-valid replies with distinct nonempty IDs required in
each cell, otherwise comparison incomplete. Incomplete does not erase observed
valid counterexamples or demonstrate a model defect caused by transport.

Mechanical gate checks output.act_completed: false for portal_attempt, true for
portal_closed and portal_left. This is separate from a text read of each plan
against its own source. Blind readers see confirmed events, state, directives,
plan and exit target, not arm names or prior verdicts. Read for repeated old
closure/extinction, uncaused revival, invented prior voluntary action and
unsupported starting location; distinguish new explicitly caused events,
prospective goals, independent environmental events and different inscriptions.
Manually verify every cited contradiction. A materially ambiguous interpretation
of whether a source fact was contradicted remains unresolved; do not settle it
with a keyword count or reviewer vote. Mere omission of a settled fact is not a
contradiction. Silence from a reader is not general reliability evidence.

Any candidate valid flag mismatch, supported contradiction, unresolved material
source issue, or incomplete comparison blocks adoption. Control failures are
the comparator, not automatic candidate failures. Even a completely clean
candidate only permits further validation, no production change here. Report
per-fixture results and quotes; no population rate or causal proof from four
samples. If control is also clean, no local separation demonstrated. Scope is
the owner-requested experiment only; the roadmap goal remains paused.

Protocol criticism accepted: the previous parenthetical was an extra instruction,
not a pure label. Specify exact boolean path and distinguish transport completeness
from model behavior. No statistically significant efficacy threshold is claimed.
