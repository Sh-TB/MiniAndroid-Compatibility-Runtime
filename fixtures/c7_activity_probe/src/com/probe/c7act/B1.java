package com.probe.c7act;

import android.app.Activity;
import android.os.Bundle;

/** W3-A6: startActivities[0] — the first queued launch. */
public class B1 extends Activity {
    public static int instances = 0;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
    }
}
