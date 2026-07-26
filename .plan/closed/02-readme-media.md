# Task 02 — Mobile README media

> **Status:** ✅ CLOSED (2026-07-25) — every live README placeholder was replaced
> with verified mobile media; the stale eight-placeholder inventory was corrected
> to the seven markers that actually existed.

## Question

Can the README demonstrate the real product, including its touch-only controls,
without exposing personal sessions or presenting desktop media as evidence for the
mobile client?

## Method

The capture used a real Chromium mobile context at a 393 × 852 CSS viewport,
device scale factor 2, touch input enabled, and the English locale. A temporary
`ROLEPLAY_DATA_DIR` contained one curated English session (`Thorn` and `Lyra`);
the tracked application and normal plugin runtime served every screen.

Three classes of evidence were kept separate:

1. **Real model boundary:** the full turn and three move suggestions came from
   actual DeepSeek calls against the same session.
2. **Real application state:** raw Director, prose, perspective and Character
   JSONL entries were rendered through the Debug drawer; no mock DOM or fixture
   text was introduced.
3. **Real touch flows:** the session manager and atomic Undo were recorded through
   the mobile controls. Undo used the long-press Send action sheet and mutated only
   the isolated copy.

Raw recordings remained in `/tmp`. Final GIFs were trimmed, wait time in the
full-turn recording was accelerated, frames were cropped to the true CSS viewport,
and representative transition frames were inspected before publication.

## Result

The README now contains:

- a complete mobile turn from composed speech/thought/action through narration
  and Character response;
- raw per-agent observability;
- atomic turn Undo through the touch action sheet;
- three generated `{speech, action}` suggestions;
- the advanced mobile action sheet with compaction and checkpoint controls;
- the clean session-list landing screen;
- a mobile landing-to-session-load flow;
- an additional PNG of the animated slash palette, requested after the original
  task was written.

Assets live under `docs/images/readme/`. PNG text remains readable at native
viewport width. GIFs are 393 × 852 (the full-turn encoder produced an equivalent
even width of 392), 12.5 fps, and remain below 3.2 MiB.

## Revisions to the stale brief

The old task claimed eight unresolved markers, but the current README contained
seven. It also requested a terminal/startup GIF and a simulated mid-compaction
frame. The product direction selected mobile-only media, so startup remains
documented as `./start.sh` in text while the associated GIF shows the mobile client
opening a session. Compaction is shown in its real long-press action sheet rather
than fabricating a progress state that disappears with that sheet.

## Acceptance evidence

- `rg '<place_' README.md` returns no matches.
- Every relative `docs/images/readme/*` reference resolves.
- No API key, provider configuration, personal session list, or Android private
  path appears in any tracked frame.
- Contact-sheet inspection covered the initial, transition, and final frames of
  every tracked GIF.

## Physical-device revision — 2026-07-25

An owner-recorded Android session replaced the original synthetic-browser
full-turn GIF. The 91.8-second source recording remained outside the repository;
long model waits were removed while interaction states were preserved. The result
is presented as two adjacent 392 × 872 GIFs:

- `full-turn-mobile.gif`: 12.0 seconds and 7,376,438 bytes, covering suggestion
  selection, submission, bounded processing, narration, Character response, and
  the next suggestion set;
- `mobile-gestures.gif`: 17.2 seconds and 6,755,682 bytes, covering suggestion
  reveal, atomic Undo, the Narrator-event gesture, event submission, and the
  resulting continued turn.

Both files use 10 fps and a 128-color measured palette. Contact sheets at
one-second intervals verified the first frame, gesture transitions, post-cut
boundaries, and final state; neither GIF retains a long loading interval.
