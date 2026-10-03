# Beat coverage label delivery, 2026-10-03

## 1. Observed correction and scope
The Director now receives "Beat elements awaiting coverage:" for the current
beat's pending anchors. Previously the renderer said "Not in play yet —
introduce as concrete perception events:", including objects already present
in canonical state/history after a replan reset coverage. Only that line and
its explanatory code comment changed; coverage collection/replan behavior,
state contracts, model settings and the final advance/do-not-restage rule are
unchanged. README and an existing consumption assertion use the new meaning.

This removes a false input assertion. It does not establish fewer story loops,
equivalent model reliability, or a complete Task69 transition guard.

## 2. Measured production-client acceptance on fixed requests
The earlier no-retry screen remains FAILED (candidate raw schema validity 7/8).
Its draws were not replaced. This separately registered screen used sixteen
fresh logical calls on two frozen requests from ONE synthetic session, with
four draws per arm/submission. The production chat_completion_json and adapter
ran over curl transport, high reasoning, 8192 tokens, existing maximum three
attempts. All attempt requests/raw envelopes/transport records and production
debug errors remain in ignored artifacts/isolated /tmp storage. Schema-valid
completion of the logical call was registered symmetrically for both arms.

| Submission | Arm | First-attempt schema-valid / logical calls | Finally accepted / logical calls | HTTP attempts |
| --- | --- | --- | --- | --- |
| 1 | control | 3/4 | 4/4 | 5 |
| 1 | coverage | 4/4 | 4/4 | 4 |
| 2 | control | 4/4 | 4/4 | 4 |
| 2 | coverage | 4/4 | 4/4 | 4 |

submission1-control-3 attempt1 omitted required
scene_blocking.destination_reachable_this_beat; validation logged rejection,
and attempt2 passed. Both replies are preserved. Seventeen HTTP200 envelopes
had distinct nonempty IDs and nonempty provider-returned reasoning.
These counts describe these repeated draws, not population defect rates.
The omission's cause remains undiagnosed; neither screen establishes a
wording-induced schema regression.

## 3. Observed content review, bounded to this fixture
The initial reader b2e90e0db47f received a truncated packet and could not
evaluate all outputs. Its partial verdict is not used as a complete gate.
The same sixteen accepted outputs were split into four intact packets:
45ba4bd559a0 (R01-R04), 98bfdc2ed66a (R05-R08), b566af8912cf (R09-R12),
3bd0573c8d46 (R13-R16). Each received actual source messages matching that
output, with opaque shuffled labels and no arm names or supplied verdict.

All sixteen returned no failure on continuing green-portal closure, canonical
contradiction/identity, Iara's waiting choice, private-information exposure
and genuine new roof damage or water entry. Main-agent reading checked the
events in both arms against source and confirmed cracking/displacement/water
rather than only repeated wind/creak. This fixture contains no private thought
or whisper probe, so absence of leaks here proves no general confidentiality
property. Complete controls also avoided fresh closure: no restaging reduction
is demonstrated. Placeholder personas, deterministic planner/Director/render
doubles during source capture and no real Character/prose generation limit
the result to these Director inputs/accepted outputs.

## 4. Delivery verification and limits
After applying the label, verify_delivery.py reused the original deterministic
fixture in a new isolated data root without editing its historical script.
Two real Runner.player_turn submissions persisted revisions 1 and 2.
Both delivered Director requests exactly matched the measured candidate
requests, including source order/schema/adapter settings. The verification
itself used model doubles, not additional provider calls. Persistence/debug
paths are retained in ignored delivery/manifest.json. Historical screen
hashes remain unchanged; their pre-delivery source fingerprint naturally
differs from the subsequently edited renderer.

Repository validation: Ruff lint passes; mypy reports no issues in 61 files;
pytest -x reports 1229 passed, 2 deselected and the existing Starlette warning
(log /tmp/alex-tavern-coverage-delivery-pytest.log). Focused consumption/data-
isolation/operator-ontology checks pass 99 tests. Format checks pass on changed
Python/artifact files. Global format checks FAIL on existing unchanged files:
uvx Ruff0.16.10 flags 34 files (including three historical Markdown snippets);
locked Ruff0.15.21 flags 31 Python files. Those files were not reformatted in
this change. Do not report a globally clean formatting check.

Task69 remains open: no durable transition producer, cross-submission physical
transition rejection or broader live-fiction cluster acceptance was added.
A truthful pending-element label does not validate arbitrary future beat plans
against canonical physical state. The delivered conclusion is a corrected
input statement with bounded production-path acceptance, not a proven narrative
improvement or a guarantee against re-proposed closed transitions.

Report critic 834a2192a7e8 retained input truthfulness, delivery verification
and the open-task limit; it rated acceptance/content counts NEUTRAL on efficacy.
Retain those counts as an execution audit, not evidence of efficacy. It raised
boundary-shift and baseline-ceiling objections; both remain explicit limits.
Its paraphrases 'proving absence of wording-induced schema regression' and
'confirmed zero regressions' are not claims made here: lack of causal evidence
is not evidence that no regression exists. The input statement was corrected;
prevention of dynamic story loops was not established.
