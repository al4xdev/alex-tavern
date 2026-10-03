# T6 confirmed units preserve the crossing but need prose craft

This is a **deterministic content read**, not an LLM replay or a proposed
runtime implementation. From accepted `d5a2ccf0` T6, three non-speech
perception events whose existing `witness_ids` include the origin audience
were kept in order and joined as separate paragraphs, with no rewrite or
offstage filter. The exact source units, assembled text and actual persisted
narration are preserved in
[`T6-EVENT-UNITS-CONTENT-PACKET.json`](T6-EVENT-UNITS-CONTENT-PACKET.json).

An independent fiction-only reader found the assembled text clearly conveys
Garran crossing, Elowen tending Cael and the later tremor/block fall; it has
no orphan pronoun. But the reader judged it a functional draft or incident
report rather than immersive RPG narration: three event paragraphs cut
between locations abruptly, and Elowen's sequence reads as a list of verbs.
The actual persisted prose has more sensory rhythm yet opens with `Do outro
lado, ele...` after the crossing sentence was removed. The comparison does
not establish that every sensory detail in the persisted version is false:
some may be supported by the prior transcript or visible scene.

For this one beat, this reader did **not** find unchanged event-content
concatenation good enough as finished fiction. It does not rule out different
paragraph joining or better Director event prose on other beats. One
candidate to test is **reader-ready event units authored at the confirmed
event boundary**, each carrying its own audience and movement binding before
assembly, without a later free rewrite. That remains a theory: no producer
has been shown to author such units reliably, and fragmentation might itself
harm fluency. No origin/destination pair has been tested, and no runtime path
has changed. The T6 event's existing `subject_id=Narrator` cannot identify
Garran as the mover from that field alone; a future contract might need an
explicit event-to-move binding, but a deterministic binding from turn-level
state may be possible without model-authored IDs.
