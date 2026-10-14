package com.probe.f324;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;

/**
 * F-NEW-324 probe — asserts the ART super-dispatch BOUNDARY law by VALUE.
 * JVMS/ART: invokevirtual/super resolution walks the receiver's class
 * chain; when a DEX INTERMEDIATE (NavigationView's f: a DEX class with no
 * onMeasure whose super is FrameLayout) does not define the method, the
 * resolution lands on the first FRAMEWORK ancestor — the bridge must see
 * THAT boundary class or every shadow keyed by a framework name silently
 * misses. Runtime face: NavigationView.onMeasure ran its DEX body but the
 * FrameLayout measure law never executed → no setMeasuredDimension →
 * [DEX-MEASURE] "FAILED(no write-back)" → the drawer menu measured 0x0.
 *
 * Rows print as F324|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F324|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // P1 — the DEX-intermediate super-dispatch (the NavigationView/f
        // shape): Leaf extends Mid [no onMeasure] extends FrameLayout.
        Leaf leaf = new Leaf(this);
        View inner = new View(this);
        leaf.addView(inner, new ViewGroup.LayoutParams(
                           ViewGroup.LayoutParams.MATCH_PARENT,
                           ViewGroup.LayoutParams.MATCH_PARENT));
        int ws = View.MeasureSpec.makeMeasureSpec(100, View.MeasureSpec.EXACTLY);
        int hs = View.MeasureSpec.makeMeasureSpec(60, View.MeasureSpec.EXACTLY);
        leaf.measure(ws, hs);
        row("P1-SUPER-THROUGH-DEX-MID",
            leaf.getMeasuredWidth() == 100 && leaf.getMeasuredHeight() == 60,
            "measured=" + leaf.getMeasuredWidth() + "x" + leaf.getMeasuredHeight()
            + " want 100x60");

        // P2 — the direct-framework control (the R-NEW-345 case): the
        // declaring class IS the framework class; must keep working.
        Direct direct = new Direct(this);
        direct.measure(ws, hs);
        row("P2-SUPER-DIRECT-FRAMEWORK",
            direct.getMeasuredWidth() == 100 && direct.getMeasuredHeight() == 60,
            "measured=" + direct.getMeasuredWidth() + "x"
            + direct.getMeasuredHeight() + " want 100x60");

        // N1 — the child was measured by the FrameLayout descent law
        // through the DEX intermediate (the super chain really ran).
        row("N1-CHILD-MEASURED",
            inner.getMeasuredWidth() == 100 && inner.getMeasuredHeight() == 60,
            "child=" + inner.getMeasuredWidth() + "x" + inner.getMeasuredHeight()
            + " want 100x60");
    }
}
