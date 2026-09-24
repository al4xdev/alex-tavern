# Existing-opening extraction screen: hall gates

**WITHDRAWN BEFORE CALLS.** This registration was challenged before execution:
T9 asks the extractor to reject a candidate equal to the current state, which
cannot test whether it understood the event. No provider calls were made under
this rule. Preserved as the rejected design, not as an active decision gate.

Registered 2026-09-24 before any model calls on this case.

## Source and selection

This is a second source case from a different session, selected by reading
archived Director proposals and their scene updates before running the
extractor on them. Source:
`plans/artifacts/p1-archive/drive-P1-r1/sessions/5c994c42/debug.jsonl`,
successful first-attempt Director responses T8 and T9, with T6/T7 establishing
the initial gate state. T6 `scene_update` says `portões: semiabertos`; T7 does
not change the gates. T8's pre-decision spatial draft still calls them
semiabertos, its event says they are forced from outside and "se escancaram",
and its update says `portões: abertos por impacto externo`. T9's pre-decision
draft and update say the gates are open; its events do not change them.

An independent text-only reader, before model calls, judged T8 `ajar -> open`
and T9 continued `open` unambiguous for **aperture**. The same reader found
T10's later claim that the gates burst inward, with the same guard entering,
ambiguous between an event replay and further structural damage; T10 is not
in this screen. No claim about door integrity, human traversability or cause
beyond the recorded event is scored.

The prior extraction result proposed a second *gap* case. Archive inspection
found newly created fissures but no comparably clean transition of a
pre-existing registered gap; using a new fissure would also test dynamic
entity registration, which the current storage path does not implement. This
door case tests the same aperture dimension on an existing physical opening.
It is an explicit change of diagnostic scope, not a post hoc relabelling of
the T29 rubble gap or proof that gap extraction is solved.

## Frozen contract and rule

Project only `scene_blocking.spatial_constraints`,
`perception_events[].content` and `scene_update`; strip all speaker, witness
and character IDs and exclude later prose. `scene_blocking` is a pre-decision
draft; events and updates can change its starting state. The public catalogue
has one label, "main hall gates", dimension `aperture`. At T8 the fixture
current state is `ajar`; at T9 it is `open`. The only candidate new state is
`open`. The extractor returns `change`, `no_change` or `uncertain` for the
dimension. `change` is legal only when the candidate differs from current and
the accepted proposal warrants the new state. `uncertain` authorises no
transition and does not assert that nothing happened.

Use the first screen's extractor instruction, schema shape and DeepSeek V4
Flash settings, changing only the public catalogue and source projection.
Run four separate curl calls per turn, eight total, with no replacement calls.
Save source/script/preregistration hashes, frozen requests, raw envelopes,
response IDs, parsed outputs and local validation. An HTTP/transport/schema
failure is invalid; do not repair or rerun it for scoring.

Technical gate: all eight calls must be valid. Content gate: T8 must return
`change` in **all four** calls; T9 must return `no_change` or `uncertain` in
**all four** calls. This is a deliberately strict, local stop/advance rule, not
a reliability estimate. A pass establishes only that this extractor shape
separates a clear opening from an already-open state on a second archived
fixture. It does not authorise a producer, a renderer change or a Task 69
closure. A failure stops this candidate; ambiguity or sampling may be the
reason, so a failure is not a general model-capability verdict.

After scoring, read every output against the source as fiction and preserve
any unscored quality or continuity concern without changing the gate. The
remaining producer decision still needs a pre-render correction/fidelity
experiment on a real accepted Director proposal, plus a case where an
independent legal change accompanies a duplicate without semantic ambiguity.
