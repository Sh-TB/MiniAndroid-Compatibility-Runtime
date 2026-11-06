package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;

/** CODER7 WAVE-3: service with an intent-filter action — the
 *  resolveService / queryIntentServices resolution target. */
public class SvcFilter extends Service {
    @Override public IBinder onBind(Intent i) { return new Binder(); }
}
