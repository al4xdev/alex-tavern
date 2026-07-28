# Android package

The Android shell embeds the canonical FastAPI application with Chaquopy and
serves the normal frontend from `http://127.0.0.1:8889/`. It does not maintain
an Android-specific backend or frontend copy.

## Reproducible local build

From the repository root:

```bash
.claude/skills/android-apk-lab/scripts/build-debug-apk.sh
```

The helper builds its toolchain in Docker, keeps SDK and Gradle caches under
the ignored `.ci-cd/android/.local/` directory, stamps `src/version.txt` with
the source commit, and produces both:

- `.ci-cd/android/app/build/outputs/apk/debug/app-debug.apk`
- `.ci-cd/android/app/build/outputs/bundle/debug/app-debug.aab`

The current matrix is compile/target SDK 36, min SDK 24, AGP 9.2.1, Gradle
9.4.1, JDK 17, Chaquopy 17 and Python 3.14. The debug package contains
`arm64-v8a` and `x86_64`.

## Finite background runtime lease

`MainActivity.onPause` starts `RuntimeLeaseService` while the Activity is still
foreground-eligible. The same-process foreground `shortService` raises the
importance of the existing Chaquopy/Uvicorn process while a user-visible call
finishes. It is not the backend owner, is `START_NOT_STICKY`, does not start at
boot and does not request a battery-optimization exemption.

The lease:

- stops when the Activity resumes;
- stops itself after 120 seconds;
- implements Android's `shortService` timeout callback;
- uses a low-importance, silent notification;
- serializes a quick pause/resume stop through `onStartCommand`, so every
  foreground-service start satisfies Android's `startForeground` contract.

The first 120 seconds have the foreground-service process-priority contract.
Any survival after the lease expires is ordinary Android cached-process
behavior and is deliberately not guaranteed.

## Physical smoke

With exactly one authorized device connected:

```bash
.claude/skills/android-apk-lab/scripts/adb-smoke.sh
```

The helper installs with `adb install -r`, launches with the real
MAIN/LAUNCHER intent, forwards port 8889, checks `/health` and `/version`, and
captures the PID, package state, bootstrap log and a screenshot.

Release publication still requires the owner's durable upload key, Play App
Signing setup, store metadata, policy declarations and track testing.
