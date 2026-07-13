# Task: Frontend internationalization and language selector

**Status:** Completed  
**Primary surface:** `src/static/index.html`, `src/static/setup.js`, `src/static/app.js`

## Goal

Make the frontend multilingual and add an interface-language selector to the configuration
modal that already opens from the header's settings button (`#settings-btn` → `Setup.open()`).

The first supported interface languages should be:

- Portuguese (Brazil), `pt-BR`;
- English, `en`.

This setting controls application chrome only. It must not translate character data, presets,
saved conversations, player input, Narrator output, or Character output. Story/model language
remains independent from interface language.

## Current behavior

- `src/static/index.html` declares `lang="pt-BR"` and contains Portuguese labels,
  descriptions, placeholders, button text, titles, and accessibility labels directly in the
  markup.
- `src/static/setup.js` and `src/static/app.js` create additional Portuguese UI text at
  runtime, including validation errors, notifications, dynamic placeholders, action labels,
  confirmation prompts, loading states, and empty states.
- The header settings button already opens the adventure configuration modal through
  `Setup.open()`, but that modal has no application-preferences section or language selector.
- No translation catalog, locale state, translation helper, or persisted interface-language
  preference exists.

## Implementation scope

1. Introduce a small frontend i18n module with translation catalogs keyed by stable message
   identifiers. Keep one source language complete and make missing keys fall back safely to it.
2. Move all user-facing frontend strings out of hardcoded HTML/JavaScript paths and into the
   catalogs. Cover static text and strings generated dynamically by `setup.js`, `app.js`, and
   other files under `src/static/`.
3. Add an **Interface language / Idioma da interface** selector to a clearly separated
   application-preferences section of the existing configuration modal.
4. Apply a selection immediately, without restarting the current session or reloading the
   page. Preserve form values, open modal state, chat history, and all current session state.
5. Persist the selected locale in `localStorage` under a dedicated versioned key. On startup,
   use the saved value; when none exists, choose a supported browser locale and otherwise fall
   back to `pt-BR`.
6. Update `document.documentElement.lang` whenever the locale changes. Translate visible text,
   placeholders, `title`, `aria-label`, confirmation dialogs, toasts, validation feedback,
   loading/error states, and dynamically inserted UI.
7. Keep identifiers and persisted domain data locale-neutral. Do not store translated labels
   as API values, preset fields, character IDs, action values, or session state.
8. Make adding another language a catalog-only operation wherever practical, without adding
   another branch throughout the UI code.

## UX placement

- Reuse the existing configuration modal opened by the ⚙️ button; do not create another
  settings modal solely for language.
- Add a small **Application preferences / Preferências do aplicativo** section near the top of
  the modal, separate from Presets and adventure configuration.
- Label each option in its own language so it remains recognizable after an accidental switch:
  `Português (Brasil)` and `English`.

## Acceptance criteria

- A user can switch between `pt-BR` and `en` from the existing configuration modal.
- The visible application updates immediately and consistently, including the setup modal,
  session list, game controls, action popup, suggestion UI, compaction/undo controls, debug
  drawer, empty/loading/error states, tooltips, and accessibility labels.
- Refreshing the page preserves the chosen interface language.
- A first visit uses a supported browser language when available and otherwise uses `pt-BR`.
- Changing interface language does not alter the active session, form contents, presets,
  conversation history, or language of model-generated content.
- `document.documentElement.lang` matches the active locale.
- No raw translation key is shown when a catalog entry is missing; fallback behavior is tested.
- Automated frontend tests cover locale selection, persistence, fallback, immediate rerendering,
  and at least one dynamic message from both `setup.js` and `app.js`.

## Validation checklist

- Search `src/static/` for remaining user-facing Portuguese/English literals and either migrate
  them or document why they are not translatable UI copy.
- Exercise both languages at desktop and mobile widths.
- Verify a locale change while a session is active and while configuration fields contain
  unsaved edits.
- Verify buttons and icon-only controls with a screen reader or accessibility inspection so
  translated `aria-label` and `title` values remain meaningful.
- Verify browser-locale detection with supported, region-variant, unsupported, and missing
  language values.

## Out of scope for this task

- Translating existing presets or automatically selecting `thorn-lyra` versus
  `thorn-lyra-pt`.
- Forcing the Narrator or Characters to answer in the interface language.
- Translating saved sessions, user-authored content, raw LLM logs, or model responses.
- Backend/API localization beyond mapping known errors to frontend-owned messages where needed.

## Open design questions

- Whether the translation catalogs should be plain JavaScript objects or JSON loaded at
  startup; prefer the simplest option that works offline with the current PWA.
- Whether locale choice should eventually become a server-side user preference if accounts or
  cross-device synchronization are introduced.

---

## Resolution Summary

This task was resolved successfully. Here is the justification for how each point was implemented:

1. **Frontend i18n Module (`src/static/i18n.js`):** Introduced a lightweight i18n module with translations dictionary keyed by locale code (`en`, `pt-BR`) and fallback logic. If a key is missing, it falls back cleanly to the source language.
2. **Catalog Migration:** Hardcoded labels, placeholders, tooltips, and dynamic notification templates in `index.html`, `app.js`, and `setup.js` were successfully externalized to the catalog dictionary. Elements utilize `data-i18n` attributes for static elements, combined with `bindTranslation` and dynamic runtime `t()` formatting for dynamically generated text.
3. **Preferences Section:** Added a dedicated "Application preferences / Preferências do aplicativo" section directly to the setup modal containing the `#interface-language` dropdown with options labeled in their respective languages.
4. **Immediate Update:** Updates are applied immediately to all visible elements using the `translateSubtree` helper without page reload or session restart. Chat history, preset forms, and session state are completely preserved.
5. **Persistence & Startup Fallback:** Active locale is persisted in `localStorage` under `rpt_interface_locale_v1`. During initialization, it detects client preferences via `navigator.languages`, matching the first supported option. Otherwise, it defaults to `pt-BR`.
6. **Lang attribute & HTML translations:** Updated `document.documentElement.lang` on language change and translated UI tooltips (`title`), dynamic alert modals (`toasts`), placeholders, and screen reader announcements (`aria-label`).
7. **Domain data isolation:** Active adventure settings, character names, presets, and model settings are kept strictly locale-neutral and remain unmodified on frontend translation.
8. **Extensibility:** Adding new locales is fully catalog-only; new dictionary modules can be plugged directly into the registry without modifying UI render scripts.

### Verification
- Implemented comprehensive automated tests (`tests/test_frontend_i18n.py`) asserting language persistence, client detection, missing key fallback, dynamic message formatting, and instant translation updates.
