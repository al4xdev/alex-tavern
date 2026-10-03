# Director-authored transition proposals: local screen incomplete and rejected

The frozen screen replayed two archived Director requests, blue T38 and kennel
T34, four fresh DeepSeek curl responses each. Every request included the
archived narrative context, an amended embedded schema requiring
`physical_proposals`, and a final reminder of the named gate's committed
closed aperture. The [pre-registration](DIRECTOR-PROPOSALS-PREREGISTRATION.md),
[script](director_proposals_screen.py), manifest, request bodies and raw
envelopes are preserved under `director-proposals-runs/`.

**Technical gate: incomplete.** All eight calls returned parseable JSON. In
blue T38, all four proposal quotes matched their draft events. In kennel T34,
three matched; one `close` proposal quoted a sentence absent from every event
and the time-skip summary. Its actual event says the gate `permanece trancado`.
This is an unmatched quote string and a conflicting action description; the
screen does not establish how the mismatch arose. Per the registered rule, this
exact annotation contract fails its prerequisite.

A separate content-only reader inspected all eight complete draft projections
without scripts or prior reports. In blue T38, three drafts explicitly narrate
`O portão azul se fecha` again and carry matching `close` proposals; one draft
keeps the gate static and correctly emits `[]`. If consumed by a validator
that rejects `close` on committed `closed`, the first three proposals would
be rejected.
Those drafts show local visibility of a repeated closure, **not** a successful
repair: their event text still contains the repeat. In two of the three,
`actor` names Garran although the cited closing sentence has no such actor;
another uses `Narrator` as the actor, outside the scene's public cast. These
actor errors are visible even before any state comparison.

In kennel T34, two drafts narrate a new closing of the gate already closed in
T33 and annotate it. Another narrates Mirella
maintaining ice on the gate, `selando a entrada`, without saying the aperture
moves closed; it nevertheless labels the passage `close`. A content reader
classified this last passage as maintenance of an existing seal, while the
word `selando` leaves room for a distinct new magical sealing action. That
ambiguity does not establish a new *aperture closure*. Two kennel proposals
also use `C3` instead of the public name Mirella, violating the proposed
output contract. We cannot score a clean producer pass by ignoring those
fields after the calls.

The screen contains no new opening or legal crossing and therefore says
nothing about annotation coverage for those actions. The generator also
changed its prose under the new prompt, so the archive's accepted drafts are
not direct coverage controls. No automatic guard or whole-draft retry is
admitted from this screen. A future variant
would need to remove or validate actor attribution, separate aperture from
seal, and then pass independent legal reopening/crossing and omission controls
before touching the runtime.
