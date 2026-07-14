# Task: Enrich JSON schemas with field descriptions for LLM guidance

**Status:** Closed without implementation (2026-07-14)  
**README evidence:** N/A (Requested by User)

## Stated behavior

- Add explicit `description` metadata fields to the JSON schemas passed to the LLM client (both for the Narrator and Character response formats).
- These descriptions should act as structured instructions that tell the model exactly what to output in each field (e.g. `narration`, `next_speaker`, `context_for_character`, `scene_update`, `mood_updates` for the Narrator; `speech` and `thought` for the Character).
- This ensures that LLMs that natively support structured output formatting (such as Gemini, llama.cpp, and DeepSeek) understand the domain requirements and validations of each field directly from the schema layout, reducing reliance on the freeform system prompt.

## Current repository state

- The JSON schemas defined in `src/agents/character.py` (`build_character_json_schema`) and `src/agents/narrator.py` (`build_narrator_json_schema`) only declare types, lists, and properties, but omit the `description` metadata key entirely.
- All field descriptions and technical instructions are currently written in the textual system prompts (such as `_build_system_prompt` in `narrator.py` and `character.py`).

## Open questions

- Will adding descriptions to the schema significantly increase token consumption in prompt caching, and is the tradeoff worth the improved compliance?
- Do all active provider adapters (e.g., llama.cpp native schema constraint, DeepSeek Flash adapter) correctly parse and enforce the `description` field when constraint grammars are generated, or do some ignore it?

## Closure decision

No change is warranted while the current role prompts and structured-output validation are
working correctly.

- `enum`, `type`, `required`, and `additionalProperties` are the enforcement mechanism: they
  constrain the JSON shape and permitted values. In particular, the Narrator's dynamic
  `next_speaker` enum already prevents any speaker outside the current allowed set.
- JSON Schema `description` is non-validating metadata. It can guide a model that reads it, but
  cannot enforce when a nullable field should be populated or what a valid narration means.
- The Narrator and Character system prompts already contain the semantic instructions proposed
  for these descriptions. Adding them to both locations would duplicate the guidance rather than
  replace a missing contract.
- The DeepSeek adapter serializes the complete schema into a system-message instruction
  (`src/llm/adapters/deepseek.py`), so every description would add prompt tokens directly. The
  llama.cpp path sends the schema for grammar-constrained output; descriptions do not strengthen
  the resulting JSON grammar.
- The local schema validator already accepts `description` as metadata
  (`src/llm/schema.py`), so this is not blocked by compatibility. It remains an optional
  experiment if debug logs later show repeated semantically invalid-but-schema-valid responses.
