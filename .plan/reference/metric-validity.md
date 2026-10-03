# Which metrics this project trusts, and why — 2026-08-06

**The register. Look up the instrument you are holding; do not read this end to
end.** The rules it applies are one page, read once, in
[`.plan/guides/MEASURING.md`](../guides/MEASURING.md).

One page, because the same failure keeps recurring in different clothes: **a
metric passes review, ranks sessions, and then a read of the actual text says it
measured the wrong thing.** It happened three times on 2026-08-06 alone, to three
different instruments, two of which were written that same day.

Standing rule this page exists to enforce:

> **Never accept a metric on the strength of its numbers. Read the records it
> flagged and the records it cleared.** A clean band, a clean count and a clean
> rate are all reproducible under a broken ruler.



## The register

| metric | status | why |
|---|---|---|
| proposal-boundary extraction screen (2026-09-24) | **LOCAL FIXTURE GATE MET; NOT PRODUCER OR FICTION ACCEPTANCE** | Two archived Director proposals from **one session**, four curl calls each. All eight valid; T28 pillar change 4/4 and no gap change, T29 no new pillar-integrity change 4/4. The T29 gap was pre-registered **unscored** because post-event aperture is not source-labelled, yet model output says `change` 4/4. These are repeated responses to two payloads, not eight independent cases or a narrative-quality rate. `plans/artifacts/69-closed-transition-contract/PROPOSAL-EXTRACTION-RESULT.md` |
| hall-gate extraction V2 (2026-09-24) | **LOCAL FIXTURE GATE MET; NOT A RELIABILITY ESTIMATE** | One archived session, three Director proposals, four fresh curl calls each. All twelve HTTP-200/schema-valid: T7 `no_change` 4/4, T8 `change` 4/4, T10 `no_change` 4/4 for named gate aperture. T8 has explicit update wording; T10's repeated guard is unscored, and its `no_change` cannot alone prove impact recognition. No new-gap, dynamic-registration, producer or renderer claim follows. `plans/artifacts/69-closed-transition-contract/DOOR-EXTRACTION-V2-RESULT.md` |
| T32 renderer retry replay (2026-09-24) | **INCOMPLETE; NO PROMPT VALIDATION** | One archived retry payload, four curl calls per correction arm, all HTTP 200 but only 7/8 schema-valid. The registered all-valid gate failed; no replacement or semantic A/B score. A later descriptive blind read disputed whether one candidate passage erased the whole creature or only expelled fragments. The original archived persisted-prose contradiction remains a separate one-turn observation, not a measured retry mechanism. `plans/artifacts/69-closed-transition-contract/T32-RETRY-V2-RESULT.md` |
| curated Director-to-prose reader (2026-09-24) | **INCOMPLETE; NO RUNTIME GUARD VALIDATED** | Three selected pairs from one session (T8 and two T32 prose variants), four curl calls each. All twelve HTTP 200, only 6/12 schema-valid; six returned schema-shaped objects instead of verdict instances. The pre-registered all-valid prerequisite failed, so no semantic score. Two valid verdict/quote pairs appear to disagree with the source reading but are descriptive only; no model error rate or general fidelity claim. `plans/artifacts/69-closed-transition-contract/PROSE-FIDELITY-LOCAL-RESULT.md` |
| blue-gate duplicate extraction screen (2026-09-24) | **LOCAL SEMANTIC FAIL; NO PRODUCER VALIDATED** | Four frozen T36–T39 proposals from one P1 session, four fresh curl calls each. All 16 HTTP-200/schema-valid; T37 positive closure and T39 same-state/no-new-action control matched 4/4, but T38 explicit repeated closure was unflagged in 3/4 and the fourth gave `change` with current=candidate `closed`. T36's discrete `ajar -> closed` fixture had only 1/4 expected `no_change`. The all-output semantic gate failed. This is no reliability estimate and does not overturn the earlier hall-gate screen's narrower result. `plans/artifacts/69-closed-transition-contract/BLUE-GATE-EXTRACTION-RESULT.md` |
| blue-gate action-only smoke test (2026-09-24) | **LOCAL SEMANTIC FAIL; NO PRODUCER VALIDATED** | Same four selected Director proposals from one session, but only event contents and time-skip summary enter the model. All 16 curl calls HTTP-200, schema-valid and with literal event quotes. T37/T38/T39 labels matched 4/4 each; T36 had one `closing_action=true` quoting a five-seconds-until-closure warning. Frozen unanimity gate failed. The quote exposes an unsupported verdict, not its mechanism; near-identical positive wording and one session preclude semantic-reliability claims. `plans/artifacts/69-closed-transition-contract/BLUE-GATE-ACTION-RESULT.md` |
| manually bound closure admission pilot (2026-09-24) | **INCOMPLETE 86/88; NO PRODUCER VALIDATED** | Eleven frozen source/synthetic cases, extractor and independent checker, four calls each. A curl transport failure and a nonliteral checker quote failed the technical prerequisite; no replacements or aggregate semantic score. Individual valid outputs include a T38 green-target `yes` citing the blue gate and four checker `entailed` verdicts when offered only a static green-gate passage for a blue-closure claim. A content-only reader confirmed those local contradictions. These are observed cases, not an error-rate estimate. `plans/artifacts/69-closed-transition-contract/CLOSURE-ADMISSION-RESULT.md` |
| support-only checker candidate (2026-09-24) | **INCOMPLETE 27/28; NOT AN ABLATION** | One schema echo invalidated the technical gate. T38's explicit closure was called insufficient 4/4 while a synthetic past-tense closure was entailed 4/4; an isolated content reader judged both complete. The candidate also changed system instruction and claim wording, so it cannot isolate the effect of withholding full source. `plans/artifacts/69-closed-transition-contract/SUPPORT-ONLY-CHECKER-RESULT.md` |
| checker source-context A/B (2026-09-24) | **INCOMPLETE 53/56; NO CHECKER VALIDATED** | Frozen request pairs differed only by `complete_events`; one schema echo, one positive citation imported from outside offered support, and one legitimate negative correction citation rejected by an overstrict validator failed the technical gate. Valid T38 explicit-closure outputs were entailed 0/4 offered-only versus 3/4 full-source; T37 generic offered quote was wrongly entailed 2/4 full-source. Local paired observations, not a reliability estimate or causal mechanism. `plans/artifacts/69-closed-transition-contract/CHECKER-CONTEXT-AB-RESULT.md` |
| two-channel checker screen (2026-09-24) | **TECHNICAL PASS 32/32; SEMANTIC FAIL; NO CHECKER VALIDATED** | Separate fields/quote validation for offered positive evidence and complete-source factual correction. Six local cases matched both labels 4/4; correction and later-reopening synthetic cases each failed offered-evidence judgment 4/4 while keeping the separate conflict flag correct. An isolated content reader confirmed the offer asserts closure and reopening is not retroactive negation. One-call checker shape stopped; these selected cases are no reliability estimate. `plans/artifacts/69-closed-transition-contract/TWO-CHANNEL-CHECKER-RESULT.md` |
| two-stage closure admission screen (2026-09-24) | **TECHNICAL PASS 52/52; STAGE A SEMANTIC FAIL; NO PRODUCER VALIDATED** | Seven independent offered-evidence Stage A cases and six independent full-source correction Stage B cases, four fresh curls each; the common synthetic A case was reused analytically, not rerun or counted three times. Stage A admitted antecedent-free bare T37 for the blue gate 2/4 and the longer T37 offer 4/4 against frozen labels. A later content reader disagreed with the longer offer's negative identity label, so that case is contested rather than calibrated literary error. Stage B distinguished explicit correction from later reopening in its selected cases, 4/4 each. Local case outcomes, not a prevalence or reliability estimate. `plans/artifacts/69-closed-transition-contract/TWO-STAGE-CLOSURE-RESULT.md` |
| identity/aspect offered-evidence screen (2026-09-24) | **INCOMPLETE 33/36; NO PRODUCER VALIDATED** | Nine frozen packets, four curls each. Three static-gate responses violated the registered identity/action quote relationship. Individual outputs bound an antecedent-free `o portão` to blue 4/4 and a two-gate competitor sentence to blue 3/4; a blind content reader rejected those bindings. The longer archived T37 antecedent label is contested between independent readers, so its 4/4 frozen-label miss is not calibrated literary error. No aggregate semantic pass or reliability estimate. `plans/artifacts/69-closed-transition-contract/IDENTITY-ASPECT-RESULT.md` |
| T38 stale-fact-only real-payload A/B (2026-09-24) | **MINIMAL TECHNICAL PASS 8/8; SINGLE-FACT REPAIR FAILS LOCAL B GATE** | A uses archived T38 Director request; B changes only `dungeon_gates` from all-open to all-sealed. Blind reader found new blue closure in A 1/4, B 4/4; the registered comparative baseline threshold was unmet, but preregistered any-B-repeat rule stops B as standalone repair. One B output also re-moved already placed characters. Registered gate checked HTTP, distinct IDs and parseable event lists; a post-hoc current Narrator-schema check also passed 8/8 but did not catch character-name zone keys or mismatched subject attribution. One payload and stochastic calls cannot establish causal direction or reliability. `plans/artifacts/69-closed-transition-contract/T38-STALE-FACT-AB-RESULT.md` |
| T38 manually guided whole-draft retry (2026-09-24) | **LOCAL COMPARATIVE PASS 8/8 SCHEMA-VALID; NO AUTONOMOUS REPAIR VALIDATED** | Exact archived T38 request and rejected draft in both arms; last feedback was generic versus a manual source-grounded contradiction report. Blind content reader judged complete drafts coherent A 0/4, B 4/4 across events, blocking, moves and updates. The B report effectively supplied a blocked-gate interpretation. One source request, four stochastic calls per arm, no automatic detector, legal-transition controls, persisted prose or runtime transaction. `plans/artifacts/69-closed-transition-contract/T38-MANUAL-RETRY-RESULT.md` |
| whole-draft contradiction reporter screen (2026-09-25) | **INCOMPLETE 21/28; NO REPORTER VALIDATED** | Two archived physical projections (T38 blue, T34 kennel) and five synthetic legal/ambiguous controls, four direct curls each. Seven JSON/quote failures, five concentrated in archived cases, stop aggregate scoring. Both technically valid kennel calls said `consistent` despite T33 persisted closure; one valid T38 report caught crossing but omitted its separate repeated closure. Independent reader confirmed material omissions. Synthetic controls passing locally do not establish reliable detection; selected projections are not full runtime payloads. `plans/artifacts/69-closed-transition-contract/WHOLE-DRAFT-REPORTER-RESULT.md` |
| Director-authored gate proposals (2026-09-25) | **INCOMPLETE; NO PRODUCER OR GUARD VALIDATED** | Two archived Director requests, four curls each. Blue T38: four literal quotes, three newly narrated repeat closures tagged and one static draft tagged `[]`. Kennel T34: three literal quotes and one unmatched `close` quote; two repeated closures tagged, one maintenance-of-ice passage tagged `close` despite no aperture movement, and two `C3` actor values despite public-name instruction. A content-only reader inspected all eight drafts. The one quote mismatch fails the frozen all-valid prerequisite. These are local case observations, not a transition-detection or repair rate; opening and legal crossing were unexercised. `plans/artifacts/69-closed-transition-contract/DIRECTOR-PROPOSALS-RESULT.md` |
| T35 Liora crossing reader split (2026-09-25) | **QUALITATIVE DISAGREEMENT; SOURCE READING RETAINED** | One report critic argued that `atravessa` plus `desaparecendo` could leave Liora in transit. A separate content-only reader of the persisted sentence, without state fields, placed her in the tunnel and rejected normal salon occupancy next beat; the source sentence says she crosses and disappears into the tunnel. T36's Director input nevertheless lists her in the salon. This is one literary-source dispute, not an aspect-classifier accuracy rate. The dissent remains recorded in `plans/artifacts/69-closed-transition-contract/T35-LIORA-SPACE-FINDING.md`. |
| authoritative typed gate transaction screen (2026-09-25) | **V1 HARNESS ERROR; V2 INCOMPLETE; NO PRODUCER VALIDATED** | Four explicitly outcome-specified counterfactual scenes, four curls each. V1 Director lists matched the local operation contract but all prose calls received HTTP 400 because direct curl omitted the DeepSeek adapter's JSON instruction. V2 used the adapter, yielding 16 locally valid Director lists and 14/16 schema-valid prose objects; two schema-shaped outputs fail the frozen all-valid gate. A blinded content read of the 14 valid prose outputs found a new opening of an already open gate in one; another invented an earlier ice seal absent from the fixture. A focused reader upheld the seal observation but disputed other spatial/metaphorical complaints, which are excluded. Later audit found V2 also omitted the shared client's language/no-dash instructions, so it is not a full production-payload replay. This is a selected-fixture boundary observation, not model reliability or causal attribution. `plans/artifacts/69-closed-transition-contract/AUTHORITATIVE-TRANSACTION-RESULT.md` |
| renderer time-packet A/B (2026-09-25) | **LOCAL JSON PASS FOR B; CONTENT GATE FAIL; NO RUNTIME PACKET** | Four fixed synthetic transactions, four fresh prose curls per case and arm. The first system-Python grade was invalid after raw responses were saved; project-environment revalidation found A 12/16 and B 16/16 schema-valid (per case A: 3/4, 3/4, 2/4, 4/4; B: 4/4 each). Blind content reading found one A new opening on an initially open gate, B recent-melt history without a confirmed melt, and B unsupported trees beyond the tunnel gate. A second reader disputed stronger spatial contradiction labels. Four B and two A outputs were in English, **demoted from candidate quality signal to harness artifact**: the direct requests omitted the shared client's explicit Brazilian-Portuguese instruction. No individual clause in B's bundle is isolated. The fixture directly supplied `viewers` and did not run Runner clustering, so this cannot establish a production roster conflict. `plans/artifacts/69-closed-transition-contract/RENDERER-TIME-PACKET-RESULT.md` |
| real T6 transit-exemption bundle (2026-09-25) | **TECHNICAL PASS 8/8; B CONTENT GATE FAIL; NO RUNTIME FIX** | One archived accepted T6 prose payload, four direct curls per arm, preserved real language/schema instructions. Blind reader of filtered text found Garran's named crossing in A 1/4 and B 4/4, but B's `-1` narrates a hand gesture after reaching the destination corridor and `-3` describes his shoulders after disappearance there; the origin zone has no perception link to that destination. These are local selected-output judgments, not a reliability rate. A deterministic pair check verified canonical-title spelling controls the current name filter's deletion on this exact sentence; the prompt-plus-filter B bundle does not isolate either component. `plans/artifacts/69-closed-transition-contract/T6-TRANSIT-EXEMPTION-RESULT.md` |
| T6 event-local reader-unit screen (2026-09-27) | **TECHNICAL PASS 12/12; CONTENT GATE FAIL; NO RUNTIME PRODUCER** | One archived accepted T6 origin-viewer payload, three independent event calls per repeat, four repeats. Garran's named crossing appears in all four assemblies; one loses the confirmed block roll and another loses the witnessed stabilization prayer, failing the registered all-four content rule. An independent fiction reader noted recurring dust/lamp images across units. The unchanged-event control was read earlier by a different reader, so no controlled fluency gain. Transit binding was manual; no destination/offstage control. Counts are local observations, not reliability or prevalence estimates. `plans/artifacts/69-closed-transition-contract/T6-EVENT-LOCAL-RESULT.md` |
| real-source ordered transaction screen (2026-09-28) | **TECHNICAL GATE FAIL; NO PRODUCER** | Two archived beats, four first calls per case; two validator-triggered retries. T38: two schema-invalid first outputs and two chains still mechanically rejected after repair; one rejected draft put an untyped Téo crossing in `other` text, which is not an accepted-bypass case. Legal T8: four mechanically accepted `ajar -> open` outputs, but three raw step lists omitted or changed Maelis/Garran events, as a source-checked fiction reader found. Deterministic `sob` interpolation made every assembled T8 gate sentence ungrammatical, so assembled-prose quality is a harness artifact. One defective source and one positive control cannot estimate reliability. `plans/artifacts/69-closed-transition-contract/REAL-TRANSACTION-PRODUCER-RESULT.md` |
| physical-only T38 draft-presence screen (2026-09-28) | **LOCAL REGISTERED PASS; NO PRODUCER** | Three packets, four direct curls each, all HTTP 200/schema-valid/distinct IDs. With manually supplied gate, state and actor, T38 F-A and F-B each returned `closed/blocked/Téo` 4/4; legal T8 returned `open/not_applicable` 4/4. A separate content reader found the labels consistent with source text. Identical F-arm samples do not establish draft invariance or explain the prior whole-transaction failure. No prose, target binding or persistence was tested. The isolated report critic called the technical prerequisite neutral, but it is retained because the registered content gate is uninterpretable without it; the critic's objection to causal wording about equal F arms was adopted. `plans/artifacts/69-closed-transition-contract/PHYSICS-ONLY-DRAFT-AB-RESULT.md` |
| T38 three-label conditioned whole-draft retry (2026-09-28) | **TECHNICAL PASS 8/8; WHOLE-DRAFT GATE FAIL; NO PRODUCER** | Exact archived T38 request and rejected draft, four generic and four physical-label retries, distinct IDs/full schema valid. Blind reader found a newly authored blue-gate closure in all eight, so both arms were 0/4 on the registered whole-draft criterion. All four label-arm drafts blocked Téo without a move; all four generic drafts narrated his crossing. One beat cannot estimate reliability or isolate a general causal mechanism. Ancillary witness/background-event complaints from the reader remain unadjudicated, rather than being silently counted or discarded; removing the closure alone was not tested. The report critic suggested a p-value from four stochastic calls on one scene and treated disqualification by one mandatory criterion as a claim of causal sufficiency; neither inference is adopted. `plans/artifacts/69-closed-transition-contract/T38-LABEL-CONDITIONED-RETRY-RESULT.md` |
| T38 event-delta feedback plus T8 opening packet (2026-09-28) | **TECHNICAL GATE FAIL 11/12; NO COMPARATIVE ADMISSION** | T38 A/B differed only by `aperture_delta=none`, four curls each; T8 P was an unpaired legal-opening packet, four curls. P-1 HTTP 200 had malformed JSON (`;` instead of `,` in scene update), so the frozen all-valid gate failed. Blind individual T38 read found repeat blue closure A 4/4, B 2/4; all eight blocked Téo without moves. Three valid P Director rewrites opened the gate and retained the guard; P-3/P-4 omitted proposed shield handling, and P-4 omitted Maelis's speech-intent event while still routing her. The archived Character Maelis actually said `segure a entrada` where her Director intent said `feche`; literal difference is not a final-turn defect. No Character call or P no-delta arm ran, so final-turn loss and causal attribution are untested. One source beat per case, no automatic delta extraction or runtime change. `plans/artifacts/69-closed-transition-contract/EVENT-DELTA-FEEDBACK-RESULT.md` |
| hand-bound semantic-program feasibility (2026-09-28) | **LOCAL TWO-READER GATE FAIL; NO PRODUCER** | A frozen template grammar rendered four selected archived beats once with first archived Character speech records appended separately. One continuity reader accepted four against the supplied obligations, but T6's far-side Garran position was not checked by the origin-view packet; this is not full semantic coverage. One fiction reader rejected four as publishable RPG prose, identifying repeated names, checklist cadence, speech-intent echo and a grammar error. These are per-beat qualitative judgements by one reader per criterion, not model calls, a calibrated error rate, or evidence against every controlled realizer. The isolated report critic correctly challenged a general claim against templates; the report now rejects only this exact pair. `plans/artifacts/69-closed-transition-contract/SEMANTIC-PROGRAM-FEASIBILITY-RESULT.md` |
| T38 program × style-reference screen (2026-09-28) | **TECHNICAL GATE FAIL 15/16; NO REALIZER** | Frozen 2×2 S/L program and T38/T39 style-reference cells, four direct curls each. All eight S narrations avoided a new closure or crossing, but L had two active openings of an already ajar gate in L×T39 and one early closure in L×T38. One of 16 JSON outputs added `_meta`; a fiction reader accepted four individual texts including that invalid output, so the all-output fiction gate also failed. One selected historical scene and one explicit counterfactual cannot estimate reliability, reference causality or general program authority. `plans/artifacts/69-closed-transition-contract/T38-PROGRAM-STYLE-CROSS-RESULT.md` |
| T38 packet-only constructive author (2026-09-28) | **ONE-SHOT TWO-READER GATE FAIL; NO REALIZER** | An isolated author saw only frozen S/L packets and wrote one text each. One continuity reader accepted both; one fiction reader rejected blocked S as repetitive/report-like and accepted legal L. This is a local L existence example, not model reliability. S's failure does not prove it unwritable or identify the missing detail. `plans/artifacts/69-closed-transition-contract/T38-CONSTRUCTIVE-PACKET-RESULT.md` |
| repetition-retry content read (2026-09-24) | **SCOPED QUALITATIVE EVIDENCE; ONE VERDICT WITHDRAWN** | Twelve purposively selected archived turns, one per P1 session; first eight then four remaining sessions. The packet omitted time-skip summaries: eleven selected turns had empty summaries, but T23's summary explicitly supplied the team reveal to the renderer. Its early-render verdict was withdrawn; T24 re-proposed the T23 accepted event. T32's persisted same-turn creature-state contradiction remains. Other discarded drafts contain conflicts removed by retries. This selection cannot estimate prevalence or retry effect. `plans/artifacts/69-closed-transition-contract/REPETITION-RETRY-CONTENT-READ.md` |
| task-77 three-turn restatement plus unchanged positions | **HISTORICAL DIAGNOSTIC; DO NOT GATE** | Published 23 windows/13 of 33 sessions has no recovered selector or case list. One explicit reconstruction over 33 current non-P3 states finds 27 windows/15 sessions, without proving the old report wrong. The detector is a lexical/position proxy: source-checked reads separate unresolved crossing, motivated resistance, ambiguous group identity, and movement within one zone. Neither count measures narrative-defect prevalence. `plans/artifacts/77-content-audit/REPORT.md` and `RECONSTRUCTION.md` |
| fact-key suffix as character-ownership classifier (2026-09-14) | **REMOVED FROM GATING** | The free-form suffix does not identify character ownership. Recorded d5a2ccf0 T8 output supplies a supported lock under `doors_state`; controlled before/after intake differs only by preservation of that entry. The historical key absence is observed, but the complete historical cause is not established by replay alone. The 11-call content read is diagnostic, not a quality-rate estimate; no blanket removal of the separate similarity check follows. `plans/artifacts/69-fact-intake-read/REPORT.md` |
| messenger state-delta screen (2026-09-14) | **INCOMPLETE; no prompt validation** | One fb62cc2f T4 request, A two and B three schema-valid responses. The minimum of three per arm fails. Main-agent source reading substituted for an unavailable isolated source reader; V8 was corrected after unblinding when a non-viewer release event was checked. Keep the raw events distinct from viewer projection and from Runner-discarded values. `plans/artifacts/69-state-delta-contract/REPORT.md` |
| opaque replanner physical-context read (2026-09-14) | **LOCAL DIAGNOSTIC; no runtime validation** | One fb62cc2f T7 request, four schema-valid outputs per arm. Candidate V5 contradicts explicitly closed arches; baseline also has continuity defects. Protocol tightened after dispatch but before reading; critics disputed whether original “regression” required comparative worsening. No claim that B is worse or that the exact historical door-sealing defect was reduced. Individual readings and disagreement: `plans/artifacts/69-replan-physical-context/REPORT.md` |
| historical P3 frozen-position comparison (task 77) | **WITHDRAWN as physical-action responsiveness, 2026-09-14** | Dispatcher converted action inputs to skips. Two inspected logs, 5d60575d and d5a2ccf0, have seven and nine recorded inputs with empty actions; steering speeches remain. This invalidates the intended four-content/six-skip treatment, not all contextual reading or evidence of spoken initiative. `plans/artifacts/77-p3-input-dispatch/REPORT.md` |
| movement/event consistency screen (2026-09-14) | **UNRESOLVED; no local benefit established** | One 8bd4d0f1 T21 request. All four original and both returned candidate outputs keep Liora in the inner corridor; two candidate calls have no HTTP response. Both baseline reproduction and minimum valid-output requirements fail. Individual fields and conservative qualitative veto: `plans/artifacts/69-movement-event-contract/REPORT.md` |
| manual prose retreat target, transcript ablation (2026-09-14) | **UNRESOLVED diagnostic; not a quality metric** | One d5a2ccf0 T32 payload, four calls per arm. Original has four schema-valid outputs; ablated has two, below the registered minimum. Initial positive arrival-at-wall classifications were disputed as possible posture adjustments and retained as ambiguous. Literary praise for a further collapse did not establish event fidelity. Source quotations and critic disagreement: `plans/artifacts/69-projectile-boundary/REPORT.md` |
| `director_authored` (task 68) | **trusted** | separates on an empty band, 0.827 against 0.857, over 3,936 records; independently re-derived off a second implementation |
| `_foreign_language` (task 65) | **trusted** | 0.012 against 1.000, nothing between, over all 3,936 records |
| `_leaks_internal_id` (task 65) | **trusted** | membership not shape; refuses to fire on `C4` where C4 is an explosive |
| `clamp_lost_half` (task 67) | **superseded** | replaces emptiness-only counting, but measures Director-vs-engine disagreement, not graph damage. Use `clamp_lost_half_unsealed` |
| `clamp_lost_half_unsealed` (task 67) | **REPORT, DO NOT GATE** | needed three repairs in one day, each found by reading a flagged case and never by the number looking wrong. Reads 5 / 0,0,0,0 / 0,4,0,0 / 2,0,0 across twelve cells |
| `named_exclusions` (task 70) | **fixed same day** | shipped with a false positive; see below |
| event-recurrence detector, `sim >= 0.6` (task 69) | **REPORT, DO NOT GATE** | unregistered until 2026-08-13 and never read. Proper sample read the same day: **2 false positives in 20 (10%)**, both *same phrasing, different content* — a different fissure swallowing different people. Fine as description, not as a guard. **43.4% of its hits are `audible_speech`**, so task 69 owns only about half of its own headline |
| session-cohort physical-kind recurrence (2026-09-05) | **DIAGNOSTIC ONLY; DO NOT GATE** | Original 33-session inventory, 16 measurable below-40 versus 15 threshold-reaching sessions. Per-session spread and fixed manual read in `plans/artifacts/69-session-cohorts/REPORT.md`. Lexical flags include continuations and uncertain identities; the read found no unequivocal completed-event reset in its 16 selected pairs. Does not estimate narrative repetition or exclude capacity/attention |
| manual roof-reset classification (2026-09-05) | **SCOPED READ; follow-up gate NOT MET** | One session, T34/T35, four curl calls per original/deletion arm. Original: one clear RESET, two continuations, one ambiguous per payload. Deletion: no clear RESET, two continuations, one absent, one ambiguous per payload. Arm labels concealed during reading, reader knew design; no reliability or corpus-quality estimate. All pass archived schema. Rule, quotes and caveats in `plans/artifacts/69-roof-input-replay/REPORT.md` |
| manual evacuation-stage classification (2026-09-05) | **EXPERIMENTAL SCOPED READ; follow-up gate NOT MET** | One session/payload, four curl calls per original/two-line-deletion arm. Original: one valid RESET, one valid CONTINUATION, one invalid continuation projection, one connection failure. Deletion: three AMBIGUOUS, one connection failure. Partial primary-reader concealment; fresh literary reader saw no rubric or arm labels. Quotations in `plans/artifacts/69-evacuation-input-replay/REPORT.md` show that preserving formation can coexist with unclear motives, positions or orders. No corpus rate, reliability estimate or quality score |
| source-checked plan-precedence comparison (2026-09-05; reviewed 2026-09-14) | **LOCAL DIAGNOSTIC; candidate failed, no quality acceptance** | Two selected sessions, four planned calls per A/B/C arm; A original, B heading plus precedence, C no planning block. Valid roof outputs: A3/3 target restagings, B2/4, C0/3; B fails its at-most-one rule. C retains concrete continuity problems. Classification is the investigator's contextual read after isolated literary readers, with quotations and invalid projections preserved in `plans/artifacts/69-plan-precedence/SOURCE-CHECK.md`. Not a lexical detector, corpus rate or calibrated quality metric. |
| `anchor_matched` / `anchors_seen` coverage as proof of absence | **INSUFFICIENT TO ASSERT AN EVENT HAS NOT OCCURRED** | In bb72dc94 T9→T10, “portões internos se fechando com estrondo” fails to match the confirmed “Os portões internos da masmorra se fecham com um estrondo metálico”; the next prompt nevertheless claims it is not yet in play. One scoped counterexample, no error rate or causal repetition effect. The heading candidate leaves coverage unchanged; its completed local content screen vetoed integration after an unexplained evacuation reversal. That verdict does not establish a causal heading effect: `plans/artifacts/69-anchor-heading-replay/REPORT.md` |
| `scene_clusters` / `scan_scene_splits` (task 71) | **trusted** | validated by reproducing all six of task 71's archived figures to every digit |
| `scan_cross_cluster_leak` (task 71) | **trusted, corrected twice** | scored per reader cluster, strict name matching, prose separated from speech reports on a measured empty band |
| `_strip_offstage_actors` (task 71) | **trusted, second version** | 3 fires, 0 false positives over 42 live narrations; the first version had 3 of each |
| `_carries_intent` (task 65) | **weak, kept permissive** | does not separate on real data; see below |
| `empty_audience` (task 67) | **REPORT, DO NOT GATE** | also cannot tell a DECLARED seal from graph damage: it filed seven turns of a man on a deliberately sealed pulpit as `graph_isolated` |
| Director-proposed `witness_ids`, as a scoping signal | **MEASURED AND REJECTED** | median `|witness_ids|`/cast = **0.95** (quartiles 0.86/0.95/1.00, n=4,843 events). The Director lists nearly the whole cast as witnesses of nearly everything, so the field carries no perception judgement. Corroborates task 67 from the other side: **the engine's clamp does all the narrowing**, and every audience number here is a property of the graph, not of the Director's intent |
| blind read of narration for room-vs-position (task 79) | **INVALID AS DOCUMENTED; baseline withdrawn 2026-09-05** | All 40 archived targets were IDs because the collector read `name` outside `mind`. The old 35/40 does not measure correctly identified characters. A name-corrected reconstruction also exposed wrong-actor evidence and movement-category errors. See `plans/artifacts/79-reader-identity-audit/REPORT.md`; no replacement acceptance baseline |
| paired reader-identity reconstruction (2026-09-05) | **DIAGNOSTIC ONLY; DO NOT GATE** | Pins the original 40 cases/20 sessions, three repeats per ID/name arm, 240 completed calls. Session-weighted automatic output and manual counterexamples are retained in `plans/artifacts/79-reader-identity-audit/REPORT.md`. Measures emitted judge labels, not validated movement or literary quality; reconstructed historical requests and joined audiences limit scope |
| text-only sequence reading and paired prose comparison (2026-09-05) | **SCOPED QUALITATIVE EVIDENCE; no quality score or reliability estimate** | Fresh readers received continuous viewer-visible fiction without code, metrics or expected conclusions. Preserve passages and uncertainty: Garran “se põe de pé” then appears “ainda de joelhos”; a preferred alternative specifies a quartet absent from its source. Check the actual consumer request after the literary read. Reports: `plans/artifacts/79-content-read/REPORT.md` and `plans/artifacts/79-content-comparison/REPORT.md`. No pooled winner rate or acceptance result |
| positional `zone_moves` string rule (task 79) | **REPORT, DO NOT GATE — not a rate** | corrected from 37.6% to 16.7% after a building-level prefix bug; then its ACCEPTED set was read for the first time on 2026-08-14: **~60-80% precise**, two failure modes (origin==destination no-ops; room changes matched by a stray preposition), and **92 positives from 15 sessions with single turns contributing 5 and 4**. Median 5.6%, 12 of 27 sessions at zero. Zero-inflated and clustered |
| `Scene.positions` novelty signal (task 79) | **MEASURED AND REJECTED** | "destination newly minted and unoccupied at T-1" — set membership only, no string matching. **Passes its validity check** (fires on 73.2% of 512 moves, not degenerate) and **fails on reading**: a genuinely new ROOM is also newly minted and empty, so it separates novel destinations, not rooms from positions. Agreement with the string rule 35.4%. Tried because a critic noticed rule 5's own corollary names it and it had never been run |
| `NSR` | **report, never gate** | ranks sessions OPPOSITE to a blind reader, Spearman +0.923 |
| `SIL` | **report, never gate** | 0.0 in 18 of 18 runs; structurally impossible, see below |
| `deaf_occupied`, `unreciprocated`, `edges_lost` | **REJECTED** | measured, do not predict damage; see below |

