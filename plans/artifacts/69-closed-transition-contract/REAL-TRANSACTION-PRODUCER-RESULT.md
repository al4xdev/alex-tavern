# Real-source transaction producer screen stopped at both boundaries

The frozen [protocol](REAL-TRANSACTION-PRODUCER-PREREGISTRATION.md) selected
two archived Director beats: closed blue gate T38 (`F`) and legitimate
ajar-to-open main gates T8 (`P`). The source hashes, exact first request
bodies, script and schema are in `real-transaction-producer-manifest.json`;
raw curl envelopes, request bodies, distinct provider IDs, mechanical
rejections and outputs are preserved in `real-transaction-producer-runs/`.
Four independent chains ran per case, with one mechanical-error retry only
when permitted. **Eight first calls and two retries** were made. Six first
responses matched the JSON schema; both retries did too. The registered
all-call technical prerequisite failed, so there is **no aggregate semantic
pass** and no producer admission.

All four `F` chains failed individually. `F-3` and `F-4` omitted the required
`result` key in an aperture step, so they were schema-invalid and not retried.
`F-1` initially tried `ajar -> closed` although the gate was already closed;
its mechanical retry changed only the source state to `closed` and proposed
`closed -> closed`, which the durable-state validator rejected. Crucially,
both drafts also hid Téo's successful crossing in an `other` text step:
`Téo Ventobravo atravessa a fresta do portão azul e desaparece na penumbra do
túnel.` This is an observed hidden-action path: the operation validator
rejected the annotated closure, while an untyped crossing remained in the
proposed narrative. It does **not** satisfy the protocol's stronger falsifier
of a *mechanically accepted* final output hiding such an action, because this
chain was rejected mechanically.

`F-2` first proposed crossings through a closed gate. After mechanical
feedback it added a `closed -> ajar` opening, but still proposed a fresh
crossing for Liora, Nix, Mirella, Doran and Bruna, all already in the tunnel
at the committed start. The validator rejected the first such crossing;
an independent fiction reader also saw the repeated team passage in both
drafts. The attempt to reopen is not itself classified as impossible here:
the failure is the re-crossing and the absence of a complete, accepted
transaction.

All four `P` first responses were schema-valid and mechanically accepted an
`ajar -> open` transition. They preserved the guard's entry and collapse.
An independent fiction reader found that `P-1` omitted Maelis's order and
Garran's shield action; `P-2` omitted Maelis and changed Garran's shield to
`a espada erguida`; `P-4` omitted Maelis and Garran, replacing his action
with an unnamed shield that `cai com estrondo`. `P-3` kept the opening,
guard, Maelis's reported order and Garran pushing the shield. This is
local content loss on a legal control, not a model error rate. The reader
also called `pelos fundos`, smoke and louder alarm bells unsupported; the
source audit rejects those particular complaints: T8's accepted Maelis
event says `pelos fundos`, and its `scene_update` supplies smoke and bells.
These are omissions and substitutions in the **Director transaction lists**.
No Character agents were run for these candidates, so the screen cannot say
whether a final persisted turn would lack Maelis's speech. In the archived
source itself, her Character-authored words say `segure a entrada` while the
Director's speech intent says `feche a entrada`; those are separate layers,
and literal agreement between them is not a valid fidelity criterion.

There is a separate **harness defect** in every assembled `P` narration.
The deterministic sentence template pasted arbitrary model-authored `cause`
after `sob`, yielding phrases such as `Portões do salão se abrem sob forçados
de fora com um estrondo` and sometimes a doubled period. The source-step
content can be read, but these assembled sentences are not evidence that
the model itself writes ungrammatical prose. No post-hoc template edit or
replacement calls were made under the frozen protocol. The content gate
already fails on `F` and the positive-control omissions independent of this
template defect.

This screen uses manually seeded gate state and tracked positions. It shows
that the exact candidate contract neither kept physical claims exclusively
in typed steps nor retained the whole legal control, even with a mechanical
retry. It does not establish model incapacity, defect prevalence, or that a
different transaction interface would fail. No runtime code or persisted
session contract changed.
