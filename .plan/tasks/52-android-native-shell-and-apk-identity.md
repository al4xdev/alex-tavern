# Task 52 — Android native shell and APK identity

> **Status:** in progress — native UX changes and device validation pending.

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

- Kotlin/manifest compilation;
- native document picker opened from the third-party plugin installer;
- status/navigation bars hidden after launch and after focus returns;
- collapsed scene facts visible as a complete row on the mobile viewport;
- launcher label/icon/version inspected from the installed package;
- regression tests and physical-device smoke evidence.

## Next stage after closure

Adapt the beta APK for Google Play distribution: release signing, Android App
Bundle, target-SDK/policy review, store metadata, privacy/data-safety declarations,
and an internal testing track.
