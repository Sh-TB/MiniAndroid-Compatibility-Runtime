package com.probe.c7act;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** W3-A2: launched from a SERVICE context — legal ONLY because the intent
 *  carries FLAG_ACTIVITY_NEW_TASK (the AOSP non-Activity-context law). */
public class NewTaskAct extends Activity {
    public static int instances = 0;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        instances++;
        Main.postMulti(this);
    }
}
