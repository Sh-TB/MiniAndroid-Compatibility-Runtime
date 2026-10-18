package com.probe.c102a;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Manifest-registered receiver — AOSP LoadedApk instantiates per delivery. */
public class ManifestRx extends BroadcastReceiver {
    public static int fired = 0;
    public static String lastAction = null;
    public static String lastExtra = null;

    @Override
    public void onReceive(Context context, Intent intent) {
        fired++;
        lastAction = intent == null ? null : intent.getAction();
        lastExtra = intent == null ? null : intent.getStringExtra("k");
        System.err.println("[C102-MRX] fired=" + fired
                + " action=" + lastAction + " k=" + lastExtra);
    }
}
