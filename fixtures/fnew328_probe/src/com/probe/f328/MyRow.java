package com.probe.f328;

import android.content.Context;
import android.widget.LinearLayout;

/**
 * The horizontal DEX subclass (the Toolbar shape): same reporting law.
 */
public class MyRow extends LinearLayout {
    public int selfW = -1, selfH = -1, childW = -1, childH = -1;

    public MyRow(Context c) { super(c); }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
        selfW = getMeasuredWidth();
        selfH = getMeasuredHeight();
        if (getChildCount() > 0) {
            childW = getChildAt(0).getMeasuredWidth();
            childH = getChildAt(0).getMeasuredHeight();
        }
        setMeasuredDimension(selfW, selfH);
    }
}
