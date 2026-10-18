package com.probe.c102a;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/**
 * CONT-98 T4 — started-service lifecycle order recorder.
 * AOSP ActiveServices law:
 *   first startService  -> onCreate + onStartCommand(intent,flags,startId=1)
 *   second startService -> onStartCommand(startId=2) ONLY (no onCreate)
 *   stopService/stopSelf -> onDestroy
 */
public class Svc extends Service {
    public static StringBuilder log = new StringBuilder();
    public static int lastStartId = 0;
    public static boolean destroyed = false;

    @Override
    public void onCreate() {
        log.append("onCreate;");
        System.err.println("[C102-SVC] onCreate");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        lastStartId = startId;
        log.append("onStartCommand:").append(startId).append(";");
        System.err.println("[C102-SVC] onStartCommand startId=" + startId);
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        destroyed = true;
        log.append("onDestroy;");
        System.err.println("[C102-SVC] onDestroy");
    }

    @Override
    public IBinder onBind(Intent intent) {
        log.append("onBind;");
        System.err.println("[C102-SVC] onBind");
        return null;
    }
}
