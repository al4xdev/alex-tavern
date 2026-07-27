/* ══════════════════════════════════════════════════════════════════════
   android-bridge.js — the whole contract between the WebView and Kotlin.

   MainActivity exposes window.AlexTavernAndroid via addJavascriptInterface.
   Everything the native shell offers the page lives here, so the surface is
   one file instead of a lookup buried in a call site.
   ══════════════════════════════════════════════════════════════════════ */

function bridge() {
    return window.AlexTavernAndroid;
}

/** Whether the page is running inside the APK rather than a browser. */
export function isNativeShell() {
    return !!bridge();
}

/**
 * Ask the native shell to restart the whole app process.
 *
 * Activating or removing a plugin replaces the supervised Python process; on
 * Android there is no supervisor, so the Activity restarts instead.
 * Returns false in a browser, where the caller falls back to its own message.
 */
export function restartApplication() {
    const native = bridge();
    if (!native || typeof native.restartApplication !== 'function') return false;
    native.restartApplication();
    return true;
}
