# Field descriptions: local result, 2026-10-03

Owner requested a controlled test of semantic field descriptions and a check of model-change quality gates. No runtime prompt/schema or provider configuration was changed; the candidate is in screen.py. Roadmap goal remains paused.

OBSERVED: 36 direct curl calls, four per fixture/arm, all HTTP200 locally schema-valid with distinct nonempty provider IDs per cell. The control used the actual current production builder. Both enhanced arms removed the same old field prose and supplied identical explicit definitions; text_contract used a field block in the system prompt, schema_contract used JSON Schema descriptions. DeepSeek serialized those descriptions into the system message: this tests instruction placement/wrapping, not semantic enforcement by a validator. Verified adapted requests: same story input and structural schema; each candidate definition appears once.

Local act_completed mismatches against confirmed current-act exit, out of four calls per cell:

| Fixture | Production | Explicit text | Schema descriptions |
| --- | --- | --- | --- |
| Closure attempt failed; expected false | 3 | 0 | 0 |
| Portal closed, still in hall; expected true | 1 | 1 | 3 |
| Portal closed, already in canyon; expected true | 1 | 4 | 4 |

These are selected fixture observations, not a population rate or proof of instruction-location effects. Both enhanced arms fail the preregistered gate. No adoption follows. The improved negative case does not establish reliable completion semantics; all four departure replies in either enhanced arm denied the already-confirmed old-act exit.

OBSERVED semantic counterexample: portal_left-schema_contract-1 has act_completed=false and says 'A passagem se alarga visivelmente' despite input confirming that the portal closed, the runes extinguished, both actors are in the canyon and no return passage is open. Its output explicitly acknowledges 'runas apagadas' while extending their instability into the canyon. The completion error is direct; the continuing open-passage premise has no separately introduced reopening in this proposal. portal_closed-schema_contract-2 says 'Com a passagem recém selada' but still returns act_completed=false. JSON validity alone misses these problems.

An isolated text evaluator examined all 36 proposals with randomized labels and source facts. Its supported flag failures agree with the direct flag check, but several added interpretations are rejected: map damage caused by physical events is not automatically an agency violation; generated beat_id prefixes are not reliable act evidence; output alone cannot prove the model interpreted act_completed as next-act completion. A new second opening, explicitly caused reversal or future exit target is not itself a violation. Retain raw review and mappings; do not quote its unsupported causal explanation as established.

The earlier owner-requested label-only screen also finished: 24 attempts, one transport timeout leaves portal_closed-control with only three valid replies and comparison incomplete. Other cells had four valid distinct-ID replies. Candidate flag errors: failed attempt 1/4, closed hall 0/4, closed/departed 2/4. Production comparator: 3/4, 0/3 valid, 2/4. Valid failures suffice to reject the label-only candidate; incomplete comparison gives no efficacy claim. Review objections based on arbitrary beat-ID structure or treating every prospective closure as a realized contradiction are not accepted; the independent act_completed mismatch remains decisive.

OBSERVED code/document boundary: tools/playtest_harness.py and tools/README.md provide repeatable scenarios and controlled model A/B comparisons with simple deterministic signals plus raw evidence for reading. PUT /config in src/main.py persists configuration and replaces Runner without a narrative-quality evaluation. Therefore there is comparison infrastructure, not an automatic narrative-quality gate preventing a model switch. No claim that every roadmap acceptance criterion is executable or that model quality is guaranteed by pytest.

Remaining hypotheses include interaction with unchanged input/STATUS and a problem in the new wording itself. This screen does not identify their contributions or prove that descriptions cannot help. Any subsequent test must separate these factors rather than assume the input is the cause. No larger architecture change or model switch was made.

Result-critic disposition: the candidate fails this preregistered zero-failure admission screen, not a universal test of field descriptions. Retain that scope explicitly. Reject claims that these outputs demonstrate strict obedience or a calibrated conservative threshold: their false answers contradict confirmed exits and the proposed definition. Reject treating local observations as significant improvements, pooling fixtures into an efficacy rate, or arguing that grammar constraints enforce the meaning of descriptions. Reject the allegation that rejection used an unstated threshold; the threshold was written before execution. One valid counterexample disproves that the candidate passed the registered clean-output gate, without attributing its cause to schema placement.
