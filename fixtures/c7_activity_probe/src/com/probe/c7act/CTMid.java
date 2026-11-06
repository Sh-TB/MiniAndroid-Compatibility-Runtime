package com.probe.c7act;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** W3-A4: the activity ABOVE the CLEAR_TOP target — must be finished by
 *  the clear-top law (onDestroy delivered). */
public class CTMid extends Activity {
    public static boolean destroyed = false;
    public static int instances = 0;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
        Main.postClearTop(this);
    }
    @Override protected void onDestroy() {
        super.onDestroy();
        destroyed = true;
    }
}
