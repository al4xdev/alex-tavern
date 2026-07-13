# Task: Character avatars (Base64 storage and UI rendering)

**Status:** Explicit future work  
**README evidence:** N/A (Requested by User)

## Stated behavior

- Add support for character profile pictures/avatars.
- Store images directly inside the character's JSON structure as Base64 strings to avoid complex local disk path management.
- Store two versions of the avatar to balance speed and quality:
  - `avatar_thumbnail`: A downscaled version (e.g., 128x128 pixels) for list views, chat bubbles, and the setup screen.
  - `avatar_full`: A higher resolution version (e.g., 512x512 pixels) that displays in a lightbox modal when clicking the avatar.
- Implement frontend resizing (via HTML5 Canvas) during file upload to keep Base64 strings compact before saving.
- **Prompt Isolation (Already Native):** No manual stripping is required on the backend. The prompt builders (`character.py` and `narrator.py`) do not serialize the whole Character object; they explicitly extract only specific fields (like `name`, `personality`, `physical_description`, and `outfit`). Therefore, adding avatar fields to `CharacterBody` will not leak them into LLM contexts.

## Difficulty Assessment

- **Overall Difficulty:** **Easy (approx. 1.5 - 2 hours of implementation)**
- **Backend changes (Easy):** Add optional avatar properties (`avatar_thumbnail`, `avatar_full`) to the `CharacterBody` dataclass in `src/models.py` and update dictionary serializers.
- **Prompt Isolation (Free):** Already handled natively by the explicit formatting loops in the agent code.
- **Frontend changes (Medium):** 
  - Add image upload controls to the character setup cards in `setup.js`.
  - Implement canvas-based image downscaling and FileReader conversion to base64.
  - Render avatars next to dialogue turns in the chat view (`app.js`).

## Current repository state

- The `CharacterBody` model only holds `name`, `physical_description`, and `outfit`.
- The frontend chat view and lobby render generic placeholders or text names for speaker identification, with no image rendering capabilities.

## Open questions

- **Downscaling details:** What are the target resolutions and compression levels for the thumbnail and full image?
- **Default avatar:** Should we show a default placeholder avatar (e.g. SVGs) if no photo is uploaded?
