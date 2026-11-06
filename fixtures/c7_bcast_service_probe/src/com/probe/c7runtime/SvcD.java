package com.probe.c7runtime;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 SVC: unbind targeting — stays alive when only SvcE unbinds. */
public class SvcD extends Service {
    public static int destroys = 0;
    @Override public IBinder onBind(Intent i) { return null; }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
