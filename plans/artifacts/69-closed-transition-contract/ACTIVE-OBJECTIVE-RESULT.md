# Active-only physical-objective diagnostic result

Date: 2026-09-21

## Decision

Under the five requirements reproduced below, the active-only catalogue
candidate does not advance to activation-resolver design: conditions 3 and 5
fail. No roteiro schema or activation resolver for this candidate follows from
this diagnostic.

This is a result for two frozen requests from one session, four calls per arm
and one blind reader batch. It is not an estimate of model reliability and does
not show that every active-only catalogue shape will fail.

## Execution

The five frozen arms were C1-A/F/G and C2-A/G. Four fresh DeepSeek V4 Flash
calls were made per arm. The execution record in
`active-objective-screen/mechanical-results.json` reports `condition_1: true`,
`f_technical_precondition: true` and zero invalid observations across its 20
rows. Its candidate-label rows record all four C1-F calls as
`test_artifact_damaged`, all four C1-G calls as `none`, and C2-G as one
`test_artifact_damaged` plus three `none`.

The 20 beat objects were shuffled with the preregistered seed and sent in one
opaque batch to the isolated reader. Its run ID was `dd9bdb9aab32`.
`blind-analysis.json` contains 20 rows and 20 distinct IDs from `item_01` through
`item_20`, which is the parser's successful fixed-contract output.

Here `valid` means curl return code zero, HTTP 200, a parseable
`choices[0].message.content`, and conformance to the complete embedded arm
schema. This compact audit joins the mechanical record to the blind rows after
the reader response was saved:

| context | arm | run | valid | label | prose objective | intrusion | agency | contradiction | sequence |
|---|---|---:|---|---|---|---:|---:|---:|---:|
| C1 | A | 1 | yes | n/a | none | yes | no | no | no |
| C1 | A | 2 | yes | n/a | none | no | no | no | no |
| C1 | A | 3 | yes | n/a | none | yes | no | no | no |
| C1 | A | 4 | yes | n/a | none | no | no | no | no |
| C1 | F | 1 | yes | test_artifact_damaged | none | yes | no | no | no |
| C1 | F | 2 | yes | test_artifact_damaged | test_artifact_damaged | yes | no | no | no |
| C1 | F | 3 | yes | test_artifact_damaged | test_artifact_damaged | yes | no | no | no |
| C1 | F | 4 | yes | test_artifact_damaged | none | yes | no | no | no |
| C1 | G | 1 | yes | none | none | no | no | no | no |
| C1 | G | 2 | yes | none | none | yes | no | no | no |
| C1 | G | 3 | yes | none | none | no | yes | no | no |
| C1 | G | 4 | yes | none | none | no | no | no | no |
| C2 | A | 1 | yes | n/a | none | no | no | no | yes |
| C2 | A | 2 | yes | n/a | none | no | no | no | no |
| C2 | A | 3 | yes | n/a | test_artifact_damaged | no | no | no | yes |
| C2 | A | 4 | yes | n/a | none | no | no | no | no |
| C2 | G | 1 | yes | none | none | no | no | no | no |
| C2 | G | 2 | yes | test_artifact_damaged | test_artifact_damaged | no | no | no | no |
| C2 | G | 3 | yes | none | test_artifact_damaged | no | no | no | no |
| C2 | G | 4 | yes | none | none | no | no | no | no |

## Fixed boundary results

| condition | fixed requirement | recorded observation | result |
|---|---|---|---|
| 1 | all 16 A/G calls technically valid; eight G labels allowed | 16/16 valid; 8/8 G labels allowed | pass |
| 2 | C1-G prose classified `none` in at least 3/4 | 4/4 | pass |
| 3 | C2-G target selection, target prose and paired agreement each at least 3/4 | selected 1/4; prose 2/4; agreement 3/4 | **fail** |
| 4 | C1-G intrusion at most 1/4 and no more than C1-A | G 1/4; A 2/4 | pass |
| 5 | G no worse than A in each context/category cell | C1 agency: G 1/4; A 0/4; the other five cells pass | **fail** |

