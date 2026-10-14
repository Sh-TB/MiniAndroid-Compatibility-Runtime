package com.probe.f322;

import android.view.ViewGroup;

/**
 * F-NEW-322 probe shape — the EXACT RecyclerView.LayoutParams family
 * solitaire carries (ay$i extends MarginLayoutParams, carries the
 * mViewHolder reference the DEX code writes BEFORE the parent sees the
 * view): a DEX-defined MarginLayoutParams subclass whose extra field the
 * app writes after construction and reads back through getLayoutParams().
 */
public class LpTag extends ViewGroup.MarginLayoutParams {
    public String tag;

    public LpTag(int w, int h) {
        super(w, h);
    }

    public LpTag(ViewGroup.LayoutParams src) {
        super(src);
    }
}
