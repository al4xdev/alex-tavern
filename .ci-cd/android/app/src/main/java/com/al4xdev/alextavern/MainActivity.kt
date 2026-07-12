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

        // Inicializa o Chaquopy Runtime
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // Tenta copiar o config.json personalizado empacotado nos assets (se houver)
        // para sobrescrever a LLM Host com o IP local do desenvolvedor no primeiro boot.
        setupLocalConfigJson(dataDir)

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

    private fun setupLocalConfigJson(dataDir: File) {
        val targetConfig = File(dataDir, "config.json")
        // Só copia se o arquivo não existir no celular (primeiro boot ou reinstalação)
        if (!targetConfig.exists()) {
            try {
                // O local do config.json no asset empacotado pela pipeline
                assets.open(".data/config.json").use { input ->
                    targetConfig.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                println("Config.json personalizado copiado com sucesso!")
            } catch (e: Exception) {
                println("Config.json personalizado não encontrado nos assets, o app inicializará com os padrões.")
            }
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
