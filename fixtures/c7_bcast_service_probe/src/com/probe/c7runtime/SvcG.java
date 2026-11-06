package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;

/** CODER7 WAVE-3: BIND_AUTO_CREATE gate law — a bind WITHOUT the flag to a
 *  not-running service must NOT create it (no onCreate/onBind/
 *  onServiceConnected); the connection connects when a startService brings
 *  the service up (AOSP ActiveServices queued-connection law). */
public class SvcG extends Service {
    public static int creates = 0, binds = 0, destroys = 0;
    @Override public void onCreate() { super.onCreate(); creates++; }
    @Override public IBinder onBind(Intent i) { binds++; return new Binder(); }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
