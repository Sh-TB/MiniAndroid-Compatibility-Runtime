package com.probe.c448;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;

/**
 * CONT-111 / F-NEW-448 probe: the AOSP View suggested-minimum family,
 * minimized (fixture-first before the runtime law).
 *
 * jwtc chess 298 evidence (CONT-107): the appcompat action-bar Toolbar
 * measures 1080x0 — Toolbar.onMeasure's final height step is
 *   max(contentHeight, getSuggestedMinimumHeight()) -> resolveSizeAndState
 * and BOTH operands answered 0 (children unmeasured + the suggested-minimum
 * family missing from the shadow layer entirely).
 *
 * getSuggestedMinimumWidth/Height are PROTECTED (AOSP): every row goes
 * through a subclass wrapper — the same access shape appcompat Toolbar uses.
 *
 * Rows (AOSP android.view.View semantics):
 *   C448-DEFAULT   fresh View: suggested h/w == 0 (no min, no background)
 *   C448-SETH      setMinimumHeight(147): suggested==get==147
 *   C448-SETW      setMinimumWidth(88): suggested==get==88
 *   C448-INDEP     axes independent: h still 147, w still 88
 *   C448-OVERWRITE setMinimumHeight(56) then (147): last-writer wins
 *   C448-NEGATIVE  a fresh view stays 0 (per-object state, no static bleed)
 *   C448-MEASURE   Toolbar-shaped measure chain: a ViewGroup whose
 *                  onMeasure computes max(childContent, suggestedMinimum)
 *                  under an AT_MOST height spec measures >= the min
 *                  (168) — the exact law the chess toolbar starved on.
 */
public class MainActivity extends Activity {

    static final int MIN_H = 147;
    static final int MIN_W = 88;

    /** Public wrappers over the protected AOSP surface (Toolbar's access). */
    public static class ProbeView extends View {
        public ProbeView(android.content.Context c) { super(c); }
        public int sugH() { return getSuggestedMinimumHeight(); }
        public int sugW() { return getSuggestedMinimumWidth(); }
        @Override public void setMinimumHeight(int h) { super.setMinimumHeight(h); }
        @Override public void setMinimumWidth(int w) { super.setMinimumWidth(w); }
    }

    /** Toolbar-shaped measure chain (the F-NEW-448 disease surface). */
    public static class ToolbarShaped extends ViewGroup {
        public int lastMeasuredH = -1;
        public ToolbarShaped(android.content.Context c) { super(c); }
        @Override protected void onMeasure(int wSpec, int hSpec) {
            int content = 0; // no measured children — the chess toolbar face
            int suggested = getSuggestedMinimumHeight();
            int want = Math.max(content, suggested);
            int mode = android.view.View.MeasureSpec.getMode(hSpec);
            int size = android.view.View.MeasureSpec.getSize(hSpec);
            int h = (mode == android.view.View.MeasureSpec.EXACTLY) ? size
                    : (mode == android.view.View.MeasureSpec.AT_MOST)
                      ? Math.min(want, size) : want;
            setMeasuredDimension(
                android.view.View.MeasureSpec.getSize(wSpec), h);
            lastMeasuredH = h;
        }
        @Override protected void onLayout(boolean ch, int l, int t, int r, int b) {}
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);

        ProbeView fresh = new ProbeView(this);
        System.err.println("[C448-DEFAULT] h=" + fresh.sugH()
                + " w=" + fresh.sugW());

        fresh.setMinimumHeight(MIN_H);
        System.err.println("[C448-SETH] suggested=" + fresh.sugH()
                + " get=" + fresh.getMinimumHeight() + " expected=" + MIN_H);

        fresh.setMinimumWidth(MIN_W);
        System.err.println("[C448-SETW] suggestedW=" + fresh.sugW()
                + " getW=" + fresh.getMinimumWidth() + " expected=" + MIN_W);

        System.err.println("[C448-INDEP] h=" + fresh.sugH()
                + " w=" + fresh.sugW()
                + " expected=" + MIN_H + "/" + MIN_W);

        fresh.setMinimumHeight(56);
        fresh.setMinimumHeight(MIN_H);
        System.err.println("[C448-OVERWRITE] h=" + fresh.sugH()
                + " expected=" + MIN_H + " (last-writer wins)");

        ProbeView other = new ProbeView(this);
        System.err.println("[C448-NEGATIVE] other=" + other.sugH()
                + " expected=0 (per-object, no static bleed)");

        ToolbarShaped ts = new ToolbarShaped(this);
        ts.setMinimumHeight(168);
        ts.measure(View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.EXACTLY),
                   View.MeasureSpec.makeMeasureSpec(1920, View.MeasureSpec.AT_MOST));
        System.err.println("[C448-MEASURE] measuredH=" + ts.lastMeasuredH
                + " expected=168 (Toolbar-shaped AT_MOST chain)");
    }
}
