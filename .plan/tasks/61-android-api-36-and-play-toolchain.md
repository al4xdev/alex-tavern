# Task 61 — Android targets API 36 on a current Play toolchain

> **Status:** open. Execute together with Task 60 so its finite background
> lease uses the modern foreground-service contract rather than a temporary
> API-33 fallback.

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
  36 and Gradle 9.1;
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

- [ ] clean Docker build completes with the declared toolchain;
- [ ] `assembleDebug` and `bundleDebug` both complete;
- [ ] APK metadata reports `minSdk 24` and `targetSdk 36`;
- [ ] APK and AAB contain the expected `arm64-v8a` runtime;
- [ ] APK passes the available 16 KB alignment verification;
- [ ] `adb install -r` preserves the existing private data and signing identity;
- [ ] cold boot reaches `/health` and `/version` on the physical XT2201-2;
- [ ] WebView remains full-screen without clipped or doubled system insets;
- [ ] native file picker and plugin process restart still cross their physical
      boundaries;
- [ ] Task 60's foreground `shortService` declares the correct permission,
      manifest type, runtime type and timeout behavior;
- [ ] Android-focused tests, full Python regression, Ruff and mypy pass;
- [ ] generated SDKs, caches and packages remain ignored by Git.

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
