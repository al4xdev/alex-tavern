# Task 51 — Android runtime and plugin integrity

> **Status:** implementation and exact APK build complete; one physical gate
> remains because the final restricted process cannot access the ADB daemon.
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
- [ ] old and new Android PIDs proving a complete restart;
- [ ] active plugin visible after that measured restarted server boots;
- [x] regression tests (785 passed, 2 deliberately deselected), Ruff and mypy;
- [x] local commits only; no push.

## Exact remaining command boundary

Run `.claude/skills/android-apk-lab/scripts/adb-smoke.sh`, record the current PID,
toggle one plugin, close Plugin Center, then record the new PID and `/plugins`.
The current execution sandbox rejects the ADB smart-socket listener with
`Operation not permitted`; this is an evidence-access limitation, not a passing
restart measurement. Do not move this task to `closed/` until the two PIDs differ
and the selected activation survives the new `/health`.
