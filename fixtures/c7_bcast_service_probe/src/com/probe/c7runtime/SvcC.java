package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 SVC: onUnbind TRUE law — onUnbind returns true → the instance
 *  stays (no onDestroy) and onRebind fires on the next bind; the RETAINED
 *  binder is re-delivered to the new connection (AOSP ActiveServices
 *  IntentBindRecord retention). */
public class SvcC extends Service {
    public static int binds = 0, rebinds = 0, unbinds = 0, destroys = 0;
    public static Object lastBinder = null;
    @Override public IBinder onBind(Intent i) {
        binds++;
        lastBinder = new Object();
        return (IBinder) lastBinder;
    }
    @Override public boolean onUnbind(Intent i) { unbinds++; return true; }
    @Override public void onRebind(Intent i) { rebinds++; }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
