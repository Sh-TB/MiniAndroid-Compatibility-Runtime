package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 WAVE-3: stopSelf(int) obeys the SAME getLastStartId guard as
 *  stopSelfResult (AOSP Service.stopSelf(int) → ActiveServices
 *  stopServiceTokenLocked). onStartCommand drives the calls: startId 2
 *  calls stopSelf(1) — STALE, the service must stay; startId 3 calls
 *  stopSelf(3) — LAST, the service dies. */
public class SvcH extends Service {
    public static int destroys = 0;
    public static boolean staleGuardWorked = false;
    @Override public int onStartCommand(Intent i, int f, int startId) {
        if (startId == 2) {
            stopSelf(1);  // stale → no stop
            if (destroys == 0) staleGuardWorked = true;
        } else if (startId >= 3) {
            stopSelf(startId);  // last → destroy
        }
        return START_NOT_STICKY;
    }
    @Override public IBinder onBind(Intent i) { return null; }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
