package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;

/** CODER7 WAVE-2 sticky catch-up law: registered AFTER a sticky broadcast
 *  — must be delivered the cached sticky IMMEDIATELY with
 *  isInitialStickyBroadcast() == true. */
public class StickyCatch extends BroadcastReceiver {
    public static int caught = 0;
    public static boolean initial = false;
    public static String val = "";
    @Override public void onReceive(Context context, Intent intent) {
        caught++;
        initial = isInitialStickyBroadcast();
        val = intent.getStringExtra("v");
    }
}
