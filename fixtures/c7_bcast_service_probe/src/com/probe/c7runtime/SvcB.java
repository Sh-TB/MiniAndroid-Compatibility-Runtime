package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 SVC: onUnbind DEFAULT law — default onUnbind returns false →
 *  the purely-bound service is destroyed when the last binding goes. */
public class SvcB extends Service {
    public static int binds = 0, unbinds = 0, destroys = 0;
    @Override public IBinder onBind(Intent i) { binds++; return null; }
    @Override public boolean onUnbind(Intent i) { unbinds++; return false; }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
