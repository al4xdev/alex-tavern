# Second local Gemma round: English
## Decision
These short English samples read more cleanly than the retained Portuguese samples,
but changing language did not meet the mechanical gate, the 600-word floor, or a
general narrative-reliability claim. Keep this result as a language probe, not a
new default-language decision or a replacement approval. This is not evidence
about DeepSeek.

## Scope and method
Three new stochastic chains repeated the Portuguese **split-contract** fixture:
blocked crossing, Bento unbars/opens and Téo crosses, no portal/position change,
then a NEW gust closes the portal with Téo staying in the tunnel. Same IQ4_XS
GGUF/server, context32768, reasoning off, sampling defaults, two concurrent chains,
output limits4096/1024, minimum600 narrator words, forced real Bento speech and
ordinary automatic planning. Initial story, stimuli, public scene/zone/target
names and goal labels were translated; actor names/IDs and generic profiles
remained unchanged. Reversing the frozen map recovers the exact PT initial state;
all nonlanguage config and server metadata match. The bilingual reader found no
changed causal mechanism or exclusion in the pairs.

This is an all-English interface/stimulus bundle, including public enum labels,
not a causal test of output-language policy alone or equal tokenizer pieces.
Actual production builders, native grammar and curl were used in isolated /tmp
sessions. The physical reviewer was the same recording mock returning True.
No semantic resampling, paid provider, owner config/server change, production
integration or Task69 closure. Each chain stopped at its first failure.

## Measured results
Only compare EN to the retained PT split round; the earlier six Portuguese
flat-contract diagnostics are excluded from this table.

| Observation | Portuguese split | English split |
|---|---:|---:|
| Complete four-submission chains | 2/3 | 2/3 |
| Committed / attempted submissions | 10/11 | 8/9 |
| Per-chain committed / attempted | 4/4, 2/3, 4/4 | 0/1, 4/4, 4/4 |
| Prose responses meeting600words | 0/13 | 0/9 |
| Prose word range, whitespace count | 115–385 | 105–320 |
| Local HTTP calls, including helper/view calls | 51 | 41 |
| Usage input / output totals | 95,200 / 13,496 | 71,944 / 9,260 |
| Largest input / output, possibly different calls | 6,411 / 683 | 5,460 / 670 |
| Largest combined single call | 7,020 | 6,053 |

EN word counts by chain: none;316/105/308/189/294;320/318/164/150.
All41 EN completions finished stop, not length. Shortness was not output-token
exhaustion. All8 accepted submissions matched the registered aperture/position
expectations and exact reload equality. ENchain1 failed on its first Director
draw: attempt_results correctly said blocked, but scene_update proposed
{"blue portal":null}; that contradicts/removes a currently closed tracked fact.
The Runner refused it and persisted state remained identical when deserialized as domain data. The all3-complete gate therefore failed; it is not an 8/9 pass.

The first Director input had3,909 tokens in every PT draw versus3,878 in every
EN draw,31 fewer (~0.8%). Most technical instructions were already English.
This sample does not support a large token saving from Portuguese-to-English
translation. Lower EN aggregate totals also include an earlier chain failure,
different prose-view/call counts and shorter histories, so they are not a language
cost comparison. Both short fixtures fit32k; no long-session context claim.

Accepted-submission input-to-last-debug-event intervals: PT20.217–35.683s,
median27.495; EN23.406–40.657s, median30.073. EN per-chain ranges26.565–40.657
and24.839–33.920, no accepted turn in chain1. EN measured wall time was also
retained separately. These are descriptive observations under concurrency,
cache/scheduling and differing call mix, not evidence English is intrinsically
faster or slower.

## Reading the generated fiction
OBSERVED, not a numerical fluency benchmark: the English prose avoids the conspicuous
Portuguese corruptions such as “fôlecr” and “reverberecho” in the earlier sample.
Both independent English readers found grammatically readable prose with recurring
mechanical diction and light/shadow padding. Examples: “newly functional aperture”,
“localized heat emanating from the wick”, and “the structural integrity of the
chamber floor continues to fail”. The narrator still sounds technical in places.

