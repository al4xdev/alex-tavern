# README media capture checklist

**Parent task:** [`../tasks/02-readme-media.md`](../tasks/02-readme-media.md)  
**Status:** Ready to capture

The README contains eight literal `<place_N:...>` placeholders. Each file below turns one
placeholder into a concrete capture task.

## Checklist

- [ ] [01 — Application banner](./01-banner.md)
- [ ] [02 — Complete turn](./02-full-turn.md)
- [ ] [03 — Raw debug log](./03-debug-log.md)
- [ ] [04 — Undo restoring state](./04-undo-state.md)
- [ ] [05 — Suggestions popup](./05-suggestions.md)
- [ ] [06 — Compaction progress](./06-compaction-progress.md)
- [ ] [07 — Session-list landing screen](./07-session-list.md)
- [ ] [08 — Startup and preset session](./08-startup-preset.md)

## Shared requirements

- Capture the real application; do not mock UI that does not exist.
- Use one visually coherent demo session across captures where possible.
- Do not expose API keys, private hostnames, personal paths, or unrelated session data.
- Keep text large enough to read in the rendered GitHub README.
- Store final media in a tracked repository directory and replace the corresponding
  `<place_N:...>` line with Markdown referencing that asset.
- After replacement, verify that no `<place_N:` marker remains for the completed item.

## Proposed filenames

These names are organizational defaults, not existing files:

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
