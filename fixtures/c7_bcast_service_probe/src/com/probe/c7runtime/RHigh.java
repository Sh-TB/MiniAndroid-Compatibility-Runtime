package com.probe.c7runtime;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** CODER7 ORDERED-BCAST: priority-50 manifest receiver — first in the
 *  ORDER chain. Asserts the AOSP seed (initial code == RESULT_OK == -1)
 *  and seeds the result for the next receiver. */
public class RHigh extends BroadcastReceiver {
    public static boolean sawInitialResultOk = false;
    @Override public void onReceive(Context context, Intent intent) {
        Order.append("High");
        sawInitialResultOk = (getResultCode() == -1);
        setResultCode(1);
        setResultData("r1");
    }
}
