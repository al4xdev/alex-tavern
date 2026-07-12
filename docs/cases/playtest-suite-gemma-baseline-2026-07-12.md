# Queued playtest baseline: Gemma 4 26B A4B

Date: 2026-07-12

## Outcome

The new automated harness completed all four maintained scenarios twice through the real
`Runner`: 8 runs, 161 LLM calls, no failed run, no LLM error, no retry, and no occurrence of the
internal `Player` marker in a prompt. The single-scenario queue behaved correctly against
llama.cpp `--parallel 1`; the entire suite took about 11 minutes 20 seconds without overlapping
conversations or turning server wait time into an HTTP timeout.

The result does not support one universal explanation. Queueing and transport were stable.
Most prose-boundary problems are strongly model/prompt-sensitive, while malformed scene deltas
also expose system boundaries that should be made stricter regardless of the chosen model.

Raw artifacts:

- `/tmp/roleplay-playtest-suite-7zkowcx7/playtest-results.json`
- `/tmp/roleplay-playtest-suite-7zkowcx7/playtest-report.md`
- `/tmp/roleplay-playtest-suite-7zkowcx7/sessions/`

The artifacts intentionally live outside the repository and the real `.data` tree.

## Configuration

- Model: `gemma-4-26B-A4B-Q4_K_XL`
- Endpoint: `http://127.0.0.1:8888`
- llama.cpp slots: `--parallel 1`
- Harness concurrency: `--max-in-flight 1`
- Repetitions: 2
- Language: English
- Context limit: 65,536
- Sampling: temperature 1.0, top-p 0.95, top-k 64

Command:

```bash
uv run python tools/playtest_harness.py \
  --model-label gemma-4-26B-A4B-Q4_K_XL \
  --repeat 2 \
  --max-in-flight 1 \
  --llm-timeout 60
```

## Results by scenario

| Scenario | Character-action candidates | Second-person narrator | Nested `physical_facts` | Redundant moods | Calls |
|---|---:|---:|---:|---:|---:|
| Character microtest | 4/8 Character outputs | 0/8 Narrator outputs | 0 | 0 | 16 |
| Consequence/POV microtest | 4/4 Character outputs | 0/10 Narrator outputs | 0 | 0 | 14 |
| Natural conversation | 19/22 Character outputs | 2/26 Narrator outputs | 0 | 1 | 50 |
| Stress regression | 32/35 Character outputs | 6/42 Narrator outputs | 3 | 4 | 81 |
| **Total** | **59/69** | **8/86** | **3** | **5** | **161** |

The Character-action signal is a regex candidate count. Manual inspection confirmed common
forms such as `I say`, `I lean`, `I glance`, `I stumble`, and `my hand ...`, but the metric should
not be read as a complete semantic classifier.

## What appears model-dependent

### Character role boundary

The focused Character microtest produced the clearest variance: repetition 1 had a physical
action candidate in all 4 outputs, while repetition 2 had none in 4 outputs. The inputs and
configuration were identical. That rules out a deterministic routing or persistence defect for
this symptom and shows sampling/model instruction-following sensitivity.

The broader evidence is still unfavorable to this Gemma build: candidates occurred in 19/22
natural Character outputs and 32/35 stress outputs. The model repeatedly wraps correct speech
and subjective thought around action tags such as “I say” or “I lean,” even though the Character
contract only permits speech and thought. The prompt is understood sometimes, but is not obeyed
reliably as context grows.

### Point of view and punctuation

Second-person narration was also stochastic: stress produced 6 hits in one repetition and zero
in the other; natural conversation produced zero and 2. Fourteen forbidden em dashes occurred
in raw model responses despite the shared explicit prohibition. Both patterns are best treated
as model/prompt compliance failures unless a different model reproduces them at a comparable
rate.

### Groundedness in the natural set

The natural scenario explicitly requested a grounded conversation and prohibited a new threat
without a cause. Nevertheless, one repetition escalated a merely warm medallion into extreme
heat, steam, ozone, structural noises, black sludge, and immediate danger. The other repetition
was calmer. This again points to model sampling and narrative momentum rather than the test set
alone: the slower scenario reduced pressure but did not eliminate runaway invention.

## What remains a system concern

### Scene delta contract is not strict enough

Three stress Narrator outputs inserted a `physical_facts` key inside `scene_update`, despite the
flat delta contract. The grammar currently allows arbitrary physical-fact keys with string or
null values, so `"physical_facts": null` is syntactically accepted. The model caused the bad
field, but the application owns the boundary and should reject reserved nested keys rather than
silently treating them as an ordinary physical fact.

This is not a request for legacy compatibility. The forward-only fix is a stricter current
contract/validation rule, followed by updating the prompt and tests. No adapter for old logs or
old nested shapes is needed.

### Incorrect bulk deletion is legal under the current semantics

In consequence/POV repetition 2, the model returned `null` for five existing facts at once:
lighting, crowd, outside weather, door, and cup position. The state correctly followed the
documented meaning of `null` and removed them, but the removals were unjustified by the story.
This is primarily a model semantic error; it is also evidence that structured syntax alone does
not guarantee a valid state transition. A future guard could reject or explicitly review broad
fact deletion, but it should be a clear invariant, not a model-specific compatibility layer.

### Location normalization can create false changes

Several first updates changed `Old Mork's Tavern — main hall, dim lighting` to the same wording
with a comma. That is not a real move, yet it becomes a persisted location update. The model
emitted the rewrite; the system currently has no semantic no-op normalization. This is lower
severity than an invented relocation but matters for regression metrics and state auditability.

## Queue conclusion

The missing queue was a real bulk-debugging problem. With one llama.cpp slot, launching several
scenarios concurrently would make later HTTP calls wait inside the server while their client
timeouts were already running. The harness queue now schedules whole scenarios with an
`asyncio.Semaphore`; queue wait is measured separately from LLM call duration. This changes no
user-facing behavior and introduces no production service dependency.

The observed queue waits reached roughly eight minutes for late jobs because all eight jobs are
created together, then admitted one at a time. That is expected and harmless: no queued job has
started an HTTP request yet. All 161 actual calls completed on their first attempt.

## Recommendation

Do not keep refining only this stress script. Keep all four sets:

1. microtests localize one contract and reveal sampling variance;
2. the natural set detects narrative runaway under ordinary dialogue;
3. the stress set preserves difficult regression coverage;
4. repetitions prevent one lucky or unlucky sample from becoming a conclusion.

The next informative experiment is an A/B model run, not another prompt rewrite in isolation.
Run the exact same scenario files and server sampling settings against a second instruction-tuned
model for at least two repetitions. If Character-action, POV, dash, and unjustified-null rates
fall sharply, prefer the stronger model before adding enforcement complexity. Regardless of the
A/B result, reserve/reject nested `physical_facts` at the application boundary because that is a
schema invariant, not a style preference.

## Verification status

After the live run and documentation update, the harness and surrounding changes passed:

- `uvx ruff check .`
- `uvx ruff format --check .`
- `uvx mypy src/ tools/playtest_harness.py`
- `uv run pytest -x` (`133 passed, 5 deselected`)

`git diff --check` also passed. The repository's real `.data` tree remained at 38 files with the
same aggregate SHA-256, `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f`.
