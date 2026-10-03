# T6: post-render guard deletes a confirmed crossing and leaves an orphan pronoun

Source: `plans/artifacts/repetition-battery/base-P3-r2/sessions/d5a2ccf0/`.
`debug.jsonl` lines 65 and 67 hold the accepted Director decision and real
prose call for T6. `state.json` holds T5/T6 narration snapshots and the
persisted T6 prose. The content-only packet is
[`T6-GARRAN-CONTENT-PACKET.json`](T6-GARRAN-CONTENT-PACKET.json).

At T5, Garran (`C18` in internal state) stands `frente da mesa central`.
T6's accepted `zone_moves` puts him `corredor lateral parcialmente obstruído,
após o vão estreito`; its confirmed event states `O instrutor Garran
atravessa o vão estreito e se posiciona do outro lado`. The event uses
`subject_id="Narrator"`, **not** Garran's ID, despite naming him in its
content. The T6 prose request includes the event but omits Garran from the
post-move `IN THIS VIEW` roster and `CAST`.

The raw model response opens: `A poeira ainda flutua em suspensão quando o
instrutor Garran Holt projeta o corpo pelo vão estreito entre os escombros
...`. Its next sentence is `Do outro lado, ele firma as botas ...`. The
persisted narration **deletes the first sentence** and opens with the
second. An independent reader given only the events and two prose versions
found that the raw version conveys the crossing, while the persisted version
loses the only sentence that names the moving actor and shows the physical
crossing. `ele` and `Do outro lado` start without local antecedents. The
reader's additional complaint that both versions omitted Elowen's speech
is outside this finding: the renderer intentionally withholds spoken words.

This is not merely a model-output hypothesis. Replaying the current
`_strip_offstage_actors(raw, T6 scene snapshot, characters, controlled_id,
T6 audience)` returns **exactly** the 1,050-character persisted narration;
the raw text is 1,221 characters. Garran remains present in the scene but
is outside this viewer cluster after his move. The guard's exact full-name
pattern removes his first sentence, then its sentence split retains the
pronoun sentence. This source and deterministic reproduction establish the
local cause of the persisted omission. The deeper boundary is temporal: the
guard applies a **post-move cluster snapshot to prose about an interval that
includes the move**. The raw response's action can be read
as a completed event of this beat even though the roster governs present
actions; its inclusion alone is not evidence of an offstage leak.

Request audit correction: this archived **prose** request has no internal
character IDs. The companion **Director** request does use IDs with a
resolving roster, which the current contract deliberately permits. An
earlier note conflated them; that warning is withdrawn. The case supplies
a historical crossing and a current-filter reproduction, not a prevalence
estimate.

A safe fix cannot simply disable the offstage guard: that guard also protects
against unconfirmed **later** actions by absent characters. This case also
shows why `subject_id` alone is not a sufficient exemption for the current
contract: the crossing event is Narrator-subject while the mover is Garran.
A future candidate needs a preregistered decision rule and tests on the real
T6 origin and destination audiences, a genuine unconfirmed offstage-action
control, an actor entering a cluster, and a pronoun-after-removal case.
Preserving Garran's event must not duplicate it for another audience or
license new actions after he leaves. No code changed as a result of this
finding.
