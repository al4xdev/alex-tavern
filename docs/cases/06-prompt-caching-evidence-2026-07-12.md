# Prompt caching: versioned positive and negative proof on both providers

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 06 |
| **Date** | 2026-07-12 |
| **Probe** | `tools/prompt_cache_probe.py` |
| **Status** | Verified on both supported provider adapters |

## Abstract

Raw usage counters proving when provider-native prompt caching hits and when it deliberately misses, for DeepSeek and llama.cpp. The append-only prompt discipline validated here is what later makes the agentic fan-out economically viable (see No. 10).

---
**Captured:** 2026-07-12 UTC  
**Status:** Verified on both supported provider adapters  
**Probe:** `tools/prompt_cache_probe.py`

### What was proved

Alex Tavern sent a unique long prompt through its production `chat_completion()` path. For each
provider the probe performed:

1. one warm request;
2. three byte-identical message repetitions;
3. one negative request with a different prefix from token zero but the same remaining reference
   text.

The adapter retained the provider's raw `usage` object and normalized cache counts into
`prompt_cache.hit_tokens` and `prompt_cache.miss_tokens`. A provider passed only when a repeated
request reported a non-zero hit and the changed-prefix request reported a smaller hit.

This proves provider-native input-prefix reuse. It does not claim that generated responses are
cached; every call generated a new completion.

### DeepSeek V4 Flash

Command:

```bash
uv run python -m tools.prompt_cache_probe --provider deepseek
```

Environment and identity:

| Field | Value |
|---|---|
| API base | `https://api.deepseek.com` |
| Model | `deepseek-v4-flash` |
| Probe session | `cache-probe-deepseek-f3cb4498` |
| Pre-client messages SHA-256 | `50a6fced684dbc6c23816c037ea3428aa3c9ecbad7b7ab7cdcc3c114e467a071` |
| API key in output/log | No |

Observed calls:

| Phase | Prompt tokens | Cache hits | Cache misses | Duration |
|---|---:|---:|---:|---:|
| Warm | 4,031 | 0 | 4,031 | 1,264.678 ms |
| Repeat 1 | 4,031 | 3,968 | 63 | 1,115.576 ms |
| Repeat 2 | 4,031 | 3,968 | 63 | 1,046.291 ms |
| Repeat 3 | 4,031 | 3,968 | 63 | 1,354.090 ms |
| Changed-prefix control | 4,032 | 0 | 4,032 | 1,351.756 ms |

The repeated requests served 98.4% of prompt tokens from DeepSeek's Context Cache. The provider's
raw successful repeat usage was:

```json
{
  "prompt_tokens": 4031,
  "completion_tokens": 1,
  "total_tokens": 4032,
  "prompt_tokens_details": {"cached_tokens": 3968},
  "prompt_cache_hit_tokens": 3968,
  "prompt_cache_miss_tokens": 63
}
```

The negative control returned zero cache hits. This matches DeepSeek's documented requirement
that cached content match from the beginning of the input.

### llama.cpp

Command:

```bash
uv run python -m tools.prompt_cache_probe --provider llama_cpp
```

The probe used the actual llama.cpp endpoint configured by Alex Tavern, after `/health` returned
`{"status":"ok"}`. Public `/props` metadata captured immediately after the run:

| Field | Value |
|---|---|
| API base | Private llama.cpp network endpoint (redacted) |
| Build | `b9950-bcde81f10` |
| Model | `gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf` |
| Quantization reported by server | `Q4_0` |
| Context | 65,536 tokens |
| Slots | 1 |
| `/metrics` exposed | Yes |
| `/slots` exposed | Yes |
| Probe session | `cache-probe-llama_cpp-803b0986` |
| Pre-client messages SHA-256 | `2843db49e9d032e7ea190cca13b6c3316d25535411c19838f58a61eeebfccc00` |

Observed calls:

| Phase | Prompt tokens | Cache hits | Cache misses | Duration |
|---|---:|---:|---:|---:|
| Warm | 5,457 | 0 | 5,457 | 5,608.674 ms |
| Repeat 1 | 5,457 | 5,437 | 20 | 1,972.302 ms |
| Repeat 2 | 5,457 | 5,456 | 1 | 36.446 ms |
| Repeat 3 | 5,457 | 5,456 | 1 | 32.692 ms |
| Changed-prefix control | 5,457 | 0 | 5,457 | 3,077.455 ms |

The best repeated request reused all but one prompt token (>99.9%). The raw successful repeat
usage was:

```json
{
  "completion_tokens": 2,
  "prompt_tokens": 5457,
  "total_tokens": 5459,
  "prompt_tokens_details": {"cached_tokens": 5456}
}
```

The negative control returned zero cached tokens. Durations are retained as observations, not as
a portable latency guarantee: hardware, batching, slot state, and model generation can change
them.

### Implementation exercised by the probes

- `LlamaCppAdapter.prepare_request()` sends `cache_prompt: true`.
- Both adapters return content plus the raw `usage` object and normalized cache hit/miss counts.
- Every JSONL LLM entry retains `usage` and `prompt_cache`; credentials remain excluded.
- Narrator prompts place stable character identity before summary/history and changing scene,
  moods, and routing.
- Character prompts keep identity/rules stable, place append-only recent events first in the user
  message, and move mood/private note/current scene context into the changing suffix.
- Retry corrections append to the user suffix instead of invalidating the stable system prefix.

The knowledge boundary is unchanged: Narrator history still excludes all thoughts; a Character
still receives only public speech, its own thoughts, its own note, and the Narrator-filtered scene
context.

### Automated validation

After implementation:

```text
uvx ruff check .      -> passed
uvx mypy src/         -> passed
uv run pytest -x      -> 162 passed
```

Unit coverage includes provider-specific request controls, response-envelope/cache normalization,
JSONL persistence, stable-prefix ordering, repeatable/negative probe construction, and refusal to
claim verification when cache counters are missing.

### Reproducing and inspecting

The probe reads provider settings from `.data/config.json`; it never prints the API key. Start the
selected backend first, then run one of the commands above. A successful process exit means both
positive and negative checks passed. Its complete secret-free JSON report is printed to stdout,
while the normal raw call evidence remains at:

```text
.data/sessions/cache-probe-<provider>-<nonce>.debug.jsonl
```

Inspect any session with:

```bash
jq -c '
  select(.usage != null)
  | {agent, provider, usage, prompt_cache, duration_ms}
' .data/sessions/<session-id>.debug.jsonl
```

### Boundaries

- DeepSeek owns cache persistence and may evict entries; its service documents caching as
  best-effort.
- llama.cpp owns KV memory and slot selection. Alex Tavern enables request-level caching but does
  not allocate, save, restore, or erase slots.
- The verified llama.cpp run used one slot. It proves reuse for the normal sequential request
  shape, not cache behavior under concurrent multi-session load.
- Compaction, history trimming, and early state changes naturally shorten the matching prefix.
  There is no stale application cache because Alex Tavern stores neither generated responses nor
  provider KV state.

### Primary references

- [DeepSeek Context Caching](https://api-docs.deepseek.com/guides/kv_cache/)
- [DeepSeek chat completion usage fields](https://api-docs.deepseek.com/api/create-chat-completion/)
- [llama.cpp server prompt caching and usage](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
