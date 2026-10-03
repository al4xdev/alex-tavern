# T35 Liora crossing persists in prose one turn before position changes

In archived `null-P1-r1/7fd84e9a`, the T35 Director says Liora `atravessa a
fresta do portão azul ... adentrando a escuridão`, but returns
`zone_moves: null`. The accepted Narrator response is present verbatim in the
saved `state.json` turn-35 history: Liora `atravessa a fresta do portão azul`
and `desaparecendo na escuridão do túnel`. The completed passage is thus in
reader-facing persisted fiction, not merely a rejected or unrendered event.

The next Director request, T36, still lists Liora among occupants of the
salon rather than the blue tunnel. Its character directory maps `C7` to
Liora Celestria. T36 again has `zone_moves: null`; T37 later says Liora is
already beyond the gate and includes `C7: túnel da equipe azul` in
`zone_moves`. The subsequent T38 request places her in the tunnel. The
[source packet](T35-LIORA-SPACE-SOURCE-PACKET.md) gives the relevant lines and
quotations. A content-only reader independently judged T35's verbs and
destination a completed traversal, not an attempt or an indefinitely pending
motion.

**Observed scope:** one archived session has a one-beat mismatch between
persisted prose and the physical position supplied to the next Director call.
T37's later move restores agreement but does not retroactively fix T36's
input. The record does not show whether this omission stems from the prompt,
the model, the Runner or a zone-granularity rule, nor does it establish how
often the mismatch occurs. A narrow interpretation that Liora remained in the
fresta until T37 is hard to reconcile with `atravessa` and `desaparecendo na
escuridão do túnel`; it also would not explain why T36 lists her as a normal
salon occupant. This is related to backlog Task 81's state/prose divergence,
not a newly promoted task.

**Effect on Task 69's next test:** T35 is a source-backed example of crossing
while a fresta remains passable, but it is not a clean *whole-draft legal
control* because the Director's `zone_moves` fails to represent the completed
crossing. A screen that scores only a proposed `cross` label and ignores that
omission would validate an annotation while the scene remains inconsistent.
The other archived candidate, T19's secret passage, narrates the door opening
although its input fact already calls it open; T40's main gate opening has no
committed prior aperture in the source packet. These three source packets do
not provide a clean combined legal-opening/crossing control. No fresh curl
screen was launched from them and no producer or repair is inferred.

**Reader disagreement recorded:** a separate critic of this report argued
that present-tense `atravessa` plus gerund `desaparecendo` might leave the
crossing in progress. A fresh fiction-only reader, given just the persisted
sentence and no state fields, placed Liora **in the tunnel** at its end and
said she could not reasonably be treated as an ordinary salon occupant in
the next scene. The direct source also says `desaparecendo na escuridão do
túnel`, not merely that she approached its threshold. We retain the narrow
one-case divergence while leaving its mechanism undiagnosed.
