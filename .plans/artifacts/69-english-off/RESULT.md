# English without reasoning on the historical act-completion cases

Observed conclusion: English did not resolve the closure problem in this Flash-off replay. All four English hall-closure plans left the completed act open. Two English canyon replies advanced correctly, but the other two did not. The fresh Portuguese control also failed on confirmed closure. This is a three-case diagnostic, not a language or model quality benchmark for all roleplay.

## Frozen comparison and observed flags

The same three retained synthetic planner requests that informed the earlier reasoning diagnostic were replayed in Portuguese and translated English, four fresh draws per language/case. Translation preserves the ambiguous CURRENT BEAT label, recent-event placement, STATUS coverage completion, facts, field descriptions/order and character IDs. A bilingual independent reader checked closure certainty and temporal order; contact and resultant-location wording was tightened before freezing. Exact inverse substitutions verify structural parity, not linguistic equivalence.

Both arms explicitly requested deepseek-v4-flash, thinking disabled, no reasoning_effort and 8192 output tokens. Twenty-four direct curl calls, concurrency four and frozen shuffled launch order; one attempt each, no retries, replacements or semantic repair. No Pro or high arm, no provider fallback or runtime change. These archived requests include obsolete prompt IDs retained for replay parity, not adopted into production.

| Confirmed source / required flag | Portuguese off: valid / correct | English off: valid / correct |
| --- | --- | --- |
| Failed closure attempt; portal remains open / false | 4/4 / 4/4 | 4/4 / 4/4 |
| Portal completely closed; people remain in hall / true | 4/4 / 0/4 | 4/4 / 0/4 |
| Portal closed after crossing; people now in canyon / true | 4/4 / 1/4 | 4/4 / 2/4 |

The pre-registered English all-cases gate fails because the sampled flags are wrong, not because of infrastructure. All 24 replies were HTTP200, schema-valid, distinct nonempty IDs, finish_reason stop and no returned reasoning text. Requested API settings and response fields verify the observable off mode, not hidden internal cognition. These repeated draws share only three inputs; the 2/4 versus 1/4 canyon difference does not establish a general English benefit.

## Textual reading: where the story still breaks

All 24 generated plans were inspected against their exact source. These are planning contracts, not prose narrator or Character outputs. Readability here cannot demonstrate reader-facing English narration quality.

- English hall draw 1 explicitly says 'The widening passage is not closing' and asks for 'another way to seal the portal'. The source says it closed completely and no open passage exists now. This is a textual continuation of the obsolete objective, in addition to the false flag.
- Portuguese hall draw 3 says 'Com a passagem já selada e as runas apagadas' but returns act_completed=false and plans a1-b2. Recognition of the correct event in prose does not make its structured decision agree. Its new collapsing floor is prospective pressure allowed by the architect prompt; it does not itself undo the already satisfied exit.
- English hall draw 4 explicitly proposes 'reversing the earlier closure'. A NEW reversal can be a legitimate next threat, but does not justify reporting that the previous confirmed closure never completed the act. Do not count all future reopening plans as source contradictions.
- English canyon draw 1 introduces "Bento's dropped coil of rope", although the source establishes a map and no rope or rope-dropping action. Its source-invented premise is separate from the proposed canyon pressure.
- English failed-attempt draw 3 has the correct false flag but its exit requires that 'the characters realize the runes need a different approach to close'. This scripts a cognitive conclusion despite the instruction to preserve character choices; flag correctness misses this contract problem.
- English canyon draw 3, a correct flag, starts with the closed portal and introduces a rockfall and route obstacle while moving to a2-b1. That is an example of a coherent objective transition, not evidence that all flag-correct plans preserve agency or every source detail.

The quoted examples establish specific continuity and field-agreement failures, not their frequency across roleplay or a general naturalness ranking. No narrator prose was generated, so this screen cannot answer whether English narration sounds better. Vocabulary and output length were not used to certify quality.

## Scope and accounting

The older disabled/high tables are historical context only; see [their report](../69-order-versus-reasoning/RESULT.md). The current Portuguese-off hall result (0/4 correct) differs from the earlier original-off 3/4. The cause of that difference is unestablished; dates and historical request model alias differ, and these tiny repeated samples do not isolate model changes. No fresh high arm was run, so this does not measure the current high advantage or show that English can replace it. The production order and labels have also evolved; this deliberately retains the old ambiguous inputs instead of benchmarking the current builder.

Provider-reported usage: 23,560 input and 5,845 output tokens. Individual curl wall time 1.884–3.040 seconds, median 2.3865, at concurrency four. These are planner calls, not full-turn latency. Word counts were not used as a quality metric.

Evidence: [protocol](PREREGISTRATION.md), replay helper, summarizer and [all 24 generated plans](TRANSCRIPTS.md). Ignored local manifest/runs retain exact request bodies, raw responses, transports, per-call session/turn/agent debug metadata, summary, reader and pre-review records. Frozen dependency hashes verified after execution. Artifact lint and format checks passed; no runtime source/config was modified and no production data was written.

Decision: retain the result as a failed English-off diagnostic on these ambiguous planning inputs. No language/default reasoning change or Task69 closure follows. It supports checking actual event/plan agreement rather than treating a fluent English plan as evidence of correct progression.

## Independent review dispositions

The source-bound plan reader independently identified the hall false flags, explicit denial of closure, and unestablished dropped rope. Its claims that new creatures, rifts or magical artifacts are automatically hallucinations are rejected: the architect is explicitly asked to introduce new external pressures. Its claim that any reversal falsifies historical closure is also rejected; a new reversal is allowed, but it does not erase prior act completion. Physical pressure on gear and prospective exit conditions are not automatically authored voluntary choices. Claims of hidden location/recency mechanisms were not adopted.

The report critic retained the flag table and concrete field/text disagreement, and requested removal of aggregate naturalness/trope assertions; those were removed. Its paraphrase that the historical baseline difference was attributed to stochastic/alias drift is rejected: the difference has no established cause. Its proposal that textual observations require an invented quality percentage was not adopted; the report retains named counterexamples without a population or semantic pass rate. No global reasoning or language superiority claim follows.
