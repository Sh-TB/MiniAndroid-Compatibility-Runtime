package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 exported law: exported="true" + android:permission —
 *  a foreign sender must additionally HOLD the permission. */
public class ExpOpen extends BroadcastReceiver {
    public static boolean delivered = false;
    @Override public void onReceive(Context context, Intent intent) {
        delivered = true;
    }
}
