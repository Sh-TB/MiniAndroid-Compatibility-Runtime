package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 WAVE-2 bring-down law: a STARTED service with a LIVE binding is
 *  torn down by stopService — AOSP ActiveServices bringDownServiceLocked
 *  delivers onUnbind(bindingIntent) BEFORE onDestroy. The wave-1/wave-2
 *  probe asserts unbinds==1 AND destroys==1; the SVC-UNBIND/SVC-STOP
 *  FileIoTrace rows prove the ORDER. */
public class SvcF extends Service {
    public static int creates = 0, binds = 0, unbinds = 0, destroys = 0;
    @Override public void onCreate() { super.onCreate(); creates++; }
    @Override public IBinder onBind(Intent i) { binds++; return null; }
    @Override public boolean onUnbind(Intent i) { unbinds++; return false; }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
