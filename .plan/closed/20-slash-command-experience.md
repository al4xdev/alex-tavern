# Task 20: Slash Command Experience

| Field | Value |
|---|---|
| Status | Closed |
| Completed | 2026-07-15 |
| Session schema change | None |

## Delivered

- Replaced the backend command descriptor with strict schema v2: localized title, summary,
  aliases and keywords; visible typed inputs; icon; and namespaced result kind.
- Replaced positional `arguments/fields/files` requests with `values/files` and kept command
  execution under the session lock with an isolated state snapshot and Base64-free debug metadata.
- Added one browser palette for core global actions, contextual session actions, active frontend
  plugin actions, and active backend plugin tools.
- Added `sdk.registerAction(descriptor, handler)` and
  `sdk.registerCommandResultRenderer(kind, renderer)`, including shared name/alias collision rules,
  plugin provenance, contextual availability, and renderer gating before execution.
- Added deterministic localized search, diacritic normalization, alias resolution, keyboard/touch/
  mouse operation, explicit empty/error states, inline field errors, and responsive desktop/mobile
  presentation with reduced-motion behavior. The first typed `/` becomes the visible sigil; a second
  slash closes slash mode and leaves one literal `/` in the speech field.
- Kept every pre-existing button/menu as an alternate entry and reused its existing handler.

## Curated hub releases

- Character Converter `1.1.0`: schema-v2 `/convert-character`, visible preset-name input, aliases,
  keywords, and `core/character-preset-draft` renderer.
- Dynamic Character Presence `0.2.0`: session action `/presence` opens, expands, refreshes, and
  focuses the existing mounted panel without adding state or HTTP paths.
- Grammar Tools and OpenRouter were reviewed and intentionally received no duplicate slash action.
- Deterministic artifacts, hashes, catalog rows, SDK docs, plugin tests, MCP validation, and hub
  checks were updated while historical artifacts remained intact.

## Validation evidence

- Core: 371 passed, 2 expected xfails.
- Focused frontend DOM/i18n harness: palette opening, keyboard completion/activation, typed form,
  disabled actions, result-renderer dispatch, aliases, keywords, diacritics, literal slash, and
  empty results.
- Hub: 39 passed; `check.py` validated four plugins and one Experience.
- Real Uvicorn/replay smoke: `/commands` returned schema v2 and Character Converter 1.1.0; command
  execution returned a preset draft while session revision stayed 0, history stayed empty, and the
  debug log contained command/model evidence without Base64.
- Desktop and mobile headless screenshots were inspected for palette/card viewport fit and layout
  stability; motion uses transient CSS transforms/opacity/clip-path and respects reduced motion.

## Boundary with S02

This task delivers discovery and execution entry points only. It does not implement workspaces,
full-screen plugin routes, `/chat`, a global non-narrative LLM context, configuration-agent loops,
skills, approval changesets, or any other Celestial/S02 capability. Character Converter remains
session-bound so its model call retains the existing session logging and transaction context.
