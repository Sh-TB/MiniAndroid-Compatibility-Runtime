package com.probe.c449;

import android.view.View;
import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;

/** The lp-deref disease surface: a ctor reading TypedArray dimensions. */
public class DerefView extends View {
    public int derefRef = -1;
    public int derefAttr = -1;
    public DerefView(Context c) { super(c); }
    public DerefView(Context c, AttributeSet a) {
        super(c, a);
        TypedArray ta = c.obtainStyledAttributes(a, R.styleable.C449);
        derefRef = ta.getLayoutDimension(R.styleable.C449_c449_deref_height, 0);
        derefAttr = ta.getLayoutDimension(R.styleable.C449_c449_deref_attr, 0);
        ta.recycle();
    }
}
