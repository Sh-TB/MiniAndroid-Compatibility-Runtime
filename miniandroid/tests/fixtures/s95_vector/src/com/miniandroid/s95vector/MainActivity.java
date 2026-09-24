package com.miniandroid.s95vector;

import android.app.Activity;
import android.os.Bundle;

/**
 * S95 Wave-A fixture (F-S95-VEC-1): real aapt2-built APK whose drawables
 * exercise the L-S95-VECTOR-1 law (binary-AXML VectorDrawable rasterization):
 *   1. iv_tri   — anydpi-v21 vector vs mdpi/hdpi PNG differential oracle.
 *   2. iv_curve — cubic bezier pathData flattening.
 *   3. iv_rot   — group rotation transform.
 * The views are declared in XML only; no fixture-specific runtime code —
 * the same evidence law as G06 (the DEX carries no hidden behavior).
 */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}
