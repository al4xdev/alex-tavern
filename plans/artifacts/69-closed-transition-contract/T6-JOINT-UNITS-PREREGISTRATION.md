# T6 joint event units: pre-registered local screen

Source: archived `d5a2ccf0` T6 accepted Director events and the actual
origin-viewer prose request. The previous event-local screen made three
**independent** model calls per beat: it kept Garran's crossing but one
assembly lost the block's several-metre roll, another lost Elowen's
stabilization prayer, and repeated dust/lamp images appeared across units.
This screen tests whether a **single call with all three events** can produce
complete, readable units for this same episode. It is not a paired comparison
with the prior three-call screen, nor a reliability, destination-projection or
automatic-binding test.

Before calls, freeze the script, source hashes, exact request and schema in
the manifest. Use the archived origin-viewer prompt up to its confirmed-event
block. Supply the same three accepted non-speech events in order. Keep the
full scene, reader transcript, cast and post-move roster; attach the prior
screen's **manually bound** note that origin viewers witnessed Garran cross
but cannot see new activity after his arrival in the corridor. Use the
production prose rules except the whole-beat 150-word floor, plus the shared
Brazilian-Portuguese and no-dash instructions. Ask for JSON with exactly
three nonempty `units`, one per event in order, each 35–90 words. Each unit
must remain intelligible if another unit is omitted for a different viewer:
no dangling pronoun or sentence fragment may depend on an absent unit.
No post-render name filter is
applied to the units. Join them in order for the reader packet; no rewriting.

Run four independent direct `curl` calls against the configured provider,
in parallel. Retain exact requests, raw envelopes, response IDs, timings,
schema verdicts and assembled outputs. No retries or replacement calls.

**Technical gate:** all 4 HTTP responses have distinct IDs and satisfy the
current local JSON Schema: exactly three nonempty string units, no extra
fields. A technical failure stops admission; valid outputs may still be read
diagnostically.

**Content gate:** an isolated continuity reader sees the four assembled texts
shuffled, their individual units, the three accepted events and the
origin-viewer boundary, but not this hypothesis. Each assembly must convey Garran's completed crossing with a
clear referent, Elowen's care and stabilization prayer, and the second
tremor with the block's several-metre roll; it must add no inaccessible
post-arrival Garran action or consequential unsupported development. A
development is consequential if it changes an actor's action, location,
physical condition, an object's state, or what a witness can know; static
sensory rendering of the supplied scene is allowed. The reader checks each
unit alone for source coverage and for references that would fail if either
other unit were omitted.

A separate isolated fiction reader sees the same shuffled assemblies and
source events, without the hypothesis or code. At least three of four must
read as continuous Brazilian Portuguese fiction rather than three incident
reports. The reader must cite actual passages and answer whether adjacent
units repeat the same image, restart with inventory-like actor/place labels,
or expose a join that breaks scene flow. These are reading prompts, not
automatic string rules; a negative judgment needs a quoted reason. Reader
disagreement is preserved, not voted away.
The previous independent-unit assemblies and archived persisted prose are
reading controls, not paired experimental arms; no efficacy comparison is
claimed across different calls or readers.

**If both content readers' criteria and the technical gate pass**, the result supports only this one-call output
interface as a local feasibility candidate. Runtime work would still need
automatic event-to-move binding, origin and destination projections, an
incoming mover, an offstage-action negative control, and a check that
per-event units can carry a full turn's fiction without a new untyped
transition path. **If it fails**, reject this frozen interface for T6 and
retain the exact failure; do not loosen this gate after reading outputs.
