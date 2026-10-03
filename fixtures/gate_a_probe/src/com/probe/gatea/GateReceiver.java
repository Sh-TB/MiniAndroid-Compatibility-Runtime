package com.probe.gatea;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** GATE A probe receiver (issue #370 §12): manifest <receiver> component
 *  with a PING intent-filter action (inspection surface must list it). */
public class GateReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) { }
}
