# Movement/event consistency diagnostic, 2026-09-14

OBSERVED source: base-P1-r2 session 8bd4d0f1, debug.jsonl line 242,
accepted Director request T21. CURRENT SCENE puts Liora in the inner corridor;
the previous narration has knocked her down and blocked its entrance, and
Riven's latest speech says she is trapped. The archived response moves C7 to
the hall, while its four events describe mist and collapses, not her escape.
Its blocking also puts her outside without explaining a route. This local
contradiction is the target, not a measure of all positional movement.

Source excerpts: CURRENT SCENE says `corredor interno da passagem secreta ...
occupants: Liora Celestria`; T20 narration says `a derruba` and `bloqueando a
entrada com um monte de entulho`; the last history speech says `Liora está
presa! Abram caminho!`. The accepted response sets `zone_moves.C7` to
`Academia Real do Primeiro Sino, Salão dos Quatro Arcos`. Its four events are a
wall rupture, a green glow ceasing, mist advancing through the hall forcing
retreat, and the passage ceiling collapsing behind Riven. None names a Liora
exit. Existing instructions already require actual movement and prohibit
teleportation; the candidate is a more explicit connection between fields,
not the introduction of an absent continuity rule.
The source cast maps C7 to Liora Celestria. The archived system says:
`Never teleport someone, invent a convenient connection, or skip the journey
just to bring characters together.`

THEORY: explicitly requiring the existing zone_moves field to agree with
resolved movement events may reduce unsupported moves. A is the exact archived
request. B replaces only the opening zone_moves instruction:

Original:
```
- "zone_moves": null OR an object mapping character_id to the zone they
  physically moved to THIS beat (an attempted movement succeeds). You may
```

Candidate:
```
- "zone_moves": null OR an object mapping character_id to the zone they
  physically reach THIS beat. Resolve the movement and its physically possible
  route in perception_events (or time_skip_summary for elapsed travel) before
  recording the destination here. An order, intended destination, or scene-wide
  retreat does not establish that someone crossed a blocked route. If no move
  is resolved, keep their current zone and omit them from zone_moves. You may
```

No heading, planning block, history, schema, provider parameter, or other
instruction changes. This is an isolated historical request screen, not a
production-builder validation or permission to ship a prompt. It tests the
whole replacement, not which clause might matter.

Eight new curl calls: four per arm, shuffled seed 694105, concurrency four.
Permit at most one separately logged connection retry per planned call only if no HTTP response
was received. Preserve every invalid or unfavorable response, with no
replacement. Validate the archived schema and preserve request/response,
timings, script and preregistration hashes.

First give a fresh reader the visible prior fiction and opaque, name-resolved
event continuations. No arms, hypothesis, score or target. Save that read before
opening the key. Then source-check every response including zone_moves,
blocking, events and time_skip_summary. A supported target is Liora placed
outside the blocked corridor by zone_moves or blocking without a resolved,
physically coherent exit in the same response. A reasoned rescue or opening
and traversal is not a defect merely because it is new: the Director can cause
events. A generic collective retreat does not explain crossing the obstruction.
An explicit recap, uncertain location, or unresolved interpretation stays
ambiguous. Also record event/state disagreement in the opposite direction and
unrelated losses of agency, confidentiality, motivation or progression; no
movement is not automatically a good continuation.

Require at least three schema-valid responses per arm and no more invalid
responses in B than A. Only schema-valid outputs enter the target counts;
invalid outputs remain visible to the literary read, explicitly excluded from
those counts after unblinding. A local follow-up is
justified only if A has at least two supported target failures, B has none,
there is no ambiguous target classification, and the source-checked literary
read finds no unresolved material deterioration in B. Otherwise the candidate
is unresolved or fails this screen; stop wording trials on this T21 payload
after this round, including changes of seed or minor rewordings. These are
pragmatic selection criteria, not calibrated statistical
thresholds. Any favorable result still requires a production-builder replay
and a separate case of legitimate travel before implementation. One session,
one payload: no general defect rate or quality gain can be inferred.

Material deterioration means a source-supported contradiction of established
position or completed action, unsupported knowledge crossing a private boundary,
authored choice for the controlled character, or a reversal of an established
decision without a new cause. For characterization, tension and progression,
retain the reader's exact passage and contextual reason; an unresolved concern
in any of these dimensions vetoes follow-up rather than being averaged into a
score. Pure wording preference is not a fidelity defect. Insufficient valid
outputs, an unreproduced A defect, or ambiguous target attribution leave the
diagnostic unresolved; a supported B target failure or material deterioration
fails the candidate screen.

The investigator may dismiss a reader concern only by quoting source text
that directly disproves its factual premise, retaining both the concern and
correction. A contested interpretation remains unresolved and vetoes follow-up;
it cannot be relabeled as a wording preference after unblinding. Any material
concern in B suffices for the veto regardless of whether A also has it; this
does not establish that the candidate caused the concern. Record the initial
read, source correction and final disposition together. Any later study has
to preregister its own success and failure rules before calls; merely running
the proposed production/travel checks will not count as passing them.
