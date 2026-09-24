# State-delta screen: incomplete

2026-09-14. One fresh isolated claim critic reviewed this report after the
execution; a second dispatch remained unavailable. This review does not repair
the source-reading deviations documented below.

One selected fb62cc2f T4 Director request, four planned generations per arm.
A preserves the recorded request; B replaces only the scene_update paragraph
with the preregistered compound-fact update instruction. The original clause
was checked against the current production system builder; no candidate prompt
was installed in runtime.

| Opaque output | Arm | Execution | Main-agent focal read |
|---|---|---|---|
| V1 | A2 | Valid | NO TRANSITION |
| V2 | B3 | Rejected: more than three next_speakers | Ineligible |
| V3 | B2 | Valid | SUPPORTED threshold fall; other state conflicts remain |
| V4 | B0 | Valid | NO TRANSITION for the original messenger; a second employee arrives |
| V5 | A1 | Rejected: more than three next_speakers | Ineligible |
| V6 | A3 | Two connection timeouts, HTTP 000, no response | Ineligible |
| V7 | A0 | Valid | AMBIGUOUS; threshold fall need not end detention |
| V8 | B1 | Valid | CONFLICT: release event exists, old retention remains; corrected after unblinding |

Only two A outputs are schema-valid, below the registered minimum of three.
B has three. Both schema-rejected responses are HTTP 200; the missing response
exhausted its one permitted connection retry. This independently stops the
candidate under the original execution requirement. The focal readings also
do not reproduce the required two clear A conflicts or three supported B
transitions. These are main-agent contextual judgments, not independent
quality measurements. Do not replace failed calls or tune this candidate on
this frozen request.

The fresh literary reader receives only the preceding visible story and opaque
events/state. A separate source-reader dispatch and a follow-up were refused
by the thread limit; the main agent performed source adjudication instead.
SOURCE-ADJUDICATION.md was saved before the main agent read the key. The key
was read while the literary reader was still working; that reader did not
receive it. This deviates from the planned order in which both verdicts would
be saved before unblinding, and is not presented as full completion of that
procedure. The original preregistration remains intact.

The [literary verdict](FICTION-VERDICT.md) is now saved. It identifies conflicting
selection instructions, orders represented as completed group movement, and
the crystal changing back to red without a relighting event. Its view is
intentionally limited to Link's witnesses; it cannot decide that an omitted
event did not happen anywhere in the full response.

An explicit later check of non-viewer events corrected the main agent too:
V8 contains “Irmã Elowen Ramires solta o mensageiro e abre caminho até a
plataforma”, while its projected state retains “mensageiro retido por Elowen
na porta leste”. The initial NO TRANSITION classification was wrong; it is
CONFLICT. This correction happened after the main agent read the key and is
not disguised as a blind judgment. The initially claimed source adjudication
was incomplete. The missing-A-response execution gate already failed without
using that classification.

V3 illustrates why source checking matters: the messenger's threshold fall is
absent from the literary packet because Link is not among its witnesses, but
it exists in the raw response. Conversely, the state turns the extinguished
crystal red without a corresponding event and calls a fragment collected while
the event still locates it in the messenger's boot. V7's discarded
`selecao_status` update also shows why raw model output and Runner projection
must remain distinct; the old `selection_status` survives. No heuristic removal
or replacement mechanism is validated here.

The projection was prepared before the separate fact-eviction correction below.
These states are below the 40-fact limit; that correction is not the prompt
intervention and is not credited as its result.

## Separate deterministic correction

Runner._update_scene now refreshes a written fact's insertion position and
enforces the existing cap after applying the whole delta. Previously, rewriting
the oldest fact and then adding another could evict the just-written fact.
Adding a fact before deleting another could also evict a third fact needlessly,
despite the completed delta fitting the limit.

Two new regression cases failed before the change; the reverse-order update
control already passed. All three now pass. The full suite passes 1,136 tests
with two deselected and one preexisting Starlette deprecation warning. Ruff
check passes. Standard mypy still reports the same three preexisting errors
at runner.py lines 873, 1291 and 1964; the global format check still reports
44 preexisting files requiring formatting.

A real persistence smoke check at the unchanged 40-fact limit saved and loaded
an isolated session under /tmp/tavern-fact-eviction-smoke-e_jwytjh. The updated
gate survived insertion and the first eviction, serialized key order survived
save/load, and a subsequent insertion evicted the next untouched fact. No
real .data session was changed. The pre-change helper docstring specifies:
“Keep the fact budget bounded, dropping the least recently written first.”
That was the documented intent, not the actual behavior of rewritten keys.
The before/after cases confirm that a rewrite now refreshes the fact's eviction
position. They do not demonstrate reduced narrative repetition or resolution
of task 69.

The claim critic rejected conflating that documented intent with existing
behavior, and rejected inferring version-policy compliance merely from the
absence of a new field. Those statements were removed. It retained the local
before/after cases, incomplete-experiment stop, and explicit correction of V8
as useful bounded evidence. No general causal narrative conclusion is promoted.
