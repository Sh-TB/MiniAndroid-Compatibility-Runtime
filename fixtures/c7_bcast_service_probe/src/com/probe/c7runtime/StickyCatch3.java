package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 sticky law: re-cached sticky (after removal, a fresh
 *  send) — the fresh receiver gets the NEW value (last-write-wins). */
public class StickyCatch3 extends BroadcastReceiver {
    public static int caught = 0;
    public static String val = "";
    @Override public void onReceive(Context context, Intent intent) {
        caught++;
        val = intent.getStringExtra("v");
    }
}
