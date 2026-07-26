package com.al4xdev.alextavern

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.view.WindowManager
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var statusView: android.widget.TextView
    private val mainHandler = Handler(Looper.getMainLooper())
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val callback = filePathCallback ?: return@registerForActivityResult
        filePathCallback = null
        callback.onReceiveValue(
            WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
        )
    }

    companion object {
        private const val SERVER_URL = "http://127.0.0.1:8889"
        private const val ASSET_URL = "file:///android_asset/index.html"
        private const val READY_POLL_INTERVAL_MS = 250L
        private const val READY_TIMEOUT_MS = 90_000L

        // The server lives in the process, not in the Activity. A recreated
        // Activity (rotation, theme change, returning from the background) must
        // not spawn a second uvicorn: the bind on 8889 would fail and kill it.
        private val serverStarted = AtomicBoolean(false)
    }

    private fun logBootstrap(message: String) {
        try {
            val logFile = File(filesDir, "bootstrap.log")
            val timestamp = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", java.util.Locale.getDefault()).format(java.util.Date())
            logFile.appendText("[$timestamp] $message\n")
            android.util.Log.d("TavernBootstrap", message)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enterImmersiveMode()
        setContentView(buildLayout())
        showStatus(getString(R.string.boot_starting))

        // Asset copying and the Chaquopy runtime extraction are both heavy disk
        // I/O — on a first boot they take seconds and would freeze the UI.
        Thread { bootServer() }.start()
        Thread { awaitServerAndLoad() }.start()
    }

    /** Loading screen up front; the WebView only replaces it once /health answers. */
    private fun buildLayout(): android.view.View {
        val container = android.widget.FrameLayout(this)

        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        // Only needed by the asset fallback below; inert on an http:// page,
        // where the frontend is same-origin with the API.
        webView.settings.allowFileAccess = true
        webView.settings.allowFileAccessFromFileURLs = true
        webView.settings.allowUniversalAccessFromFileURLs = true
        webView.addJavascriptInterface(AndroidBridge(), "AlexTavernAndroid")
        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                webView: WebView?,
                newCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                filePathCallback?.onReceiveValue(null)
                filePathCallback = newCallback
                val pickerIntent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "application/zip"
                }
                return try {
                    fileChooserLauncher.launch(pickerIntent)
                    true
                } catch (error: Exception) {
                    logBootstrap("file chooser ERROR: ${error.message}")
                    filePathCallback?.onReceiveValue(null)
                    filePathCallback = null
                    false
                }
            }
        }
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false
            }
        }
        webView.visibility = android.view.View.GONE
        container.addView(webView)

        statusView = android.widget.TextView(this).apply {
            setPadding(48, 48, 48, 48)
            textSize = 14f
            setTextIsSelectable(true)
            movementMethod = android.text.method.ScrollingMovementMethod()
        }
        container.addView(statusView)
        return container
    }

    private fun enterImmersiveMode() {
        window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            window.attributes = window.attributes.apply {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }
        WindowCompat.setDecorFitsSystemWindows(window, false)
        WindowInsetsControllerCompat(window, window.decorView).apply {
            hide(WindowInsetsCompat.Type.systemBars())
            systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) enterImmersiveMode()
    }

    /**
     * Restarts the process which owns Python and Uvicorn after plugin changes.
     *
     * Javascript interfaces are visible to every page loaded in this WebView,
     * so the call is accepted only from Alex Tavern's local frontend. The
     * separate relay process survives long enough to kill and relaunch us.
     */
    private inner class AndroidBridge {
        @JavascriptInterface
        fun restartApplication() {
            mainHandler.post {
                val currentUrl = webView.url.orEmpty()
                val trustedPage = currentUrl.startsWith("$SERVER_URL/") || currentUrl == ASSET_URL
                if (!trustedPage) {
                    logBootstrap("restartApplication: rejected untrusted page $currentUrl")
                    return@post
                }

                logBootstrap("restartApplication: handing off to restart relay")
                val restartIntent = Intent(this@MainActivity, RestartActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    putExtra(RestartActivity.EXTRA_MAIN_PID, android.os.Process.myPid())
                }
                startActivity(restartIntent)
            }
        }
    }

    private fun showStatus(message: String) {
        mainHandler.post {
            statusView.visibility = android.view.View.VISIBLE
            statusView.text = message
        }
    }

    private fun revealWebView(url: String) {
        logBootstrap("revealWebView: loading $url")
        mainHandler.post {
            statusView.visibility = android.view.View.GONE
            webView.visibility = android.view.View.VISIBLE
            webView.loadUrl(url)
        }
    }

    /**
     * Prefers the server-hosted frontend, which is same-origin with the API.
     *
     * Falls back to the copy in the APK assets when the server serves no
     * frontend — whether Chaquopy packages the non-.py files under src/static
     * is not something the build can assert, so this decides at runtime
     * instead of shipping a blank screen. api.js already points BASE_URL at
     * 127.0.0.1:8889 when the page protocol is file:.
     */
    private fun frontendUrl(): String {
        return if (httpStatus("$SERVER_URL/") == 200) {
            "$SERVER_URL/"
        } else {
            logBootstrap("frontendUrl: server has no frontend, falling back to APK assets")
            ASSET_URL
        }
    }

    /** Prepares the data dir and starts Python, at most once per process. */
    private fun bootServer() {
        if (!serverStarted.compareAndSet(false, true)) {
            logBootstrap("bootServer: server already started in this process, skipping.")
            return
        }
        try {
            val dataDir = File(filesDir, "data")
            logBootstrap("bootServer: dataDir is ${dataDir.absolutePath}")
            if (!dataDir.exists()) {
                logBootstrap("bootServer: dataDir did not exist. mkdirs() returned: ${dataDir.mkdirs()}")
            }

            // Copia recursivamente a estrutura de dados (roleplay_data) dos assets para o armazenamento do celular
            copyAssetsFolder("roleplay_data", dataDir)
            logBootstrap("bootServer: copyAssetsFolder complete.")

            if (!Python.isStarted()) {
                // applicationContext, not the Activity: the interpreter outlives
                // any single Activity instance and must not pin it in memory.
                Python.start(AndroidPlatform(applicationContext))
                logBootstrap("bootServer: Chaquopy started.")
            } else {
                logBootstrap("bootServer: Chaquopy was already running.")
            }

            val py = Python.getInstance()
            logBootstrap("bootServer: passing dataDir to android_runner.start_server...")
            py.getModule("android_runner").callAttr("start_server", dataDir.absolutePath)
            logBootstrap("bootServer: server exited.")
        } catch (e: Throwable) {
            // Chaquopy surfaces Python failures as PyException, a RuntimeException;
            // catching Throwable keeps errors during Python.start() visible too.
            logBootstrap("bootServer ERROR: ${e.message}\n${e.stackTraceToString()}")
        } finally {
            serverStarted.set(false)
        }
    }

    /** Polls /health so the frontend never loads against a socket that is not listening. */
    private fun awaitServerAndLoad() {
        val deadline = System.currentTimeMillis() + READY_TIMEOUT_MS
        while (System.currentTimeMillis() < deadline) {
            if (httpStatus("$SERVER_URL/health") == 200) {
                logBootstrap("awaitServer: /health answered, loading frontend.")
                revealWebView(frontendUrl())
                return
            }
            val waited = (READY_TIMEOUT_MS - (deadline - System.currentTimeMillis())) / 1000
            showStatus(getString(R.string.boot_starting_waiting, waited))
            try {
                Thread.sleep(READY_POLL_INTERVAL_MS)
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
                return
            }
        }
        logBootstrap("awaitServer: timed out after ${READY_TIMEOUT_MS}ms.")
        showStatus(getString(R.string.boot_failed))
    }

    /** Response code for a GET, or -1 when the request could not be made at all. */
    private fun httpStatus(url: String): Int {
        return try {
            val connection = URL(url).openConnection() as HttpURLConnection
            connection.connectTimeout = 1000
            connection.readTimeout = 1000
            connection.requestMethod = "GET"
            try {
                connection.responseCode
            } finally {
                connection.disconnect()
            }
        } catch (e: Exception) {
            -1
        }
    }

    private fun copyAssetsFolder(assetDirPath: String, targetDir: File, overwrite: Boolean = false) {
        try {
            val assetsList = assets.list(assetDirPath)
            if (assetsList == null) {
                logBootstrap("copyAssetsFolder: assets.list('$assetDirPath') returned null")
                return
            }

            if (assetsList.isEmpty()) {
                val relativePath = assetDirPath.removePrefix("roleplay_data/").removePrefix("roleplay_data")
                if (relativePath.isEmpty()) {
                    logBootstrap("copyAssetsFolder: relativePath is empty for '$assetDirPath'")
                    return
                }
                val targetFile = File(targetDir, relativePath)
                if (targetFile.exists() && !overwrite) {
                    // Preserve the configuration the user already changed on the device.
                    return
                }
                targetFile.parentFile?.mkdirs()
                assets.open(assetDirPath).use { input ->
                    targetFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                logBootstrap("copyAssetsFolder: copied '${targetFile.absolutePath}'")
            } else {
                for (asset in assetsList) {
                    val subAssetPath = if (assetDirPath.isEmpty()) asset else "$assetDirPath/$asset"
                    copyAssetsFolder(subAssetPath, targetDir, overwrite)
                }
            }
        } catch (e: Exception) {
            logBootstrap("copyAssetsFolder ERROR for '$assetDirPath': ${e.message}\n${e.stackTraceToString()}")
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
