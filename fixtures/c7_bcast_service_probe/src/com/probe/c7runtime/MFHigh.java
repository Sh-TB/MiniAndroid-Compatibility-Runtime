package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 per-filter law: priority-30 witness between the two
 *  MultiFilter deliveries (MFA@60 &lt; MFH@30 &gt; MFB@15). */
public class MFHigh extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        Order.append("MFH");
    }
}