## The three that failed a read on 2026-08-06

### 1. `_INTENT_CARRIED_RATIO` — a band that was an artifact of the sample

A two-arm replay of 20 synthetic replies on one scene produced mandated
`0.39-0.79` against unmandated `0.00-0.29`: an empty band, and 0.34 shipped at
its midpoint with a confident write-up.

A 40-turn live cell flagged 9 of 42 case-C events, and **a read of all 9 found
every one compliant**, several nearly verbatim. The cause was Portuguese
morphology — reported form says *"ordena que todos formarem"*, the character says
*"formem"* — which exact token matching cannot pair, plus the subject's own name,
which reported form always states and direct speech never does.

Pooled real and synthetic compliant replies span `0.15-0.79` against the same
control's `0.00-0.29`: **the clouds overlap and no threshold separates them.**
Stem-prefix matching was tried and made the overlap worse, because it lifts the
control too. Now 0.15, chosen by which error is affordable rather than by a band,
and the constant says so at length.

**Transferable:** twenty samples from one scene is not a distribution. A band
that appears at n=20 and vanishes at n=42 was never there.

### 2. `named_exclusions` — a false positive the archive could not show

Shipped with `\bmenos\b` in its exclusion-lead list. In Portuguese `menos` is
ordinarily the comparative, so narration like *"despenca a menos de dois metros
de Link"* read as excluding Link. It fired **15 times in one fresh session and
zero times across all 631 archived prompts**, which is exactly how it passed
review: the corpus it was validated on happened not to contain the shape.

