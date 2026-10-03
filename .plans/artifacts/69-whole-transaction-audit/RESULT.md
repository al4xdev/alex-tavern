# Whole-transaction auditor: candidate stopped

The frozen high-thinking auditor did not meet its preregistered gate: all 36
logical calls had to terminate valid, match the frozen status and survive
whole-content reading without unsupported or incomplete findings. See
[PREREGISTRATION.md](PREREGISTRATION.md). Do not
integrate this candidate into the Director or infer Task 69 completion. This is
a diagnosis screen over controlled source/transaction packets, not a persisted
Runner or prose-quality test. No runtime code changed.

## 1. Observed execution, with all failures retained

Nine packets each received four logical calls to DeepSeek V4 Flash, thinking
high, maximum 8192 output tokens. The actual JSON client/adapter used curl;
only its existing maximum-three-attempt transport/envelope/JSON/schema policy
could retry. No semantic feedback or replacement logical calls were used.
Frozen source, protocol, schema and exact-request hashes still match.

| Controlled packet | First-attempt valid / 4 | Terminal valid / 4 | Raw attempts | Frozen status matched / 4 |
| --- | ---: | ---: | ---: | ---: |
| Continuing closed observation + blocked attempt | 4 | 4 | 4 | 4 |
| Hidden blue opening AND Téo crossing | 4 | 4 | 4 | 4 |
| Fresh closure of already closed blue portal | 4 | 4 | 4 | 4 |
| Legal opening + wounded guard/order/shield | 1 | 4 | 7 | 4 |
| Supported reopening + crossing | 1 | 2 | 10 | 2 |
| Green opening hidden in blue cause | 4 | 4 | 4 | 4 |
| Independent events reordered | 4 | 4 | 4 | 4 |
| Supported opening/crossing reduced to ajar/blocked | 0 | 1 | 12 | 1 |
| Door identity explicitly unknown | 2 | 4 | 6 | 0 |

Observed counts: 24/36 first-attempt valid; 31/36 terminal schema-valid,
decision-consistent and literal-quote-valid. All 55 raw attempts returned HTTP
200 with distinct response IDs and nonempty provider reasoning. Of these,
31 ended with `stop` and valid JSON; 24 ended with `length` at 8192 completion
tokens. Twenty-two truncated attempts had no final content, two had incomplete
content. Five logical calls exhausted all attempts: reopening repeats 1/3 and
source-loss repeats 1/3/4. Their recorded terminal failure is token-limit truncation, not an HTTP error;
this does not establish why deliberation consumed the available output.
Quoted evidence proves provenance, not that findings are substantively correct.
The nine controlled packets are the analysis units; repeated draws here do not
estimate a population defect rate or demonstrate an effect of reasoning.

## 2. Content reading found defects beyond status matching

Three blinded Gemini readers received whole sources, transactions and all 31
terminal reports, without expected labels or earlier judgments: `2d3e11b58e57`
(packets 1–3), `169b996038c2` (4–6), `c70bea1351d2` (7–9). Main reading checked
their objections against literal reports. A second isolated reader,
`6eb48be8e0f9`, received actual auditor instructions plus disputed existing
packets/reports, without prior verdicts.

Observed: all four hidden-opening/crossing reports identified BOTH physical
claims, and all four hidden-cause reports identified the green opening.
Permission was defensible in the twelve delivered clean continuing-state,
guard-entry and independent-order reports and the two delivered reopening
reports. These are local readings, not guarantees for future scenes.

