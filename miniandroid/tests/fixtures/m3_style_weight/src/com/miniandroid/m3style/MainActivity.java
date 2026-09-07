package com.miniandroid.m3style;

import android.app.Activity;
import android.os.Bundle;

/**
 * M3 style/weight law fixture (no interaction): the geometry law under test
 * is entirely in the XML+style resource layer — buttons whose layout_width/
 * height/weight/margin come ONLY from the style= bag and its parent chain,
 * plus a direct-attribute override (AOSP obtainStyledAttributes precedence)
 * and a match-parent row measured to the remaining height after a fixed
 * header (LinearLayout second-pass remeasure law).
 */
public class MainActivity extends Activity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}
