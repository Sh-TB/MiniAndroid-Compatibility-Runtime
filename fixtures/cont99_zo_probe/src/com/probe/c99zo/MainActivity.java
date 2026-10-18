package com.probe.c99zo;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;

/**
 * CONT-99 T6 — sibling z-order, bringToFront and elevation probe (V1-C99ZO).
 * Deterministic FrameLayout on bg #FFFFFFFF; three OVERLAPPING siblings at
 * 45-degree diagonal offsets + one unrelated sibling:
 *
 *   A red 300x300   at (50,50)   added FIRST  (bottom of z stack)
 *   B green 300x300 at (150,150) added SECOND
 *   C blue 300x300  at (250,250) added THIRD  (top of z stack)
 *   D yellow 100x100 at (900,100) added FOURTH (unrelated region)
 *
 * AOSP laws under test:
 *   L1 insertion order = paint order (last added paints last = on top):
 *      PHASE1 (100,100)=RED (200,200)=GREEN (300,300)=BLUE (950,150)=YELLOW
 *   L2 bringToFront() moves the child to the END of the child array:
 *      PHASE2 idx(A)=3, (200,200)=RED (A over B), (300,300)=RED (A over C),
 *      (400,400)=BLUE (C beyond A's reach), (100,100)=RED, (950,150)=YELLOW.
 *   L3 unrelated sibling regions are never disturbed.
 *   L4 elevation state round-trips (getElevation answers what was set).
 */
public class MainActivity extends Activity {
    FrameLayout root;
    View a, b, c, d;

    View box(int size, int color, int x, int y, String tag) {
        View v = new View(this);
        v.setBackgroundColor(color);
        v.setTag(tag);
        FrameLayout.LayoutParams lp =
                new FrameLayout.LayoutParams(size, size);
        lp.leftMargin = x;
        lp.topMargin = y;
        v.setLayoutParams(lp);
        return v;
    }

    void order(String phase) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < root.getChildCount(); i++) {
            sb.append(root.getChildAt(i).getTag()).append(",");
        }
        System.err.println("[C99-ZO] " + phase
                + " count=" + root.getChildCount()
                + " order=" + sb
                + " idxA=" + root.indexOfChild(a)
                + " idxB=" + root.indexOfChild(b)
                + " idxC=" + root.indexOfChild(c));
    }

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        root = new FrameLayout(this);
        root.setBackgroundColor(0xFFFFFFFF);
        a = box(300, 0xFFCC2222, 50, 50, "A");
        b = box(300, 0xFF22CC22, 150, 150, "B");
        c = box(300, 0xFF2222CC, 250, 250, "C");
        d = box(100, 0xFFCCCC22, 900, 100, "D");
        root.addView(a); root.addView(b); root.addView(c); root.addView(d);
        setContentView(root);
        System.err.println("[C99-ZOVER] V1-C99ZO");

        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            public void run() {
                try {
                    order("PHASE1");
                    a.bringToFront();
                    root.requestLayout();
                    root.invalidate();
                    order("PHASE2");
                    c.setElevation(20);
                    System.err.println("[C99-ZOEL] elevC="
                            + c.getElevation()
                            + " elevA=" + a.getElevation());
                    System.err.println("[C99-ZODONE] printed");
                } catch (Throwable t) {
                    System.err.println("[C99-ZOERR] " + t);
                }
            }
        }, 1200);
    }
}
