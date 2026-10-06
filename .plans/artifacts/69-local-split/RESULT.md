# First local Gemma physical-beat round, 2026-10-05

1. MEASURED, narrow fixture: Gemma-4-26B-A4B-StyleTune-QK-Heretic IQ4_XS, owner server context32768, reasoning off, default stochastic sampling. Actual Director, forced Bento Character, prose, perspective and automatically triggered planner calls ran through Runner transactions, curl, isolated /tmp data, save and reload. Human action was Iara observing her lamp; fixture-supplied causes were NPC/world stimuli. Character personas were generic factory placeholders. No paid DeepSeek request, server/config alteration, or production activation.

2. MEASURED, contract controls: flat physical_steps failed first submission in all3 chains; textual field descriptions still failed all3. Both produced valid native-grammar JSON but illegal operation fields, with unchanged persisted state. Split aperture_changes/attempt_results omitted irrelevant fields and lowered mechanically to the same physical validator. Split succeeded on all3 first submissions; full four-submission chains completed2/3 (chain1 and chain3). Chain2 committed blocked/open-crossed turns, then was rejected after a generated planner and Director proposed Bento entering the tunnel despite the explicit no-movement stimulus. Persisted state remained unchanged. Gate all3 chains was NOT met. Split gate success does not erase the six preceding failures.

3. MEASURED: split had10 committed submissions out of11 attempted: per-chain4/4,2/3,4/4. Each committed result matched blue closed/open/open/closed at its reached stage, green closed, Téo hall/tunnel/tunnel/tunnel; every reload matched persisted data. Semantic admission callback was a recording mock returning True, not a validated reviewer. Aperture/crossing fixture and fixed operation order only, not general six-family ownership or Task69 closure. A correct state does not mean correct prose.

4. OBSERVED textual defects: chain3 turn2 prose opens “no momento em que o portal azul se fecha por completo”, restaging the historic Turn1 closure as current, although current confirmed event was only a blocked push. Chain2 turn3 narrates Bento fetching an alcove bar and using it as a lever rather than removing the blocking bar; the Director had already introduced “retira uma barra pesada da alcova”, so distortion exists upstream as well as prose. Chain1 turn3 contains “uma transição física clara que remove Téo da zona principal”, showing mechanical wording despite correct final crossing. Word oddities include “fôlecr” (chain3 turn2), “reverberecho” (chain1 turn5). These are bounded readings, not an error-rate detector or cross-model comparison.

5. MEASURED word-floor failure:13 generated prose responses, all115–385 whitespace-delimited words, each requested at least600. Per-chain counts287/285/115/135/205;361/307;385/375/206/171/175/257. Some turns generate separate viewer prose, hence response count differs from turn count. All57 responses across three variants finished stop, none length. Output reservation4096 narrator1024 character; no evidence these short outputs were caused by token exhaustion.

6. MEASURED resource sample:57 total local HTTP calls (3 flat,3 described,51 split). Usage sums117607 input and16246 output tokens, including every retained attempt/view/helper call. Largest single input6411, output683, combined7020, comfortably within32768 for this short fixture; no long-session context claim. Split committed-turn log interval from input timestamp to last event ranged20.22–35.68 seconds, median27.495 across10 submissions. This is a log interval proxy under up to two concurrent chains, not isolated latency or per-call durations added serially.

7. Decision: keep this local model as a development/testing candidate, but this round does not justify replacing the Director outright or claiming narrative reliability. State/contract failures, old-event prose restaging, word-floor misses and upstream causal drift remain concrete defects. The first useful implementation signal is separate operation contracts rather than expecting irrelevant empty placeholders. Independent reader findings must be checked against raw source and viewer scope. Production and task status remain unchanged; all failures retained.

Evidence: directories69-local-chain,69-local-described,69-local-split, frozen manifests and source hashes; runs contain original requests/raw transport, generated output, state starts/persisted/reload checks, copied debug JSONL and summary. Reproduce in an isolated /tmp ROLEPLAY_DATA_DIR. No semantic resampling or hidden hand-authored future history.

Reviewer 61307c7b0b93 accepted the bounded claim structure, while warning that these are generic personas, stochastic small samples, a mocked semantic gate, and log interval proxies. Its agreement is not an independent correctness score. Word-floor observations do not establish quantization or training-language as the cause. User's English-language hypothesis remains untested in this Portuguese round; any English comparison must retain scenarios, validation and acceptance rules, translate the narrative stimuli/history, and be reported separately.

Independent text reader225f6305c249 quoted the same old-closure restaging,
mechanical diction, invented alcove-bar cause and Portuguese defects. Its alleged
audible_speech omissions are rejected: the actual renderer removes those events
and lexical dialogue is displayed separately. The packet contained backend events,
which cannot establish a renderer omission of events it never received. Its alleged
offstage visual leaks also remain unproved: actual C3 renderer requests include
all three actors under IN THIS VIEW through the larger physical staging scope,
and shared public facts. Sound perception is not the same as visual perception,
but this packet does not isolate that boundary. No general privacy failure is
claimed. The phrase “transição física clara” is observed mechanical diction,
not proof that an internal machine field or private fact leaked.

The reader described generic illumination paragraphs as generated to meet the
word floor; that causal explanation is unsupported and not adopted. All word
counts were below the floor. Stylistic repetition is observed, not assigned a
training, language, quantization or prompting cause. No critic vote is scored.

Validation: scoped Ruff check and format passed; frozen source/dependency hashes
remain unchanged for all three manifests. No runtime Python change, so this round
does not repeat the full repository test suite. Raw provider calls and actual
transaction boundaries, including refusal rollback and reload, were exercised.
Full public generated text is retained in [TRANSCRIPTS.md](TRANSCRIPTS.md).
