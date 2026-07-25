package com.al4xdev.alextavern

import android.annotation.SuppressLint
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
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

        setContentView(buildLayout())
        showStatus("Iniciando servidor…")

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

        val logButton = android.widget.Button(this).apply {
            text = "Ver Logs de Boot"
            layoutParams = android.widget.FrameLayout.LayoutParams(
                android.widget.FrameLayout.LayoutParams.WRAP_CONTENT,
                android.widget.FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = android.view.Gravity.BOTTOM or android.view.Gravity.END
                setMargins(0, 0, 32, 100) // Margens para não sobrepor botões virtuais
            }
            setOnClickListener { showLogsDialog() }
        }
        container.addView(logButton)
        return container
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
            showStatus("Iniciando servidor… (${waited}s)\n\n${tailBootstrapLog()}")
            try {
                Thread.sleep(READY_POLL_INTERVAL_MS)
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
                return
            }
        }
        logBootstrap("awaitServer: timed out after ${READY_TIMEOUT_MS}ms.")
        showStatus(
            "O servidor não respondeu em ${READY_TIMEOUT_MS / 1000}s.\n\n" +
                "Log de boot:\n\n${tailBootstrapLog()}"
        )
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

    private fun tailBootstrapLog(lines: Int = 12): String {
        return try {
            val logFile = File(filesDir, "bootstrap.log")
            if (!logFile.exists()) return ""
            logFile.readLines().takeLast(lines).joinToString("\n")
        } catch (e: Exception) {
            ""
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
                    // Preserva a configuração que o usuário já alterou no aparelho.
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

    private fun showLogsDialog() {
        val logFile = File(filesDir, "bootstrap.log")
        val logs = if (logFile.exists()) logFile.readText() else "Nenhum log de inicialização encontrado."

        val textView = android.widget.TextView(this).apply {
            text = logs
            setPadding(40, 40, 40, 40)
            setTextIsSelectable(true)
            movementMethod = android.text.method.ScrollingMovementMethod()
            textSize = 12f
        }

        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Logs de Boot do App")
            .setView(textView)
            .setPositiveButton("Fechar", null)
            .setNeutralButton("Limpar") { _, _ ->
                try {
                    logFile.writeText("")
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            .setNegativeButton("Copiar") { _, _ ->
                try {
                    val clipboard = getSystemService(android.content.Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
                    val clip = android.content.ClipData.newPlainText("TavernLogs", logs)
                    clipboard.setPrimaryClip(clip)
                    android.widget.Toast.makeText(this, "Logs copiados!", android.widget.Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            .show()
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
