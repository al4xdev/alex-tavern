# Model-only V4 Pro prose reviewer: local gate failed

Status: FAILED. The model-only challenger detects the retained missing inspection
in all four draws, but rejects the sensory control three times and leaves material reading disputes. No app model
setting changed, no reviewer activated, no earlier failure rescored. Task69 and
remaining roadmap requirements are still open.

1. MEASURED DeepSeek execution:20 logical reviews,20 curl attempts, all HTTP200, distinct
response IDs, finish_reason stop, reasoning present, schema-valid and boolean/
issues-consistent on first attempt. No transport/schema retry, semantic resampling,
new producer generation or persisted story mutation. Four independent calls ran
concurrently. All frozen hashes and runtime request equality verified after calls.
Every current builder request equals its retained Flash HTTP JSON object except
'model': deepseek-v4-pro. Historical source/prose snapshots were preserved;
current source freezing and request equality guard the reviewer boundary despite
the owner's unrelated roteiro event-description edit. This does not claim the
whole checkout is unchanged or infer the models' internal implementation.

2. OBSERVED primary reading of every source/prose/decision pair:

| Retained condition | Fresh Pro judgments | Prior Flash judgments |
| --- | --- | --- |
| Complete prose | Accepted4/4, empty issues | Accepted4/4 |
| Missing admitted inspection, counterfactual complete source | Inspection detected4/4, rejected4/4 | Detected3/4; accepted one |
| Added green opening/Bento courtyard crossing | Unsupported outcomes identified4/4 | Identified4/4 |
| Neutral cold draft | Accepted1/4; rejected r4-2/r4-3/r4-4 | Accepted2/4; rejected two |
| Four retained fresh-render controls | Each accepted once, empty issues | Each accepted once |

Flash numbers are the existing failed screen, not new paired contemporaneous
calls. This small descriptive contrast is not a comparative reliability rate,
a causal model-scale effect, or proof that Pro is generally better/worse.
Fresh-render controls have n=1 review each; no fresh render occurred here and
those four decisions cannot estimate repeat variance. Counterfactual missing
prose originally followed an incomplete Director; changing its required admitted
events is a canary, not an actual new generation.

3. OBSERVED disputed sensory rejection: r4-2/r4-3/r4-4 explicitly treat 'Um sopro de ar frio
varre o salão, carregando cheiro de terra molhada e ferro' as a new ventania or
physical transition. The sentence changes no aperture or actor position, and
Bento already supplies the blue-opening cause. Neutral compatible sensory
expansion was allowed before calls. The retained reasoning considers that
allowance and then chooses the stricter interpretation: this is not evidence
that the allowance was absent, context truncated or reasoning disabled.
The primary reading treats these as false rejections. Blinded Gemini
reader24b9d5eab318 instead reports a material ambiguity: whether the negative
source clause excludes storms/causal drivers or all noticeable air currents.
This disagreement is not resolved by votes or model authority; it prevents a
local pass independently of accepting either classification. Model substitution
alone did not establish the predeclared component admission boundary.

4. OBSERVED additional objection in r2-3: besides the grounded missing inspection,
the reviewer says 'sombras dos dois vultos que ali permanecem' is a position
contradiction because Téo's crossing appears in the next paragraph. The primary
reading finds that inference unsupported: mentioning the shadows of the two
remaining figures does not assert there are only two people before crossing,
and a single beat's prose may describe the remaining pair before focusing on
Téo's departure. The registered rule does not require every narrated instant to
equal final state, nor does it mandate paragraph-by-paragraph timestamping.
Reader24b9d5eab318 considers a chronological leak plausible and initially calls
the objection grounded, but also records the alternate framing as unresolved.
The source does not impose paragraph-by-paragraph timestamps or require all
characters to cast shadows in each sentence. This issue is retained as disputed,
separately from the correctly detected inspection; correct rejection cannot
automatically validate every accompanying issue.

5. Configuration/checks: V4 Pro thinking enabled/high, cap16384, timeout180,
same reviewer system/schema/client/adapter, existing maximum3 transport/JSON/
schema attempts available but unused. Probe passed Ruff lint/format before
freeze. No production implementation changed, so no new production test suite
is claimed. Curl credentials were supplied only through stdin; requests, HTTP
responses, errors/reasoning, results and blinded reader packet remain in ignored
local evidence. Logs isolated under /tmp/alex-tavern-prose-challenger; real .data
read only for credentials. Source requests and prose are exact retained inputs. Reader24b9d5eab318
received eight shuffled pairs without model/expected labels or reasoning;
focused screenwriter-reader850017a8b8ad received only the two disputed pairs
and reviewer instruction, without prior verdicts.

6. OBSERVED unresolved reader disagreement: the focused reader considers the
sensory and shadow objections optional literal readings rather than necessary
physical contradictions. It also invents pressure/temperature facts and quotes
an unsupported tunnel description; those premises and its physical explanation
are rejected. Its favorable verdict is not accepted as proof or used to override
the first reader. The primary interpretation remains that cold breath need not
be a gale and shadows of two figures need not enumerate the entire hall, but
these are text readings, not mechanically established ground truth. The source's
weather wording and prose staging leave disagreement unresolved in this screen.
That independently fails the preregistered ambiguity rule. No resampling,
retrospective acceptance or majority arbitration occurred.

Two separate Gemini reader invocations evaluated8 and2 pairs respectively;
pairs are not separate calls. They used server-configured AGY, not the frozen
DeepSeek curl transport. Protocol/report critics are additional text-only
invocations, recorded by their run IDs;20 counts the DeepSeek challenger reviews,
not all model use during the work. Full provider envelopes/settings for AGY are
not controlled by this probe; prompts/results remain in ignored local evidence.

7. THEORY next intervention, not yet frozen: first test an explicit source-scope
clarification that distinguishes the old aperture-changing storm from compatible
sensory air movement, retaining the prohibition on new storm/portal-change causes.
This changes source representation and supplied scope information; it must not
be called a model-only or schema-only contrast. Keep the retained texts and
defect controls, freeze a new protocol, and test before adopting the wording.
Explicit per-event evidence extraction with a separate additions check remains
a different hypothesis for later; changing both together cannot attribute a gain.
Neither proposal is already proved. A component pass still requires fresh cases,
upstream admission and real transaction/recovery tests before activation.

Task69 closure is defined by its actual requirements: input reconciliation of
already satisfied anchors, cross-submission repeat coverage, live ceiling-family
cluster/read evidence, and a written disposition of semantic comparison remain
unchecked. This local reviewer is one candidate path toward those requirements,
not a new universal prose-verification requirement or a substitute for them.
The failed candidate cannot activate; it does not justify closing the task or
requiring an owner decision on a scope already specified.

Protocol review b80c0925f8fc preceded the pause; reconstruction review
1bec8f46078c clarified source freezing and text-based dispute stopping before
calls. The prior report a16263d records the Flash failure. A new source-scope
clarification must be distinguished from evidence-schema decomposition: changing
both together cannot identify which intervention mattered. These diagnostics
serve the durable-state/beat work; no universal prose verifier is required as a
substitute for Task69's actual physical-family and live continuity requirements.

Report critic e64714ff1056: preserved its concern about using a hallucinating
reader to settle a dispute by leaving the dispute unresolved. Clarified separate
DeepSeek/AGY ledgers; its assertion of10 additional calls confuses pairs with
invocations and is not adopted. Its request for a new owner scope decision is
not adopted: the existing task specifies the closure requirements. No physical
necessity linking opening to a cold draft, model-scale cause or proven cure by
schema decomposition is claimed.
