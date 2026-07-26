# README media capture checklist (historical)

**Parent task:** [`../02-readme-media.md`](../02-readme-media.md)  
**Status:** CLOSED / SUPERSEDED (2026-07-25)

This was the original eight-item capture inventory. The live README actually
contained seven placeholders, and the accepted delivery deliberately revised
some briefs toward verified mobile product evidence. The authoritative closure,
assets and acceptance evidence are in the parent task above.

## Checklist

- [x] [01 — Application banner](./01-banner.md)
- [x] [02 — Complete turn](./02-full-turn.md)
- [x] [03 — Raw debug log](./03-debug-log.md)
- [x] [04 — Undo restoring state](./04-undo-state.md)
- [x] [05 — Suggestions popup](./05-suggestions.md)
- [x] [06 — Compaction progress](./06-compaction-progress.md)
- [x] [07 — Session-list landing screen](./07-session-list.md)
- [x] [08 — Startup and preset session](./08-startup-preset.md)

The checkmarks mean the media track was resolved, not that every stale filename
or shot description below was followed literally. See “Revisions to the stale
brief” in the parent closure.

## Shared requirements

- Capture the real application; do not mock UI that does not exist.
- Use one visually coherent demo session across captures where possible.
- Do not expose API keys, private hostnames, personal paths, or unrelated session data.
- Keep text large enough to read in the rendered GitHub README.
- Store final media in a tracked repository directory and replace the corresponding
  `<place_N:...>` line with Markdown referencing that asset.
- After replacement, verify that no `<place_N:` marker remains for the completed item.

## Proposed filenames

These were organizational defaults, not the final accepted filenames:

```text
docs/media/readme/01-banner.webp
docs/media/readme/02-full-turn.gif
docs/media/readme/03-debug-log.webp
docs/media/readme/04-undo-state.gif
docs/media/readme/05-suggestions.webp
docs/media/readme/06-compaction-progress.webp
docs/media/readme/07-session-list.webp
docs/media/readme/08-startup-preset.gif
```
