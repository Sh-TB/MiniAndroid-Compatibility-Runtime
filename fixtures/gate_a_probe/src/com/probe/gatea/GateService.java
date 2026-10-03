package com.probe.gatea;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** GATE A probe service (#371 PHASE B5): lifecycle dispatch evidence —
 *  onCreate → onStartCommand per ActiveServices law, onDestroy on
 *  stopService/stopSelf. Static state is read back by the probe ops. */
public class GateService extends Service {
    public static int creates = 0;
    public static int startCommands = 0;
    public static int destroys = 0;
    public static String lastStartAction = "";
    public static int lastStartId = -1;
    public static Object lastBoundBinder = null;

    @Override public void onCreate() { super.onCreate(); creates++; }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        startCommands++;
        lastStartAction = intent != null ? intent.getAction() : null;
        lastStartId = startId;
        return START_STICKY;
    }
    @Override public IBinder onBind(Intent intent) {
        Object b = new Object();
        lastBoundBinder = b;
        return (IBinder) b;
    }
    @Override public void onDestroy() { super.onDestroy(); destroys++; }
}
