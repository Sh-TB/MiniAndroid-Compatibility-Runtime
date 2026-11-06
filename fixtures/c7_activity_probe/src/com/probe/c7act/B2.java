package com.probe.c7act;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** W3-A6: startActivities[1] — the second queued launch (FIFO); this is
 *  the task top that drives the next chain step. */
public class B2 extends Activity {
    public static int instances = 0;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
        Main.postTop(this);
    }
}
