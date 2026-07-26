"""Guarantees the backend needs to hold when it runs packaged inside the APK.

None of this is reachable from the desktop suite by accident: under Chaquopy
there is no repo root, no .git, and no meaningful working directory. Each check
here stands in for a failure that otherwise only shows up on a phone.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / ".ci-cd" / "android"


def test_static_mount_resolves_from_the_package_not_the_cwd() -> None:
    """A cwd-relative mount kills the import under Chaquopy, before any bind."""
    source = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    assert 'StaticFiles(directory="src/static"' not in source
    assert "StaticFiles(directory=STATIC_DIR" in source

    # Importing from an unrelated cwd is the actual regression guard.
    subprocess.run(
        [sys.executable, "-c", "import src.main; assert src.main.app"],
        cwd="/",
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin"},
    )


def test_build_commit_is_readable_without_a_git_directory(tmp_path: Path) -> None:
    """The APK ships no .git, so the CI stamp is the only way to identify a build."""
    package = tmp_path / "src"
    shutil.copytree(ROOT / "src", package, ignore=shutil.ignore_patterns("__pycache__"))
    (package / "version.txt").write_text("deadbeefcafe1234\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c", "from src.build_info import build_commit; print(build_commit())"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )

    assert result.stdout.strip() == "deadbeefcafe1234"


def test_ci_stamps_the_commit_into_the_packaged_sources() -> None:
    action = (ANDROID / "action.yml").read_text(encoding="utf-8")
    assert "src/version.txt" in action
    assert "github.sha" in action


def test_chaquopy_dependencies_stay_pure_python() -> None:
    """Native wheels have no Android build: Chaquopy cannot compile extensions."""
    gradle = (ANDROID / "app" / "build.gradle").read_text(encoding="utf-8")

    # pydantic 2 pulls pydantic-core (Rust); uvicorn[standard] pulls
    # uvloop/httptools/watchfiles. Both fail the APK build outright.
    assert 'install "pydantic<2"' in gradle
    assert "pydantic>=2" not in gradle
    assert "uvicorn[standard]" not in gradle


def test_android_passes_the_runtime_data_dir_into_python_before_import() -> None:
    """Chaquopy's PyObject.put does not mutate Python's os.environ mapping."""
    activity = (
        ANDROID
        / "app"
        / "src"
        / "main"
        / "java"
        / "com"
        / "al4xdev"
        / "alextavern"
        / "MainActivity.kt"
    ).read_text(encoding="utf-8")
    runner = (ANDROID / "app" / "src" / "main" / "python" / "android_runner.py").read_text(
        encoding="utf-8"
    )

    assert 'callAttr("start_server", dataDir.absolutePath)' in activity
    assert 'get("environ")?.put' not in activity

    configure_at = runner.index('os.environ["ROLEPLAY_DATA_DIR"] = data_dir')
    import_app_at = runner.index("import src.main")
    assert configure_at < import_app_at


def test_android_identity_matches_the_pwa() -> None:
    app = ANDROID / "app"
    manifest = (app / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    strings = (app / "src" / "main" / "res" / "values" / "strings.xml").read_text(encoding="utf-8")
    gradle = (app / "build.gradle").read_text(encoding="utf-8")

    assert 'android:label="@string/app_name"' in manifest
    assert 'android:icon="@mipmap/ic_launcher"' in manifest
    assert '<string name="app_name">Alex Tavern</string>' in strings
    assert 'versionName "0.1"' in gradle
    assert (app / "src" / "main" / "res" / "mipmap-nodpi" / "ic_launcher.png").read_bytes() == (
        ROOT / "src" / "static" / "icon-512.png"
    ).read_bytes()
    assert (
        app / "src" / "main" / "res" / "drawable-nodpi" / "ic_launcher_foreground.png"
    ).read_bytes() == (ROOT / "src" / "static" / "icon-maskable-512.png").read_bytes()


def test_android_restarts_the_python_process_after_plugin_changes() -> None:
    app = ANDROID / "app"
    java = app / "src" / "main" / "java" / "com" / "al4xdev" / "alextavern"
    manifest = (app / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    main_activity = (java / "MainActivity.kt").read_text(encoding="utf-8")
    restart_activity = (java / "RestartActivity.kt").read_text(encoding="utf-8")

    assert 'addJavascriptInterface(AndroidBridge(), "AlexTavernAndroid")' in main_activity
    assert 'currentUrl.startsWith("$SERVER_URL/") || currentUrl == ASSET_URL' in main_activity
    assert "putExtra(RestartActivity.EXTRA_MAIN_PID, android.os.Process.myPid())" in main_activity
    assert 'android:name=".RestartActivity"' in manifest
    assert 'android:exported="false"' in manifest
    assert 'android:process=":restart"' in manifest
    assert "Process.killProcess(mainPid)" in restart_activity
    assert "getLaunchIntentForPackage(packageName)" in restart_activity


def test_android_shell_supports_native_files_and_immersive_mode() -> None:
    activity = (
        ANDROID
        / "app"
        / "src"
        / "main"
        / "java"
        / "com"
        / "al4xdev"
        / "alextavern"
        / "MainActivity.kt"
    ).read_text(encoding="utf-8")

    assert "ActivityResultContracts.StartActivityForResult()" in activity
    assert "override fun onShowFileChooser(" in activity
    assert "WebChromeClient.FileChooserParams.parseResult" in activity
    assert "fileChooserLauncher.launch(pickerIntent)" in activity
    assert "window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)" in activity
    assert "LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES" in activity
    assert "hide(WindowInsetsCompat.Type.systemBars())" in activity
    assert "BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE" in activity
    assert "if (hasFocus) enterImmersiveMode()" in activity
    assert "Ver Logs de Boot" not in activity
    assert "showLogsDialog" not in activity
    assert "tailBootstrapLog" not in activity
    # The boot screen exists before the WebView does, so the frontend's i18n
    # cannot reach it: those strings are native resources, localized the native way.
    assert "showStatus(getString(R.string.boot_starting))" in activity
    strings = (ANDROID / "app/src/main/res/values/strings.xml").read_text(encoding="utf-8")
    localized = (ANDROID / "app/src/main/res/values-pt/strings.xml").read_text(encoding="utf-8")
    for key in ("boot_starting", "boot_starting_waiting", "boot_failed"):
        assert f'name="{key}"' in strings
        assert f'name="{key}"' in localized
