package com.probe.c7act;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** W3-A3: launchMode="singleTop" — a re-launch of the TOP instance must
 *  route through onNewIntent (no new instance, no lifecycle restart). */
public class STTop extends Activity {
    public static int instances = 0;
    public static int newIntents = 0;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
        Main.postTopRelaunch(this);
    }
    @Override protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        newIntents++;
        Main.postCtChain(this);
    }
}
