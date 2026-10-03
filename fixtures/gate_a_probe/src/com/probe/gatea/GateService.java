package com.probe.gatea;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** GATE A probe service (issue #370 §12): manifest <service> component.
 *  Never started by the probe — its existence is what the manifest
 *  inspection surface must prove. */
public class GateService extends Service {
    @Override public IBinder onBind(Intent intent) { return null; }
}
