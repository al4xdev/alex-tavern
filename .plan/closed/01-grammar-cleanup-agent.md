# Task 01: Optional grammar cleanup plugin

**Status:** Completed on 2026-07-13

## Delivered behavior

- Grammar cleanup is opt-in through activation of the curated Grammar Tools plugin or the Clean
  Writing Experience. There is no parallel core configuration flag.
- Grammar Tools 2.0.0 makes one provider-neutral structured model call for the submitted
  `speech`, `thought`, and `action` fields.
- The prompt limits the operation to grammar, spelling, agreement, and punctuation while
  preserving language, meaning, voice, person, tense, facts, intent, and field boundaries.
- Empty input skips the call. Invalid output or provider failure escapes to the pre-commit plugin
  containment policy: the plugin draft is discarded, the plugin is disabled for the boot, and the
  original input continues.
- The raw API payload is retained only in the append-only debug log. The effective input is
  persisted in history and returned by the turn API so the optimistic player bubble can be updated.
- Rewritten history entries carry `input_transformed`, rendered as a persistent "Adjusted by
  plugin" indicator in the frontend.

## SDK and observability

- Backend plugins receive `context.model.call_json(...)`, the only public model-call API.
- Calls use the active provider, shared client, server-owned config and secrets, strict JSON Schema
  validation, shared retries and timeout, and the normal per-session debug log.
- The SDK derives `session_id`, `turn_number`, and `agent = "plugin:<plugin_id>"` from the hook
  context. Plugins declare the review permission `model.call`.
- Each turn records `turn_input` before filters and `turn_input_effective` after filters, including
  the transformed field names.
- The live contract exports the service as `services.model.call_json`.

## Agent authoring documentation

The plugin hub MCP exposes `plugin_docs(document="model-calls")`. The hub documentation covers the
signature, strict schema example, provider adaptation, logging, failure semantics, tests, and
forbidden direct access to clients, provider payloads, or secrets.

## Source and package

- Core SDK and contracts: `src/plugins/`
- Core reference plugin: `plugins/examples/turn_counter/`
- Curated source: `../alex-tavern-plugins/plugins/grammar_tools/`
- Curated artifact: `artifacts/grammar-tools-2.0.0.zip`
- Artifact SHA-256: `7b4fd31f4fcbea4cfb63fad81b034dc73a22da986f30f6acee00427b8309e94e`

The obsolete core grammar example and curated 1.0.0 artifact were removed. Runtime snapshots under
`.data/plugins/hub` were not edited.

## Validation evidence

- Core test suite covers the provider boundary, strict structured response, redacted logging, raw
  versus effective input, persistence, and plugin failure rollback.
- Plugin-local tests cover one-call correction, empty input, field-boundary rejection, erased
  content, and provider failure.
- The hub checker, MCP stdio boundary, deterministic artifact hash, Python quality gates, frontend
  module parsing, and full core suite were run before closure.
