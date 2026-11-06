package com.probe.c7act;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** W3-A2: the service-side startActivity caller. Action NEWTASK_OK
 *  launches WITH FLAG_ACTIVITY_NEW_TASK (AOSP-legal); action NEWTASK_BAD
 *  launches WITHOUT the flag (must throw AndroidRuntimeException — the
 *  exception propagates synchronously into the caller's startService). */
public class SvcNT extends Service {
    public static String lastError = "";
    @Override public IBinder onBind(Intent i) { return null; }
    @Override public int onStartCommand(Intent intent, int flags, int id) {
        String act = intent != null ? intent.getAction() : "";
        if ("NEWTASK_BAD".equals(act)) {
            try {
                startActivity(new Intent(this, NewTaskAct.class));
                lastError = "NO-THROW";
            } catch (Throwable t) {
                lastError = t.getClass().getSimpleName()
                        .concat(":").concat(String.valueOf(t.getMessage()));
            }
        } else if ("NEWTASK_OK".equals(act)) {
            Intent i = new Intent(this, NewTaskAct.class);
            i.addFlags(0x10000000);  // FLAG_ACTIVITY_NEW_TASK
            try {
                startActivity(i);
                lastError = "LAUNCHED";
            } catch (Throwable t) {
                lastError = "THREW:" + t.getClass().getSimpleName();
            }
        }
        return START_NOT_STICKY;
    }
}