The overall active-only boundary therefore fails.

Condition 3 failed at the intended function of the field. C2-G run 3 is
`item_10`: the beat says that the central mana artifact "começa a rachar
sozinho" and hot fragments fall, while `physical_objective` is `none`; its blind
row classifies that prose as `test_artifact_damaged`. Runs 1 (`item_04`) and 4
(`item_09`) selected `none` and their blind rows classify no damage. Only run 2
(`item_17`) both selected and wrote the target. The 3/4 agreement count is
therefore not evidence that the target worked: two agreements are `none`/`none`.

Condition 5 failed on one concrete C1-G beat. Run 3 (`item_12`) states "Asword
tenta puxar Link para perto de si" and "Liora reúne os de mana alta". Its blind
row marks this as settling voluntary actions for named candidates. The four
C1-A rows have `agency_violation: false`. The fixed gate deliberately allows no
noise-floor adjustment, so this cell fails even though the other five
context/category comparisons pass.

## Full-versus-active contrast

The separate contrast was technically evaluable but did not meet its fixed
rule:

- C1-F future-test intrusion: 4/4;
- C1-G future-test intrusion: 1/4;
- C1-A future-test intrusion: 2/4.

The rule required F at least 3/4, G at most 1/4 and A at most 1/4. The baseline
failure matters: even without a catalogue, two C1 beats introduced mana
measurement apparatus before team selection. `item_02` starts public weighing
with a `Cristal de Registro`; `item_13` distributes evaluation runes that
measure mana and cooperation. This design does not establish that the prior
prompt block caused the reduction. The preregistration designated
the contrast non-causal because F uses the `scenario-authorized` heading and a
planning-target guidance sentence while C1-G uses the `active entries` heading
and omits that guidance, in addition to removing the future entry.

C1-G still produced one intrusion. In `item_19`, bronze insignias on a pedestal
emit pulses that measure and expose candidates' mana reserves; its blind row
marks `future_test_intrusion: true`. Thus the only-label-`none` schema prevented
selection of the future label but did not fully prevent future test material in
the beat prose under the preregistered definition.

## Consequence for Task 69

This diagnostic assesses the prompt boundary; it does not test the durable
transition store. The separate `RUNNER-TRANSITION-RESULT.md` is cited as
reporting a passing
repeated-state Runner test and a passing two-turn synthetic
`intact -> damaged -> destroyed` Runner test. This catalogue did not reliably
connect an active roteiro objective to the prose or to its selected label.
Implementing an activation resolver behind this interface would formalize a
producer contract that failed its permission gate.

The cited Task 69 record marks the task open. A deterministic follow-up used
the recorded T27 to T29 pillar sequence to choose separate pillar and rubble-gap
fixture properties. **Source-boundary correction, 2026-09-24:** the accepted
T29 Director proposal's pre-decision spatial draft leaves a narrow basal gap;
its later event says blocks obstruct it, but complete closure of **access** is
explicit only in the persisted narration. Neither boundary settles whether
the aperture dimension itself becomes `closed`. The fixture rejects a repeated
`destroyed` pillar value and applies a manually chosen `ajar -> closed` gap
transition as a synthetic storage contrast. This verifies storage behavior,
not that the gap transition can be extracted from the Director proposal. The duct's smaller access improvement
is excluded because the source does not fix a single vocabulary edge. See
[the corrected pillar-pair result](PILLAR-PAIR-RESULT.md).

## Artifacts

- preregistration: `ACTIVE-OBJECTIVE-PREREGISTRATION.md`;
- payload and execution scripts: `build_active_objective_payloads.py` and
  `run_active_objective_diagnostic.py`;
- raw provider envelopes: `active-objective-screen/raw-*.json`;
- parsed responses and mechanical validation:
  `active-objective-screen/response-*.json` and `mechanical-results.json`;
- blind material: `blind-items.json`, `blind-key.json`, `blind-prompt.txt`,
  `blind-reader.md` and `blind-analysis.json`;
- fixed verdict: `active-objective-screen/diagnostic-result.json`.