Observed: hidden-opening repeat 1 and hidden-reclosure repeat 1 also alleged
uncertainty in Bento's unchanged speech intent, `Bento pede que Téo pare de
forçar a folha.` Their explanation demanded a physical identity for `a folha`.
The sentence is copied from the proposed beat and declares no physical state
change. Both independent readings and main reading found these additional
allegations unwarranted. The refusal still had a grounded physical reason;
the extra findings nevertheless violate the gate against unsupported findings.

Observed: the sole delivered source-loss report quoted `intervenção nova
suficiente para abrir a passagem` against `blocked` and correctly questioned
that result. It did not explicitly identify the lost `Téo atravessa para o
túnel.` or separately address why the recorded opening stopped at `ajar`.
Both readers found the crossing diagnosis incomplete. Main reading treats
this as incomplete coverage, without demanding a particular issue count or
category: a combined finding could have covered both meanings. The source's
declared attempt has actor/target but no intent, so using the proposed beat
to establish what attempt must be preserved also deserves clarification.

## 3. The ambiguous-door status counter is not evidence of misbinding

The frozen expectation was `uncertain`; all four final reports instead derived
`reject` from an `untyped_change` issue, one also retaining an uncertainty.
Thus the mechanical status comparison remains 0/4; it is not retroactively
changed to a pass. But its interpretation as four semantic errors is withdrawn:
these reports explicitly acknowledge unknown identity and do not bind the door
to blue or green. They question the closure's missing typed operation, initial
state or supported cause, separately from identity.

The initial pre-call reader had endorsed `uncertain`; the two later readers
found refusal defensible. Main reading finds an unresolved policy scope:
the system forbids extra TRACKED changes in `other`, while the category says
`extra untyped change` more broadly, and the source places closure only in an
uncommitted proposed beat. Whether an unregistered door needs typing and what
support is required for proposed new events were not cleanly isolated. Absence
of a supplied cause for an unknown door does not prove physical impossibility.
Do not call this a demonstrated identity hallucination or a calibrated
uncertainty failure. The original gate still fails on exhaustion and unsupported
findings even if this fixture's expected label was defective.

## 4. Emitted reasoning is evidence of deliberation, not causal diagnosis

Observed in reopening repeat 1 attempt 2: the provider explanation says the
transaction might be clean, then says `But hmm, 'diagnose all independent
problems' suggests there are some.` Its third attempt debates whether the
uncommitted proposed crossing counts as support despite the typed opening.
This packet's input was 1098 tokens; all three attempts exhausted the 8192
output ceiling without final JSON. Prompt wording and source-role ambiguity
are hypotheses for a future controlled contrast, not established causes of
the truncation. A larger budget has not been tested as a fix for either truncation or the two
unsupported speech-identity findings. No word-count compliance was tested.

## 5. Decision and reproducibility

Stop this exact candidate. The next experiment should separately define
committed facts, supported new causes and permitted proposed outcomes, and
isolate unknown identity from an independently unsupported new transition.
Preregister it before new provider calls; retain this failed gate. No auditor
was admitted to runtime, no automatic repair was implemented, and no roadmap
closure follows from these packets.

Local evidence: `manifest.json`, `graded-results.json`, all request/raw/transport
files under `runs/`, and the isolated debug data root `/tmp/alex-tavern-whole-audit`.
Raw JSON is ignored/local, not durable tracked evidence. Tracked protocol/script
and this report preserve the method and bounded findings; reproducing new
stochastic outputs is not expected to give identical counts.

Validation: offline `validate` completed over all 36 results; all frozen hashes
match; Ruff lint passed. Execute the script with an isolated `ROLEPLAY_DATA_DIR`
and `PYTHONPATH=.`. Ruff 0.16.10 format-check requests one line-wrap change in
the frozen `literal` helper; that unchanged frozen artifact is intentionally
preserved and the formatting check is not claimed green. No runtime Python was
modified, so the earlier 1229-pass runtime suite was not rerun for this artifact.

Report critic `b2433bad6d46` retained the stop decision, bounded counts,
unsupported speech findings and missing crossing diagnosis. Its objection to
`output-budget failures` was addressed by naming observed token-limit truncation
without inferring its cause. Clean-control readings and hash/lint checks are
retained despite its NEUTRAL verdicts: they document false-veto controls and
frozen-experiment integrity, rather than reassurance. Its suggestion that the
truncations are “almost certainly infinite deliberation loops” is unsupported
by this contrast and is not adopted. The untested higher-budget counterfactual
is explicitly removed even though the critic had accepted it.
