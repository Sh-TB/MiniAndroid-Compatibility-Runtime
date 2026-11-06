package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 WAVE-3: manifest receiver with a MIME data filter
 *  (&lt;data android:mimeType="text/plain"&gt;) — the IntentFilter.matchData
 *  type half. Delivers only intents carrying a matching (or wildcard)
 *  MIME type. */
public class MimeRecv extends BroadcastReceiver {
    public static int deliveries = 0;
    @Override public void onReceive(Context c, Intent i) { deliveries++; }
}
