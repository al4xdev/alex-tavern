# Flash reasoning effort labels on the original act-completion cases

Working result: all four requested labels recognize confirmed hall closure in all four draws. Each label still makes at least one wrong act-completion decision in the canyon case. This run does not establish high as logically superior to low. The registered lower-level promotion rule fails, and no runtime setting was changed. Independent review found that its asymmetric threshold cannot establish which effort is better; the automatic recommendation to retain high was withdrawn. The effort search ends here, without claiming that any level fixes Task69.

## What was compared

Three exact retained Portuguese ambiguous next-beat requests, four fresh single-attempt curl draws per requested effort: minimal, low, medium, high. Forty-eight attempts total, concurrency four; first batch contains one of each label and remaining launches use the frozen shuffled order. Messages, schema, old CURRENT BEAT label, event placement, facts, IDs and 8192 output-token cap remain equal per case; only reasoning_effort differs between thinking-enabled arms. These are historical planner inputs, not the current production builder or full Director/Character/prose chains.

The owner’s minimum and med names were sent as API values minimal and medium. Current official [Thinking Mode documentation](https://api-docs.deepseek.com/guides/thinking_mode/) maps minimal to low and medium to high. Thus four accepted request labels represent two documented effective levels. Received token quantities cannot independently establish server-internal effort mapping. Max was not requested or tested.

Every outgoing request explicitly uses deepseek-v4-flash, thinking enabled and one of those four effort names. All 46 HTTP200 envelopes identify deepseek-flash. No Pro, stored model default, fallback, runtime setting change or semantic repair. Invalid/timeout outputs were not retried or replaced. Production files being edited concurrently by the owner were outside this replay; declared adapter/schema/source hashes stayed unchanged.

## Observed completion decisions

Counts below are correct flags out of four planned draws per source case. Transport and contract failures are separated from semantic misses.

| Requested label | Documented effective level | Failed attempt, stays open / false | Closed in hall / true | Closed after canyon crossing / true | Total correct / planned; schema-valid |
| --- | --- | --- | --- | --- | --- |
| minimal | low | 3/4, one timeout | 4/4 | 3/4, one wrong flag | 10/12; 11 valid |
| low | low | 4/4 | 4/4 | 3/4, one wrong flag | 11/12; 12 valid |
| medium | high | 4/4 | 4/4 | 1/4, two wrong flags and one timeout | 9/12; 11 valid |
| high | high | 4/4 | 4/4 | 2/4, one wrong flag and one invalid JSON | 10/12; 11 valid |

All 45 valid plans have distinct nonempty response IDs, nonempty returned reasoning and finish_reason stop. There are five wrong flags among those 45 plans. The two remaining transport calls timed out at180 seconds with no envelope; high canyon draw1 returned HTTP200/stop but unescaped control character makes its JSON unparsable. All 46 received envelopes finish stop, none reports token-budget truncation. Its invalid JSON is a contract failure, not a counted logical flag error.

The strict preregistered working rule required both minimal and low to achieve12/12 valid/correct replies, with no verified confirmed-state/current-objective denial. Both labels have a wrong canyon flag and minimal additionally has a timeout. This is sufficient not to promote low under that rule. It does not prove high is better; high also fails this diagnostic. Small repeated samples on three shared inputs are neither statistical equivalence nor population reliability estimates. Lower sample failures cannot be attributed to transport alone because explicit wrong flags and textual denials are retained.

## Reading the plans and expressed explanations

A fresh source-bound reader received all45 valid plans and the invalid-JSON result, shuffled with opaque IDs, no effort names, expected flags or provider reasoning. Two then-pending calls later timed out and added no text. Its findings were verified after unblinding against actual source and generated fields. No word count or similarity score measures quality here.

- Low canyon draw1 (opaque O44) treats the passage as still sucking debris toward the distant hall and proposes 'iniciar o fechamento da passagem'. The source explicitly says it closed after crossing and no return passage is open. Its returned explanation says closure 'não foi confirmado', which is false for the supplied event. This is a source-reading miss, not merely a boolean typo; it also cannot diagnose hidden cognition.
- Minimal canyon draw3 (O36) similarly plans the old portal widening and returns false. Medium canyon draw2 (O40) ends with 'revelando se o portal se fechou ou se rompeu de vez', reopening uncertainty the source had resolved.
- High canyon draw4 (O48) and medium canyon draw1 (O38) acknowledge closure in their returned explanations, then introduce a new canyon fissure while keeping act_completed=false/a1-b2. The NEW pressure itself can be legitimate, but it does not retroactively undo satisfaction of the old exit. Longer expressed reasoning did not guarantee the right field decision.
- High failed-attempt draw1 (O02) returns expected_actors=['C1','Bento'] although its field asks for IDs and the roster defines Bento as C2. Its false act flag is correct and its JSON schema passes because actor items are only strings. Boolean/schema correctness therefore does not certify reference fidelity even at high effort.
- All sixteen valid hall plans advance to a2-b1 and acknowledge closure. Minimal hall draw1 reignites runes as a NEW countdown, without declaring the old act incomplete. That illustrates a permissible new reversal, not automatic historical restaging.

The reader also objected to voluntary exit targets, invented route geometry and environmental effects. Those are not all accepted as errors: an observable prospective condition is not automatically an authored choice, new pressure may affect gear, and a new rockfall blocking a path is not inherently incompatible with the portal already being closed. These objections are retained as unresolved or rejected literary interpretations, not added to a semantic failure percentage. No ranking of narrator prose naturalness follows because no narrator prose was generated.

## Time, usage and evidence

| Requested label | Median curl wall seconds, all12 draws | Median provider-reported reasoning tokens, received envelopes |
| --- | ---: | ---: |
| minimal | 4.716 | 412 |
| low | 4.204 | 315.5 |
| medium | 6.675 | 700 |
| high | 6.156 | 587 |

These are source-balanced short planner calls at concurrency four, including timed-out draws in latency but excluding absent envelopes from token medians. They are not full-turn latency or a causal effort-budget calibration. Total reported usage over all46 envelopes, including invalid JSON:47,604 input and44,388 output tokens; timeout usage is unknown. Shared8192 cap counts reasoning plus final output. Larger/longer thinking did not establish higher accuracy in this sample.

Evidence: [protocol](PREREGISTRATION.md), screen/summarizer and [all terminal plans](TRANSCRIPTS.md). Ignored local manifest/runs retain exact requests/raw/transports/errors, session/agent/turn debug records, usage/finish/reasoning, summaries, opaque reader mapping and independent reviews. Hash parity was checked before and after execution, artifact Ruff checks pass, and the active runtime configuration was not modified.

Registered result: low did not meet the full-pass rule and has not been admitted to production by this experiment. That result is unchanged. The report critic correctly identified that demanding perfection only from a challenger does not establish the incumbent’s superiority; an automatic keep-high recommendation is therefore withdrawn, rather than presented as an empirical finding.

Post-review engineering recommendation, explicitly provisional: use Flash with reasoning low for further isolated Task69 work. It is the lowest documented enabled level, it produced fewer misses in this small sample, and the concrete old-objective error also occurred at high; no demonstrated high advantage justifies calling it necessary here. This recommendation is a judgement under uncertainty, not a passed preregistered promotion gate, non-inferiority claim or production admission. The existing app configuration remains unchanged, with high still configured. No further paid tier experiment is planned; the unresolved work is the plan/state/source boundary. No Task69 closure or semantic reviewer admission follows. Historical off results are context only, not an extra concurrent control.

## Review dispositions

The isolated report critic confirmed accounting and source-bound examples but classified the automatic keep-high recommendation as WORSE THAN ABSENT because the gate was asymmetric. That recommendation was withdrawn; the original failed promotion gate remains reported, and the later limited working recommendation is labeled as judgement rather than experimental proof. The critic’s percentage estimates of causal latency overhead and universal canyon failure are not adopted: timings are observations under concurrency, and many canyon replies were correct. Its inferred hidden dramatic-tension mechanism is not established by returned reasoning. The text reader’s actor-ID finding and five closure errors were checked against raw source/output, while its agency/geometry objections are qualified above.

A final isolated decision review retained the distinction between a failed promotion gate and a provisional engineering choice. Its concern about the word 'effective' was resolved by saying 'lowest documented enabled level'; the API's alias mapping is a separate documented fact. Runtime configuration status is stated without attributing an untested causal or approval requirement to it.
