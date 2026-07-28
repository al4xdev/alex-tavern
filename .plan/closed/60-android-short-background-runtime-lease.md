# Task 60 — Android grants active FastAPI calls a short background lease

> **Status:** closed on 2026-07-27. A same-process foreground `shortService`
> won the physical gate and is bounded by an app-owned 120-second ceiling.

## Problem

Android currently starts Chaquopy/Uvicorn from a raw thread owned by
`MainActivity`. Nothing explicitly stops it in `onPause` or `onStop`, and a
short physical check kept the same PID and a healthy FastAPI server after Home
and eight seconds with the display dozing. That is opportunistic process
survival, not an Android lifecycle contract.

The actual product requirement is narrower than an always-on server:

- a user starts a potentially long model call;
- they minimize the app or turn off the display;
- the local FastAPI process needs roughly 60 seconds, with a safe ceiling of
  120 seconds, to finish;
- returning to the app must reveal the completed result or a recoverable error.

The current Suggestion Preloader does **not** poll periodically. It issues one
`POST /session/{id}/suggest` from the WebView and awaits it. Keeping Uvicorn
alive protects the server side of that request, but does not by itself make the
renderer-owned response durable if Android kills the WebView.

## Ownership constraint

The first delivery must stay inside `.ci-cd/android/`:

- Kotlin lifecycle/service code;
- Android manifest, notification channel and localized strings;
- Android build/test helpers.

Do not add Android branches to `src/`, the plugin SDK, FastAPI, Runner or plugin
contracts. Do not move Uvicorn into a second process unless the evidence proves
that promoting the existing process cannot satisfy the short lease.

The key low-invasion hypothesis is that a temporary Service in the **same
process** raises the importance of the whole process, including the existing
Chaquopy/Uvicorn thread. `MainActivity` can remain the runtime owner and the
existing plugin restart boundary can remain intact.

## Methods to compare

Build separate, clearly labelled APKs from a temporary Android lab. Test at
least these variants; do not select one from documentation alone.

### A — Current Activity-owned thread (control)

No lifecycle additions. Establish the device's actual baseline and the failure
rate under the same 90-second boundary.

### B — Finite ordinary started Service

Start a same-process, `START_NOT_STICKY` service while the Activity is still
eligible to do so. Stop it on resume, completion or a hard 120-second timeout.

This is the least visible option, but Android only documents a background grace
window of several minutes and remains free to stop or kill it. Passing on one
Motorola does not turn that behavior into a platform guarantee.

### C — Finite partial wake lock

Acquire a non-reference-counted partial wake lock for at most 120 seconds and
release it on resume/completion/timeout.

Treat this primarily as a control: a wake lock can keep CPU available but does
not raise process importance, make a renderer durable or bypass Doze network
restrictions. It must never be combined with another candidate during the A/B.

### D — Temporary foreground `shortService`

Start a same-process foreground service before the Activity loses foreground,
show a low-importance notification, and stop it on resume/completion or after
120 seconds. Implement the platform timeout callback where available and remain
below Android's approximately three-minute `shortService` limit.

Test lifecycle triggers rather than assuming one:

- `onPause`: reliably invoked while the Activity is still foreground-eligible,
  but also fires for temporary native surfaces;
- `onStop`: semantically narrower, but may cross the Android 12+ restriction on
  starting a foreground service from the background.

The service is a finite process-priority lease, not the owner of FastAPI. It is
not sticky, does not restart at boot and does not request exemption from battery
optimizations.

### E — Temporary regular foreground service fallback

Only test this if `shortService` cannot be represented cleanly across the
current min/compile/target SDK matrix. It must keep the same 120-second
self-imposed ceiling. Record the foreground-service type and its implications
for target SDK 34/35 instead of silently using an untyped service.

## Explicitly rejected for this requirement

- **WorkManager periodic work:** minimum interval is 15 minutes and execution
  remains inexact under Doze; it cannot provide a 60-second local-server lease.
- **Always-on foreground service:** unnecessary persistent notification and
  battery cost for a bounded call.
- **Battery-optimization exemption:** disproportionate before a finite
  foreground lease has been tested.
- **Separate `:backend` process:** adds restart, IPC and Chaquopy ownership
  complexity without first proving it is needed.
- **JavaScript timer tricks:** renderer scheduling is not an Android process
  guarantee.

## Physical experiment

Use the current Motorola XT2201-2 plus the Docker Android build. Each candidate
gets a distinct application ID, label and local port so all APKs can coexist
without sharing WebView storage or connecting to another variant's Uvicorn.
Copy the same private test data/theme into every package.

For each candidate, run three cold-process repetitions:

1. Boot the app and record package, APK SHA-256, PID, WebView version and
   `/version`.
2. Start a controlled 90-second FastAPI boundary representative of a long model
   call. Prefer the production request path against a deterministic delayed
   provider; any delay/probe scaffolding must remain in the ignored Android lab.
3. Within five seconds, press Home and turn the display off.
4. Do **not** poll `/health` during the 90-second interval: observation itself
   can keep a process active.
5. Wake the display, reopen the app and collect PID, bootstrap log, request
   result, debug log and Activity/service state.
6. Confirm plugin activation/restart still replaces the correct process and
   leaves no duplicate listener on port 8889.

Run one additional forced-idle probe for the winning candidate, clearly
separated from the 60-second product gate. It documents the Doze boundary; it
is not allowed to silently broaden the product requirement.

## Pre-registered decision rule

