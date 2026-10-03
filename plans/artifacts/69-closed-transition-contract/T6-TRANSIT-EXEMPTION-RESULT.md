# T6 transit exemption: crossing preserved, content gate fails

The [frozen screen](T6-TRANSIT-EXEMPTION-PREREGISTRATION.md) replayed the
actual accepted `d5a2ccf0` T6 prose request four times per arm through direct
DeepSeek curl. A used the logged messages and current post-render offstage
filter. B appended a time-scoped reminder of Garran's already-confirmed
crossing and simulated an exemption from the name filter for that moved
actor while keeping the T6 origin audience unchanged. This is a **prompt plus
filter bundle**, not an ablation or a runtime implementation. The actual
archived request already contains the shared client's Brazilian-Portuguese
and JSON instructions, unlike the earlier synthetic fixture. All eight
requests were frozen before dispatch; each returned a distinct response ID
and a schema-valid `narration` object. None used the filter's empty-result
fallback.
Request audit correction: the archived **Director** prompt contains internal
character IDs with the roster that resolves them, as the current contract
deliberately allows. The archived **prose** request used in this replay has
no `C` identifiers; an earlier note incorrectly conflated the two prompts.
The replay is still one historical payload, not a production reliability
estimate.

A blind fiction reader received only the eight **filtered** texts, their
confirmed non-speech events and Garran's prior/new position. After unblinding:

| arm | reader found named, conveyed crossing | material finding |
|---|---:|---|
| A, current filter | 1/4 | In three outputs the saved text begins with `ele` or `suas botas` and lacks a named crossing. |
| B, transit exemption | 4/4 | `T6-B-1` narrates Garran raising a hand after arrival; `T6-B-3` describes his dust-covered shoulders after he disappears into the isolated corridor. |

The A exception is instructive. `T6-A-3` starts `Garran Holt cruza o vão` and
survives the current name filter. The archived failing raw sentence used
`instrutor Garran Holt`, matching the full canonical name `Instrutor Garran
Holt`; this A response used the shorter `Garran Holt`. The guard's behavior
thus depends on how the model writes the name, not only on whether the
crossing is authorized. A direct deterministic pair check with the T6 scene
and filter confirms this mechanism: `Instrutor Garran Holt cruza o vão. A
pedra range.` becomes `A pedra range.`, while `Garran Holt cruza o vão. A
pedra range.` remains intact. This establishes this exact string-dependent
case, not how often a model chooses either spelling.

B's clearest violation is `T6-B-1`: `Do outro lado, ele se ergue, ergue uma
das mãos acima da cabeça num gesto breve, e planta os pés no corredor`. The
accepted event authorizes reaching the other side, not a new hand signal
there. In the T6 scene graph, the origin salon has **no perception link** to
Garran's destination corridor after the crossing, and the origin audience's
confirmed events contain no such gesture. This is a failure under the
registered zero-new-action-after-arrival rule; whether a hand gesture would
be harmless in another scene is a different question. `T6-B-3` says Garran
disappears into the corridor, then describes dust settling on his shoulders
there. That is post-departure staging beyond this view. The same output gives
Maelis unconfirmed steps, but she remains in the origin cluster, so **her
movement is not evidence against the Garran filter exemption**. Other
reader complaints, such as a reference to Link's bag or the exact side of
scattered rubble, may be licensed by the older transcript or ambiguous
spatial wording and are **not** counted as decisive failures here.

The registered all-four B content gate fails. The candidate preserves the
selected crossing but also lets unconfirmed post-departure staging survive
in this real payload. This is a local boundary observation, not proof that
all paragraph-level exemptions fail or that the prompt change caused it. No
runtime prompt, guard or producer changed. The next candidate must bind
viewer-authorized event content to the transient actor more narrowly than
“exempt this mover for the whole paragraph,” while preserving a coherent
sentence chain and testing origin/destination audiences and real offstage
controls. This one crowded turn cannot certify that design.
