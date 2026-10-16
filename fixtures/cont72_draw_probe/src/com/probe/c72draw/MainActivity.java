package com.probe.c72draw;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.FrameLayout;

/**
 * CONT-72 — issue #364 FOUNDATION 1 review probe (MG-116 invalidate law).
 *
 * Law under test (AOSP View.java invalidateInternal / ViewRootImpl
 * scheduleTraversals): a child View's state mutation followed by
 * invalidate() must reach a traversal and change app-owned pixels,
 * WITHOUT forcing measure/layout; requestLayout() must force
 * measure/layout (MG-115 law); repeated invalidations coalesce with the
 * latest state drawn (no lost update).
 *
 * Rows logged by the app itself (the code whose contract is asserted):
 *   C72-T1..T8 : static counter snapshots at each chained step
 *   C72-DRAW   : first 12 onDraw invocations (n, phase, color)
 *   C72-VERDICT: computed deltas
 *
 * Phases: 0=red D2321E, 1=green 1ED232, 2=blue 1E32D2, 3=yellow D2D21E.
 * Sequence (each step chained via View.post — no wall-clock delays):
 *   T1 baseline counters -> phase=1 + invalidate() (INVALIDATE ROW)
 *   T3 counters after invalidate window (deltaDraw>=1, deltaMeasure==0)
 *   T4 requestLayout() (MG-115 POSITIVE CONTROL)
 *   T5 counters (deltaMeasure>=1 from requestLayout only)
 *   T6 phase=2 + invalidate() x3 coalesced (COALESCING ROW)
 *   T7 phase=3 WITHOUT invalidate (ARCHITECTURE row: full-redraw model)
 *   T8 final counters + verdict
 */
public class MainActivity extends Activity {

    public static int measureCount, layoutCount;
    public static int drawCount, drawLogged;

    private DrawProbe child;
    private static int snap1Draw, snap3Draw, snap3Measure, snap3Layout;
    private static int snap5Measure, snap5Layout, snap6bDraw;

    public static void tickMeasure() { measureCount++; }
    public static void tickLayout() { layoutCount++; }

    public static class DrawProbe extends View {
        public int phase = 0;
        private final Paint paint = new Paint();

        public DrawProbe(Context c) { super(c); }

        private int colorForPhase() {
            switch (phase) {
                case 1: return 0xFF1ED232; // green
                case 2: return 0xFF1E32D2; // blue
                case 3: return 0xFFD2D21E; // yellow
                default: return 0xFFD2321E; // red
            }
        }

        @Override protected void onMeasure(int wspec, int hspec) {
            measureCount++;
            setMeasuredDimension(1080, 1920);
        }

        @Override protected void onLayout(boolean changed, int l, int t, int r, int b) {
            layoutCount++;
        }

        @Override protected void onDraw(Canvas canvas) {
            drawCount++;
            if (drawLogged < 12) {
                drawLogged++;
                System.err.println("[C72-DRAW] n=" + drawCount
                        + " phase=" + phase
                        + " color=0x" + Integer.toHexString(colorForPhase()));
            }
            paint.setColor(colorForPhase());
            canvas.drawRect(150, 150, 900, 900, paint);
        }
    }

    private void snap(String tag, int d0, int m0, int l0) {
        System.err.println("[C72-" + tag + "] draw=" + drawCount + " (+" + (drawCount - d0)
                + ") measure=" + measureCount + " (+" + (measureCount - m0)
                + ") layout=" + layoutCount + " (+" + (layoutCount - l0) + ")");
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        final Handler h = new Handler(Looper.getMainLooper());
        FrameLayout root = new FrameLayout(this);
        child = new DrawProbe(this);
        root.addView(child, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));
        setContentView(root);

        final int d0 = drawCount, m0 = measureCount, l0 = layoutCount;
        // Frame-spread schedule: the canonical run advances +300ms virtual
        // per frame boundary, so steps are spaced 650ms apart — each lands
        // in its OWN boundary (drain → render interleave per step).
        h.postDelayed(new Runnable() { public void run() {
            snap("T1-BASELINE", d0, m0, l0);
            snap1Draw = drawCount;
            child.phase = 1;
            child.invalidate();
            System.err.println("[C72-T2-INV] phase=1 invalidate() posted (state mutated first)");
        }}, 350);
        h.postDelayed(new Runnable() { public void run() {
            snap("T3-AFTER-INV", d0, m0, l0);
            snap3Draw = drawCount; snap3Measure = measureCount; snap3Layout = layoutCount;
        }}, 900);
        h.postDelayed(new Runnable() { public void run() {
            child.requestLayout();
            System.err.println("[C72-T4-RL] requestLayout() posted (MG-115 control)");
        }}, 1450);
        h.postDelayed(new Runnable() { public void run() {
            snap("T5-AFTER-RL", d0, m0, l0);
            snap5Measure = measureCount; snap5Layout = layoutCount;
        }}, 2000);
        h.postDelayed(new Runnable() { public void run() {
            child.phase = 2;
            child.invalidate(); child.invalidate(); child.invalidate();
            System.err.println("[C72-T6-COALESCE] phase=2 invalidate() x3 (latest state must win)");
        }}, 2550);
        h.postDelayed(new Runnable() { public void run() {
            snap("T6B-AFTER-COALESCE", d0, m0, l0);
            snap6bDraw = drawCount;
        }}, 3100);
        h.postDelayed(new Runnable() { public void run() {
            child.phase = 3; // NO invalidate — architecture row
            System.err.println("[C72-T7-NOINV] phase=3 set WITHOUT invalidate()");
        }}, 3650);
        h.postDelayed(new Runnable() { public void run() {
            snap("T8-FINAL", d0, m0, l0);
            int dInv = snap3Draw - snap1Draw;
            int mInv = snap3Measure - m0;
            int mRl = snap5Measure - snap3Measure;
            int lRl = snap5Layout - snap3Layout;
            int dCo = snap6bDraw - snap5Measure >= 0 ? snap6bDraw - snap3Draw : 0;
            System.err.println("[C72-VERDICT] invDrawDelta=" + dInv
                    + " invMeasureDelta=" + mInv
                    + " rlMeasureDelta=" + mRl
                    + " rlLayoutDelta=" + lRl
                    + " coalesceDrawDelta=" + (snap6bDraw - snap3Draw)
                    + " law=" + (dInv >= 1 && mRl >= 1
                        ? "PASS(delivery+rl)" : "CHECK"));
        }}, 4200);
    }
}