Now requires a universal (`todos menos`). The archived before-number was
re-checked and is unaffected — all 371 hits were real.

**Transferable:** validating a guard against one corpus proves it works on that
corpus. Run it on fresh output before trusting the rate.

### 3. `empty_audience` — the right defect, counted at the wrong threshold

Reported **2** on the fresh cell, which reads as nearly clean. The transcript:

> **Garran**: *"Todos para o corredor lateral agora!"* — audience **1**
> **Nix**: *"Todo mundo pro corredor novo, agora!"* — audience **1**

**19 of 72 scoped records reached two or fewer witnesses with 21 characters
present.** Two were empty; the metric saw those and missed seventeen. Worse, a
zone-graph fix could drive it to zero and leave all seventeen — the
reclassification trap task 67 already warned about, through a door the warning
did not cover.

`clamp_lost_half` replaces the emptiness test with proposed-against-persisted,
which is non-circular for the same reason the existing classification is: it
never asks the suspect graph whether an audience was right.

**Transferable:** when a metric counts an extreme, ask what the near-miss
population looks like. It is usually larger and usually the same defect.

### …and then over-counted, corrected 2026-08-12

Widening the metric gave it a floor problem at the other end. On the verification
cell (`d0cc98e5`) it reported two residual losses, 19 → 18 and 20 → 19. Reading
them: in both, the Director had listed **the speaker inside their own
`witness_ids`**, the clamp dropped them correctly, and the counter scored that
as a lost witness.

