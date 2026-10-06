# Conversation Translator — local delivery

Implemented typed `EngineInput` and `EngineOutput` at the conversation boundaries,
replacing the backend `turn.input` hook with `engine.input` and adding
`engine.output`. The host projects reader-visible texts and owns response structure.
Canonical persistence remains session JSON. Derived translations live in SDK
plugin storage; the frontend reads the normal session APIs.

Conversation Translator 1.0.0 lives alongside curated plugin sources in
`../alex-tavern-plugins/plugins/conversation_translator/`. Grammar Tools source
3.0.0 uses the new input contract and runs before translation. Initial scope is
conversation inputs, turn/history texts and suggestions/openings. Scenario and
character configuration are outside scope. Enable English narrative language
before activating the plugin. Neither plugin was installed in the owner's data.

Required input failures do not advance. Output failures after commit retain the
latest generated response per operation in session `presentation.json`; recovery
validates operation ID, revision and viewer under the same lock. The UI retries
presentation rather than generating another turn or suggestion.

Validation:

- Core: 1,250 tests passed, 2 deselected; one existing dependency warning.
- Plugin MCP tests: Translator 10 passed; Grammar Tools 5 passed. Both manifests,
  entrypoints and syntax validated and both local ZIPs packed in `artifacts/`.
- Ruff lint passed; mypy passed for 62 source files. All 17 changed/new Python
  files passed formatting. Global formatting reports 33 unrelated files; their
  HEAD versions also fail the same formatter. Those files were left unchanged.
- All 28 frontend modules passed Node syntax checks, adapter registry loaded,
  and HTML parsed.
- Isolated Playwright/HTTP run: committed turn recovery kept generated turns at
  2; suggestion recovery kept generated suggestions at 1; rereading state kept
  translation calls at 11. Controlled failures returned expected HTTP 503.
- Local llama.cpp real SDK run used temporary data, English canonical speech
  and narration, Portuguese displayed text, persistent translation cache and
  debug records containing plugin agent/session/turn/operation metadata.

Provider checks used the production request builder and actual shared adapter
payloads via curl. The final local model was
`Gemma-4-26B-A4B-StyleTune-QK-Heretic.i1-IQ4_XS.gguf`.
OBSERVED: manual inspection of one four-sentence fixture translated three times
per direction showed none of the preregistered defects in those six outputs.
The isolated critic identified the fixture's narrow coverage; this is a seam and
fixture check, not an estimate of general translation accuracy or narrative quality.
Earlier rejected prompt outputs are retained with the preregistration and final
raw requests/responses. All checks after owner steering used local inference.

No commits, remote operations, publication, catalog changes or real session/config
mutations were performed. Existing OpenRouter source/catalog changes and unrelated
planning artifacts were preserved.
