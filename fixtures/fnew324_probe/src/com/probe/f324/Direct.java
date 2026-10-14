package com.probe.f324;

import android.content.Context;
import android.widget.LinearLayout;

/**
 * The control shape: a DEX class extending a FRAMEWORK class directly —
 * the R-NEW-345 case (declaring class IS the framework class) that must
 * keep working unchanged.
 */
public class Direct extends LinearLayout {
    public Direct(Context c) {
        super(c);
    }

    @Override
    protected void onMeasure(int wspec, int hspec) {
        super.onMeasure(wspec, hspec);
    }
}
