package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 SVC: stopSelfResult(startId) law — ActiveServices
 *  stopServiceTokenLocked answers false when startId != lastStartId (the
 *  service is NOT stopped); true only for the LAST startId. The probe
 *  drives the calls from inside onStartCommand (AOSP: stopSelfResult is a
 *  Service API — callable on the service itself). */
public class SvcA extends Service {
    public static int creates = 0, starts = 0, destroys = 0;
    public static int lastStartId = -1;
    public static boolean lastStopAnswer = false;
    @Override public void onCreate() { super.onCreate(); creates++; }
    @Override public int onStartCommand(Intent i, int f, int startId) {
        starts++; lastStartId = startId;
        if (i != null && "com.probe.c7runtime.STOP_OLD".equals(i.getAction())) {
            lastStopAnswer = stopSelfResult(1);  // an OLD startId → false
        } else if (i != null
                && "com.probe.c7runtime.STOP_LAST".equals(i.getAction())) {
            lastStopAnswer = stopSelfResult(startId);  // LAST startId → true
        }
        return START_STICKY;
    }
    @Override public IBinder onBind(Intent i) { return null; }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
