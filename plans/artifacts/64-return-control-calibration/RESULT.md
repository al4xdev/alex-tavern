# Task 64 return-control wording screen: result

## Decision

**Stopped as technically incomplete under the preregistration.** The 40 scheduled
curl calls returned HTTP 200, but only 37 parsed as valid Director decisions under
their embedded schema. No reader packet was sent, no production wording changed,
and neither arm is accepted. The frozen protocol required all 40 valid responses
before any behavioural conclusion.

Among the technically valid responses, the archived positive-control payload
(`54bcdace` T11) returned `true` in only 1/4 fresh A calls, and negative control
`00997daa` T33 returned `false` in only 1/4 fresh A calls. If the technical gate
had passed with these counts unchanged, both would have failed the separately
registered baseline condition. These are descriptions of selected payloads;
the technical failure prevents any formal evaluation of the later gates.

## Technical record

The source, exact reconstructed requests, raw envelopes, HTTP metadata, parsed
responses, registered text and frozen reader contexts are under this directory.
`wording_screen.py prepare` froze five post-task-70 session payloads and contexts
before `collect`. For each payload, the builder replaced the registered
`return_control` block once and asserted that reversing that replacement restored
the A request object exactly. The collection made four fresh calls per
payload/arm at most four concurrently, with no retry of an HTTP 200.

Three HTTP 200 responses failed the local contract:

| case | arm/run | reason |
|---|---|---|
| target `b11b38dc` T13 | A1 | `next_speakers` had more than three entries |
| target `b11b38dc` T13 | B4 | response content contained extra data after one JSON object |
| control `00997daa` T33 | B4 | `next_speakers` had more than three entries |

No HTTP or transport failure remained after collection. The invalid responses
were neither repaired nor replaced. `mechanical-summary.json` contains all 40
records, with field presence and the normalised boolean for each valid one.

## Mechanical observations, not an acceptance verdict

Each cell scheduled four calls. Fractions below are the number matching that
cell's preregistered direction over all four scheduled calls; an invalid response
counts as invalid, not as a match.

| payload | A expected / observed | B expected / observed | valid A/B |
|---|---:|---:|---:|
| T, invitation conditional on Link | false 3/4 | true 2/4 | 3/3 |
| P, held creature beat | true 1/4 | true 4/4 | 4/4 |
| N1, Garran and Doran already acting | false 1/4 | false 2/4 | 4/3 |
| N2, evacuation already moving | false 4/4 | false 2/4 | 4/4 |
| N3, Marta already organizing rescue | false 4/4 | false 1/4 | 4/4 |

The exact registered decision order is technical gate, baseline stability,
candidate mechanical gate, then blind content read. The technical gate failed,
so later gates are not evaluated as conclusions. The 3/4 `true` count on N3-B is
retained as a selected-control observation; no blind semantic verdict was made.

## Post-task-70 cohort audit correction

`audit_post70.py` independently re-read `state.json` and accepted Director
records in the nine sessions already cited by Task 64. It counts only committed
turns (`turn_number <= state.revision`), keeping the last valid Director response
per turn after retries. The archived log has one valid but uncommitted Director
response at `d0cc98e5` T37; it is excluded. The nine committed revisions sum to
**314** in the currently retained snapshots. The earlier **323** quoted in the
task and roadmap is not reproducible from those snapshots; its original
calculation was not recovered. It happens to equal the sum of nine
`revision + 1` values, but that arithmetic does not prove how it was derived.
The per-session counts are:

| session | committed turns | `return_control=true` | protagonist routed | distinct union |
|---|---:|---:|---:|---:|
| `34390b86` | 40 | 2 | 1 | 3 |
| `d0cc98e5` | 36 | 1 | 0 | 1 |
| `00997daa` | 35 | 1 | 2 | 3 |
| `b11b38dc` | 32 | 1 | 0 | 1 |
| `55d03896` | 36 | 1 | 0 | 1 |
| `21f7c4e1` | 32 | 0 | 4 | 4 |
| `c76037ff` | 31 | 0 | 2 | 2 |
| `09aabf25` | 37 | 1 | 1 | 2 |
| `54bcdace` | 35 | 3 | 0 | 3 |
| **total** | **314** | **10** | **10** | **20** |

Every session has at least one of the two routes. The Runner treats either a
controlled character in the speaker queue or `return_control=true` as a burst
stop (`src/runner.py:_beat_settled`). Thus **0/9 sessions lack both handoff
routes**; **2/9 lack any `return_control=true`** and use only speaker routing.

In the retained snapshots, the per-turn counts are 10/314 for
`return_control=true`, 10/314 for protagonist routing and 20/314 for their
disjoint union. They describe this nine-session archive; turns within a session
are not independent samples. Earlier pooled-turn p-values should not be used as
evidence for a mechanism, both because of that clustering and because the 323
denominator is not reproduced here. The cohort still shows 0/9 sessions without
either handoff route, which is the task's original session-level checkpoint.

## Next action

Task 64 remains open as a calibration question. This wording trial stops on its
registered condition, and the same frozen payloads should not be used for a
third wording. A future trial, if one is warranted by a new source reading,
needs new cases and its own preregistered baseline-stability check at the
Director decision boundary.
