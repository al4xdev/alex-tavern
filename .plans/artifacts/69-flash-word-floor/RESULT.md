# Flash without reasoning: 600-word replay

Observed result: the retained local English Gemma outputs missed 600 words in 9/9 draws. Flash met it in only 1/27 logical replays of those same nine prose inputs. This closes the narrow word-floor question for these samples; it does not select a production model or close Task 69.

## Frozen method

All nine actual English prose requests were replayed three times each through the production DeepSeek adapter/client and curl. Messages, scene, history, confirmed events, scope, schema and 4096 output-token budget were retained. Native local JSON grammar differs from DeepSeek JSON-object plus schema-in-system adaptation; this is a provider-path comparison, not a pure model-weights experiment. Local has one retained draw per input, Flash three; no population reliability estimate follows.

Every one of 35 outgoing HTTP attempts explicitly requested 'deepseek-v4-flash', 'thinking.type=disabled', and no 'reasoning_effort'. No Pro, fallback, runtime configuration change or new Director/Character chain was used. The response envelope labels all 34 received JSON envelopes 'deepseek-flash', with no reasoning text.

The pre-registered primary metric is whitespace-delimited narration words >=600, with the full-pass gate 27/27. Schema/transport failure is a nonpass. Only existing bounded error retries apply, never short-output or semantic retries. The manifests and actual request bodies were frozen before paid execution; source hashes remained unchanged.

## Results on these inputs

| Retained prose input | Local words (one draw) | Flash words (draws 1 / 2 / 3) |
| --- | ---: | --- |
| chain2-t2-call2 | 316 | 290 / 264 / 439 |
| chain2-t3-call6 | 105 | 329 / 132 / 415 |
| chain2-t4-call11 | 308 | 478 / 354 / 360 |
| chain2-t5-call18 | 294 | 574 / 465 / 554 |
| chain2-t5-call19 | 189 | 350 / 418 / 404 |
| chain3-t2-call2 | 320 | 184 / 333 / 0 |
| chain3-t3-call6 | 318 | failed / 534 / 465 |
| chain3-t4-call11 | 164 | 600 / 272 / 428 |
| chain3-t5-call15 | 150 | 540 / 421 / failed |

Flash: 25/27 schema-valid final outputs, including one empty narration; 24 nonempty. Among the 25 valid outputs, word count range 0–600, median 415. Exactly one met the floor. The local range was 105–320, median 294, with 0/9 meeting it. These counts describe the retained inputs, not all roleplay or all languages.

There were 35 attempts for 27 logical draws: 34 HTTP-200 JSON envelopes, nine of which contained forbidden extra keys such as '_comment', '_note' or 'additionalProperties'; one final curl attempt timed out at 240 seconds without a response body. One draw exhausted three schema-invalid responses; another exhausted two schema-invalid responses and the timeout. All 34 received envelopes ended with 'stop', so their short outputs were not reported as output-budget truncations. Empty string satisfied the current string-only schema but is not useful narration.

Provider-reported usage across received envelopes: 47,906 input and 17,128 output tokens, including failed schema attempts. Maximum input 1,949, output 729. Logical-call wall time at concurrency three: 2.267–250.714 seconds, median 5.042, including retries. This isolated timing is not comparable to prior full Runner turn time; tokenizers differ, and absent timeout usage is unknown.

## Reading the prose against its actual source

An independent text-only reader examined 26 terminal results with their exact source messages and local texts while the last draw was pending. The last draw ended in failure, adding no valid prose. The findings below were checked against the retained messages and outputs; they are observations, not a narrative quality score.

- The sole 600-word output, 'chain3-t4-call11' draw 1, says Bento moves into the tunnel, 'out of the hall entirely'. Its current blocking explicitly says 'Bento: hall'; confirmed events describe floor cracking/collapse only. Historical 'follow them into the tunnel' is present as an action, so the input contains a competing cue, but the current blocking instruction says to narrate from it. Meeting the word floor did not preserve that boundary.
- 'chain2-t4-call11' draw 2 replays 'The iron bar gives way' and Téo crossing the threshold. The sole confirmed event is the lantern flickering in a draft from an already opened portal. This is visible historical restaging, not lexical similarity detection.
- All three Flash draws of the subjectless opening case 'chain2-t3-call6' assign bar removal to Bento and crossing to Téo, unlike the retained local prose which assigned both to Téo. The actual prose events omit the actor subjects, so this is observed resolution of ambiguous input, not proof that Flash always follows named actors or that the missing subject caused the local error.
- Flash supplies concrete sensory prose, but also repetitive spatial inventory and inaction: 'In the courtyard, nothing has changed' and 'She does not move toward the portal. She does not speak.' These phrases conflict with the prompt's request to omit actors with no new events. No floor-enabled/disabled control was run, so attributing filler to the 600-word instruction would be unproved.

Reader claims of spontaneous bar relocking and material inconsistencies are not promoted here without a full per-source adjudication. No semantic pass rate or claim of overall Flash superiority is made.

## Evidence and decision

The frozen [protocol](PREREGISTRATION.md), replay helper, summarizer and [all terminal prose outputs](TRANSCRIPTS.md) are retained. Ignored local 'manifest.json' and 'runs/' hold exact messages, source metadata/hashes, every request/raw/transport/result/client log, summary and independent reader evidence. Tests used isolated /tmp data. No runtime Python, provider configuration or prompt changed.

Decision: this Flash-without-reasoning sample fails the 600-word gate too. Longer observed text alone is insufficient to choose it, because the long output still violates blocking and another output restages history. These results do not demonstrate a training-language, reasoning, quantization or recent model regression cause. Reasoning-enabled behavior was not tested.

Independent report review accepted the numerical and source-fidelity claims, with no causal promotion. It classified credential-handling detail as neutral; that detail was removed from the findings. The quantitative counterreading conditions the floor on schema validity (1/25), which still fails the registered gate. The historical action cue in the 600-word example remains explicit, so this is not reported as length-induced drift.
