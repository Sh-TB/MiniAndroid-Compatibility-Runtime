package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 exported law: android:exported="false" — a FOREIGN
 *  sender (modeled sender identity) must NOT reach this receiver; the
 *  same-package sender always may (AOSP same-uid law). */
public class ExpLocked extends BroadcastReceiver {
    public static boolean delivered = false;
    @Override public void onReceive(Context context, Intent intent) {
        delivered = true;
    }
}
