package com.al4xdev.alextavern

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Process
import android.util.Log

/**
 * Relaunch relay hosted in a dedicated process.
 *
 * MainActivity owns Chaquopy and Uvicorn, so recreating only the Activity
 * leaves the old plugin runtime alive. This process kills that owner and then
 * starts a clean application process which boots the newly selected plugins.
 */
class RestartActivity : Activity() {

    companion object {
        const val EXTRA_MAIN_PID = "com.al4xdev.alextavern.extra.MAIN_PID"
        private const val RELAUNCH_DELAY_MS = 350L
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val mainPid = intent.getIntExtra(EXTRA_MAIN_PID, -1)
        if (mainPid > 0 && mainPid != Process.myPid()) {
            Log.d("TavernBootstrap", "restart relay: stopping main process $mainPid")
            Process.killProcess(mainPid)
        }

        Handler(Looper.getMainLooper()).postDelayed({
            val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
            if (launchIntent != null) {
                Log.d("TavernBootstrap", "restart relay: launching clean application process")
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
                startActivity(launchIntent)
            } else {
                Log.e("TavernBootstrap", "restart relay: launcher intent not found")
            }
            finishAndRemoveTask()
        }, RELAUNCH_DELAY_MS)
    }
}
