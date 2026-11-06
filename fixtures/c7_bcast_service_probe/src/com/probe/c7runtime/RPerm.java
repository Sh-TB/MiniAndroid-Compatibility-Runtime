package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7: receiver-permission law — android:permission held by the
 *  sender (declared in uses-permission) → delivery allowed. */
public class RPerm extends BroadcastReceiver {
    public static boolean delivered = false;
    @Override public void onReceive(Context context, Intent intent) {
        delivered = true;
    }
}
