package com.probe.c7act;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** W3-A4: the FLAG_ACTIVITY_CLEAR_TOP target (standard mode — the target
 *  itself is destroyed and a FRESH instance launches). */
public class CTBase extends Activity {
    public static int instances = 0;
    public static boolean firstUp = false;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
        if (instances == 1) {
            firstUp = true;
            Main.postCtMid(this);
        } else {
            Main.postDisabledTry(this);
        }
    }
}
