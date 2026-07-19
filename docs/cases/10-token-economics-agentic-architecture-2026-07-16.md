# Token economics as an architectural enabler

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 10 |
| **Evidence window** | 2026-07-11 through 2026-07-16 UTC |
| **Source** | DeepSeek usage and cost CSVs (2026-07-17) |
| **Status** | Interim V1; update through the 1.0 release |

## Abstract

Provider-billing evidence used as an explicit upper bound on project spend. The measured 89.57% input cache-hit ratio changes the economic trade-off of the agentic fan-out (Director, Prose, Character, Perspective, Historian, Drive), with no-cache and alternative-provider counterfactuals and an explicit attribution-limitations section. The append-only prompt discipline of No. 06 is what makes these numbers reachable.

---
**Captured:** 2026-07-16  
**Evidence window:** 2026-07-11 through 2026-07-16 UTC
**Provider export:** DeepSeek usage and cost CSVs generated on 2026-07-17  
**Status:** Interim V1 case study; update through the Alex Tavern 1.0 release

### Abstract

Alex Tavern deliberately favors explicit agent boundaries over minimizing model calls. A turn may
involve a Director, prose renderer, Character agents, perspective initialization or revision, a
Historian, and development-only critics or evaluators. This is more complex than one omniscient
prompt, but it makes authority, privacy, validation, replay, and failure attribution explicit.

The economic premise is that provider-native prefix caching makes large stable contexts cheap
enough that token count is not the first optimization target. During the project-aligned billing
window, the account's DeepSeek V4 Flash activity contains **73,755,780 tokens across 4,176 requests
for USD 1.5172**. This is an **upper bound**, not an exact Alex Tavern total, because the provider
export aggregates all applications using the account. Of 72,786,759 Flash input tokens,
**65,191,552 were cache hits (89.57%)**. Applying the prices recorded in the export, the same Flash
input volume charged entirely at its cache-miss rate would have produced an estimated total cost of
**USD 10.46**, including unchanged output. The observed Flash total was about 14.50% of that
counterfactual.

This does not prove that additional agents are free or always beneficial. It supports a narrower
decision: for this workload and provider, collapsing semantic responsibilities merely to save
input tokens would optimize the wrong constraint. Correctness and knowledge isolation come first;
latency, dependency topology, and output volume remain real constraints.

### 1. Question

Should Alex Tavern keep a comparatively complex multi-agent architecture when a simpler design
could use fewer calls and fewer prompt tokens?

The working hypothesis is:

> When stable prefixes dominate model input and provider-native caching is effective, separate
> semantic authorities can improve correctness and observability at acceptable monetary cost.

The hypothesis is intentionally conditional. It must be revisited if cache behavior, provider
prices, latency, workload shape, or product scale changes.

### 2. Data and method

The source archive was downloaded from the provider dashboard as
`usage_data_2026-06-17_2026-07-16.zip`. Its internal CSVs cover rows through 2026-07-16 and contain:

- daily cost by model;
- cache-hit input tokens;
- cache-miss input tokens;
- output tokens;
- request counts;
- the per-token price applied to each category.

The repository's first commit is dated 2026-07-10 23:02:07 in America/Sao_Paulo, which is
2026-07-11 02:02:07 UTC. Provider billing rows are aggregated by UTC date and cannot be split by
time of day. The project window therefore begins at the complete 2026-07-11 UTC row. Earlier rows
in the export belong to activity before this repository existed and are excluded from the primary
result.

Date filtering alone does not establish application attribution. Surviving Alex Tavern
`debug.jsonl` records use `deepseek-v4-flash`, and no runtime evidence shows the project calling
`deepseek-v4-pro`. A separate repository-local coding-tool configuration selects V4 Pro, consistent
with the user's recollection that Pro usage came from development tooling rather than Alex Tavern.
V4 Pro is therefore excluded from the project's primary workload. Even the remaining Flash rows
may include unrelated account activity, so their USD 1.5172 total is reported only as a ceiling on
project-attributable provider spend. The exact project total cannot be recovered from this export.

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

### 3. Results

#### 3.1 Volume and observed cost

| Project-attribution scope | Cache-hit input | Cache-miss input | Output | Requests | Observed cost |
|---|---:|---:|---:|---:|---:|
| **V4 Flash account activity, project ceiling** | **65,191,552** | **7,595,207** | **969,021** | **4,176** | **USD 1.5172** |

Cache hits represented 89.57% of the Flash input tokens and 88.39% of its billed tokens including
output. The same account window contains another 47,043,441 V4 Pro tokens across 721 requests for
USD 1.3742. That usage is attributed to separate development tooling and excluded here.

#### 3.2 Where the money went

| Cost component | V4 Flash project ceiling |
|---|---:|
| Cache-hit input | USD 0.1825 |
| Cache-miss input | USD 1.0633 |
| Output | USD 0.2713 |
| **Observed** | **USD 1.5172** |

The colloquial observation that “around one hundred million tokens cost cents” is directionally
correct only for a cache-hit-dominated slice. At the prices captured in this export, 100 million
cache-hit input tokens alone would cost approximately USD 0.28 on V4 Flash. In the
project-aligned window, 65.19 million Flash cache-hit tokens cost approximately USD 0.1825. It is
not correct for an arbitrary mixture of cache misses and generated output.

#### 3.3 Counterfactual without cache pricing

| Model | Observed | All input at miss price | Difference |
|---|---:|---:|---:|
| V4 Flash project ceiling | USD 1.5172 | USD 10.4615 | USD 8.9443 (85.50%) |

