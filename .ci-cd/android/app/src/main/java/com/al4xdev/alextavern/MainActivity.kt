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

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val dataDir = File(filesDir, "data")
        if (!dataDir.exists()) {
            dataDir.mkdirs()
        }

        // Copia recursivamente a estrutura de dados (roleplay_data) dos assets para o armazenamento do celular
        copyAssetsFolder("roleplay_data", dataDir)

        // Inicializa o Chaquopy Runtime
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // Executa o Uvicorn FastAPI em background thread
        Thread {
            try {
                val py = Python.getInstance()
                
                // Define a variável de ambiente apontando para a pasta privada do Android
                val os = py.getModule("os")
                os.get("environ")?.put("ROLEPLAY_DATA_DIR", dataDir.absolutePath)
                
                // Executa o servidor FastAPI pelo Uvicorn usando o módulo auxiliar
                val runner = py.getModule("android_runner")
                runner.callAttr("start_server")
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()

        // WebView nativa para exibir o PWA local
        webView = WebView(this)
        setContentView(webView)

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

        // Carrega o frontend local empacotado nos assets do APK
        webView.loadUrl("file:///android_asset/index.html")
    }

    private fun copyAssetsFolder(assetDirPath: String, targetDir: File, overwrite: Boolean = false) {
        try {
            val assetsList = assets.list(assetDirPath) ?: return
            if (assetsList.isEmpty()) {
                val relativePath = assetDirPath.removePrefix("roleplay_data/").removePrefix("roleplay_data")
                if (relativePath.isEmpty()) return
                val targetFile = File(targetDir, relativePath)
                if (targetFile.exists() && !overwrite) {
                    return
                }
                targetFile.parentFile?.mkdirs()
                assets.open(assetDirPath).use { input ->
                    targetFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
            } else {
                for (asset in assetsList) {
                    val subAssetPath = if (assetDirPath.isEmpty()) asset else "$assetDirPath/$asset"
                    val shouldOverwrite = overwrite || subAssetPath.contains("/defaults/")
                    copyAssetsFolder(subAssetPath, targetDir, shouldOverwrite)
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
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
