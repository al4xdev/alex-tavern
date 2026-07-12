package com.al4xdev.alextavern

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

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
        
        val dataDir = File(filesDir, "data")
        logBootstrap("onCreate: Starting, dataDir is ${dataDir.absolutePath}")
        
        if (!dataDir.exists()) {
            val created = dataDir.mkdirs()
            logBootstrap("onCreate: dataDir did not exist. mkdirs() returned: $created")
        } else {
            logBootstrap("onCreate: dataDir already exists.")
        }

        // Copia recursivamente a estrutura de dados (roleplay_data) dos assets para o armazenamento do celular
        logBootstrap("onCreate: Invoking copyAssetsFolder for 'roleplay_data'...")
        copyAssetsFolder("roleplay_data", dataDir)
        logBootstrap("onCreate: copyAssetsFolder complete.")

        // Inicializa o Chaquopy Runtime
        logBootstrap("onCreate: Starting Chaquopy...")
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
            logBootstrap("onCreate: Chaquopy started.")
        } else {
            logBootstrap("onCreate: Chaquopy was already running.")
        }

        // Executa o Uvicorn FastAPI em background thread
        logBootstrap("onCreate: Spawning FastAPI server thread...")
        Thread {
            try {
                val py = Python.getInstance()
                
                // Define a variável de ambiente apontando para a pasta privada do Android
                val os = py.getModule("os")
                os.get("environ")?.put("ROLEPLAY_DATA_DIR", dataDir.absolutePath)
                logBootstrap("FastAPI Thread: Environment ROLEPLAY_DATA_DIR set to: ${dataDir.absolutePath}")
                
                // Executa o servidor FastAPI pelo Uvicorn usando o módulo auxiliar
                logBootstrap("FastAPI Thread: Loading android_runner.start_server...")
                val runner = py.getModule("android_runner")
                runner.callAttr("start_server")
                logBootstrap("FastAPI Thread: Server exited.")
            } catch (e: Exception) {
                logBootstrap("FastAPI Thread ERROR: ${e.message}\n${e.stackTraceToString()}")
                e.printStackTrace()
            }
        }.start()

        // WebView nativa para exibir o PWA local
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowFileAccessFromFileURLs = true
        webView.settings.allowUniversalAccessFromFileURLs = true

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false
            }
        }

        // Criar o container de layout e o botão de logs flutuante
        val container = android.widget.FrameLayout(this)
        container.addView(webView)

        val logButton = android.widget.Button(this).apply {
            text = "Ver Logs de Boot"
            val params = android.widget.FrameLayout.LayoutParams(
                android.widget.FrameLayout.LayoutParams.WRAP_CONTENT,
                android.widget.FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = android.view.Gravity.BOTTOM or android.view.Gravity.END
                setMargins(0, 0, 32, 100) // Margens para não sobrepor botões virtuais
            }
            layoutParams = params
            setOnClickListener {
                showLogsDialog()
            }
        }
        container.addView(logButton)
        setContentView(container)

        // Carrega o frontend local empacotado nos assets do APK
        logBootstrap("onCreate: Loading webview URL...")
        webView.loadUrl("file:///android_asset/index.html")
    }

    private fun copyAssetsFolder(assetDirPath: String, targetDir: File, overwrite: Boolean = false) {
        logBootstrap("copyAssetsFolder trace: path='$assetDirPath' overwrite=$overwrite")
        try {
            val assetsList = assets.list(assetDirPath)
            if (assetsList == null) {
                logBootstrap("copyAssetsFolder trace: assets.list('$assetDirPath') returned null")
                return
            }
            logBootstrap("copyAssetsFolder trace: assets.list('$assetDirPath') size=${assetsList.size}: [${assetsList.joinToString(", ")}]")
            
            if (assetsList.isEmpty()) {
                val relativePath = assetDirPath.removePrefix("roleplay_data/").removePrefix("roleplay_data")
                if (relativePath.isEmpty()) {
                    logBootstrap("copyAssetsFolder trace: relativePath is empty for '$assetDirPath'")
                    return
                }
                val targetFile = File(targetDir, relativePath)
                if (targetFile.exists() && !overwrite) {
                    logBootstrap("copyAssetsFolder trace: file '${targetFile.absolutePath}' exists and overwrite is false. Skipping.")
                    return
                }
                logBootstrap("copyAssetsFolder trace: Copying asset file '$assetDirPath' to '${targetFile.absolutePath}'...")
                targetFile.parentFile?.mkdirs()
                assets.open(assetDirPath).use { input ->
                    targetFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                logBootstrap("copyAssetsFolder trace: Successfully copied file '${targetFile.absolutePath}'")
            } else {
                for (asset in assetsList) {
                    val subAssetPath = if (assetDirPath.isEmpty()) asset else "$assetDirPath/$asset"
                    val shouldOverwrite = overwrite || subAssetPath.contains("/defaults/")
                    copyAssetsFolder(subAssetPath, targetDir, shouldOverwrite)
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
