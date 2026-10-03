package com.probe.gatea;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** GATE A probe receiver (#371 PHASE B5): manifest intent-filter delivery
 *  evidence for the sendBroadcast → onReceive dispatch law. */
public class GateReceiver extends BroadcastReceiver {
    public static int manifestDeliveries = 0;
    public static String lastManifestAction = "";
    public static String lastReceiverContext = "none";

    @Override public void onReceive(Context context, Intent intent) {
        manifestDeliveries++;
        lastManifestAction = intent != null ? intent.getAction() : null;
        lastReceiverContext = context != null ? "bound" : "null";
    }
}
