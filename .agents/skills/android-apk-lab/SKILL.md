---
name: android-apk-lab
description: Sets up Alex Tavern's reproducible Android environment, builds the Chaquopy/FastAPI APK in Docker, and validates install, boot, HTTP, plugins, WebView and process restart on a physical device over ADB. Use when creating or debugging Android builds, installing a local APK, investigating errors that only appear on the phone, testing plugin activation/installation, or preparing evidence before an Android commit.
---

# Android APK lab

Always work from the checkout root. Consult `.plan/tasks/` and `AGENTS.md`
before editing. Do not push. Do not uninstall the app without authorisation:
`adb install -r` preserves the data; `adb uninstall` wipes the whole private
directory.

The flow's two scripts live next to this skill, not in a root-level `scripts/`:

```fish
set lab .agents/skills/android-apk-lab/scripts
```

They find the repository root on their own, so they can be called from any
directory.

## Required flow

1. Confirm local changes and the device:

   ```fish
   git status -sb
   adb devices -l
   ```

2. Run proportional regressions before the build:

   ```fish
   uv run pytest -q tests/test_android_packaging.py tests/test_frontend_architecture.py tests/test_plugins.py tests/test_plugin_hub.py
   uvx ruff check .
   uvx ruff format --check .
   uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py tools/replay_llm.py tools/replay_session.py
   ```

3. Run `$lab/build-debug-apk.sh`. The first use downloads an isolated SDK into
   `.ci-cd/android/.local/` (Git-ignored); later uses reuse the SDK, Gradle and
   the same `debug.keystore`. The stable key is essential for installing with
   `-r`.

4. Run `$lab/adb-smoke.sh`. The script installs over the top, starts the app,
   sets up a local forward to the device's port 8889, checks `/health` and
   `/version`, and collects PID, package, active window, boot log and a
   screenshot. It accepts an APK path as its first argument; with no argument it
   uses the debug build just produced.

5. Exercise the changed boundary by hand. A static test is no substitute:

   - plugin install: tap `Choose file` and confirm the Android document picker
     opens;
   - activation/deactivation: close the store, record the previous PID and
     confirm the PID changes after the relaunch;
   - fullscreen: take an unlocked screenshot and confirm the status and
     navigation bars are absent;
   - persistence: query `/plugins` after the new process comes up.

6. Run `uv run pytest -x`, record the APK's SHA-256, and only then commit
   locally if there is explicit authorisation.

## Diagnosis over ADB

Use these commands in fish:

```fish
# Android backend reachable from the host
adb forward tcp:18889 tcp:8889
curl -fsS http://127.0.0.1:18889/health | jq .
curl -fsS http://127.0.0.1:18889/version | jq .
curl -fsS http://127.0.0.1:18889/plugins | jq .

# Boot and process evidence
adb shell pidof com.al4xdev.alextavern
adb logcat -d -s TavernBootstrap
adb shell run-as com.al4xdev.alextavern tail -80 files/bootstrap.log
adb shell dumpsys window | rg 'mCurrentFocus|alextavern'

# Visual evidence and native hierarchy
adb exec-out screencap -p > /tmp/alex-tavern-screen.png
adb shell uiautomator dump /sdcard/alex-tavern-ui.xml
adb pull /sdcard/alex-tavern-ui.xml /tmp/alex-tavern-ui.xml
```

`uiautomator` sees the document picker well, but may represent the WebView's
contents as a single node. In that case, use the screenshot, logcat and the HTTP
response as complementary evidence.

If the device is locked, `NotificationShade` will be the active window and a
screenshot may come out black. Wake the screen and ask the owner to unlock; do
not try to work around a PIN or biometrics.

## Known failures and what to decide

- `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: the keystore in use changed. Do not
  uninstall. Recover the key from
  `.ci-cd/android/.local/android-home/debug.keystore`, or the key that signed
  the installed APK.
- `Permission denied` when copying plugins into private storage does not imply a
  missing Android permission. ZIP/Git metadata can carry read-only modes; copy
  the contents into a fresh tree and let the process create the destinations.
- healthy server with HTTP 500: separate the Uvicorn boot from the endpoint
  failure; read `bootstrap.log`, the HTTP response and the Python traceback.
- persisted activation with no effect: reloading the WebView does not restart
  Chaquopy. Confirm the bridge calls `RestartActivity` in the `:restart`
  process and that the main PID was replaced.
- `adb` with no access to the daemon/socket: run outside the sandbox or request
  the appropriate ADB authorisation; do not start polling loops.

## Contracts the APK must preserve

- backend and frontend come from the canonical source; do not create an Android
  copy of the runtime;
- `ROLEPLAY_DATA_DIR` must be set before importing `src.main`;
- data lives in `files/data`, not in external storage;
- the JavaScript bridge accepts a restart only from the trusted local frontend;
- `RestartActivity` stays unexported and in a separate process;
- Chaquopy dependencies stay pure Python (`pydantic<2`, Uvicorn without extras);
- the build records the commit in `src/version.txt`, which stays Git-ignored.
