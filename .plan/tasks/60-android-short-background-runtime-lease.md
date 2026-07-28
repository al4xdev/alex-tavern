# Task 60 — Android grants active FastAPI calls a short background lease

> **Status:** open. The preferred shape is deliberately small, but remains a
> hypothesis until the physical-device matrix below proves it.

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

- [ ] labelled APK and source SHA for every tested method;
- [ ] three-run matrix for Home and display-off, including negative results;
- [ ] no observer polling during the protected interval;
- [ ] hard proof that all leases/resources end by 120 seconds;
- [ ] cold boot, configuration, session and plugin restart smoke tests;
- [ ] physical `/health`, `/version`, PID and bootstrap evidence;
- [ ] Android build green and canonical Python/frontend suites unchanged;
- [ ] implementation confined to `.ci-cd/android/`;
- [ ] selected behavior documented in the Android lab README;
- [ ] task moved to `.plan/closed/` only after the winning APK crosses the
      physical gate.

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
