# Task 61 — Android targets API 36 on a current Play toolchain

> **Status:** closed on 2026-07-27. The Docker/CI build and physical APK now
> use the coherent API-36 toolchain together with Task 60's `shortService`.

## Problem

The Android package currently builds with:

- `compileSdk 33` and `targetSdk 33`;
- Android Gradle Plugin 8.0.2 and Gradle 8.0.2;
- Kotlin Gradle Plugin 1.8.20;
- Chaquopy 15.0.1.

That build still runs on the physical Android 14 device, but it is not eligible
for a new Google Play submission after 31 August 2026. New apps and updates
must then target Android 16 / API 36. The old compile SDK also prevents Task 60
from expressing Android's `shortService` foreground-service type directly.

This task makes the Android build current and Play-toolchain-ready. It does not
publish the app or pretend that store listing, policy declarations and private
release keys can be completed in source control.

## Target matrix

Use this coherent matrix unless a real build exposes an incompatibility:

| Component | Target |
|---|---|
| compile / target SDK | 36 |
| minimum SDK | 24, unchanged |
| Android Gradle Plugin | 9.2.1, newest supported by Chaquopy 17 |
| Gradle | 9.4.1 |
| Java | 17 |
| Kotlin | AGP 9 built-in Kotlin (KGP 2.3.10), no separately pinned plugin |
| Chaquopy | 17.0.0 |
| Python runtime | 3.14 |

AGP 9.2.1 supports API 36, requires Gradle 9.4.1 and JDK 17.
Chaquopy 17 officially supports AGP 9.0 through 9.2 and Python 3.14. Built-in
Kotlin removes the obsolete independent Kotlin 1.8.20 pin; JVM target follows
the Android Java target. AGP 9.3 is newer in isolation but deliberately excluded
until Chaquopy declares it supported. API 37 remains on the SDK Manager preview
channel, so this task does not pull preview platforms into the release builder.

Do not update one member of this matrix while leaving an accidental mixed
toolchain behind.

## Scope

- migrate the root and app Gradle files to the supported plugin DSL;
- remove the explicit `org.jetbrains.kotlin.android` plugin and legacy
  `android.kotlinOptions`;
- update the reproducible Docker builder and isolated SDK to API/build-tools
  36 and Gradle 9.4.1;
- set `compileSdk` and `targetSdk` to 36 while keeping `minSdk 24`;
- upgrade Chaquopy without forking Python dependencies or runtime source;
- audit target-SDK behavior changes from Android 14, 15 and 16 that touch this
  shell: foreground-service types, notification behavior, edge-to-edge,
  predictive back and package/process lifecycle;
- retain the current immersive WebView layout under mandatory edge-to-edge;
- build both the installable debug APK and a debug AAB as packaging evidence;
- verify the APK's 64-bit native libraries for 16 KB page alignment;
- keep Task 60's implementation entirely under `.ci-cd/android/`.

## Forward-only rules

- no compatibility branch for the old Gradle, Kotlin or SDK matrix;
- no second Android project or copied runtime;
- no checked-in SDK, Gradle cache, keystore, APK or AAB;
- no reduction of `targetSdk` after compilation succeeds;
- no fallback to the old Python 3.11 Android runtime after the canonical 3.14
  dependency set crosses the physical gate.

## Physical and build gates

- [x] clean Docker build completes with the declared toolchain;
- [x] `assembleDebug` and `bundleDebug` both complete;
- [x] APK metadata reports `minSdk 24` and `targetSdk 36`;
- [x] APK and AAB contain the expected `arm64-v8a` runtime;
- [x] APK passes the available 16 KB alignment verification;
- [x] `adb install -r` preserves data when the debug signing identity matches;
- [x] cold boot reaches `/health` and `/version` on the physical XT2201-2;
- [x] WebView remains full-screen without clipped or doubled system insets;
- [x] native file picker and plugin process restart retain their physical
      boundaries;
- [x] Task 60's foreground `shortService` declares the correct permission,
      manifest type, runtime type and timeout behavior;
- [x] Android-focused tests, full Python regression, Ruff lint and mypy pass;
- [x] generated SDKs, caches and packages remain ignored by Git.

## Closure report

### Final toolchain

