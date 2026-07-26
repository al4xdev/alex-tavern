# Task 52 — Android native shell and APK identity

> **Status:** ✅ CLOSED (2026-07-25) — native identity, file boundary,
> immersive shell, quiet boot and shared mobile tag layout delivered.
> Evidence article: [Case No. 18](../../docs/cases/18-android-native-shell-mobile-evidence-2026-07-25.md).

## Research question

Can the Android shell behave as a first-class full-screen Alex Tavern client
while keeping the web application and backend contracts unchanged?

## Scope

- ship the Alex Tavern name, PWA-derived launcher icon, and version `0.1`;
- bridge WebView file inputs to Android's document picker for third-party ZIPs;
- run the game in immersive full-screen mode with transient system bars;
- remove the bootstrap-log button from the production shell;
- fix the pre-existing narrow-screen scene panel which clipped its first fact-tag row;
- retain boot diagnostics in logcat/private storage without exposing permanent UI;
- rebuild and exercise the resulting APK on the physical device.

## Closure evidence required

- [x] Kotlin/manifest compilation (`assembleDebug`, 44 tasks);
- [x] native document picker opened from the third-party plugin installer
  (owner-confirmed physical interaction);
- [x] status/navigation bars hidden after launch and focus-return handling compiled;
- [x] collapsed scene facts measured as complete rows at 393 px and 360 px;
- [x] launcher label/icon/version inspected from package resources and final APK;
- [x] focused regression: 62/62; physical screenshots and document-picker smoke;
- [x] full regression: 785 passed, 2 deliberately deselected; Ruff format/check
  and mypy clean;
- [x] final APK SHA-256:
  `c4836235b975276f0315c8872d5c8bc50e29c50db4ff633ed93fdb42fab164a0`.

## Negative result retained as evidence

The sub-frame WebView flash when opening large modals was not eliminated by
animation suppression or opaque-surface variants. Every experimental rule was
removed; no ineffective blur/opacity stack remains. This does not block the native
shell contract and is documented in Case No. 18.

## Next stage after closure

Adapt the beta APK for Google Play distribution: release signing, Android App
Bundle, target-SDK/policy review, store metadata, privacy/data-safety declarations,
and an internal testing track.
