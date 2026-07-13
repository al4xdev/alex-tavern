# Task: Help Menu, Localized Guides & Skip Turn next_speaker Loop Fix

**Status:** Completed and closed
**Closed:** 2026-07-13
**README evidence:** `README.md`
**Detailed report:** [walkthrough.md](file:///home/alex/.gemini/antigravity-cli/brain/d16b955d-246f-453e-8845-7c0804525a7f/walkthrough.md)

## Goal

Implement an interactive sliding Help Drawer and a localized Quick Tips Banner in the game frontend. Keep the codebase entirely vanilla and dependency-free. Also, fix the loop bug where skipping a turn yields control back to the player immediately instead of allowing NPCs or the Narrator to react.

## Acceptance criteria

- [x] Create localized help markdown files for roleplay rules, history compaction, settings, shortcuts, mobile gestures, and the hover/long-press action menu.
- [x] Implement dynamic localization in the frontend to load Portuguese or English markdown guides with a fallback.
- [x] Create a dismissible random quick tip banner mapped to translated strings.
- [x] Fully translate the Narrator Event Hint modal.
- [x] Fix the loop bug where skipping a turn fails to exclude the player character from the Narrator's `next_speaker` options.

## Closure evidence

- Help guides are loaded dynamically in PT or EN from `src/static/help/{locale}/{topic}.md` based on active application preferences.
- A fallback is in place: if a localized article does not exist, the app gracefully falls back to the English version under `src/static/help/en/`.
- Tips banner selects a random warning from `warning.json` upon loading or starting a session, displays it via `i18n`, and navigates to the target guide on click.
- Narrator Event Hint Modal is fully translated via PWA `i18n` matching.
- Player character `C1` is always excluded from `next_speaker` choices in Uvicorn turns, avoiding skip-turn prompting loops.
- Staged, validated (all 190 tests passed), and committed all changes.