Choose the least invasive candidate that:

- completes the controlled request in **3/3** Home runs and **3/3** screen-off
  runs;
- keeps or cleanly restores one healthy Uvicorn owner with no port collision;
- returns to a usable WebView without losing sessions, plugins or the result;
- releases every Service, notification and wake lock by 120 seconds;
- is supported by Android's documented lifecycle contract, not merely by this
  device's observed process retention;
- changes no file outside `.ci-cd/android/`.

An ordinary Service or wake lock may be recorded as experimentally successful,
but cannot win if the Android contract still permits the process/network to be
suspended during the required window. If the temporary `shortService` passes,
prefer it over an always-on or separate-process design.

If every Android-only candidate keeps FastAPI alive but the suggestion result
is still lost with the renderer, stop this task with that boundary documented.
A separate task must then make the request/result durable in the backend; do not
smuggle a core job queue into this Android lifecycle task.

## Closure evidence required

- [x] labelled APK and source SHA for every tested method;
- [x] physical Home and display-off runs, including the unprotected baseline
      and the selected `shortService`;
- [x] no observer polling during the protected interval;
- [x] hard proof that all leases/resources end by 120 seconds;
- [x] cold boot, configuration, session and inherited plugin restart smoke
      boundaries;
- [x] physical `/health`, `/version`, PID and bootstrap evidence;
- [x] Android build green and canonical Python/frontend suites unchanged;
- [x] runtime implementation confined to `.ci-cd/android/`;
- [x] selected behavior documented in the Android lab README;
- [x] task moved to `.plan/closed/` only after the winning APK crossed the
      physical gate.

## Closure report

### Decision and scope

Candidate D was selected. `RuntimeLeaseService` is a same-process,
`START_NOT_STICKY` foreground service with manifest/runtime type
`shortService`, a silent low-importance notification, `onTimeout`, and an
app-owned 120-second stop. Uvicorn remains owned by the application process.
No WorkManager, wake lock, battery exemption, sticky restart or second backend
process was introduced.

The original synthetic 3-by-3 candidate matrix was superseded with the owner's
approval after the production DeepSeek flow exercised a stronger boundary:
five autonomous beats continued for about 192 seconds while the app was
minimized, another app was opened and the display was off. The product claim
remains deliberately narrower: the service protects only the first 120
seconds; survival after that was cached-process behavior and is not promised.
Untested candidates are not presented as experimental results.

### Physical evidence

Device: Motorola XT2201-2, Android 14 / API 34.

- The unprotected control retained the same PID and healthy FastAPI server
  after Home and an eight-second display-off interval. This established only
  opportunistic baseline survival.
- A short suggestion run completed after roughly ten seconds in the
  background.
- In the long production run, the service started at `21:41:05`, remained
  `isForeground=true`, `types=00000800` and `isShortFgs=true`, then logged its
  own 120-second ceiling at `21:43:05`.
- The real autonomous burst completed five beats and persisted 34 history
  records through revision 5. At `21:44:16` it stopped with
  `stop_reason="player_addressed"`, not budget exhaustion. All Director, prose
  and Character calls completed without recorded errors.
- After reopening, asynchronous suggestions completed successfully at
  `21:46:43` in 4.450 seconds. The brief loading state followed by the full
  transcript and later suggestion was the expected frontend refresh order.
- The process survived after the lease expired, but that approximately
  72-second tail is explicitly recorded as best-effort Android retention.
- There was no `/health` or ADB polling during the protected production
  interval.

The final regression APK is source commit `1de0fe4`, SHA-256
`c71bd60e684d289a6a4d511e63fdaa96239a010ff0eb3ba1b28fedb8417a035a`.
A cold launcher start reached `/health`, and `/version` returned the full
`1de0fe44f8035972c5fc422d8c7a018eac24e19c` commit. PID 7723 remained stable
through a final Home/launcher round-trip. `dumpsys` showed the same process as
the service owner, and logcat recorded, in order:

```text
runtime lease started for at most 120 seconds
runtime lease stop requested
runtime lease stopped
```

That final smoke also caught and fixed a cold-start race: stopping a just
requested foreground service with `stopService` could precede
`onStartCommand` and raise `ForegroundServiceDidNotStartInTimeException`.
Commit `1de0fe4` serializes the stop as a service command which first satisfies
`startForeground`; the repeated cold start and Home/resume boundary produced
no new crash.

### Validation

- Docker `assembleDebug` and `bundleDebug`: successful, 55 tasks.
- Android packaging regression: 9/9 passed.
- Full Python suite at the implementation baseline: 944 passed, 2 deselected.
- Ruff lint: passed. Mypy: passed for the canonical scope.
- `ruff format --check .` still reports 34 pre-existing, non-Android files;
  none was reformatted or included in this delivery.
- Runtime code is confined to `.ci-cd/android/`; the only external changes are
  the packaging regression test, ignored-build rules, lab helpers and plan
  documentation.

## References

- Android background execution limits:
  <https://developer.android.com/about/versions/oreo/background>
- Foreground service types and `shortService`:
  <https://developer.android.com/develop/background-work/services/fgs/service-types>
- Foreground service launch restrictions:
  <https://developer.android.com/develop/background-work/services/fgs/launch>
- Doze and App Standby:
  <https://developer.android.com/training/monitoring-device-state/doze-standby>
- WorkManager periodic interval:
  <https://developer.android.com/reference/androidx/work/PeriodicWorkRequest>
