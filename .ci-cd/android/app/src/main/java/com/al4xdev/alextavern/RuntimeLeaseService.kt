package com.al4xdev.alextavern

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat

/**
 * A finite process-priority lease for an in-flight local backend request.
 *
 * Uvicorn remains owned by the application process. This same-process service
 * only tells Android that the process is completing short, user-visible work
 * after the Activity is no longer visible.
 */
class RuntimeLeaseService : Service() {

    companion object {
        private const val TAG = "TavernRuntimeLease"
        private const val CHANNEL_ID = "runtime_lease"
        private const val NOTIFICATION_ID = 51
        private const val MAX_LEASE_MS = 120_000L

        fun start(context: Context) {
            val intent = Intent(context, RuntimeLeaseService::class.java)
            ContextCompat.startForegroundService(context, intent)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, RuntimeLeaseService::class.java))
        }
    }

    private val handler = Handler(Looper.getMainLooper())
    private val expireLease = Runnable {
        Log.i(TAG, "runtime lease reached its 120-second ceiling")
        stopSelf()
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val foregroundType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            ServiceInfo.FOREGROUND_SERVICE_TYPE_SHORT_SERVICE
        } else {
            0
        }
        ServiceCompat.startForeground(
            this,
            NOTIFICATION_ID,
            buildNotification(),
            foregroundType,
        )
        handler.removeCallbacks(expireLease)
        handler.postDelayed(expireLease, MAX_LEASE_MS)
        Log.i(TAG, "runtime lease started for at most 120 seconds")
        return START_NOT_STICKY
    }

    /**
     * Android 14 calls this shortly before enforcing the shortService timeout.
     * The app's own 120-second ceiling should always stop us first.
     */
    override fun onTimeout(startId: Int) {
        Log.w(TAG, "Android shortService timeout received")
        stopSelf(startId)
    }

    override fun onDestroy() {
        handler.removeCallbacks(expireLease)
        ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
        Log.i(TAG, "runtime lease stopped")
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.runtime_lease_channel),
            NotificationManager.IMPORTANCE_LOW,
        ).apply {
            description = getString(R.string.runtime_lease_channel_description)
            setShowBadge(false)
        }
        manager.createNotificationChannel(channel)
    }

    private fun buildNotification(): android.app.Notification {
        val openApp = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
        val contentIntent = PendingIntent.getActivity(
            this,
            0,
            openApp,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_runtime_lease)
            .setContentTitle(getString(R.string.runtime_lease_title))
            .setContentText(getString(R.string.runtime_lease_message))
            .setContentIntent(contentIntent)
            .setCategory(NotificationCompat.CATEGORY_PROGRESS)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .build()
    }
}
