# Token economics as an architectural enabler

**Captured:** 2026-07-16  
**Evidence window:** 2026-06-18 through 2026-07-16 UTC  
**Provider export:** DeepSeek usage and cost CSVs generated on 2026-07-17  
**Status:** Interim V1 case study; update through the Alex Tavern 1.0 release

## Abstract

Alex Tavern deliberately favors explicit agent boundaries over minimizing model calls. A turn may
involve a Director, prose renderer, Character agents, perspective initialization or revision, a
Historian, and development-only critics or evaluators. This is more complex than one omniscient
prompt, but it makes authority, privacy, validation, replay, and failure attribution explicit.

The economic premise is that provider-native prefix caching makes large stable contexts cheap
enough that token count is not the first optimization target. The billing export examined here
contains **511,961,017 tokens across 8,240 requests for USD 7.9055**. Of 509,511,887 input tokens,
**493,134,592 were cache hits (96.79%)**. Applying the prices recorded in the export, the same input
volume charged entirely at cache-miss rates would have produced an estimated total cost of
**USD 198.02**, including the unchanged output cost. The observed total was about 4% of that
counterfactual.

This does not prove that additional agents are free or always beneficial. It supports a narrower
decision: for this workload and provider, collapsing semantic responsibilities merely to save
input tokens would optimize the wrong constraint. Correctness and knowledge isolation come first;
latency, dependency topology, and output volume remain real constraints.

## 1. Question

Should Alex Tavern keep a comparatively complex multi-agent architecture when a simpler design
could use fewer calls and fewer prompt tokens?

The working hypothesis is:

> When stable prefixes dominate model input and provider-native caching is effective, separate
> semantic authorities can improve correctness and observability at acceptable monetary cost.

The hypothesis is intentionally conditional. It must be revisited if cache behavior, provider
prices, latency, workload shape, or product scale changes.

## 2. Data and method

The source archive was downloaded from the provider dashboard as
`usage_data_2026-06-17_2026-07-16.zip`. Its internal CSVs cover rows through 2026-07-16 and contain:

- daily cost by model;
- cache-hit input tokens;
- cache-miss input tokens;
- output tokens;
- request counts;
- the per-token price applied to each category.

The raw archive is **not committed** because it contains account and redacted credential metadata.
This case study retains only aggregates. Costs were recomputed as:

```text
observed cost =
    cache-hit input × cache-hit price
  + cache-miss input × cache-miss price
  + output × output price
```

The no-cache counterfactual keeps output unchanged and charges all input at the corresponding
model's cache-miss price:

```text
no-cache counterfactual =
    total input × cache-miss price
  + output × output price
```

This is a billing counterfactual, not a claim that every cached request would otherwise have been
sent unchanged or that provider pricing will remain stable.

## 3. Results

### 3.1 Volume and observed cost

| Model | Cache-hit input | Cache-miss input | Output | Requests | Observed cost |
|---|---:|---:|---:|---:|---:|
| DeepSeek V4 Flash | 76,880,512 | 8,305,039 | 1,056,848 | 4,489 | USD 1.6739 |
| DeepSeek V4 Pro | 416,254,080 | 8,072,256 | 1,392,282 | 3,751 | USD 6.2316 |
| **Total** | **493,134,592** | **16,377,295** | **2,449,130** | **8,240** | **USD 7.9055** |

Cache hits represented 96.79% of all input tokens and 96.32% of all billed tokens including
output.

### 3.2 Where the money went

| Cost component | DeepSeek V4 Flash | DeepSeek V4 Pro | Total |
|---|---:|---:|---:|
| Cache-hit input | USD 0.2153 | USD 1.5089 | USD 1.7242 |
| Cache-miss input | USD 1.1627 | USD 3.5114 | USD 4.6741 |
| Output | USD 0.2959 | USD 1.2113 | USD 1.5072 |
| **Observed** | **USD 1.6739** | **USD 6.2316** | **USD 7.9055** |

The colloquial observation that “around one hundred million tokens cost cents” is directionally
correct only for a cache-hit-dominated slice. At the prices captured in this export, 100 million
cache-hit input tokens alone would cost approximately USD 0.28 on V4 Flash or USD 0.3625 on V4
Pro. It is not correct for an arbitrary mixture of cache misses and generated output.

### 3.3 Counterfactual without cache pricing

| Model | Observed | All input at miss price | Difference |
|---|---:|---:|---:|
| DeepSeek V4 Flash | USD 1.6739 | USD 12.2219 | USD 10.5480 (86.30%) |
| DeepSeek V4 Pro | USD 6.2316 | USD 185.7932 | USD 179.5616 (96.65%) |
| **Total** | **USD 7.9055** | **USD 198.0151** | **USD 190.1096 (96.01%)** |

The result is consistent with Alex Tavern's controlled cache probes, which separately verified
positive repeated-prefix reuse and a changed-prefix negative control. See
[Task 09 prompt-caching evidence](./09-prompt-caching.md).

## 4. Architectural decision supported by the evidence

The project will not collapse independently owned responsibilities into one model call merely to
reduce token count. The current direction keeps explicit boxes when they enforce a meaningful
boundary:

