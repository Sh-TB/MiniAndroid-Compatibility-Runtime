package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-3: manifest receiver with a scheme data filter
 *  (&lt;data android:scheme="content"&gt;) — the IntentFilter.matchData
 *  data half. Delivers only intents whose data Uri carries that scheme. */
public class SchemeRecv extends BroadcastReceiver {
    public static int deliveries = 0;
    @Override public void onReceive(Context c, Intent i) { deliveries++; }
}
