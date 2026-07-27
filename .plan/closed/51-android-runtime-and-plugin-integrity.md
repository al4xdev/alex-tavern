# Task 51 — Android runtime and plugin integrity

> **Status:** ✅ CLOSED (2026-07-27) — the canonical runtime, metadata-free
> plugin publication and Android process-restart boundary all crossed their
> physical-device gates.
> Evidence article: [Case No. 17](../../docs/cases/17-android-runtime-plugin-integrity-2026-07-25.md).

## Research question

Can the canonical FastAPI/plugin runtime run inside Chaquopy without Android-only
storage forks, while preserving atomic plugin publication and applying activation
changes through a real process restart?

## Scope

- resolve the packaged static root independently of the process working directory;
- pass the private Android data directory before importing the backend;
- publish hub and installed plugin trees without copying unwritable metadata;
- preserve the generic `/plugins/restart` contract while providing an Android
  process-restart boundary;
- verify hub synchronization, all curated installs, activation/deactivation,
  process replacement, persistence, and the complete Python test suite.

## Closure evidence required

- [x] reproducible debug APK build;
- [x] HTTP health/version/plugin inventory from the physical device earlier in
  the session;
- [x] old and new Android PIDs proving a complete restart;
- [x] active plugin visible after that measured restarted server boots;
- [x] regression tests (785 passed, 2 deliberately deselected), Ruff and mypy;
- [x] local commits only; no push.

## Physical closure evidence — 2026-07-27

ADB reached the physical XT2201-2 after being run outside the restricted process.
The installed application reported build commit
`008c27bd1c5f24988d633ba452af324fd77bf0fa`, the final evidence commit, and
`/health` returned `{"status":"ok"}` before and after both transitions.

The Plugin Center then exercised the native close-and-restart boundary twice:

1. PID `13801` deactivated `dev.alex-tavern.suggestion-preloader`; closing the
   Plugin Center relaunched the app as PID `14141`. The new `/plugins` response
   reported the plugin inactive and omitted it from `loaded`.
2. PID `14141` reactivated the same plugin; closing the Plugin Center relaunched
   the app as PID `14424`. The new `/plugins` response reported `state: current`,
   `active: true`, and included the plugin in `loaded`.

The second pass restored the device's original active set. In both cases
`bootstrap.log` recorded `restartApplication: handing off to restart relay`
followed by a fresh Chaquopy/Uvicorn boot and a successful `/health`.

The local APK retained the recorded SHA-256
`c4836235b975276f0315c8872d5c8bc50e29c50db4ff633ed93fdb42fab164a0`.
`adb install -r` could not replace the existing package because its signing key
differed; the app was deliberately not uninstalled because that would erase the
private plugin state under test. The measured installed build identifies the
same final source commit, so this signing-key mismatch does not weaken the
process-replacement or persistence evidence.
