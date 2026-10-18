package com.probe.c103a;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

/** Declared <service> with one meta-data child (c103.svcmeta=hello). */
public class MyService extends Service {
    @Override public IBinder onBind(Intent intent) { return null; }
}
