package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 sticky catch-up: fresh receiver AFTER
 *  removeStickyBroadcast — must receive NOTHING. */
public class StickyCatch2 extends BroadcastReceiver {
    public static int caught = 0;
    @Override public void onReceive(Context context, Intent intent) {
        caught++;
    }
}
