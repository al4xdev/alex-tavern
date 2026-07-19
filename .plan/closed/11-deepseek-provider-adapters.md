# Task: Server-owned LLM provider adapters and DeepSeek V4 Flash

**Status:** Completed and closed
**Closed:** 2026-07-12
**README evidence:** `README.md`, section `Multi-provider LLM architecture`
**Detailed report:** [`../02-deepseek-provider-integration-2026-07-12.md`](../02-deepseek-provider-integration-2026-07-12.md)

## Goal

Replace llama.cpp-specific runtime coupling with an adapter boundary, add DeepSeek V4 Flash in
non-reasoning mode, and let the user switch providers from the existing setup interface. Provider
settings and secrets must remain exclusively in the server-owned `.data/config.json`.

## Acceptance criteria

- [x] Discover and verify the exact account model and non-reasoning API contract.
- [x] Represent each OpenAI-compatible provider with its own adapter.
- [x] Keep backend and frontend provider adapters in separate adapter directories.
- [x] Keep shared HTTP, retry, logging, parsing, and validation provider-neutral.
- [x] Preserve native JSON Schema for llama.cpp and adapt DeepSeek to JSON Object plus local schema validation.
- [x] Store provider-specific settings and API keys only in `.data/config.json`.
- [x] Redact secrets from `GET /config` and preserve a stored key when the UI submits a blank field.
- [x] Switch the active provider atomically without restarting the application.
- [x] Add responsive llama.cpp/DeepSeek configuration to the existing setup modal.
- [x] Keep `/config` network-only in the service worker and avoid browser storage for provider data.
- [x] Extend the repeatable playtest harness for provider-aware A/B suites.
- [x] Validate a real DeepSeek turn through the complete backend.
- [x] Run a controlled 8-run DeepSeek/Gemma comparison and document the non-equivalent quality profile.
- [x] Resolve every actionable coupling finding produced by the parallel architecture audit.

## Closure evidence

- Real `/models` discovery returned `deepseek-v4-flash` and `deepseek-v4-pro`.
- Real non-reasoning JSON Object request completed without `reasoning_content`.
- Real application turn completed through Narrator and Character using the DeepSeek adapter.
- Config persisted across an isolated Uvicorn restart without exposing the API key.
- Eight fair DeepSeek scenario runs completed; both invalid schema responses were rejected and retried.
- Backend adapter metadata is the source of truth for provider defaults and secret policy;
  frontend adapters own provider-specific form behavior without hardcoded provider HTML.
- The final post-audit validation evidence is recorded in the detailed report and closed audit.
- The architecture audit and remaining preexisting coupling risks are recorded in
  [`../03-adaptability-coupling-audit-2026-07-12.md`](../03-adaptability-coupling-audit-2026-07-12.md).

## Security closure

With explicit owner authorization, `.data/config.json` was removed only from the Git index and
remains available locally. The existing `.data/` ignore rule covers configuration, keys,
sessions, presets, and debug logs. CI/CD and packaged runtimes must create their own isolated data
directory instead of inheriting repository development state.
