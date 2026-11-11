package c7.w12;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** CODER7 WAVE-12 — the type-less service (NO manifest
 *  foregroundServiceType). The 3-arg startForeground MANIFEST-sentinel
 *  law (AOSP API-34 javadoc) throws
 *  MissingForegroundServiceTypeException on it (W06). */
public class PlainService extends Service {
    @Override public int onStartCommand(Intent intent, int flags,
                                        int startId) {
        try {
            startForeground(43, new android.app.Notification(),
                android.content.pm.ServiceInfo
                    .FOREGROUND_SERVICE_TYPE_MANIFEST);
            Rec.bad("W06", "no-throw (missing-type law missing)");
        } catch (Throwable t) {
            Rec.ok("W06", "MANIFEST sentinel no-type threw "
                + t.getClass().getSimpleName());
        }
        Rec.flush(this, "c7w12_results.jsonl");
        return Service.START_STICKY;
    }

    @Override public IBinder onBind(Intent intent) {
        return new android.os.Binder();
    }
}
