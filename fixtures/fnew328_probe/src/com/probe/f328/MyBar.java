package com.probe.f328;

import android.content.Context;
import android.widget.LinearLayout;

/**
 * The vertical DEX subclass (the AppBarLayout shape): a REAL onMeasure
 * override that delegates to super and REPORTS what the super pass
 * produced — the probe reads the super's answers from DEX.
 */
public class MyBar extends LinearLayout {
    public int selfW = -1, selfH = -1, childW = -1, childH = -1;

    public MyBar(Context c) { super(c); }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
        // AOSP AppBarLayout.onMeasure reads exactly these after super.
        selfW = getMeasuredWidth();
        selfH = getMeasuredHeight();
        if (getChildCount() > 0) {
            childW = getChildAt(0).getMeasuredWidth();
            childH = getChildAt(0).getMeasuredHeight();
        }
        // keep the super's answer (pure probe — no reshaping)
        setMeasuredDimension(selfW, selfH);
    }
}
