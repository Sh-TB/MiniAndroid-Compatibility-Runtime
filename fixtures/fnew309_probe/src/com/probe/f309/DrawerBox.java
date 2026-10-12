package com.probe.f309;

import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;

/**
 * F-NEW-309 probe container — the support-v4 DrawerLayout shape, renamed
 * or not: a DEX-defined ViewGroup whose LayoutParams is the AOSP inner
 * class family
 *   Container$LayoutParams extends MarginLayoutParams
 *   - own int field gravity
 *   - (Context, AttributeSet) ctor reads android:layout_gravity through
 *     Context.obtainStyledAttributes(attrs, { 0x010100F3 }).getInt(0, 0)
 *     (the exact const solitaire's R8-renamed DrawerLayout.a[0] carries).
 * The runtime's inflation must generate THIS LayoutParams from the XML
 * attrs (AOSP ViewGroup.generateLayoutParams law) so the container's own
 * drawer checks observe the real gravity.
 */
public class DrawerBox extends ViewGroup {

    /** The DrawerLayout_Layout styleable: { android:layout_gravity }. */
    static final int[] STYLEABLE = { 16842931 };  /* 0x010100F3 */

    public static class LayoutParams extends ViewGroup.MarginLayoutParams {
        public int gravity;

        public LayoutParams(Context c, AttributeSet attrs) {
            super(c, attrs);
            TypedArray a = c.obtainStyledAttributes(attrs, STYLEABLE);
            gravity = a.getInt(0, 0);
            a.recycle();
        }

        public LayoutParams(int width, int height) {
            super(width, height);
            gravity = 0;
        }
    }

    public DrawerBox(Context c, AttributeSet attrs) {
        super(c, attrs);
    }

    @Override
    protected LayoutParams generateDefaultLayoutParams() {
        return new LayoutParams(-2 /* WRAP_CONTENT */, -2);
    }

    @Override
    public ViewGroup.LayoutParams generateLayoutParams(AttributeSet attrs) {
        return new LayoutParams(getContext(), attrs);
    }

    @Override
    protected boolean checkLayoutParams(ViewGroup.LayoutParams p) {
        return p instanceof LayoutParams;
    }

    @Override
    protected void onMeasure(int wspec, int hspec) {
        setMeasuredDimension(getDefaultSize(getSuggestedMinimumWidth(), wspec),
                             getDefaultSize(getSuggestedMinimumHeight(), hspec));
    }

    @Override
    protected void onLayout(boolean changed, int l, int t, int r, int b) {
    }

    /** AOSP DrawerLayout g(View)/j(View) law: drawer gravity bit check. */
    public static boolean isDrawerView(View child) {
        ViewGroup.LayoutParams p = child.getLayoutParams();
        if (!(p instanceof LayoutParams)) return false;
        int g = ((LayoutParams) p).gravity;
        return (g & (Gravity.LEFT | Gravity.RIGHT | Gravity.START | Gravity.END)) != 0;
    }
}
