package com.probe.c449;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;

/**
 * CONT-112 probe: the framework style-routing + typed-value deref family,
 * minimized (fixture-first).
 *
 * jwtc chess 298 evidence (CONT-112):
 *  1. The Toolbar tag carries style=?attr/toolbarStyle; the theme resolved
 *     the attr to @style/Widget.Material3.Toolbar whose deref returned the
 *     style's first bag item (a color) — the style= walk silently missed and
 *     Toolbar.onMeasure's getSuggestedMinimumHeight() floor answered 0
 *     (Toolbar 1080x0 inside its 1080x168 ActionBarContainer).
 *  2. ActionBarOverlayLayout$LayoutParams.<init> read android:layout_height
 *     = ?attr/actionBarSize through the TypedArray; the reader passed the
 *     raw ATTRIBUTE word 0x7f040006 through and the Toolbar's LayoutParams
 *     height became 2130968582px.
 *
 * Rows (AOSP android.view semantics):
 *   C449-FLOOR-MIN     XML-inflated FloorView (app-DEX class, style=
 *                      parent-chain) seeds getMinimumHeight()==168
 *                      (android:minHeight=?attr/c449BarSize chain).
 *   C449-FLOOR-MEASURE the same view measures 1080x168 under an AT_MOST
 *                      spec — max(content, suggestedMinimum).
 *   C449-DEREF-REF     getLayoutDimension on a REFERENCE slot
 *                      (@dimen/c449_bar) answers 168, not the raw id.
 *   C449-DEREF-ATTR    getLayoutDimension on an ATTRIBUTE slot
 *                      (?attr/c449BarSize) answers 168, not the raw id.
 */
public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.main);

        FloorView fv = (FloorView) findViewById(R.id.floor);
        System.err.println("[C449-FLOOR-MIN] minH="
                + (fv != null ? fv.getMinimumHeight() : -999)
                + " expected=168 (style parent chain ?attr -> @dimen)");
        if (fv != null) {
            fv.measure(View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.EXACTLY),
                       View.MeasureSpec.makeMeasureSpec(1920, View.MeasureSpec.AT_MOST));
            System.err.println("[C449-FLOOR-MEASURE] measuredH=" + fv.lastMeasuredH
                    + " expected=168 (max(content, suggestedMinimum))");
        }
        DerefView dv = (DerefView) findViewById(R.id.deref);
        System.err.println("[C449-DEREF-REF] val="
                + (dv != null ? dv.derefRef : -999)
                + " expected=168 (REFERENCE @dimen deref)");
        System.err.println("[C449-DEREF-ATTR] val="
                + (dv != null ? dv.derefAttr : -999)
                + " expected=168 (ATTRIBUTE ?attr deref)");
    }
}