#### 3.4 Alternative-provider counterfactual

Provider choice materially changes the conclusion even when cache reuse is held constant. The
following counterfactual applies each provider's published standard API prices to the same
65,191,552 cache-hit input tokens, 7,595,207 cache-miss input tokens, and 969,021 output tokens from
the Flash ceiling.
It does not assume that the alternative model would achieve the same quality, latency, or output
length.

```text
alternative-provider cost =
    observed cache-hit input x published cache-read price
  + observed cache-miss input x published uncached-input price
  + observed output x published output price
```

| Model and price snapshot | Input | Cached input | Output | Estimated cost | Multiple of observed DeepSeek |
|---|---:|---:|---:|---:|---:|
| **Observed V4 Flash ceiling** | export prices | export prices | export prices | **USD 1.52** | **1.00x** |
| GPT-5.6 Luna | USD 1.00/M | USD 0.10/M | USD 6.00/M | USD 19.93 | 13.14x |
| GLM-5.2 | USD 1.40/M | USD 0.26/M | USD 4.40/M | USD 31.85 | 20.99x |
| Claude Sonnet 5, introductory price through 2026-08-31 | USD 2.00/M | USD 0.20/M | USD 10.00/M | USD 37.92 | 24.99x |
| GPT-5.6 Terra | USD 2.50/M | USD 0.25/M | USD 15.00/M | USD 49.82 | 32.84x |
| Claude Sonnet 5, standard price from 2026-09-01 | USD 3.00/M | USD 0.30/M | USD 15.00/M | USD 56.88 | 37.49x |
| GPT-5.6 Sol | USD 5.00/M | USD 0.50/M | USD 30.00/M | USD 99.64 | 65.68x |

The source prices are snapshots from the official
[OpenAI GPT-5.6 announcement](https://openai.com/index/gpt-5-6/),
[Claude Platform pricing](https://platform.claude.com/docs/en/about-claude/pricing), and
[Z.AI model pricing](https://docs.z.ai/guides/overview/pricing), accessed on 2026-07-16. OpenAI
publishes a 90% cache-read discount for GPT-5.6. Anthropic publishes cache reads at 0.1x base input
price and explicitly lists Sonnet 5 cache-read prices of USD 0.20/M during the introductory period
and USD 0.30/M afterward. Z.AI directly lists USD 0.26/M cached input for GLM-5.2.

This normalized comparison is useful for budget sensitivity, but it is not a vendor benchmark:

- tokenizers differ; Anthropic states that Sonnet 5's tokenizer can produce approximately 30%
  more tokens than its earlier tokenizer, and no cross-provider token-count equivalence is assumed;
- the calculation treats observed cache hits as reads and observed misses as ordinary uncached
  input; it excludes GPT-5.6's 1.25x cache-write charge and Anthropic's 1.25x five-minute or 2x
  one-hour cache-write charges because the aggregate DeepSeek export does not reveal an equivalent
  write lifecycle;
- cache eligibility, retention, explicit breakpoint behavior, and eviction differ by provider;
- reasoning effort, generated length, retries, tool fees, batch discounts, subscriptions, and
  provider-specific long-context modifiers are excluded;
- the DeepSeek baseline is an account-level Flash ceiling rather than an exact project total,
  whereas each alternative applies one model's prices to that entire ceiling.

The result sharpens the architectural claim: caching makes the separated design affordable on
every priced alternative shown, but DeepSeek's cache economics are unusually favorable for this
specific high-prefix-reuse workload. At the same measured volume, changing providers without
changing token shape could raise the ceiling from about USD 1.52 to roughly USD 20-100. Provider
abstraction remains strategically useful, but provider selection is part of the architecture's
economic envelope rather than an interchangeable detail.

#### 3.5 Broader archive context

The complete provider archive begins on 2026-06-18, before Alex Tavern's first commit. Across that
broader account window it contains 511,961,017 tokens and USD 7.9055 of cost. Those totals are not
used to claim project expenditure; they are retained only to explain the source archive and why a
naive whole-file aggregation overstates Alex Tavern's measured cost.

The result is consistent with Alex Tavern's controlled cache probes, which separately verified
positive repeated-prefix reuse and a changed-prefix negative control. See
[Task 09 prompt-caching evidence](./06-prompt-caching-evidence-2026-07-12.md).

### 4. Architectural decision supported by the evidence

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

### 5. Why simulations and tests belong in the cost model

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

### 6. What caching does and does not justify

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

### 7. Decision hierarchy for V1

Until new measurements overturn it, Alex Tavern prioritizes:

1. knowledge-boundary correctness and human agency;
2. one authoritative owner for each state transition;
3. narrative consistency and quality;
4. transaction, undo, replay, and observability guarantees;
5. player-visible latency and safe concurrency;
6. token and monetary efficiency.

Cost is last in this ordering because the measured cached workload makes it a weak constraint, not
because cost never matters.

### 8. V1.0 update protocol

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

### 9. Reproduction notes

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

### Related evidence

- [Verified prompt caching](./06-prompt-caching-evidence-2026-07-12.md)
- [DeepSeek provider integration](./02-deepseek-provider-integration-2026-07-12.md)
- [Multi-character memory retention](./07-multi-character-memory-retention-2026-07-14.md)
- [Speech audience model](./08-speech-audience-model-2026-07-15.md)
- [Character output guard](./09-character-output-guard-2026-07-15.md)
