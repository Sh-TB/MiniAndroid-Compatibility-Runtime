package com.miniandroid.densitymatrix;

import android.app.Activity;
import android.os.Bundle;

/** G04 §4 density-matrix fixture: two wrap_content ImageViews —
 *  @drawable/icon_alias (reference chain into the density-bucketed icon)
 *  and @drawable/icon_nodpi (DENSITY_NONE). The rendered pixel geometry
 *  proves bucket selection + BitmapFactory scaling + FIT_CENTER. */
public class MainActivity extends Activity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}