Both counters now subtract the subject and de-duplicate. The threshold was never
affected — one in twenty is far from 0.5 — but `clamp_worst_loss` and
`clamp_evidence` are the fields a human reads to find a real graph bug, and they
were pointing at a non-bug. After the correction the cell has **no losses of any
size**, and the pre-fix baseline still has its six.

**Transferable:** a metric's evidence field has to survive being read even when
its headline count is already below threshold. The count was right both times;
the pointer was wrong.

### …and then measured the wrong thing, split 2026-08-12

A second post-fix cell (`00997daa`) came back with `clamp_lost_half` = **2**
where the first had 0. On the pre-registered criterion that is a partial
regression, and the honest reading of one cell at 0 and another at 2 is that
n=1 had closed the task too early.

Reading the two: both are a character **behind an explicitly sealed zone** —
Garran on the far side of the collapse the narration describes — with the
Director proposing nineteen courtyard witnesses across the seal and the clamp
correctly cutting it to one. The engine is right. The Director over-proposed.

So the metric never measured graph damage. It measures **disagreement between
the Director and the engine**, and that has two causes:

1. the graph is wrong — 67's actual defect;
2. the Director ignores a correct seal — a prompt-side issue, arguably not a
   defect at all.

`clamp_lost_half_unsealed` counts only cause 1, and across three cells reads
**6 → 0 → 0** with no crossover: every pre-fix loss unsealed, both post-fix
losses sealed. Sealing is detected by **asymmetry, not emptiness** —
`zones[Z] == []` while another zone still lists Z, which is the residue a
`zone_link_updates` seal leaves. A zone *born* isolated is empty both ways and
keeps counting, because that is damage.

