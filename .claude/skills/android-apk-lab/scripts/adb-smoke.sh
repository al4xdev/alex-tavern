#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../../.." && pwd)"
apk="${1:-$repo_root/.ci-cd/android/app/build/outputs/apk/debug/app-debug.apk}"
package="com.al4xdev.alextavern"
activity="$package/.MainActivity"
host_port="${ALEX_TAVERN_ADB_PORT:-18889}"

[[ -f "$apk" ]] || { printf 'APK not found: %s\n' "$apk" >&2; exit 1; }
device_count="$(adb devices | awk 'NR > 1 && $2 == "device" { count++ } END { print count + 0 }')"
[[ "$device_count" == "1" ]] || {
    printf 'Expected exactly one authorized device, found %s.\n' "$device_count" >&2
    adb devices -l
    exit 1
}

sha256sum "$apk"
adb install -r "$apk"
adb shell am force-stop "$package"
# Match a real launcher tap. Starting only by component creates a different
# root intent, so a later icon tap may stack a fresh MainActivity above the
# tested one and falsely resemble a process restart.
adb shell am start -W \
    -a android.intent.action.MAIN \
    -c android.intent.category.LAUNCHER \
    -n "$activity"
sleep 8
adb forward "tcp:$host_port" tcp:8889

curl -fsS "http://127.0.0.1:$host_port/health"
printf '\n'
curl -fsS "http://127.0.0.1:$host_port/version"
printf '\n'
adb shell pidof "$package"
adb shell dumpsys package "$package" | grep -E 'versionCode=|versionName=' | head -2
adb shell dumpsys window | grep -E 'mCurrentFocus|alextavern' | head -20
adb shell run-as "$package" tail -80 files/bootstrap.log || true
adb exec-out screencap -p > /tmp/alex-tavern-screen.png
printf 'Screenshot: /tmp/alex-tavern-screen.png\n'
