# Task: Character Converter System (Character.ai & Raw Description to Tavern Schema)

**Status:** Explicit future work  
**README evidence:** N/A (Requested by User)

## Stated behavior

- Add a character converter utility (e.g., CLI command, REST endpoint, or frontend button).
- Accept character description inputs as either:
  - Raw text (freeform descriptions, second-person style like Character.ai cards, or third-person blurbs).
  - Images (JPEG/PNG of a character, processed via a vision LLM to generate description and profile).
- Invoke a structured LLM pass (using a system prompt that understands the architectural differences of the tavern) to output a validated character schema:
  - Map properties to separate `mind` (name, personality, knowledge, current_mood) and `body` (name, physical_description, outfit) structures.
  - Enforce conversion rules:
    - **No Physical Actions:** The character's personality and dialogue examples must not contain any descriptions of physical actions or gestures (e.g., `*cora*`, `*sorri*`, `*olha para você*`, `*smiles*`, `*sighs*`).
    - **Separate Speech & Thought:** Speech examples must be converted to plain text dialogue, and any actions/gestures or internal states in the original description must be mapped to psychological description in the personality/thoughts block.
    - **Third Person:** The personality field must be normalized to third-person format.
- Output a JSON structure directly compatible with user presets (`.data/presets/{name}.json`).

## Current repository state

- No automated character parser or converter exists.
- Character additions (like Yasmin and Fernanda) must be translated and cleaned up manually by hand or by developer agents to conform to the `models.py` schema and validation regex (`_PHYSICAL_ACTION_RE` in `src/agents/character.py`).

## Open questions

- Should the converter run as an API endpoint (`POST /presets/convert`) or as an off-line developer tool in `tools/`?
- How should image uploads be handled in the API and stored (e.g., temporary storage, backend base64 processing)?
- Vision model requirements: does the current active provider configuration support multimodal input (vision) for image-based generation, or does it require a fallback/specific model selection?
