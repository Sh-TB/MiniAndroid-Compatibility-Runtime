package com.probe.f325;

import android.content.Context;
import android.widget.LinearLayout;

/**
 * F-NEW-325 probe shape — a DEX LayoutParams subclass that declares NO
 * fields of its own reading the FRAMEWORK-declared width/height through
 * a DEX ref class (the exact DrawerLayout$g -> width shape), PLUS a real
 * DEX-declared field whose qualified slot must keep working (the
 * F-NEW-160/F-NEW-321 faces).
 */
public class MyLP extends LinearLayout.LayoutParams {
    public String tag;  // a REAL DEX-declared field (the qualified face)

    public MyLP(int w, int h) {
        super(w, h);
    }
}
