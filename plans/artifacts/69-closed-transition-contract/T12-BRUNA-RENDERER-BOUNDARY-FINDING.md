# Real T12 crossing: post-move roster leaves beat time ambiguous

Source: `plans/artifacts/repetition-battery/base-P1-r1/sessions/ea6620fb/`
`debug.jsonl` line 145 is the accepted Director call for T12; line 146 is
the real prose request and response. The saved `state.json` contains the
T11/T12 scene snapshots and persisted T12 narration.

The T11 narration snapshot places Bruna (`C8`, internal source identifier)
at `passagem estreita, avançando`. T12's accepted `zone_moves` places `C8`
at `novo corredor, mais à frente`; its confirmed `physical_outcome` says
`Bruna atravessa a passagem ... e chega ao outro lado`. The T12 narration
snapshot has the new position. Bruna is absent from the T12 narration
audience, which is the remaining perception cluster.

In the actual T12 prose user message, `IN THIS VIEW` says it lists **“the
only people whose PRESENT actions you may narrate”** and omits Bruna. `CAST`
also has no Bruna entry (another character's outfit mentions her name, but
does not supply her appearance). The same message's `CONFIRMED EVENTS OF
THIS BEAT` includes Bruna's complete crossing. This is a **source-observed
time-scope ambiguity**: the renderer must depict a crossing witnessed during
the beat, while its roster describes who may be shown acting in the present
after the move. A reader can treat the crossing as a completed event of this
beat and the roster as a restriction on subsequent actions; the prompt does
not spell out that distinction. The absent `CAST` entry is an appearance
information gap, not a prohibition on mentioning Bruna.

The actual raw prose response **did** narrate Bruna crossing, and the saved
T12 narration is byte-identical to that raw text. This turn therefore shows
this prompt shape in production and a locally successful crossing render,
**not** a fiction failure caused by the roster. It cannot establish
how often the conflict occurs or which instruction the model follows in
other scenes. The case is structurally closer to the intended boundary than
the synthetic time-packet fixture, which supplied `viewers` manually, but
the T12 scene also has a collapsing beam, multiple moves and a dense prior
transcript; it is not a clean one-variable control for prompt causality.
