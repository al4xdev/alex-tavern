#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../../.." && pwd)"
lab_root="${ALEX_TAVERN_ANDROID_LAB_ROOT:-$repo_root/.ci-cd/android/.local}"
sdk_root="$lab_root/sdk"
gradle_cache="$lab_root/gradle-cache"
android_home="$lab_root/android-home"
tools_zip="$lab_root/commandlinetools.zip"
tools_url="https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip"
tools_sha256="4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583"

mkdir -p "$lab_root" "$sdk_root" "$gradle_cache" "$android_home"

if [[ ! -x "$sdk_root/cmdline-tools/latest/bin/sdkmanager" ]]; then
    docker run --rm --user root \
        -v "$lab_root:/lab" \
        ubuntu:24.04 bash -lc "
            set -euo pipefail
            apt-get update -qq
            apt-get install -y -qq ca-certificates curl unzip
            curl -fsSL '$tools_url' -o /lab/commandlinetools.zip
            echo '$tools_sha256  /lab/commandlinetools.zip' | sha256sum -c -
            mkdir -p /lab/sdk/cmdline-tools/latest
            unzip -q /lab/commandlinetools.zip -d /lab/unpacked
            cp -a /lab/unpacked/cmdline-tools/. /lab/sdk/cmdline-tools/latest/
        "
fi

if [[ ! -x "$sdk_root/platform-tools/adb" ||
      ! -d "$sdk_root/platforms/android-33" ||
      ! -d "$sdk_root/build-tools/33.0.2" ]]; then
    docker run --rm --user root \
        -v "$sdk_root:/opt/android-sdk" \
        -e ANDROID_SDK_ROOT=/opt/android-sdk \
        gradle:8.0.2-jdk17 bash -lc "
            set -euo pipefail
            set +o pipefail
            yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses >/dev/null
            license_status=\${PIPESTATUS[1]}
            set -o pipefail
            test \"\$license_status\" -eq 0
            /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager \
                'platform-tools' 'platforms;android-33' 'build-tools;33.0.2'
        "
fi

git -C "$repo_root" rev-parse HEAD > "$repo_root/src/version.txt"
mkdir -p "$repo_root/.ci-cd/android/app/src/main/assets"
cp -a "$repo_root/src/static/." "$repo_root/.ci-cd/android/app/src/main/assets/"

docker run --rm --user root \
    -v "$repo_root:/workspace" \
    -v "$sdk_root:/opt/android-sdk" \
    -v "$gradle_cache:/home/gradle/.gradle" \
    -v "$android_home:/root/.android" \
    -e ANDROID_SDK_ROOT=/opt/android-sdk \
    -e GRADLE_USER_HOME=/home/gradle/.gradle \
    -w /workspace/.ci-cd/android \
    gradle:8.0.2-jdk17 bash -lc '
        set -euo pipefail
        apt-get update -qq
        apt-get install -y -qq python3-distutils
        gradle assembleDebug --no-daemon
        chown -R 1000:1000 /workspace/.ci-cd/android/app/build /root/.android
    '

apk="$repo_root/.ci-cd/android/app/build/outputs/apk/debug/app-debug.apk"
sha256sum "$apk"
printf 'APK: %s\n' "$apk"
