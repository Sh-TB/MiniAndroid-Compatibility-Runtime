package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 ORDERED-BCAST: priority-30 aborter — abortBroadcast() must stop
 *  every lower-priority pending receiver of this ordered broadcast while
 *  the final resultReceiver still runs (AOSP abortBroadcast doc). */
public class RAbort extends BroadcastReceiver {
    public static boolean called = false;
    @Override public void onReceive(Context context, Intent intent) {
        called = true;
        Order.append("Abort");
        setResultData("aborted-here");
        abortBroadcast();
    }
}
