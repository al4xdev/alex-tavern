# Task: Provider-native prompt caching

**Status:** Completed and closed  
**Closed:** 2026-07-12  
**Commit:** `b2985c4 feat: implement verified prompt caching`  
**README evidence:** `README.md`, section `Verified prompt caching`  
**Detailed proof:** [`../../../docs/09-prompt-caching.md`](../../../docs/09-prompt-caching.md)

## Original question

The README identified prompt caching as a possible future optimization but did not specify
provider behavior, ownership, invalidation, observability, or proof that caching occurred. The
repository had no cache request option, response metric, probe, or regression coverage.

## Architecture decision

Exploration showed that Alex Tavern should not implement a local cache of generated responses or
own provider KV state:

- DeepSeek Context Caching is automatic and provider-owned.
- llama.cpp owns its KV/prompt cache and generation slots.
- Alex Tavern owns cache-friendly prompt ordering, provider-specific request adaptation, and
  preservation of the providers' real cache counters.
- Exact-prefix matching makes normal scene/history/compaction changes self-invalidating. No
  application cache key or manual invalidation layer is needed.

The task therefore changed from “build a cache” to “make provider-native caching explicit,
observable, reproducible, and demonstrably effective.”

## Acceptance criteria

- [x] Preserve raw provider `usage` instead of discarding the response envelope after content.
- [x] Normalize provider-specific cache counters as `prompt_cache.hit_tokens/miss_tokens` in the
  session JSONL.
- [x] Send `cache_prompt: true` only through the llama.cpp adapter.
- [x] Keep DeepSeek caching automatic without inventing a request flag or client cache key.
- [x] Put stable Narrator and Character prompt content ahead of frequently changing state while
  preserving knowledge isolation.
- [x] Keep retry corrections in the changing suffix instead of invalidating the stable system
  prefix.
- [x] Add a deterministic warm/repeat/negative provider probe.
- [x] Prove a non-zero cache hit on the real DeepSeek API.
- [x] Prove a non-zero cache hit on the configured real llama.cpp server.
- [x] Preserve exact models, hashes, counters, timing observations, and limitations in a
  versioned Markdown document.
- [x] Put the verified capability and practical JSONL examples near the top of the public README.
- [x] Add regression tests and pass lint, type checking, and the complete test suite.

## Closure evidence

### DeepSeek V4 Flash

- Warm request: `0 / 4,031` cached tokens.
- Identical repeat: `3,968 / 4,031` cached tokens (98.4%).
- Changed-prefix control: `0 / 4,032` cached tokens.

### llama.cpp

- Server build: `b9950-bcde81f10`.
- Model: `gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf`.
- Configuration observed through `/props`: 65,536-token context, one slot.
- Warm request: `0 / 5,457` cached tokens.
- Best identical repeat: `5,456 / 5,457` cached tokens (>99.9%).
- Changed-prefix control: `0 / 5,457` cached tokens.

### Automated verification

- `uvx ruff check .`: passed.
- `uvx mypy src/`: passed.
- `uv run pytest -x`: 162 passed.
- `git diff --check`: passed before commit.

## Explicit non-goals

- No generated-response cache.
- No application-owned cache keys or persistence.
- No llama.cpp slot allocation, save/restore, or eviction manager.
- No claim about concurrent multi-session cache retention from the one-slot sequential proof.

Explicit slot management would be a separate deployment task only if a concurrent benchmark
demonstrates that llama.cpp's automatic slot/prompt-cache behavior is insufficient. It is not
unfinished work from Task 09.

## Final state

There is no remaining actionable prompt-caching work in the current architecture. Normal agents
use the provider-native cache path automatically, every real call can expose cache evidence in
JSONL, and both supported backends have controlled positive and negative proof.
