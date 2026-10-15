package com.probe.tsp;

import android.app.Activity;
import android.content.res.TypedArray;
import android.os.Bundle;

public class SecondActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        TypedArray ta = obtainStyledAttributes(R.styleable.TspTest);
        int inherited = ta.getColor(R.styleable.TspTest_tspInherited, 0);
        // F7 isolation: MainActivity applied TspOverlayOne/Two/Three and
        // TspDeepChain1 on ITS theme; this fresh activity (TspThemeB) must
        // see NONE of that state.
        boolean ov = ta.hasValue(R.styleable.TspTest_tspOverlayOnly);
        int deep = ta.getInt(R.styleable.TspTest_tspDeepAttr, -1);
        System.out.println("[TSPROBE] F7 second-tspInherited="
                + String.format("%08x", inherited)
                + " want=ffaabbcc (TspThemeB own chain)");
        System.out.println("[TSPROBE] F7b second-overlayOnly-present=" + ov
                + " want=false (no leakage from MainActivity applyStyle)");
        System.out.println("[TSPROBE] F7c second-deepAttr=" + deep
                + " want=-1 (no leakage from MainActivity TspDeepChain1 apply)");
        ta.recycle();
    }
}
