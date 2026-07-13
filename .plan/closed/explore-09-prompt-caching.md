# Explore: Task 09 — Prompt caching

**Date:** 2026-07-12  
**Scope:** Current prompt construction, provider-adapter boundary, DeepCode reference,
DeepSeek Context Caching, and the installed llama.cpp server.

> **Implementation update (2026-07-12):** Task 09 is complete. Both live probes passed and the
> canonical, versioned results now live in `docs/09-prompt-caching.md`; the public README contains
> the verified counters and practical JSONL examples. Findings below describe the pre-change
> architecture and remain useful as design history, but statements saying evidence is missing
> have been superseded by that document.

## Executive finding

Prompt caching is not one provider-neutral switch. The current system has three distinct
concerns:

```text
prompt construction
└── stable prefix before changing state/history
    ├── DeepSeek API
    │   ├── cache is automatic and provider-owned
    │   └── proof: usage.prompt_cache_{hit,miss}_tokens
    └── llama.cpp
        ├── KV reuse is server/slot-owned
        ├── cache_prompt is enabled by default in the installed build
        └── proof: usage.prompt_tokens_details.cached_tokens
```

The application already produces cache-friendly prompts in at least one real session, but it
currently discards both providers' cache evidence. Therefore cache use is plausible, not yet
proved by an Alex Tavern artifact.

## Current request and adapter path

- Every agent reaches the same `chat_completion()` path through
  `chat_completion_json()` (`src/llm/client.py:37-182`).
- `PreparedRequest.extra_payload` is already the adapter-owned extension point for request fields
  (`src/llm/adapters/base.py:9-15`). DeepSeek uses it for `thinking`; llama.cpp currently adds
  nothing (`src/llm/adapters/deepseek.py:38-68`, `src/llm/adapters/llama_cpp.py:35-42`).
- The response contract only extracts a string. `ProviderAdapter.extract_content()` and
  `extract_openai_content()` discard the rest of the response envelope, including `usage`
  (`src/llm/adapters/base.py:47-69`, `src/llm/client.py:128-142`).
- The JSONL records duration and an estimated token count, but receives neither the response
  envelope nor normalized token/cache usage (`src/llm/debug_log.py:83-130`).
- The shared HTTP client is process-wide, while Runner locks serialize work per roleplay session;
  different sessions may still reach one inference server concurrently (`src/main.py:38-55`,
  `src/runner.py:165`, `src/runner.py:361`).

This means provider-specific request controls fit the adapters, while evidence needs a richer
adapter response contract plus shared JSONL fields. A slot allocator would additionally need
session/agent identity and server-wide ownership; neither is currently in the adapter contract.

## DeepSeek behavior

DeepSeek's official documentation states that Context Caching is enabled by default and requires
no request change. It matches prefixes beginning at token zero and returns:

- `usage.prompt_cache_hit_tokens`
- `usage.prompt_cache_miss_tokens`

Cache creation is best-effort and asynchronous; a hit is not guaranteed on every repetition.
The current docs describe complete persisted prefix units at request boundaries, common-prefix
detection, and fixed intervals for long inputs.

Sources:

- <https://api-docs.deepseek.com/guides/kv_cache/>
- <https://api-docs.deepseek.com/api/create-chat-completion/>

No DeepSeek cache flag belongs in the adapter for this API. Its missing responsibilities are
preserving/normalizing the returned usage and exposing it to the debug evidence path.

## llama.cpp behavior in the installed build

The locally installed binary reports:

```text
llama-server version 9950 (bcde81f10), Unsloth build
```

Its bundled official source and help establish that:

- `--cache-prompt` defaults to enabled;
- repeated `/chat/completions` requests report reused tokens under
  `usage.prompt_tokens_details.cached_tokens`;
- `cache_prompt` can be explicit per request and defaults to `true`;
- automatic slot selection compares the incoming prefix with slot contents;
- `id_slot` can pin a request to a slot;
- this build also has a host-memory prompt cache (`--cache-ram`, default 8192 MiB) and can save
  idle slots into it;
- `--metrics` and `/slots` provide server-side observability when enabled.

Evidence in the installed checkout:

- `/home/alex/.unsloth/llama.cpp/tools/server/README.md:514`
- `/home/alex/.unsloth/llama.cpp/tools/server/README.md:1328-1360`
- `/home/alex/.unsloth/llama.cpp/tools/server/server-task.cpp:389-397`
- `/home/alex/.unsloth/llama.cpp/tools/server/tests/unit/test_chat_completion.py:54-73`
- `/home/alex/.unsloth/llama.cpp/tools/server/server-context.cpp:1545-1634`

The configured llama.cpp endpoint (`192.168.0.183:8888`) was unreachable during this
exploration. Its running version, flags, slot count, and actual cache counters remain unverified.
The behavior of the installed build cannot be presented as proof about that remote process.

## Evidence from an existing real DeepSeek session

The surviving real debug file `.data/sessions/cca69ccb.debug.jsonl` contains two narrator and two
Lyra calls through DeepSeek. It has no `usage` field, so it cannot prove a provider cache hit.
It does prove that the exact prompts have reusable prefixes:

