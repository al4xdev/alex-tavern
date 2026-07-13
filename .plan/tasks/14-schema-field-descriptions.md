# Task: Enrich JSON schemas with field descriptions for LLM guidance

**Status:** Explicit future work  
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