**Transferable, and the sharpest one about THRESHOLDS on this page:** a metric that compares two
components attributes the gap to whichever component you already suspect. It
took a cell where the *other* component was at fault to notice. Two cells is the
minimum for any metric defined as a disagreement.

## ⚠ READ THIS FIRST: the session is the unit, and almost every p-value here ignored that

Added 2026-08-12 after measuring session-to-session variance under **identical
code**, four sessions per group:

| metric | mean | sd | range | sessions needed to see a 10-point change |
|---|---|---|---|---|
| **split rate** | 49.1% | **17.9** | 28.6 - 67.3 | **~51 per arm** |
| frozen-position rate | 88.3% | 6.1 | 81.0 - 95.5 | ~6 per arm |
| `return_control` rate | 2.7% | 3.9 | 0.0 - 8.3 | ~3 per arm |
| `empty_audience` | — | — | **0 or 7** | bimodal, one decision drives all 7 |

**The split rate swings by a factor of two on identical code**, and every
comparison this project has made on it used three or four sessions.

### The error underneath it

Nearly every test in these files - including most of the ones written on
2026-08-12 - was a Fisher exact on **pooled turns or pooled records**:
`16/29 vs 3/78`, `58/108 vs 30/108`, `168/610`. That treats each turn as an
independent draw. **It is not.** One Director decision - sealing a pulpit -
produces seven empty-audience records in one session. One graph shape produces
thirty split narrations. The correlated unit is the **session**, and pooling
turns inside it inflates the effective n by roughly an order of magnitude, which
makes p-values look far stronger than the evidence is.

