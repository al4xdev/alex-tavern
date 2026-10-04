# Confirmed-event prose review: local gate failed

Status: FAILED. One missed confirmed event and two unsupported sensory objections
prevent admission. No production reviewer or model setting changed; Task69 and
all earlier failed gates remain open. This is a component screen on one controlled
scene, not an estimate of narrative reliability.

1. MEASURED execution:24 logical calls,25 retained curl attempts, all HTTP200:
16 fixed reviews,4 fresh production renders,4 reviews of those renders. All20
reviews were schema-valid and boolean/issues-consistent on their first attempt.
Three renders were first-attempt valid; fresh1 added the unsupported root field
`type`, triggering one existing schema retry. All4 terminal renders succeeded.
Its request variants were [0,0]: two HTTP attempts of the same frozen
initial body, not the separate echo-correction variant or semantic resampling. All
responses finished with stop and emitted reasoning. Credentials used curl stdin;
real .data was read only for credentials. Starting synthetic states lived under /tmp/alex-tavern-prose-admission,
were saved and reloaded under real session locks; rendered drafts did not replace them.

2. OBSERVED reading of every source/prose/reviewer pair, with independent shuffled
Gemini text-only reader81839af03068 checking all8 pairs and20 judgments:

| Fixed condition | Decisions across four fresh reviews | Meaning check |
| --- | --- | --- |
| Actual complete prose | Accepted4/4, empty issues | Confirmed outcomes preserved |
| Absent prose paired with complete confirmed events | Rejected3/4; accepted r2-3 | Lamp inspection missed once |
| Complete prose plus green opening/Bento courtyard crossing | Rejected4/4 | Unsupported green transition identified |
| Complete prose plus neutral cold draft | Accepted2/4; rejected r4-1/r4-2 | Two unsupported sensory objections |

The absent prose is an actual retained output, but pairing it with complete
confirmed events is counterfactual. It originally followed a Director output
that omitted the lamp event. This screen measures detection of a missing admitted
event, not historical renderer omission frequency or upstream completeness.
No keyword/name matcher or sentence-per-event requirement supplied these grades.

3. OBSERVED false negative: the confirmed event says Iara approaches the blue
portal's bar with the lit lantern and examines its locking mechanism. In r2-3
reasoning the reviewer sees this event, then treats the lantern beside the
opening's column as equivalent examination. The prose instead illuminates
walls/shadows and later the floor. It depicts neither examination at the bar
nor an obstruction resolving that event. This is a semantic judgment in this
draw, not evidence of input truncation or failure to notice the field.

4. OBSERVED false positives: r4-1 and r4-2 reject 'Um sopro de ar frio varre o
salão, carregando cheiro de terra molhada e ferro.' They treat it as forbidden
new ventania or an unlisted physical transition. It causes no portal opening,
closure or actor movement; blue is opened by Bento's supported intervention.
Neutral compatible sensory expansion was allowed before calls. The primary
reading and isolated reader find these issues unsupported. Agreement alone is
not evidence: the cited sentence and the source constraints supply the check.
The r3-3 explanation also overstates that no aperture-change cause exists;
Bento's blue-opening cause does exist. Its specific green-opening and Bento
position objections remain grounded, but its wording is not faultless.

5. OBSERVED fresh delivery: all4 new actual production renderer outputs preserve
Iara's lamp inspection, Bento's bar removal/blue opening and Téo's crossing;
all4 corresponding reviewers accept with empty issues. Lantern light reveals
bar/locking details in each output. Compatible metal, light and tunnel details
are literary expansion, not separately proven canonical facts. The four outputs
share one retained complete Director packet and one public viewer cluster.
There were no new Director/Character/planner calls, whole player_turn commits,
undo/recovery, private-viewer tests or app activation. Successful local render
controls cannot compensate for fixed-case reviewer errors.

6. Configuration: V4 Flash, thinking enabled/high,16384 cap,180-second timeout;
unchanged renderer150-word floor. Existing max3 transport/JSON/schema attempts
and fixed production echo correction were available; only one schema retry was
used. Production builders/client/schema were exercised. Probe Ruff lint/format
passed before freeze. No production code changed for this screen, and the prior
1234-test suite is prior evidence, not a new run. Request/response/reasoning and
frozen manifests remain in ignored local evidence beside this report. Execution
logs originally used /tmp/alex-tavern-prose-admission; no owner-play session was
used as a baseline.

7. THEORY and next action: test the supported V4 Pro reviewer against these
same retained pairs, changing only the model identifier in the HTTP request.
This tests model/configuration sensitivity without claiming stronger models
solve the issue. A pass would permit fresh-case and upstream-contradiction tests
and a new isolated Runner transaction/recovery candidate, never Task69 closure
or automatic activation. Compaction and autonomous-burst commit boundaries
still require separately scoped recovery evidence.

Protocol critics008bbf9d7b06/565872fa01a3 led to pre-call scope clarifications.
Report critic2a4f562d2e92 reviewed the earlier draft; the reconstructed record
retains its bounded claims. Reviewer accuracy, renderer delivery and full-chain
admission remain separate. This record has been reconstructed from retained
results after the temporary draft disappeared; executed protocol/manifests
were not edited or re-frozen.

Reconstructed-report critic c920dac9180f: retained concerns about narrow scene
breadth and locally ignored raw evidence. Its proposed contradictions were
checked against the frozen script/protocol and rejected: [0,0] denotes request
variant indices rather than attempt indices; the protocol explicitly permits
neutral sensory expansion; reconstruction changed no pre-call rule or hash;
the report claims session-lock use, not complete RuntimeState fidelity. A
renderer can omit an admitted event, so the counterfactual canary is not an
impossible pipeline state. No aggregate error rate, parameter-scale mechanism
or universal automated narrative guarantee is adopted from this review.
