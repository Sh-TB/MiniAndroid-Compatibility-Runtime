package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-3: android:enabled="false" manifest receiver — invisible to
 *  every dispatch (AOSP disabled-components law). */
public class DisRecv extends BroadcastReceiver {
    public static int deliveries = 0;
    @Override public void onReceive(Context c, Intent i) { deliveries++; }
}