**What this does and does not invalidate:**

- **Sound:** tests whose unit already IS the session. Task 64's *"control never
  returned in 5 of 12 sessions versus 0 of 9"*, p=0.045, is a real test.
- **Direction probably right, confidence overstated:** task 71's leak
  (16/29 → 3/78) and task 67's split-rate change. The effects are large and
  visible per session, but the quoted p-values are not defensible.
- **Never trust at n≤4:** anything built on the split rate.

**The rule going forward:** count the metric per session, then compare
sessions. If that leaves too few points to test, say so instead of pooling turns
to manufacture significance.

## The sharpest case on this page: 0.02 similarity, and a reader sees one paragraph

Found 2026-08-12 by reading `c76037ff`, after task 71 shipped that morning.

Its five-person cluster got sixteen narrations, eight of them with no events at
all, so the renderer described the room instead. Consecutive pairs score **0.02**
on sequence similarity. Every repetition instrument in this project reads that
as two unrelated paragraphs, and every one of them is wrong: the imagery is the
same every time.

| word | small cluster | main cluster |
|---|---|---|
| `quietude` | **44%** | 3% |
| `penumbra` | **50%** | 0% |
| `halos` | **19%** | 0% |
| `colunas` | **19%** | 0% |

A stillness vocabulary the busy half of the scene never touches. The model
varies its wording enough to defeat sequence similarity while saying the same
thing, which is exactly the failure mode a language model should be expected to
have and exactly the one `SequenceMatcher` cannot see.

