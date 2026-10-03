# Task 69: authoritative physical transaction candidate, not a design decision

**Status 2026-09-25:** this candidate was subsequently screened with four
counterfactual fixtures; the corrected run failed its end-to-end technical
gate and exposed unconfirmed physical claims in valid renderer prose. The
[result](AUTHORITATIVE-TRANSACTION-RESULT.md) supersedes the future-tense test
instructions below. The text remains the preregistration-era design rationale,
not an approved architecture.

The same-generation `physical_proposals` screen asked the Director to write
an ordinary event and then label it. A proposal could quote text absent from
its own event, and a gate that merely remained ice-sealed could be labelled
`close`. Dropping the failed actor field does not make that redundant
annotation into a source of truth. The next hypothesis changes the ownership boundary:
the Director chooses an **ordered physical transaction** before any event,
position, state or prose side effect is committed.

For a gate, the transaction's only physical operations are `open`, `close`,
and `cross`. The prompt uses a unique public gate name and public character
names, never internal IDs. The server maps these to registered entities after
generation; an unresolved or ambiguous name rejects the whole draft. `open`
and `close` change only the aperture dimension. `cross` changes a named
character's side and requires the gate to be passable *at that point in the
ordered sequence*. A magical seal is a separate dimension and cannot silently
count as aperture closure. The server derives final aperture and side
occupancy. It derives a zone move only when that named gate connects two
distinct zones; crossing an interior gate can leave the zone unchanged. A
second independently model-authored `zone_moves` for the same crossing would
allow the T35 disagreement to recur. `close` on an already closed aperture and
crossing a still-closed gate reject the whole batch before side effects.

This is not yet a complete narrative contract. The Director can omit a
required action, or write an untyped physical change in another free-text
event; the prose renderer can add a change the transaction did not authorize.
The candidate is viable only if controlled full-draft reads show that the
transaction covers all consequential event text and that final viewer prose
agrees with the transaction-derived state. The Runner must preserve the human's agency:
an attempted action supplied by a controlled character is an attempt until
the accepted Director transaction establishes an outcome; no model-authored
speech or new choice is assigned to that character.

**Prerequisite fixture for a future frozen curl screen:** construct four
clearly labelled counterfactual scenes with exact initial aperture and
positions: (1) closed gate, attempted crossing remains blocked; (2) open gate,
crossing succeeds; (3) closed gate, explicit reopening precedes crossing; (4)
closed gate, ice seal is maintained with no new aperture closure. Each case
needs a specified intended beat that exercises its outcome, so an empty list
cannot pass merely by omitting the scene. Run four fresh real-provider calls
per case with a schema frozen before execution. Independently inspect every
output event, time-skip, derived final state and actual renderer output for
each viewer used in the fixture. Any missing required outcome, unsupported
physical change, illegal operation, state/prose mismatch or invalid response
stops that candidate; no call is replaced. This is a small contract screen,
not a reliability estimate: it has one gate, controlled beats and only four
stochastic calls per case. A local pass would permit a separate archived-payload
integration test with the messier multi-character topology, not production
admission.

The archived T35, T19 and T40 packets are excluded as clean legal controls:
T35 crosses in persisted prose without an immediate zone move, T19 opens a
passage already marked open, and T40 has no committed prior gate aperture.
The exact fixtures and experimental schema were frozen and run after this
candidate was written; the **production** schema was not changed.
