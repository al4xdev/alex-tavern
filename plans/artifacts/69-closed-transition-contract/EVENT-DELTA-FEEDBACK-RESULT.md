# Event-delta full-draft screen incomplete; valid drafts expose mixed fidelity

The [frozen protocol](EVENT-DELTA-FEEDBACK-PREREGISTRATION.md) compared the
archived T38 three-label retry (`A`) against an otherwise identical request
with `aperture_delta=none` added (`B`). A separate T8 packet (`P`) tested a
legal `ajar -> open` gate event and retention of its adjacent guard, Maelis
and Garran actions. The source and script hashes, exact request bodies and
Narrator schema are in `event-delta-feedback-manifest.json`; all curl
requests, raw envelopes, provider IDs and parsed outcomes are preserved in
`event-delta-feedback-runs/`.

There were **12 direct curls**, with distinct provider IDs. A and B each had
4/4 HTTP 200, full-schema-valid outputs. P had 3/4: `P-1` returned HTTP 200
but malformed JSON, with a semicolon after the `scene_update.entrada` value
where a comma was required. It was retained and not retried. **The registered
all-12 technical prerequisite failed, so there is no aggregate semantic
pass or comparative admission.** The remaining outputs support only
individual diagnostic reads.

An independent reader saw eight shuffled T38 drafts without A/B labels,
alongside the committed T37 ending and Téo's last attempt. After unblinding,
it found a new blue-gate closure in A-1 through A-4 and B-3/B-4. B-1 and
B-2 instead described the gate as already closed and kept Téo in the hall
without another closure. All eight drafts blocked Téo and left the five
teammates in the blue tunnel; none proposed a `zone_moves` entry for Téo.
Thus the valid T38 drafts contain two locally coherent B examples, but the
frozen rule demanded B **4/4** and the total technical gate already failed.
No causal claim or reliability estimate follows from the 2-versus-0 read.

The three valid legal-opening rewrites show mixed fidelity **within the
Director proposals**. All three open the previously ajar main gates and
retain the guard's entry and collapse. P-2 changes Garran's shield handling
by handing the shield to someone else. P-3 omits the proposed shield action,
adds a sword and drops Garran's proposed shout. P-4 omits the Director's
Maelis speech-intent event and shield action, assigning Garran a new
evacuation speech intent instead. P-4 still routes Maelis as a next speaker;
no Character call was run, so the final turn cannot be called silent on
Maelis's order. Likewise P-3's proposed `segure a entrada` differs from the
archived Director proposal's `feche a entrada`, but matches the **actual
Maelis Character speech** in that source turn. It is not scored as lost
meaning. A second source-layer read prompted this correction; its claim
that P-3 explicitly said Garran had *no* shield is unsupported by the raw
draft, which merely omits shield handling. P has no paired no-delta arm,
and no loss can be attributed to that field.

The four B drafts show that adding `aperture_delta=none` to a final state did
not consistently prevent narration of the prior closure on this beat. The P
Director rewrites retained the opening but did not all retain adjacent
proposed actions; without a paired P arm or Character execution, the delta
field cannot be blamed for that drift, nor can a final-turn loss be inferred.
The archived
T38 rejected draft and T8 accepted draft were supplied as uncommitted
assistant messages in an offline test; no session was modified. The gate and
actor were manually selected, no automatic delta producer or renderer was
exercised, and no production code or persisted session schema changed.
