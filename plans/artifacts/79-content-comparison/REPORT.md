# Content comparison of current-turn blocking

2026-09-05. Keep the shipped current-turn blocking path and quality acceptance open, as fixed before this diagnostic. The text readers found some preferable phrasing with blocking, but the source check prevents treating that as demonstrated quality acceptance. The beam-crossing ambiguity remains in both variants. No fluency score, movement percentage or pooled winner rate is introduced.

## Design and evidence

Two targeted archived prose requests: bb72dc94 T9 and ea6620fb T12. Three calls per request with the original BLOCKING section and three removing exactly that section; same remaining messages, settings, confirmed events and preceding reader transcript. Call order seed 790906, maximum six simultaneous calls. Display order and same-index pairing use seed 790907. The protocol and explicit no-production-change decision were saved before dispatch. Source paths/lines/hashes are in `manifest.json`; `runs/` preserves exact curl requests, envelopes, execution snapshot and timings.

One bb72dc94 with-blocking request received HTTP 429; the provider reported “Your current concurrency is 5, which exceeds your concurrency limit of 5”. It remains missing and was not replaced. Eleven responses returned HTTP 200 with a nonempty parsed narration. Subsequent validation against the archived JSON Schema accepted ten and rejected `pedra-without-0`: its object also contains `narration_2: ""`, forbidden by `additionalProperties: false`. Results are retained in `schema-check.json`. The collector's initial parsing check was insufficient to establish schema validity.

The incomplete pair was shown as incomplete and its reader declined to compare it. The schema failure was discovered after the blind reading: evacuation pair 1 includes the extracted narration from that invalid envelope. Its literary judgment is preserved, but it is not a comparison between two contract-valid outputs. Only evacuation pair 3 and the three beam pairs have two schema-valid outputs. No replacement calls or retrospectively edited reader packets were used.

Each fresh reader received only one preceding visible scene and three opaque pairs, without arm identity, code or metrics. Reader packets are `reader-cedro.md` and `reader-pedra.md`; pair labels were joined to the saved `reader-key.json` after their judgments. One reader per scene means differences between scenes cannot measure reader reliability. These are immediate prose comparisons, without attaching archived downstream character replies to counterfactual prose.

## What the readers actually preferred

OBSERVED qualitative preferences; the pairs are alternatives within their original scene, not independent sessions.

| scene / pair | reader's response | reason and limit |
|---|---|---|
| beam / 1 | B, with blocking | Mostly rhythm: less interruption, clear closing phrase “isolando-os do salão em chamas”. The alternative introduces a shield during the escape. |
| beam / 2 | slight preference for B, with blocking | Less repetition of heat and a promising dark passage; “a madeira ... resiste” in A leaves resistance to pressure versus continued support unclear. |
| beam / 3 | B, with blocking | In A, “Asword, que estreita a passagem” assigns the narrowing to him, and “a madeira, que cede com um grunhido” grammatically assigns the grunt to wood. B has its own wording problem: “A passagem estreita se estreita”. |
| evacuation / 1 | B, with blocking; projection-only comparison | Explicit evacuation authorization and named quartet make the scene easier to follow, but that membership is unsupported, as checked below. A puts the scroll back in Garran's hand after the prior text left it on the floor; A's envelope also fails schema validation. |
| evacuation / 2 | no comparison | A is missing. The reader finds the available B, without blocking, legible but notes that “o salão inteiro se desloca” overgeneralizes who leaves. |
| evacuation / 3 | A, with blocking | B says “os dois dedos ausentes apontando”, a literal bodily contradiction, and returns the scroll to Garran's hand without showing a pickup. |

The beam reader's more important finding applies to all supplied alternatives: Asword pushes the beam, Marta and Link advance toward the opening, then it falls “behind the group”. Their completed crossing is implicit at the most dangerous moment. The reader cannot place the precise escape instant and group membership securely. This is a scoped comprehension concern, not proof that all elided motion is wrong.

## Check what the renderer was actually allowed to say

The primary source read covers all eleven extracted narratives against the actual request, including the schema-invalid projection. Per-output observations are retained in [SOURCE-CHECK.md](SOURCE-CHECK.md). This is a manual comparison, not an exhaustive semantic validation. The following examples explain why a blind preference is evidence to examine, not an acceptance score.

In evacuation pair 1, the preferred with-blocking text specifies “Link, Asword, Mirella e Seraphine formam um primeiro grupo”. The supplied event says only that students form hesitant groups and begin moving. BLOCKING lists these characters separately at their waiting marks; neither it nor the preceding transcript assigns that exact first quartet. The reader's reason for clarity therefore depends partly on added group membership; that reason cannot establish a supported improvement under the renderer's confirmed-events-only rule. Other descriptive differences, such as the appearance of the route, need separate judgment about permissible sensory elaboration; they are not automatically counted as defects.

In the beam input, Marta and Link “avançam em direção à abertura”, while the later event says the beam blocks the corridor “atrás do grupo”. Both arms inherit those phrases. The reader's unresolved crossing is present at the event boundary, not demonstrated to be caused or cured by supplying blocking. With-blocking pair 1's “isolando-os do salão em chamas” makes an implicit group interpretation more explicit without establishing who crossed.

The evacuation input also corrects an initial tracing mistake. A draft attributed the students' completed grouping to the prose renderer because it was absent from the Director's original perception_events list. But the same Director response includes `time_skip_ticks: 2` and `time_skip_summary: Os alunos formam grupos hesitantes e começam a se mover em direção à rota de serviço, enquanto Garran mantém a ordem e o alarme continua soando.` The debug time_skip record and actual prose request both carry that summary. Runner._apply_time_skip materializes it as an observation. **The attribution to renderer invention is withdrawn before becoming a plan conclusion.** The next Director response sets `group_formation` to “hesitante, quartetos ainda não formados”. That later return remains a continuity concern, documented in the [original sequence read](../79-content-read/REPORT.md), but the earlier grouping was supplied to the renderer.

## Limits and decision

This experiment is selected from two already-read scenes; one call returned HTTP 429 and another failed schema validation. The same reader judged each scene's repeated alternatives, and removing a block tests its combined information and instructions. Favorable phrasing may be stochastic. Nothing here establishes a corpus effect or which part of the block helps. The fixed decision holds: keep the current path, retain the concrete favorable and unfavorable passages, and leave quality acceptance open. No implementation or schema change follows from a reader's preference alone.

The source check changes what counts as evidence: a preferred passage may add unsupported detail, and an apparent renderer invention may already be an upstream confirmed event. Inspect the actual consumer request before attributing a narrative defect to that consumer.

## Reproduction

With the local source archives and configured provider available, `uv run python plans/artifacts/79-content-comparison/replay_content.py prepare` prepares an absent manifest, and the `run` subcommand dispatches the calls into an absent `runs/` directory. Existing results are protected against overwrite. The original execution snapshot remains in `runs/executed-script.py`; after the run, the source script's preparation guard was corrected to allow the artifact directory to exist while still refusing an existing manifest. The run's initial parsing check does not perform full schema validation; `schema-check.json` records the separate full validation described above.

## Review disposition

The claim critic accepted the scoped qualitative decision and requested evidence for the transport explanation, per-output source audit and later formation reset. The provider's reported limit, linked audit and quoted next-turn field supply those missing details. The later schema check additionally disqualifies evacuation pair 1 as a comparison between valid outputs; its text-only judgment remains explicitly limited to the narration projection.
