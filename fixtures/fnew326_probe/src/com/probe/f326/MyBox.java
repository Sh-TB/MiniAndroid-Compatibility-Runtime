package com.probe.f326;

import android.content.Context;
import android.view.ViewGroup;
import android.widget.LinearLayout;

/**
 * F-NEW-326 probe receiver — the subclass-owner face. javac binds the
 * unqualified getChildMeasureSpec call to owner = ViewGroup (the only
 * declarer on the compile classpath); the probe build script then
 * byte-patches that method_id's class_idx to MyBox — reproducing the
 * exact support-lib R8 artifact shape (solitaire: DrawerLayout m@5133 et
 * al. reference child-class-owned getChildMeasureSpec while NO DEX class
 * declares it; real devices resolve through the framework super chain to
 * ViewGroup.getChildMeasureSpec).
 */
public class MyBox extends LinearLayout {
    public MyBox(Context c) {
        super(c);
    }

    /** The R8-shape call site (owner patched to MyBox post-D8). */
    public int probeSpec(int spec, int pad, int dim) {
        return ViewGroup.getChildMeasureSpec(spec, pad, dim);
    }
}