| Agent | First prompt | Second prompt | Shared character prefix |
|---|---:|---:|---:|
| Narrator | 4,505 chars | 5,103 chars | 4,505 chars (100% of the first prompt) |
| Character: Lyra | 2,729 chars | 3,010 chars | 2,383 chars (87.3% of the shorter prompt) |

For the Narrator, the second serialized role/content sequence was the entire first sequence plus
new history. This is the ideal prefix-growth shape. For Lyra, the first difference was the new
`SCENE CONTEXT`, after a stable system prefix.

These numbers are character-level diagnostics, not token-level cache counters. Only provider
`usage` can prove an actual hit.

## Prompt layout findings

### Narrator

Current order (`src/agents/narrator.py:105-176`):

```text
system rules + speaker ids + world directives + language + schema instruction
└── story summary (only after compaction)
    └── current scene
        └── optional routing constraint
            └── character sheets, including mood
                └── append-only public history
```

- When summary, scene, routing, sheets, and mood remain unchanged, history grows by appending;
  the real session above demonstrates full-prefix reuse.
- A scene or mood update changes content before history and invalidates reuse from that point.
- A forced-speaker constraint appears before character sheets/history and can shorten the hit.
- The first compaction introduces or rewrites `STORY SO FAR` at the start of the user message and
  replaces old history, so the system prefix remains valid but most of the user suffix changes.
- Exact-prefix caches do not need an application invalidation call for ordinary prompt changes:
  the changed tokens naturally miss. Explicit invalidation only becomes relevant if the app owns
  saved slots/cache keys.

### Character

Current order (`src/agents/character.py:70-99`, `src/agents/character.py:177-191`):

```text
identity + personality + knowledge + mood + private note + rules + language + schema
└── current filtered scene context
    └── public speech + own thoughts from recent history
```

- Mood and compacted private note precede the large stable rule block, so either change prevents
  reuse of those rules.
- The filtered current context precedes recent history and normally changes every Character call;
  history cannot contribute to the shared prefix even though it is largely append-only.
- Different characters deliberately have different private prefixes. Provider caches may retain
  multiple prefixes, while a simple one-slot/last-prompt llama.cpp setup alternates Narrator and
  Character prompt families.

### Summarizers and suggestions

- Public and private compaction calls are manual and much less frequent, so their cache value is
  lower than Narrator/Character calls (`src/agents/summarizer.py:115-174`).
- Private compactors have one prefix per character; their changing note and evicted window are in
  the user message.
- Suggestions reuse the Narrator user builder but use a different system prompt
  (`src/agents/narrator.py:312-405`).

## DeepCode reference implementation

The DeepCode clone does two relevant things rather than implementing its own response cache:

1. It orders default system messages from broadly stable to runtime/project-specific content and
   has a regression test named `createSession appends default system prompts in
   prefix-cache-friendly order`
   (`/home/alex/git/my/deepcode/packages/core/src/session.ts:1144-1173`,
   `/home/alex/git/my/deepcode/packages/core/src/tests/session.test.ts:1107-1142`).
2. It retains and recursively aggregates provider `usage`, including both
   `prompt_tokens_details.cached_tokens` and DeepSeek's direct hit/miss fields, per model
   (`/home/alex/git/my/deepcode/packages/core/src/session.ts:145-204`,
   `/home/alex/git/my/deepcode/packages/core/src/tests/session.test.ts:2970-3017`).

The reusable pattern is stable-prefix ordering plus provider evidence. It is not a client-side
cache of generated responses.

## Required proof artifact for Task 09

The user requires the completed task to preserve live proof in a Markdown file named for Task 09
and to place the verified capability prominently near the top of the public README.

The proof is incomplete until both rows below contain captured non-zero provider counters:

| Provider | Controlled probe | Required evidence |
|---|---|---|
| DeepSeek | Send the same long prefix in consecutive calls, preserving model and serialized messages | first call's hit/miss followed by a later `prompt_cache_hit_tokens > 0` |
| llama.cpp | Send the same long prefix twice to the actual configured server with cache enabled | server version/flags plus later `usage.prompt_tokens_details.cached_tokens > 0` |

The artifact also needs:

- UTC timestamp, model, provider/base URL without credentials, and llama.cpp build/flags;
- sanitized request identity (hash or fixture name) proving both requests used the same prefix;
- full `usage` objects for miss and hit calls;
- duration/TTFT when available, clearly secondary to the token counter;
- a negative probe with a changed early prefix showing a miss or sharply smaller hit;
- the exact command/test entry point needed to reproduce the evidence;
- no claim that caching was tested in README until both live probes pass.

## Prepared public README section

This draft is intended to appear near the top of the README after the introductory architecture
summary. It must not be copied verbatim until Task 09 has implemented usage capture and both live
provider probes above have passed. Angle-bracket values are evidence placeholders, not estimated
numbers.

### Top-of-README callout

