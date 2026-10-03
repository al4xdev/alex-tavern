# Two-stage closure admission: frozen before provider calls

The [one-call two-channel checker](TWO-CHANNEL-CHECKER-RESULT.md) was technically
valid (32/32) but failed to judge an offered closure independently when the
same request also contained a later correction or reopening. This candidate
separates those readings into two independent model calls. It tests a
manually bound closure **assertion**, not final durable state or renderer repair.

**Stage A, offered-evidence entailment:** input contains only `subject`, a
positive claim and ordered literal `offered_support`. No `complete_events`,
prior state, Director update, expected label, character IDs, Stage B output or
later narration. Output is `verdict: entailed|insufficient|contradicted` plus
literal `support` excerpts. `entailed` requires both target identity and a
completed closing action in the offered text. Narratorial present tense such
as `O portão azul se fecha com um baque`, when it depicts the completed impact,
counts as an assertion of closure; future warnings, a static sealed gate and
generic `o portão` without resolved identity do not. An `entailed` result needs
a nonempty literal quote from the offer. Negative verdicts may include literal
offered passages explaining rejection or an empty list.

**Stage B, source retraction:** input contains the same named subject and claim
plus the full ordered Director `perception_events[].content` and
`time_skip_summary`. It does **not** receive Stage A's passages, verdict or
reasoning. Output is `retracted: boolean` and literal `evidence_quote` from the
complete source when true; empty quote when false. Retraction means the source
explicitly corrects the claim so that the closure **never happened**. A later
reopening is a separate physical event, not a retroactive denial. The stage
does not decide final aperture or whether the prior durable state already had
the gate closed. A future warning with no narrated closure is **not** a
retraction; `retracted=false` means only "no explicit correction found", not
"the closure occurred".

Freeze seven distinct Stage A requests (four calls each):

| Packet | Offered text | Expected |
| --- | --- | --- |
| `t38_explicit` | archived explicit present-tense blue-gate closure | entailed |
| `t37_bare` | archived bare `o portão se fecha` fragment | not entailed |
| `t37_with_antecedent` | archived blue-gate antecedent plus time-skip closure | not entailed under the independent content read below |
| `t36_future` | archived five-second warning about blue gate | not entailed |
| `t38_weak` | archived static green gate offered for blue claim | not entailed |
| `wrong_target` | archived blue closure offered for green claim | not entailed |
| `synthetic_common` | synthetic `O portão azul se fecha com um baque.` | entailed |

An isolated content reader **before these calls** judged the two T37 antecedent
passages ambiguous: `o portão` could be a main access sealing all groups rather
than unambiguously the blue gate. The packet is therefore a negative identity
control, not a manufactured positive. `not entailed` permits `insufficient` or
`contradicted` for the admission decision; individual reasons are retained.

Freeze six independent Stage B source requests (four calls each): archived
T38 blue closure, archived T37 blue time-skip closure, archived T36 future
warning, synthetic common closure alone, **the identical synthetic closure
followed by an explicit correction that it never closed**, and **the identical
synthetic closure followed by a real reopening**. Expected `retracted` is
false for the first four and for reopening; true only for correction. The
synthetic correction/reopening/plain cases reuse the **same four Stage A
outputs from one byte-identical request**. They are not counted as three
independent Stage A cases. Stage B's inputs differ only in their complete
event sequences; it receives neither A results nor A passages.

Freeze both final prompts, schema, 13 exact request bodies,
source/script/preregistration hashes and configured DeepSeek V4 Flash settings
before calling. Use direct curl, `json_object`, thinking disabled, with no
temperature/top-p/seed override. Four fresh calls per request body, **52
total**, no retry or replacement. Save every request, raw envelope, provider
ID, HTTP/transport status, parsed output and grade. Secrets enter curl-config
stdin. No private ID enters any prompt.

Technical prerequisite: all 52 calls HTTP 200, distinct IDs, schema valid;
Stage A support quotes, when present, must be literal substrings of offered
passages, and `entailed` requires at least one. Stage B `retracted=true`
requires a nonempty literal quote from the complete source; false Stage B uses
an empty quote.
Otherwise the screen is incomplete and neither stage earns a semantic pass.
If technically valid, each Stage A bundle must match its frozen admission
label in 4/4 and each Stage B source must match its retraction label in 4/4.
Report Stage A and Stage B gates separately; the overall candidate meets its
local rule only if both stage gates pass. There is no one-to-one pairing or
pooled event-acceptance rate for the independent controls. An isolated
content-only reader, blinded to labels, inspects any disputed positive or
retraction against its actual input and records a specific falsifier; it does
not replace failed calls or change the frozen thresholds.

Any explicit present-tense closure missed by A, generic/future/wrong-target
offer admitted by A, or correction and reopening confused by B stops this
candidate. A pass would establish only these manually bound occurrence
boundaries. It would **not** justify persisting final `closed` after the
reopening beat, infer automatic target binding, or authorize Runner integration.
