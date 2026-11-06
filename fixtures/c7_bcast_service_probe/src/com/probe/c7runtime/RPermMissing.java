package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7: receiver-permission law — the sender does NOT hold
 *  com.probe.c7runtime.MISSING → NO delivery (denied, loud trace). */
public class RPermMissing extends BroadcastReceiver {
    public static boolean delivered = false;
    @Override public void onReceive(Context context, Intent intent) {
        delivered = true;
    }
}
