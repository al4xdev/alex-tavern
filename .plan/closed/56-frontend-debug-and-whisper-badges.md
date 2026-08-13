# Task 56 — The debug drawer and false whisper badges in the frontend

> **Status (2026-07-26): CLOSED WITH CONFIDENCE.**
> Fixed on branch `refactor/pre-1.0-cleanup`, with reproduction and validation in a
> real browser at both desktop and mobile viewports.

## Symptom

Turning debug on made the frontend show:

```text
Could not load debug log: bindTranslation is not defined
```

After turning debug off, many `🤫 whispered to ...` badges stayed visible in the
transcript. The behaviour occurred on the PC as well as in the mobile PWA.

## Pre-fix reproduction

Playwright run against the real session `1cad8c55`:

| State | Desktop | Mobile |
|---|---:|---:|
| Drawer active after turning debug on | yes | yes |
| `bindTranslation is not defined` toast | yes | yes |
| Drawer active after turning debug off | no | no |
| Toggle checked after turning off | no | no |
| Drawer `display` after turning off | `none` | `none` |
| Whisper badges still in the transcript | 16 | 16 |

The drawer was not stuck. What remained were transcript badges unrelated to the
debug state.

## Confirmed causes

### A dependency lost in the drawer extraction

Commit `6319304` moved `makeCopyBtn` into `src/static/debug-drawer.js`, but the
module imported only `t` and `translateDocument`. The function kept calling
`bindTranslation`, producing the error only when a real log entry was rendered.

### A zone audience labelled as a whisper

`renderHistory` treated any `TurnRecord.audience != null` as a whisper. The current
model also uses `audience` for acoustic zone perception, and distinguishes the
origin in `audience_origin`:

- `whisper`: an explicit confidential audience;
- `zone`: an audience computed from position/acoustics.

All 38 records with an audience in session `1cad8c55`'s final state had
`audience_origin="zone"`. That is why the frontend produced 16 enormous badges
listing nearly the whole cast, despite there being no explicit whisper.

This was neither a drawer leak nor persistent debug content. Character thoughts
remain reader-visible by contract: the README defines the transcript as literary
presentation, and the private boundaries hold between the agents/characters.

## Implementation

- `src/static/debug-drawer.js`: imports `bindTranslation` explicitly.
- `src/static/app.js`: preserves `audience_origin` in the buffer and renders `🤫`
  only when the origin is `whisper`.
- `src/static/sw.js`: shell cache advanced from `rpt-shell-v24` to `rpt-shell-v25`.
- tests: pin the import, include the drawer in the i18n sweep, and distinguish an
  explicit whisper from a zone audience.

There was no change to the backend, the persisted schema, agency or any narrative
boundary.

## Validation

- Real Playwright Chromium at desktop `1440x900` and mobile `393x852` with touch:
  - turning debug on loads the log with no error toast;
  - turning it off removes `active`, unchecks the toggle and results in
    `display:none`;
  - zero console errors;
  - zero false whisper badges in the real session.
- `48 passed`: frontend architecture, i18n and whisper UI.
- `node --check` on every module in `src/static/` and the adapters.
- parsing of `src/static/index.html`.
- `git diff --check`.

## Result

Debug mode opens and closes correctly in both layouts, the log renders again, and
acoustic zone perception no longer appears as a whisper in the normal transcript.
