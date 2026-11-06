package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;

/** CODER7 WAVE-2 registration-permission law: registered with the
 *  broadcastPermission com.probe.c7runtime.DYNPERM which the probe does
 *  NOT hold → every send to it is DENIED (loud BCAST-DENY, no delivery).
 *  DynNoPerm (registered WITHOUT a permission on the same action) is the
 *  control: delivered. */
public class DynPerm extends BroadcastReceiver {
    public static int deliveries = 0;
    @Override public void onReceive(Context context, Intent intent) {
        deliveries++;
    }
}
