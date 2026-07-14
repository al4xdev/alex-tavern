# Task 15 closure: Native character presets and avatars

**Status:** Completed on 2026-07-14

## Delivered design

- Native forward-only presets live in `.data/presets/{preset-name}.json` with schema version 1,
  canonical `mind`/`body`, timestamps, optimistic revision, and one optional compact avatar.
- Per-name weak-reference locks and flush/fsync/rename writes protect concurrent CRUD. Replacing an
  existing preset requires explicit confirmation plus its current revision; stale writes return a
  conflict.
- The API lists summaries, returns preset data without Base64, serves binary avatars with ETags,
  and supports revision-checked save/delete.
- The setup UI provides a complete preset library, editable draft cards, save/load/replace/delete,
  avatar selection, and stable initial fallback.
- The browser center-crops an input up to 10 MiB once to 256×256 WebP at about 0.82 quality. The
  backend verifies WebP container length, dimensions, and a 256 KiB processed cap.
- Sessions persist only `character_preset_ids`. Avatar bytes never enter `GameState`, history,
  prompts, logs, or localStorage; revisioned avatar URLs are fetched once per preset and rendered
  in setup/chat.

The reduced scope deliberately removed full images, duplicate thumbnail/full storage, lightboxes,
and dynamic insertion into an active session. Dynamic presence remains Task 13.

## Validation

CRUD, public redaction, avatar validation, revision conflict, and concurrent replacement tests pass.
The complete core suite passes with 255 tests, and prompts/state remain free of avatar Base64.
