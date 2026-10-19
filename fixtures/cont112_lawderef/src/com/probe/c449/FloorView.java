package com.probe.c449;

import android.view.View;

/** Toolbar-shaped measure chain (the F-NEW-448 disease surface). */
public class FloorView extends View {
    public int lastMeasuredH = -1;
    public FloorView(android.content.Context c) { super(c); }
    public FloorView(android.content.Context c, android.util.AttributeSet a) {
        super(c, a);
    }
    @Override protected void onMeasure(int wSpec, int hSpec) {
        int content = 0; // no children — the chess toolbar face
        int suggested = getSuggestedMinimumHeight();
        int want = Math.max(content, suggested);
        int mode = View.MeasureSpec.getMode(hSpec);
        int size = View.MeasureSpec.getSize(hSpec);
        int h = (mode == View.MeasureSpec.EXACTLY) ? size
                : (mode == View.MeasureSpec.AT_MOST)
                  ? Math.min(want, size) : want;
        setMeasuredDimension(View.MeasureSpec.getSize(wSpec), h);
        lastMeasuredH = h;
    }
}
