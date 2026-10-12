package com.probe.f324;

import android.content.Context;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

/**
 * F-NEW-324 probe shape — the EXACT NavigationView inheritance shape:
 * a DEX class whose super chain crosses a DEX INTERMEDIATE before the
 * framework boundary (NavigationView extends f [DEX, no onMeasure]
 * extends FrameLayout). The leaf's onMeasure super-dispatch must reach
 * the FrameLayout measure law THROUGH the DEX intermediate.
 */
public class Mid extends FrameLayout {
    public Mid(Context c) {
        super(c);
    }
    // no onMeasure — the ART super resolution continues PAST this class
}
