# Task 51 — Android runtime and plugin integrity

> **Status:** in progress — implementation complete; final APK/device evidence pending.

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

- reproducible debug APK build;
- HTTP health/version/plugin inventory from the physical device;
- old and new Android PIDs proving a complete restart;
- active plugin visible after the restarted server boots;
- regression tests, Ruff, formatting, mypy, and full pytest;
- local commits only; no push.