**Transferable, and it generalises past repetition:** lexical distance measures
whether the WORDS changed. Nothing on this page measures whether anything
HAPPENED. When those two come apart, the reader tracks the second one, and every
instrument here tracks the first.

## The recurrence detector that carried a whole task, unread

Task 69's headline symptom - the Director re-proposing events it already
resolved - was **9.8% of events, 97 of 987**, produced by `sim(a,b) >= 0.6` over
events within three turns. The threshold had **no derivation, no empty band, no
false-positive population and no entry on this page**, and nobody had read its
hits until 2026-08-13.

Read, five flagged pairs from `55d03896`:

| sim | verdict on reading |
|---|---|
| 0.80 | ✅ genuine: *"A mesa central desaba parcialmente na fenda, revelando um duto"* twice |
| 0.70 | ✅ genuine: the same rune re-applied, restated |
| 0.68 | ~ the second EXTENDS the first (adds a screech) |
| 0.66 | ~ a progression: the rune is *started*, then *completed* |
| **0.62** | ❌ **false positive**: *"O clarão verde **continua** pulsando"* against *"O clarão verde **cessa de repente**"* - opposite events sharing vocabulary |

And the 0.4-0.6 band it clears contains at least one plausible repeat (a creature
crossing a wall, described twice at 0.41).

**So the 9.8% is not a rate.** It is the output of an instrument with roughly
half precision on a read of five, in the band where this project has already been
burned twice. Task 69's symptom is **OBSERVED, not MEASURED**, until someone
reads a proper sample.

**One thing that partly survives**: a biased instrument applied to both halves of
the same session can still detect a *difference*, provided the bias is constant.
It is not quite constant - baseline similarity between unrelated events (>=10
turns apart, so they cannot be repeats) drifts **+0.013** upward from first half
to second, rising in 14 of 19 sessions. That is small against the 0.29-to-0.60
gap, so it cannot manufacture the whole effect, but it is the right size to
inflate it.

**Transferable:** an instrument nobody has read is not a weaker instrument, it is
an unknown one, and a task can be built on it for weeks. This one was found by a
critic that had never seen the code, asking why a similarity score was standing
in for whether anything happened.

### The proper sample was read, same day — 2 false positives in 20 (10%)

Systematic sample (every 35th) of all **703** flagged pairs across the **33
distinct** sessions, each read individually:

| | |
|---|---|
| genuine re-proposals | **18 of 20** |
| false positives | **2 of 20 = 10%** |

Better than the *"roughly half precision"* the read of five suggested, and the
five-case estimate above is superseded rather than deleted — it was right that
the instrument needed reading and wrong about how badly it performs.

**Both misses share one shape: same phrasing, different content.**

- a fissure swallows **Mirella, Liora and Lucan**; one turn later a *new* fissure
  swallows **Cael, Ysara, Oriana and Téo** (`d0cc98e5` T28→T29);
- **Nix** shouts to back off the fissure edge, **Bruna** shouts to fall back to
  the arches because the fire will surround them (`5d60575d` T20→T22).

Neither is a repeat. Both score high because Portuguese emergency-shouting has a
small vocabulary. **A lexical detector cannot see that the people are different**,
which is the same blindness as *"opposite events sharing vocabulary"*, one level
up: it is not the words that changed, it is who they happened to.

**Verdict unchanged: REPORT, DO NOT GATE.** 10% is fine for describing a corpus
and not fine for blocking a Director's output.

**And the population is not what the task using it assumed.** Of the 703 pairs,
**43.4% are `audible_speech`** — the Director re-summarising speech — against
24.3% `physical_outcome` and 28.6% `observation`. Task 69 is about physical
events, so slightly more than half of its own headline number is somebody else's
defect. Pooled recurrence over the full archive is **703/5,064 = 13.9%**, per
session **median 12.5%, sd 5.2pts, range 4.6-24.9%** (n=31) — which is, unusually
for this page, a spread that does **not** destroy the pooled figure.

## An agreement figure needs chance agreement as its control

Recorded 2026-08-13, found by a critic given the numbers with the prose removed.

Two instruments were compared: one calling 16.7% of moves a reposition, the other
calling 93.2%. The reported agreement was **24.5%** — and with those two marginals
the arithmetic **ceiling** is 23.4% and the chance floor is 21.2%. The reported
figure exceeded its own ceiling (so a denominator was inconsistent somewhere), and
the entire feasible range corresponds to **kappa between 0 and 0.03**.

**An agreement percentage between two classifiers with lopsided base rates is
pinned by those base rates and carries almost no information.** It looked like
evidence and was arithmetic.

**Transferable, and it is rule 3 applied to a shape nobody thinks of as a metric:**
*the control for an agreement figure is chance agreement.* Compute it before
quoting the raw percentage, and if one classifier is near-degenerate — 93.2% one
way — say so instead, because that fact explains the agreement entirely.

## Matching a NAME: the failure that keeps recurring

### ⚠ It recurred again on 2026-08-13, in a NEW instrument, written after this page

**The fifth.** Task 79's hierarchical detector asked whether a destination's first
comma-segment was a **substring of** the origin. Every zone in the scenario is
named `Academia Real do Primeiro Sino, <somewhere>`, so it scored **every move
anywhere inside the academy** as *"repositioning inside a space they never left"*:
hall to outer courtyard, hall to meeting hall, meeting hall to east gardens. One
turn of `17ec48d5` scored 21 such moves and all 21 were the cast walking outdoors.

| | pooled | per session |
|---|---|---|
| the inflated rule | **37.6%** (228/606) | — |
| **corrected** (full origin plus a comma) | **16.7%** (101/606) | median **5.6%**, sd 22.0pts, range 0-79.3%, **12 of 27 sessions at zero** |

**The number that justified a task was about 2x too high, for three weeks.**

