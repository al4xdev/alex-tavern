# Capture 02: Complete turn

**README placeholder (`README.md:19`):**

```text
<place_2:gif of a full turn — player submits an action, narration streams in, a character responds, mood/scene update in the debug panel>
```

## What to capture

Record one uninterrupted turn showing this sequence:

1. The human submits an action.
2. Narrator text appears with its frontend typewriter reveal.
3. A non-controlled Character responds.
4. The debug/state panel shows the resulting mood or scene update.

Choose a turn where the Narrator actually routes to another Character and changes at least
one visible mood or scene field; otherwise the GIF would not demonstrate the behavior named
by the placeholder.

The current UI reveals a completed response character by character; it does not stream model
tokens from the backend. The capture should show the visible reveal without claiming transport
streaming.

## Deliverable

- Preferred output: `docs/media/readme/02-full-turn.gif`.
- Trim idle time before submission and after the state update.
- Replace the literal `<place_2:...>` line in `README.md`.

## Done when

- A viewer can follow input → Narrator → Character → state change without explanatory text
  outside the GIF.