| Boundary | Why a separate operation is justified |
|---|---|
| Director | Chooses typed events, routing, and proposed state changes without writing literary prose. |
| Resolver/code validation | Clamps proposals against presence, zones, agency, and schemas before reality changes. |
| Prose renderer | Sees confirmed reader-safe facts, not private sheets, thoughts, internal IDs, or future plans. |
| Character | Produces subjective speech, thought, and action intent from viewer-safe context only. |
| Perspective engine | Maintains one character's potentially incomplete or incorrect identity knowledge. |
| Historian | Compacts public and private evidence without crossing audience boundaries. |
| Drive/roteiro | Adds momentum and planning without granting the prose renderer authority over future reality. |

This design is not complexity for its own sake. Earlier playtests showed that one overloaded
Narrator selected events, resolved actions, routed speakers, invented NPC behavior, exposed
private context, mutated the world, and wrote prose. Failures then became difficult to localize:
passivity, identity leaks, duplicated speech, knowledge transfer, and contradictory physical
outcomes all emerged from the same call.

Separating those responsibilities increases call count, but it also makes invalid authority flows
unrepresentable or locally rejectable. Cheap cached input changes the trade-off: the project can
buy stronger semantic boundaries without paying the uncached price for the full stable context on
every call.

## 5. Why simulations and tests belong in the cost model

The export covers development activity, not only end-user gameplay. During the measured period,
the project repeatedly used real-provider boundaries for:

- multi-run playtests to distinguish stable behavior from lucky samples;
- the 29.1/29.3 counter-canon benchmark;
- blind critics and bias-controlled review cycles;
- identity, whisper, compaction, routing, and continuity probes;
- malformed structured-output retries and provider-boundary smoke tests;
- before/after comparisons of architectural increments.

Those tokens are research and verification expenditure. They should not be projected directly as
the runtime cost of one normal player session. Conversely, they should not be dismissed as waste:
stochastic systems require repeated observations, and the project uses them to replace intuition
with artifacts, debug logs, and reproducible acceptance criteria.

The billing export does not identify which requests belong to Alex Tavern, coding agents, or other
experiments sharing the account/API-key label. It therefore cannot quantify the exact fraction
spent on simulations. Repository debug artifacts establish that such runs occurred, but account
totals are used here only for the broad token-economics observation.

## 6. What caching does and does not justify

Caching supports:

- stable instruction and identity prefixes;
- several narrowly scoped calls that share large invariant prefixes;
- generous context ceilings when truncation would damage correctness;
- repeated evaluation and blind-review protocols;
- delaying premature token minimization until measured cost requires it.

Caching does **not** justify:

- long sequential chains on the player's visible latency path;
- duplicated authorities or two competing memories;
- sending private data to an agent that should never see it;
- calls with no new semantic work;
- unbounded autonomous loops;
- assuming provider cache retention or prices are permanent;
- ignoring output tokens, which are not prefix-cache hits.

The principal optimization target is therefore the dependency graph, not raw call count. Calls
that do not depend on one another may run concurrently. Calls with a true data dependency remain
sequential. Deterministic predicates suppress work when there is no new evidence to process.

## 7. Decision hierarchy for V1

Until new measurements overturn it, Alex Tavern prioritizes:

1. knowledge-boundary correctness and human agency;
2. one authoritative owner for each state transition;
3. narrative consistency and quality;
4. transaction, undo, replay, and observability guarantees;
5. player-visible latency and safe concurrency;
6. token and monetary efficiency.

Cost is last in this ordering because the measured cached workload makes it a weak constraint, not
because cost never matters.

## 8. V1.0 update protocol

This case study is provisional and should be updated before the 1.0 release with:

1. a fresh provider export covering the completed architecture;
2. per-agent call, token, cache, latency, and retry attribution from Task 32;
3. runtime-session totals separated from development simulations;
4. p50/p95 visible-turn latency and critical-path decomposition;
5. cache-hit ratios by Director, Prose, Character, Perspective, Historian, and Drive;
6. an ablation or comparable baseline showing cost and quality with fewer combined calls;
7. revised no-cache and alternative-provider counterfactuals;
8. explicit thresholds that would trigger prompt reshaping, batching, or architecture reduction.

The decision remains falsifiable. If the final system shows low cache reuse, unacceptable latency,
or cost that scales materially with normal play, the architecture should be simplified or its call
topology changed. The present evidence supports continuing the separated design while measuring
those risks.

## 9. Reproduction notes

The aggregate calculations can be reproduced locally without extracting account metadata to the
repository:

```bash
unzip -p ~/Downloads/usage_data_2026-06-17_2026-07-16.zip \
  amount-2026-06-17_2026-07-17.csv \
  | awk -F, 'NR > 1 { totals[$3 FS $6] += $8 } END { for (k in totals) print k, totals[k] }'
```

Use the `price` column from the same CSV to recompute each component, then compare the sum with
`cost-2026-06-17_2026-07-17.csv`. Do not publish raw rows: even though keys are masked, the export
contains account identifiers and credential labels.

## Related evidence

- [Verified prompt caching](./09-prompt-caching.md)
- [DeepSeek provider integration](./deepseek-provider-integration-2026-07-12.md)
- [Multi-character memory retention](./multi-character-memory-retention-2026-07-14.md)
- [Speech audience model](./speech-audience-model-2026-07-15.md)
- [Character output guard](./character-output-guard-2026-07-15.md)