What makes this one worth its own entry rather than a tally mark: **it is the same
failure as task 76's two shipped false positives — a wing and a building read as
rooms — reproduced by an author who had read that lesson, written it into this
page, and cited it in the very file the new detector lived in.** Knowing the rule
did not prevent it. The pattern is not ignorance, it is that *prefix containment
looks like hierarchy* and hierarchy is what these names accidentally encode.

**The only defence that has ever worked here is reading the disagreement set.**
This was caught by printing 15 of the 127 entries the corrected rule rejects and
looking at them, not by either number seeming wrong. Both numbers looked fine.

**Transferable rule, stronger than the old one:** *never match a name with a
string heuristic* was not enough, because it reads as advice about proper nouns.
The operative version is: **any test of the form "is A part of B" over
model-authored place names is measuring a naming convention until you have read
the set it separates.** Substring, prefix, suffix and token overlap are all the
same trap.


Three times this month, in three different components, a guard matched a proper
name against Portuguese prose and fired on an ordinary word. It is the single
most repeated mistake in this register, so it gets a rule rather than a third
war story.

| where | matched | actually |
|---|---|---|
| `named_exclusions` (task 70) | `\bmenos\b` | *"despenca **a menos de** dois metros"* — a distance |
| `_strip_offstage_actors` (task 71) | any name token, case-insensitive | *"um **véu** opaco"* — Portuguese for veil, and Noa **Véu**'s surname |
| `scan_cross_cluster_leak` (task 71) | first names | inflated the pre-71 leak rate from 55% to 72% |

Every one passed review, and two passed a corpus. The corpus is the trap: a name
guard validated on 631 archived prompts fired 15 times on the first fresh
session, because the archive happened not to contain the shape.

**The rule.** A guard that matches a model-authored NAME must:

1. **require more than one token** where the name has more than one, matched
   adjacent — `Marta Ferrolume` is not a word anybody writes by accident, and
   `Marta` is;
2. **require the capital** where the name is a single token, since an ordinary
   noun mid-sentence does not carry one;
3. **drop any pattern that also matches something legitimate in scope** — a
   name shared with an on-stage character decides nothing;
4. **be replayed over real output including the sentences it should NOT touch.**
   The true-positive count is the cheap half. The false-positive population is
   the evidence.

Applied to `_strip_offstage_actors`, that took it from 6 fires with 3 false
positives to 3 fires with 0, over the same 42 narrations.

**And the asymmetry that decides the tuning:** for a guard that DELETES text, a
false positive destroys prose the reader is entitled to and a false negative
leaves one stray sentence. They are not the same cost, so when two variants
score equally on the true positives, take the stricter one.

## The three that were measured and rejected

`deaf_occupied` (an occupied zone that can hear nothing), `unreciprocated` (A
hears B, B does not hear A) and `edges_lost` (an edge present at turn N gone at
N+1), each computed per turn over all 16 archived sessions:

| session | `deaf`·turns | `unrecip`·turns | actual empty audiences |
|---|---|---|---|
| `oldcode-P1-r3` | 288 | **1764** | **0** |
| `drive-P1-r3` | 243 | 9 | **0** |
| `base-P1-r2` | **0** | 270 | **10** |
| `oldcode-P1-r1` | 0 | 0 | 2 |

**None predicts the damage.** Graph damage is *exposure*, not damage — a broken
edge costs nothing until someone speaks across it.

`deaf_occupied` was additionally just wrong: `zones[Z] = []` does not make Z
deaf, because same-zone perception is implicit. It was flagging ordinary closed
rooms, and 36 of 106 archived `zone_link_updates` deliberately create that state.

They remain useful as **diagnostics** — they are how the fresh cell's wiped hall
and `base-P1-r2`'s T20→T21 edge deletion were both located — and they are
recorded here as rejected so nobody re-derives them as dashboard numbers. Each
would look entirely plausible on a dashboard and rank sessions wrong.

## `SIL`, and why a constant is not always worthless

`SIL` is 0.0 in **18 of 18** runs including both 2026-08-06 cells.
`perception_events` requires one item and the prose floor is 150 words, so a
silent turn is structurally impossible. As a *guard* it is dead and must gate
nothing.

**It is not dropped**, because it is the standing evidence for **task 72**: the
engine cannot be still. A metric that always reads the same value still
documents a structural fact, as long as nobody mistakes it for a check that
passed.

## The critic subagent — first run, 2026-08-13

The instrument defined in `.plan/reference/critic-protocol.md`, measured for the
first time. It reviewed `.plan/CHECKPOINT-2026-08-13.md` in isolation: the
content and the critic prompt, no code, no task files, no history, no author.
27 claims extracted, 7 marked WORSE THAN ABSENT, 8 demoted, 2 promoted.

**It found two defects a human reader of the same document had missed.** Both are
verifiable in the text alone, which is the point:

1. **The phase's top-priority metric is stated twice, incompatibly.** The task-79
   row carries the post-audit figures (median 6.8%, sd 7.0pts, range 0.5-25.4%);
   the "standing numbers" table 111 lines later still carries the pre-audit ones
   (median 6%, sd 9.0pts, range 0-44%). Same metric, a range nearly twice as wide,
   no label saying which run is current — under a heading that invites quoting.
2. **A generalisation contradicted by the list it summarises.** *"Not one was
   caught by a number looking wrong... seven for seven, and it is the standing
   method"* sits four lines below a bullet reading *"Killed by a control that cost
   nothing, under a rule written before the number existed."* At least two of the
   seven were caught numerically. Promoted to "the standing method", that sentence
   reads as licence to skip controls — the opposite of what the same document
   demands elsewhere.

It also caught `"the mechanism is that settled state does not bind the output"`
sitting under a ✅ in a **mechanism** column with nothing behind it, and
`"every headline number carries its per-session spread"` asserted in a file where
four headline numbers do not.

### What it costs

**Isolation produces false alarms, and that is the design, not a defect.** The
critic called 76's *"firings track opportunity 6/6"* unsupported — *"the classic
shape of a detector that cannot see the negative case"*. The reasoning is sound
and the conclusion is wrong: that finding came from a cross-tabulation that did
include negative cases (a 53%-comma-named session with zero sibling pairs), which
is recorded elsewhere and was withheld from the critic on purpose. The verdict
still did its job — it is a ruling on whether *the text carries its own weight*,
and that text did not.

Budget for roughly one such alarm per document. The exchange is a good one.

### Status

**TRUSTED as a reader of documents. It gates nothing.** It cannot rule on the
world, only on whether a page supports what it says. When the critic and a reader
of the code disagree, the reader wins and the disagreement is recorded here — the
same rule that applies to every other instrument on this page.

n=1 document. Ask again after five.
