package c7.w12;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 WAVE-12 — the TYPED foreground service (manifest
 *  foregroundServiceType="dataSync|location" → bitmask 9). The FGS-type
 *  laws land here:
 *   W03: 3-arg startForeground with the manifest SUBSET (9 ⊆ 9) —
 *        dispatched, the FGS start-foreground contract satisfied;
 *   W04: 3-arg startForeground with an UNDECLARED type (CAMERA=64 ⊄ 9)
 *        — the AOSP subset law throws IllegalArgumentException;
 *   W05: stopForeground(STOP_FOREGROUND_REMOVE) +
 *        stopForeground(STOP_FOREGROUND_DETACH) — both dispatch.
 *  Each op try/catch'd: a missing engine API is an honest FAIL row. */
public class W12Service extends Service {
    @Override public void onCreate() { super.onCreate(); }

    @Override public int onStartCommand(Intent intent, int flags,
                                        int startId) {
        try {
            startForeground(41, new android.app.Notification(),
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
                | android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
            Rec.ok("W03", "3arg type=9 (dataSync|location) subset dispatched");
        } catch (Throwable t) {
            Rec.bad("W03", "throw:" + t.getClass().getName());
        }
        try {
            startForeground(41, new android.app.Notification(),
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);
            Rec.bad("W04", "no-throw (subset law missing)");
        } catch (IllegalArgumentException ie) {
            Rec.ok("W04", "subset violation threw "
                + ie.getClass().getSimpleName());
        } catch (Throwable t) {
            Rec.bad("W04", "throw:" + t.getClass().getName());
        }
        try {
            stopForeground(Service.STOP_FOREGROUND_REMOVE);
            stopForeground(Service.STOP_FOREGROUND_DETACH);
            Rec.ok("W05", "stopForeground REMOVE+DETACH dispatched");
        } catch (Throwable t) {
            Rec.bad("W05", "throw:" + t.getClass().getName());
        }
        Rec.flush(this, "c7w12_results.jsonl");
        return Service.START_STICKY;
    }

    @Override public IBinder onBind(Intent intent) {
        return new android.os.Binder();
    }
}
