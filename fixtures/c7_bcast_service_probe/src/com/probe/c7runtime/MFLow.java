package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 per-filter law: priority-5 witness after the second
 *  MultiFilter delivery. */
public class MFLow extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        Order.append("MFL");
    }
}