| Component | Delivered |
|---|---|
| compile / target / minimum SDK | 36 / 36 / 24 |
| Android Gradle Plugin | 9.2.1 |
| Gradle / Java | 9.4.1 / 17 |
| Kotlin | AGP 9 built-in Kotlin, KGP 2.3.10 |
| Chaquopy / Python | 17.0.0 / 3.14 |
| packaged ABIs | `arm64-v8a`, `x86_64` |

AGP 9.3 and API 37 preview were intentionally not mixed into the supported
Chaquopy 17 matrix. AndroidX Core 1.18.0 is the latest stable compatible with
compile SDK 36; 1.19.0 requires the API 37 preview platform.

### Build and artifact evidence

The clean isolated Docker build at source commit `1de0fe4` completed
`assembleDebug` and `bundleDebug` successfully, 55 tasks:

- APK SHA-256:
  `c71bd60e684d289a6a4d511e63fdaa96239a010ff0eb3ba1b28fedb8417a035a`
- AAB SHA-256:
  `82b2d32537964c74f88b0ac233623f47955c51a94032482724ccde5936d54969`
- APK metadata: package `com.al4xdev.alextavern`, version `0.1`,
  `minSdk 24`, `targetSdk 36`, `compileSdk 36`.
- APK native code and AAB entries include both `arm64-v8a` and `x86_64`.
- `zipalign -c -P 16 -v 4` returned `Verification successful`.
- The packaged `src/version.txt` contains the full
  `1de0fe44f8035972c5fc422d8c7a018eac24e19c` source SHA.

Gradle still reports a generic Gradle-10 deprecation notice emitted by the
Chaquopy 17 plugin. The build scripts' own deprecated assignment syntax was
removed; this upstream warning does not affect the green Gradle 9.4.1 build.

### Physical gate

On the Motorola XT2201-2 (Android 14 / API 34), the final APK installed with
the matching debug identity, cold-launched through the real MAIN/LAUNCHER
intent, loaded the server-hosted frontend and returned:

```json
{"status":"ok"}
{"commit":"1de0fe44f8035972c5fc422d8c7a018eac24e19c","debug":false}
```

Bootstrap recorded Python 3.14.0, the canonical private data directory, 32
packaged static entries and the bind on `127.0.0.1:8889`. Package state
reported target SDK 36, and PID 7723 remained stable through a Home/resume
smoke. The modern server-only WebView kept immersive layout and the native
file-picker/restart bridge from Tasks 51–52; the bridge's packaging regression
and the earlier physical restart gate remain valid because those components
were not replaced.

An isolated build initially used a different ephemeral debug key, and Android
correctly rejected `adb install -r` with
`INSTALL_FAILED_UPDATE_INCOMPATIBLE`. With the owner's authorization the old
debug install was removed; the final APK was installed cleanly. A subsequent
same-key `adb install -r` to commit `1de0fe4` preserved the new data and passed
the cold-start smoke. Release signing remains an owner operation.

### Regression evidence

- `tests/test_android_packaging.py`: 9 passed.
- Full canonical pytest run: 944 passed, 2 deselected.
- `ruff check .`: passed.
- Canonical mypy scope: passed, 60 source files.
- `ruff format --check .`: 34 known pre-existing non-Android files would be
  reformatted; this task did not touch them.
- SDKs, Gradle caches, keystores, APKs and AABs remain ignored and absent from
  the commit.

## Play readiness boundary

Closing this task means the source and CI can produce a current API-36 APK/AAB.
Before an actual Play release, the owner still needs:

- a durable private upload/release signing setup;
- Play App Signing and package ownership;
- store listing, screenshots and content rating;
- privacy policy and Data safety declarations;
- foreground-service declarations requested by Play Console;
- closed/internal-track review on representative Android versions.

Those are release operations, not reasons to keep the source toolchain stale.

## References

- Google Play target API requirements:
  <https://developer.android.com/google/play/requirements/target-sdk>
- Android Gradle Plugin 9.0 compatibility:
  <https://developer.android.com/build/releases/agp-9-0-0-release-notes>
- Built-in Kotlin migration:
  <https://developer.android.com/build/migrate-to-built-in-kotlin>
- Chaquopy 17 version compatibility:
  <https://chaquo.com/chaquopy/doc/current/versions.html>
- Android 15 target behavior changes:
  <https://developer.android.com/about/versions/15/behavior-changes-15>
- Android 16 target behavior changes:
  <https://developer.android.com/about/versions/16/behavior-changes-16>
- Foreground service types:
  <https://developer.android.com/develop/background-work/services/fgs/service-types>
