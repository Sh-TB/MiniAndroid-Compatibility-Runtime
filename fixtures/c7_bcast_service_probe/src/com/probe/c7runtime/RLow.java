package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 ORDERED-BCAST: priority-10 manifest receiver — the LAST in the
 *  ORDER chain; on the ABORT action it must be SKIPPED (abort stops
 *  lower-priority pending receivers) unless the send was non-ordered
 *  (AOSP checkSynchronousHint: abort on a non-ordered broadcast is a
 *  log-only no-op, so delivery continues). */
public class RLow extends BroadcastReceiver {
    public static boolean called = false;
    @Override public void onReceive(Context context, Intent intent) {
        called = true;
        Order.append("Low");
    }
}
