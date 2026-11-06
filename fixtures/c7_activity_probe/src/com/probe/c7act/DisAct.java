package com.probe.c7act;

import android.app.Activity;
import android.os.Bundle;

/** W3-R04: android:enabled="false" activity — unresolvable; the launch
 *  attempt must NEVER instantiate it. */
public class DisAct extends Activity {
    public static int instances = 0;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
    }
}