ENchain2 turn3 has a concrete actor swap: “as Téo wrenches the obstruction free”.
The Director operation cause names Bento and its first event has subject_id C2,
but the actual renderer prompt renders only “removes the heavy bar and pulls the
blue portal leaf until it is fully open”, with no grammatical subject; the crossing
event likewise says “steps through...”. The prose assigns the intervention to Téo.
That source loses the event actor attribution; it cannot be described as a model
ignoring an explicit Bento subject in its renderer input. Input ambiguity is a
plausible contributor, not a counterfactually demonstrated cause.

ENchain2 turn4 introduces “A sudden gust of air...” in prose. The Director already
introduced “a sharp draft...” despite the test stimulus stating no new gust.
This source/input discrepancy is upstream, not invented solely by the renderer;
a draft through an opened passage versus an external gust is a possible weaker
reading, so no equivalent aperture/position contradiction is claimed. It still
shows that correct tracked state does not guarantee preservation of every stimulus.

In ENchain3, the admitted physical events and prose preserve Bento's intervention,
Téo's crossing and the newly caused final closure. The reviewer found no actor
swap or repeated old closure in that chain. Its additional floor collapse was
already admitted by the Director and was not prohibited by the fixture's narrower
portal/position rules. Therefore its appearance in prose is not a fabricated
renderer event. Claims such as “the blue portal rekindles itself” add magical
details not confirmed in that turn; their acceptability as sensory expansion is
not resolved by the aperture gate.

The old Turn1 closure was not freshly re-enacted in these nine English prose
responses as it was in the cited Portuguese chain3 turn2. This bounded reading
does not establish that English fixes restaging or that the problem is absent in
other scenes. Rich personas and long sessions were not evaluated.

## Implication
This round does not decide which language/model should become the runtime default.
The current evidence supports cleaner surface writing in these samples, not a
successful replacement of the Director or an explanation for DeepSeek degradation. Actor attribution reaching prose and repeated technical
diction remain concrete issues to investigate; the inference that language alone
solves them is unsupported.

[Protocol](PREREGISTRATION.md), [generated transcripts](TRANSCRIPTS.md),
[Portuguese baseline](../69-local-split/RESULT.md). Retained runs include frozen
manifests/hashes, raw requests/responses/transports, exact renderer contexts and
viewer/staging scopes, debug JSONL, start/persisted states, reload/rollback checks,
usage/timing comparison and independent reader records.

## Independent review and validation
Report reader4865dc1ea8ec challenged promoting English from these unequal small
samples; the recommendation was narrowed to retaining this diagnostic result,
without a new runtime-language policy. Its summary overstated subjectless input
as a demonstrated cause of the actor swap; no subject-injection counterfactual
was run, so that causal attribution remains a hypothesis. It also described the
prose cap as1024; actual narrator cap was4096, character cap1024. All nine prose
requests explicitly contained the600-word instruction.

Readers7e8d272710b1 andff79f2b50e68 independently read each surviving English chain
with actual adapted renderer messages. Their claims that the word floor caused
padding, or that a closed aperture implies a prior magical hum, are not established
by this experiment. Reader7e8d272710b1 also called the shared C2/C3 final prose a
viewpoint failure: the call had larger C1/C2/C3 staging and retained zone audibility,
so hall descriptions alone do not prove a privacy leak or a false actor position.
That finding remains qualified; no generalized view-leak verdict is adopted.
Grammatical fluency is a reading judgment; agreement is not an accuracy score.

Checks: all41 requests/raw responses/transport records retained, every transport
HTTP200 and exit0; all three chains terminal; refused turn leaves start/persisted
state equal; all accepted state/reload assertions true. Experiment dependencies
match frozen hashes. Scoped Ruff check/format pass. Runtime Python was unchanged;
no gratuitous full-suite rerun. This screen wrote synthetic /tmp sessions and
artifacts; it did not change the owner's .data config, existing sessions, secrets,
or server settings. No task closure, remote Git operation, or further model call
is required to finish this report.
