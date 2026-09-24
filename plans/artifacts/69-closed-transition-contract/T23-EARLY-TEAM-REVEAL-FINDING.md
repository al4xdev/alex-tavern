# T23 early-render claim withdrawn, source correction 2026-09-24

**WITHDRAWN:** the earlier version of this finding said the T23 renderer invented the second team's plaque reveal before the Director accepted it. That conclusion came from reading only `perception_events` and `scene_update` in the T23 Director response. It omitted the same response's `time_skip_summary`, so the text-only reader received an incomplete accepted-event packet. Its chronology verdict cannot validate the early-render claim.

The complete T23 Director response (archived `p1-archive/07218133` debug line 210) has `time_skip_ticks: 1` and `time_skip_summary: "A diretora vira mais três placas, revelando os nomes de Asword, Bruna Ferrugem e Téo Ventobravo, e anuncia a composição da segunda equipe sem que Liora interrompa."` The Runner records that skip at debug line 211. The **actual T23 prose request** at line 212 includes the summary as a `CONFIRMED EVENTS OF THIS BEAT` observation, alongside Liora's step. Both the first and retried T23 prose render an event that was explicitly supplied as confirmed; the T23 renderer did not anticipate it on its own. The T23 `scene_update` does not record the new team, but that alone is a separate state-capture question, not proof of renderer invention.

T24's accepted Director output (line 214) again announces the same three names, turns their plaques, and sets `scene_update.selection_status` to the second team formed; the persisted T24 narration repeats the act. This is a **source-observed repeat across Director beats**, with the T23 time-skip summary as its earlier accepted occurrence. It may be relevant to Task 69's duplicate-event boundary. Whether the time-skip summary should have updated durable state, or why the Director repeated the reveal, remains undiagnosed. No prevalence, renderer-fidelity failure or retry effect follows from this sequence.

The old [three-turn source packet](T23-TEAM-CHRONOLOGY-SOURCE-PACKET.txt) is retained as evidence of the faulty method: it omitted the `time_skip_summary` and the actual prose request. Future event packets must include every event the renderer received, including time-skip summaries, before a prose-fidelity judgment.

The [corrected two-turn packet](T23-TEAM-CHRONOLOGY-CORRECTED-PACKET.txt) includes the summary and the exact confirmed-events block sent to prose.
An independent text-only reader of that corrected packet agreed that T23 prose
renders a supplied confirmed event and that T24 narrates the same plaque reveal
again. The remaining uncertainty is the intended timing of a time-compressed
event versus a new live action at T24; the source text alone cannot assign a
mechanism.
