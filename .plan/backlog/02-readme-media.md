# Task: Replace README media placeholders

**Status:** Eight unresolved placeholders  
**README evidence:** `README.md:3`, `19`, `163`, `222`, `262`, `388`, `434`, `465`

**Execution checklist:** [`../02-readme-media/README.md`](../02-readme-media/README.md)

## Missing assets

1. Banner screenshot or GIF showing a running scene and action controls.
2. Full-turn GIF showing player input, narration, character response, and state update.
3. Debug-panel screenshot showing raw Narrator and Character calls.
4. Undo GIF showing mood and scene restoration.
5. Suggestion-popup screenshot.
6. Compact-session screenshot with the simulated progress bar active.
7. Session-list landing-screen screenshot.
8. Startup/new-session GIF using `./start.sh` and a preset.

## Current repository state

- Each location still contains a literal `<place_N:...>` marker.
- The only image assets currently tracked are application icons under `src/static/`;
  there are no README screenshots or GIFs.

## Open questions

- The README does not specify the asset directory, capture dimensions, theme, example
  session, or whether sensitive prompt/session content must be redacted.
