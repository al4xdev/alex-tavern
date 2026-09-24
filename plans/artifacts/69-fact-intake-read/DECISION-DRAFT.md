# Candidate: stop inferring character ownership from a key suffix

OBSERVED from accepted Director output d5a2ccf0 T8, debug line 92: an event
describes smoke coming “de trás das portas trancadas”; the proposed state
contains `doors_state: trancadas`. The existing `dungeon_gates` describes
closed stone arches, not confirmed locking of the upper-wing steel doors.
The isolated content reader therefore finds the locking information supported,
while retaining uncertainty about the overly generic key's exact referent.

The current intake predicate rejects any new key ending in `_action`,
`_position`, `_stance`, `_state` or `_status`, before checking similarity.
An already existing key with the same suffix is accepted. The rule claims to
identify per-character transient state, but the suffix of `doors_state` names
no character and cannot distinguish a door's lock from a character's posture.
This is a proposed correction to deterministic intake, not a claim that a
prompt change improves model behavior.

PROPOSED DECISION: remove only that suffix veto. Retain the existing cap,
exact-key update behavior, secrecy cleanup and separate similarity predicate.
The latter also has questionable refusals in the content read, but simple
addition can preserve duplicates, unsupported assertions and contradictions;
this decision does not validate removing or replacing it.

Tradeoff: character-scoped or redundant facts previously blocked solely by a
suffix can now enter the bounded state. This proposal does not assert that
all such facts are useful, or that a label proves their content true. It stops
the program treating a spelling pattern as evidence of an actor's ownership.
The content reader's alarm and messenger cases have qualifications; the
locked-door case is the concrete supported loss motivating this narrow change.

Verification required before accepting the code change: a regression using the
recorded locked-door delta must fail under the old suffix veto and preserve
the fact after its removal; existing exact updates, similarity handling,
eviction and secrecy checks must remain intact. Check the real historical next
request/state before claiming that this loss actually occurred in that run.
This does not establish better subsequent fiction or close task 69.

## Follow-up

The proposal above preceded the regression and destination checks. The completed
checks and the claim critic's narrower historical attribution are recorded in
[REPORT.md](REPORT.md). Treat “concrete supported loss” above as a candidate
observation at drafting time, not proof of the historical execution path.