```markdown
> [!NOTE]
> **Provider-native prompt caching is verified on both supported backends.** DeepSeek reuses
> matching prefixes automatically through its Context Cache, while llama.cpp reuses the local
> KV cache through `cache_prompt`. Alex Tavern preserves stable prompt prefixes and records the
> provider's real hit/miss token counters in each session's debug JSONL. This is an inference
> optimization, not a response cache: every roleplay response is generated normally.
```

Publication gate for this callout:

- Replace “is verified” with “is supported by both provider APIs” if either live probe is still
  missing.
- Do not say that Alex Tavern records counters until the JSONL response-usage change is present.
- Keep “provider-native” and “not a response cache”; the application does not cache generated
  narration or Character output.

### Detailed README section

````markdown
## ⚡ Prompt caching

Alex Tavern sends growing roleplay context on every generation. Re-evaluating the unchanged
prefix would waste time locally and cost additional input processing on a hosted provider, so
the prompt layout keeps stable instructions before changing scene/history content and lets each
backend reuse the matching prefix.

The cache belongs to the inference provider, not to the FastAPI application:

| Backend | Cache behavior | Evidence returned to Alex Tavern |
|---|---|---|
| DeepSeek | Context Caching is automatic; no cache flag or application cache key is required | `usage.prompt_cache_hit_tokens` and `usage.prompt_cache_miss_tokens` |
| llama.cpp | The adapter sends `cache_prompt: true`; the server reuses matching KV-cache tokens from its slots/prompt cache | `usage.prompt_tokens_details.cached_tokens` |

Each LLM entry in `.data/sessions/<session-id>.debug.jsonl` retains normalized usage alongside
the raw provider fields. That makes cache behavior inspectable per Narrator, Character, or
Summarizer call rather than inferred from latency.

DeepSeek example from the Task 09 live probe:

```json
{
  "agent": "<captured-agent>",
  "provider": "deepseek",
  "usage": {
    "prompt_tokens": <captured-total>,
    "completion_tokens": <captured-completion>,
    "total_tokens": <captured-total-with-completion>,
    "prompt_cache_hit_tokens": <captured-non-zero-hit>,
    "prompt_cache_miss_tokens": <captured-miss>
  }
}
```

llama.cpp example from the same controlled prefix probe:

```json
{
  "agent": "<captured-agent>",
  "provider": "llama_cpp",
  "usage": {
    "prompt_tokens": <captured-total>,
    "completion_tokens": <captured-completion>,
    "total_tokens": <captured-total-with-completion>,
    "prompt_tokens_details": {
      "cached_tokens": <captured-non-zero-hit>
    }
  }
}
```

For a quick session-level view:

```bash
jq -c '
  select(.usage != null)
  | {
      turn: .turn_number,
      agent,
      provider,
      prompt_tokens: .usage.prompt_tokens,
      deepseek_hit: .usage.prompt_cache_hit_tokens,
      deepseek_miss: .usage.prompt_cache_miss_tokens,
      llama_cached: .usage.prompt_tokens_details.cached_tokens,
      duration_ms
    }
' .data/sessions/<session-id>.debug.jsonl
```

A normal turn can miss part of the cache whenever early state changes. Scene updates, mood
updates, a different forced-speaker constraint, or manual compaction alter the prompt at that
point; the unchanged prefix remains reusable and the changed suffix is evaluated normally. No
manual invalidation is required because both backends match the actual prompt content.

The Task 09 evidence records the exact models, llama.cpp build and server flags, sanitized prompt
identity, positive repeated-prefix probes, and an early-prefix negative probe:
`<link-to-versioned-task-09-evidence>`.
````

### Values to copy from the completed proof

The final README edit must copy, not retype from memory:

- one compact successful DeepSeek JSONL entry with non-zero hit tokens;
- one compact successful llama.cpp JSONL entry with non-zero cached tokens;
- the exact evidence-document link after deciding its versioned repository location;
- the tested llama.cpp build and relevant flags in the evidence file, not necessarily in the
  top-level callout;
- the final normalized JSONL field names implemented by the task. If normalization changes the
  shape shown above, update the prose and `jq` command to match the real log.

## Scope boundaries and open questions

- Capturing normalized usage in JSONL is sufficient to establish whether caching already works;
  a UI cache setting or application cache key is not required for that evidence.
- Explicit `cache_prompt: true` is llama.cpp-specific and fits its adapter. It is redundant on the
  installed build but makes intent observable and protects against different server defaults.
- Explicit slot assignment is a separate deployment feature. It requires a policy for slot
  ownership across `(session, agent)`, concurrency, eviction, restarts, server discovery, and old
  llama.cpp versions. None exists today.
- The installed build's host-memory prompt cache may make manual slot pinning unnecessary. Only a
  concurrent multi-session benchmark against the deployed server can establish that.
- Prompt reordering changes model input semantics as well as performance. Narrator and Character
  behavioral regressions therefore need testing independently of cache-hit tests.
- The real DeepSeek debug sample strongly suggests useful cacheability, but its four calls predate
  usage capture and cannot retrospectively prove hits.
