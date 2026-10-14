package com.probe.f323;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

/**
 * F-NEW-323 probe shape — a DEX-defined ViewGroup subclass that exposes
 * the AOSP ViewGroup detach/attach family the RecyclerView ChildHelper
 * machinery drives through real DEX (solitaire ay$5.c / ay.a synthetic
 * accesses):
 *   detachViewFromParent(int)   — child leaves mChildren, mParent KEPT
 *   attachViewToParent(V,I,LP)  — child re-enters at index, mParent kept,
 *                                 mLayoutParams replaced (AOSP View.java
 *                                 child.mLayoutParams = params)
 *   removeDetachedView(V, Z)    — FULL removal (mParent cleared)
 */
public class Detacher extends LinearLayout {
    public Detacher(Context c) {
        super(c);
    }

    public void detachIdx(int i) {
        detachViewFromParent(i);
    }

    public void attachIdx(View v, int i, ViewGroup.LayoutParams lp) {
        attachViewToParent(v, i, lp);
    }

    public void removeDet(View v) {
        removeDetachedView(v, false);
    }
}
