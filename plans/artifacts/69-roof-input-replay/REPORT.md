# Task 69: the ceiling replay does not meet its follow-up criterion

2026-09-05. OBSERVED in a manual read of 16 curl responses from two archived payloads in one session, 8bd4d0f1: each unchanged payload produced one clear fresh roof opening, two continuations and one ambiguous collapse. Removing the three planning lines produced no clear fresh opening, but retained ambiguity. The registered gate did not pass. Do not adopt the deletion or claim a causal diagnosis from this result.

## Input and fixed rule

Source: `plans/artifacts/repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl`, last successful recorded Director requests at T34 and T35, pinned with line numbers and SHA in `manifest.json`. At T33 the output said `O teto da câmara oculta desaba com um estrondo, abrindo um buraco ... e a entrada fica soterrada.` Later facts say `câmara_oculta: teto desabou, buraco aberto` and `entrada_câmara: soterrada`, while the plan still says `Current beat: O teto da câmara oculta desaba de repente` and `Not in play yet ... pedras do teto desabado, entrada soterrada da câmara, gritos de alunos próximos`.

A preserves the recorded messages. B removes exactly three lines: Current beat, Not in play yet, The beat ends when. Facts, history, act, clock and other instructions stay byte-identical. This bundles removing planning requirements with shortening the prompt; it does not isolate semantic conflict. The older task said "with no mandatory UPCOMING EVENT injection on those turns". T34 instead contains `UPCOMING EVENT (incorporate this into your narration): CLOCK SIGNAL: the scene has produced no material change for 2 turns; only waiting remains. Compress time now (time_skip_ticks) unless someone is visibly mid-action.` This block requests time compression rather than commanding a roof collapse.

The [preregistration](PREREGISTRATION.md), saved before dispatch and hashed in run metadata, required at least 3/4 RESET in A and at most 1/4 in B on BOTH payloads, all valid and no ambiguous cases, to warrant expanding this bundled-deletion experiment. Four replicates per arm/payload, randomized seed 690905, concurrency four, archived deepseek-v4-flash model name, original max_tokens and json_object, thinking disabled. The provider may have changed since the historical run. Replicates and adjacent turns are not independent sessions.

## Read before revealing arms

OBSERVED manual classification of the full parsed outputs in shuffled opaque order. Judgments and quoted evidence were saved before opening read-order.json. Arm labels were concealed; the reader knew the design and could infer it from prose, so this is not an independently blinded judge. No reliability estimate. RESET requires a fresh initial collapse/opening; CONTINUATION includes the existing hole, another explicit block or a distinct roof section; ABSENT means no roof event beyond background blocking; AMBIGUOUS retains reset-versus-further-damage uncertainty.

| payload / arm | RESET | CONTINUATION | ABSENT | AMBIGUOUS | allocated calls |
|---|---:|---:|---:|---:|---:|
| T34 A original | 1 | 2 | 0 | 1 | 4 |
| T34 B deletion | 0 | 2 | 1 | 1 | 4 |
| T35 A original | 1 | 2 | 0 | 1 | 4 |
| T35 B deletion | 0 | 2 | 1 | 1 | 4 |

The session is the unit, n=1; there is no between-session spread to report. These small counts describe manual labels, not corpus rates or a measured quality improvement. The A repeatability criterion fails on both turns. Even counting every ambiguous A as RESET would give only 2/4, still below the pre-specified 3/4. The zero-ambiguity requirement also fails.

Readings that determine the outcome:

- R05 (T34 A): `O teto da câmara desaba com estrondo, abrindo um buraco`; R10 (T35 A): `abrindo um rombo`. Both stage the initial opening anew without identifying a remaining section: RESET.
- R11 (T34 A): `O teto acima da arquibancada norte ... uma seção inteira se desprende`; R12 (T35 A): `Uma segunda laje do teto norte se desprende`. Distinct/additional material: CONTINUATION.
- R13 (T34 B): `Um novo bloco do teto da câmara se solta ... sobre o monte de escombros`. Additional block onto existing debris: CONTINUATION.
- R03/R14 (B): `O teto da câmara oculta se desfaz ...`. No fresh opening or explicit remaining section; disintegration of remnants remains possible: AMBIGUOUS.
- R08 (T35 A) says `desaba com estrondo`, but its state says `desabou por completo`; completion of partial damage is not ruled out. R15 (T34 A) says `Um novo desabamento soterrou completamente a entrada`; additional debris versus re-staged burial is unresolved. Both AMBIGUOUS.

## Output validity and wider reading

All 16 returned HTTP 200 and parseable JSON. A separate check with `src.llm.schema.validate_json_schema` against the exact schema embedded in the archived system message accepted all 16. The collector's initial check only established a parsed perception_events list; it did not establish schema validity. Missing return_control and the scene_change kind looked suspicious during reading. The embedded schema has a return_control property but excludes it from required, and its event_kind enum explicitly contains scene_change. Both are permitted by this historical schema. No retry or replacement was made. Schema conformance does not establish semantic consistency.

Full-output reading found concrete changes outside the roof in several responses: new fissures and darkened lamps (R00), ice forming and cracking (R02), mist striking Maelis's boot (R04), a drained bracelet charge (R06). It also found inconsistencies: R04 attributes its Maelis event to C3 (Mirella Valecourt), rather than C17 (Diretora Maelis Ordan). R05 says `A névoa está subindo pelo duto!` while scene_update sets `névoa_subindo_pelo_duto: false`; the output provides no intervening stopping event. R01 largely sustains sparks, orders and faint calls rather than clearly advancing the rescue. These are qualitative observations without an all-defects metric; no arm-wide superiority follows.

## What this changes

The two selected archival roof payloads now have contemporary isolated replays, and neither meets the pre-specified unchanged-arm repeatability criterion. The state/planning juxtaposition remains visible. Treat semantic conflict as a hypothesis: a beat can describe an ongoing disaster, and this comparison does not isolate what the planning text means to the model. Causal contribution and a production remedy remain undiagnosed. Current code and durable-state design are unchanged.

Artifacts: replay_roof.py prepares/runs/creates the opaque dossier; manifest.json pins source requests; runs preserve exact requests, raw envelopes, execution snapshot/hash and timings; manual-judgments.json precedes unmasking; schema-check.json records the archived contract validation; summary.json joins labels to arms. Raw JSON follows the existing local artifact policy. 

Local provenance check: preregistration mtime 2026-09-05T16:36:22.505117+00:00; dispatch metadata started 2026-09-05T16:36:24.008925+00:00. Script snapshot, manifest and preregistration SHA-256 all match execution metadata. These local records are not immutable third-party timestamping.

## Review disposition

The isolated critic accepted the failed gate and payload-level counts as OBSERVED, falsifiable by the saved output-to-label join or a contradictory contextual read. It rejected “strongest payloads” because no ranking was defined; the report now says selected. It also rejected treating semantic conflict as established; that claim is demoted to THEORY, including the motivating wording retained in the preregistration. Clock and schema claims now carry their exact operative text. The manual categories are a scoped reading instrument, not a validated quality measure.
