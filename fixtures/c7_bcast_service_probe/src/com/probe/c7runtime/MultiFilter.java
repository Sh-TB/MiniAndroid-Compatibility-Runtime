package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-2 per-filter law: TWO filters over the SAME action MF at
 *  priorities 60 and 15 — AOSP resolves per (receiver, filter) pair, so
 *  this receiver is delivered TWICE per MF broadcast (once per matching
 *  filter), interleaved at its own filter priorities. Filter B also
 *  declares MFCAT + category MFCC. */
public class MultiFilter extends BroadcastReceiver {
    public static int deliveries = 0;
    @Override public void onReceive(Context context, Intent intent) {
        deliveries++;
        if (deliveries == 1) Order.append("MFA");
        else if (deliveries == 2) Order.append("MFB");
        else Order.append("MFC");
    }
}
