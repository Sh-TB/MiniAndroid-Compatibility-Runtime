package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;

/** CODER7 WAVE-2 registration-permission law: CONTROL receiver registered
 *  WITHOUT a broadcastPermission on the same action — delivered. */
public class DynNoPerm extends BroadcastReceiver {
    public static int deliveries = 0;
    @Override public void onReceive(Context context, Intent intent) {
        deliveries++;
    }
}
