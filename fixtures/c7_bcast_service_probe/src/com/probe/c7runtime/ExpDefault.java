package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 exported law: NO android:exported attribute but the
 *  component HAS an intent-filter — the AOSP PackageParser default law:
 *  targetSdk &lt;= 30 defaults to EXPORTED. */
public class ExpDefault extends BroadcastReceiver {
    public static boolean delivered = false;
    @Override public void onReceive(Context context, Intent intent) {
        delivered = true;
    }
}
