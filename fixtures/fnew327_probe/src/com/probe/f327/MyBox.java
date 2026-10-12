package com.probe.f327;

import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;

/**
 * F-NEW-327 probe receiver: reads boxMax/boxMin through the 4-arg
 * obtainStyledAttributes(AttributeSet, styleable, defStyleAttr,
 * defStyleRes) — the value lives ONLY in the defStyleRes style
 * (F327_BoxStyle: 280dp/48dp), the Widget.Design.NavigationView
 * android:maxWidth shape. The AOSP AttributeResolution law answers the
 * STYLE stage (4) when the XML (1) and the theme (5) miss.
 */
public class MyBox extends android.view.View {
    public final int boxMax;
    public final int boxMin;

    public MyBox(Context c) {
        this(c, null, 0);
    }

    public MyBox(Context c, AttributeSet attrs, int defStyleAttr) {
        super(c, attrs, defStyleAttr);
        // The exact NavigationView ctor shape: defStyleRes = the style
        // resource, defValue = -1 (the AOSP NavigationView mMaxWidth law).
        TypedArray ta = c.obtainStyledAttributes(attrs,
                R.styleable.F327, defStyleAttr, R.style.F327_BoxStyle);
        boxMax = ta.getDimensionPixelSize(R.styleable.F327_boxMax, -1);
        boxMin = ta.getDimensionPixelSize(R.styleable.F327_boxMin, -1);
        ta.recycle();
    }
}
