package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 ORDERED-BCAST: priority-20 manifest receiver — reads the result
 *  the previous receivers carried (AOSP result propagation) and records
 *  the verdict for the probe. */
public class RMid extends BroadcastReceiver {
    public static boolean chainSeen = false;
    public static String detail = "";
    @Override public void onReceive(Context context, Intent intent) {
        Order.append("Mid");
        int code = getResultCode();
        String data = getResultData();
        int k = getResultExtras(true).getInt("k", -1);
        chainSeen = (code == 2 && k == 7);
        detail = "code=" + code + " data=" + data + " k=" + k;
    }
}
