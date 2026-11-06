package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 WAVE-3: android:enabled="false" service — startService answers
 *  null ComponentName, bindService false (AOSP not-installed shape). */
public class DisSvc extends Service {
    public static int creates = 0;
    @Override public void onCreate() { super.onCreate(); creates++; }
    @Override public IBinder onBind(Intent i) { return null; }
}
