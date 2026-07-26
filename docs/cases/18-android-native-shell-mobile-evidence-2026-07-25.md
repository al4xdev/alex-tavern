# From embedded WebView to named application: the Alex Tavern Android shell

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 18 |
| **Date** | 2026-07-25 |
| **Kind** | Native-shell integration + mobile visual validation |
| **Roadmap** | Closed Task 52 (`.plan/closed/52-android-native-shell-and-apk-identity.md`) |
| **Commits** | `eb3f52a`, `8bd5c4e`, `869b616`, `45d6c4a` |
| **Status** | Delivered and validated; Google Play adaptation is the next stage |

## Abstract

The beta APK initially exposed the web product through a generic Android shell: an
incorrect app identity, no PWA-derived launcher art, visible system bars, a permanent
bootstrap-log control, and no native implementation for HTML file selection. Mobile
validation also exposed a pre-existing responsive defect in the shared PWA: a fixed
collapsed scene height showed half of a wrapped tag row. This work gave the APK the
Alex Tavern identity and version `0.1`, introduced the missing native file and
immersive-mode boundaries, retained diagnostics outside normal UI, and fixed the
shared scene panel using measured row geometry. An unrelated WebView modal flash was
investigated frame by frame; unsuccessful CSS mitigations were removed instead of
being accumulated.

## 1. Method

Native boundaries were tested on the physical device through ADB screenshots,
UIAutomator, package inspection and direct user interaction. Shared responsive behavior
was reproduced at 393 px and 360 px in a touch-enabled Playwright context. Video was
examined as contact sheets when a defect lasted less than one rendered frame.

The acceptance rule was boundary-specific:

- Android document picker, package identity and system bars require a device;
- scene wrapping and slash/composer behavior belong to the shared web source and can
  be measured reproducibly in Chromium;
- a visual mitigation that did not eliminate its defect had to be removed before the
  next hypothesis.

## 2. Native identity and packaging

The manifest now reads `@string/app_name`, whose value is **Alex Tavern**, and uses
launcher resources derived from the existing PWA icon and maskable icon. The debug
package remains `com.al4xdev.alextavern`; `versionCode` is 1 and `versionName` is
`0.1`. `aapt dump badging` on the final APK reports:

```text
package: name='com.al4xdev.alextavern' versionCode='1' versionName='0.1'
sdkVersion:'24'
targetSdkVersion:'33'
application-label:'Alex Tavern'
```

The build stages canonical `src` and `src/static` rather than maintaining an Android
fork. A stable isolated SDK, Gradle cache and debug keystore make `adb install -r`
reproducible and preserve on-device data between iterations.

## 3. The missing file boundary

HTML `<input type=file>` does not automatically launch a useful Android document
picker from this WebView configuration. `WebChromeClient.onShowFileChooser` now
receives the callback, launches `FileChooserParams.createIntent()` through the
Activity Result API, and returns the selected URI through
`parseResult`. A ZIP-specific `ACTION_OPEN_DOCUMENT` intent is the defensive fallback.
The user confirmed that **Choose file** opened the system file manager from the
third-party plugin installer.

This is deliberately Kotlin-owned. The plugin installer still receives an ordinary
browser `File`; no Android URI or permission branch enters the JavaScript or Python
plugin contracts.

## 4. Immersive shell and quiet boot

`WindowInsetsControllerCompat` hides status and navigation bars, permits transient
reveal by swipe, draws into display cutouts on supported versions and reapplies the
mode whenever window focus returns. Physical screenshots show the product occupying
the full display without permanent system bars.

The permanent “Ver Logs de Boot” control and its dialog were removed. Boot still has
a minimal **Iniciando Alex Tavern…** status while Chaquopy extracts and `/health`
comes up; detailed evidence continues in Logcat and `files/bootstrap.log`. On timeout,
the UI reports a short diagnostic instruction instead of dumping implementation logs
into the product.

## 5. A measured responsive fix, not another fixed height

The original mobile rule forced the scene panel to 74 px. At 393 px the panel had
`scrollHeight = 93 px`; the third row began at approximately 63.6 px, so the collapsed
surface displayed roughly 10 px of a tag it could not complete. The fix introduced a
single CSS contract, `--scene-collapsed-height`, consumed by both layout and JavaScript
overflow detection:

- desktop: 44 px;
- large layout: 48 px;
- phone: 64 px, ending before the next flex row begins.

Post-fix probes established:

| Viewport | Collapsed result | Expanded result |
|---|---|---|
| 393 px | Two complete fact tags; no partial third row | All four tags visible |
| 360 px | One complete fact tag; no partial next row | All four tags visible |

The fix is in the canonical PWA, so Android and browser deployments share the same
geometry rather than carrying an APK-only style override.

## 6. Negative result: the modal flash

Opening Settings or Plugin Center on the physical WebView produced a very brief mixed
frame. ADB video showed no Activity recreation and no server reload. Three CSS
hypotheses were tried: disabling the modal animation, forcing an opaque surface, and
more specific transition suppression. A hybrid WebView tile frame remained.

All experimental CSS was removed. The evidence points to WebView tile composition,
but the work does not claim a fix. This negative result matters because retaining
several ineffective blur/opacity rules would have converted an unresolved visual
artifact into permanent styling debt.

## 7. Reproducible lab and current evidence

A repository-local `android-apk-lab` skill now documents the exact build and ADB
workflow, failure signatures, private-directory behavior and safe reinstall policy.
Its scripts:

- provision/reuse an isolated SDK and Gradle cache;
- stamp the current commit into `src/version.txt`;
- build in Docker with Java 17 and Chaquopy Python 3.11;
- install with the stable debug key;
- collect health, version, PID, active window, bootstrap log and screenshot.

The final build completed in 6 seconds with 44 Gradle tasks and produced:

```text
c4836235b975276f0315c8872d5c8bc50e29c50db4ff633ed93fdb42fab164a0
```

Focused Android/plugin/frontend tests passed 62/62. The complete suite passed 785
tests with two deliberately deselected; Ruff format/check and mypy were clean.

## 8. Next stage: Google Play

The beta APK is not yet a Play release. The next program must be explicit rather than
hidden inside debug packaging:

1. raise `compileSdk`/`targetSdk` to the Play-required current level and review behavior
   changes;
2. create a release keystore outside Git and configure reproducible release signing;
3. generate an Android App Bundle (`.aab`) with monotonically increasing version codes;
4. review cleartext traffic and backup policy, minimizing both for production;
5. prepare app name, descriptions, icon, feature graphic, phone screenshots and support
   contact;
6. document privacy policy and Data safety declarations for local session data,
   provider keys and network calls;
7. run pre-launch reports and distribute first through an internal testing track;
8. retain the debug APK pipeline as a separate development artifact.

## Conclusion

The shell is now recognizably Alex Tavern and owns the boundaries only Android can
own: launcher identity, document selection, process relaunch and system UI. Shared
roleplay, plugin and responsive contracts remain in the canonical application. The
next change is therefore a distribution project, not another round of WebView fixes.
