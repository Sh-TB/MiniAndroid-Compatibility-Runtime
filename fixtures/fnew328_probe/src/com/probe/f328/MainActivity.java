package com.probe.f328;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

/**
 * F-NEW-328 probe — asserts the FRAMEWORK LinearLayout.onMeasure SUPER
 * law. A DEX subclass of LinearLayout (vertical) whose onMeasure calls
 * super.onMeasure: the AOSP LinearLayout pass must (a) measure the
 * children with getChildMeasureSpec specs, (b) size the self per the
 * spec mode (wrap content = the children total), so the subclass reads
 * REAL values after the super call.
 *
 * The solitaire face: the appcompat AppBarLayout (a DEX LinearLayout
 * subclass) super call answered handled_void — no child measure, the
 * Toolbar measured 0 wide, the hamburger became untappable (target=0),
 * the drawer menu-content pipeline stayed unreachable BY INPUT.
 *
 * Rows print as F328P|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F328P|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── P1: vertical subclass, wrap_content height ──
        // The exact AppBarLayout shape: vertical LinearLayout DEX subclass,
        // match_parent width, wrap_content height, one match_parent x 48px
        // child. AOSP: super measures the child (EXACTLY 1080 x EXACTLY 48),
        // the self answers width 1080, height = child 48 (+padding 0).
        MyBar bar = new MyBar(this);
        bar.setOrientation(LinearLayout.VERTICAL);
        View child = new View(this);
        bar.addView(child, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 48));
        int ws = View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.EXACTLY);
        int hs = View.MeasureSpec.makeMeasureSpec(1920, View.MeasureSpec.AT_MOST);
        bar.measure(ws, hs);
        row("P1-VERTICAL-WRAP", bar.childW == 1080 && bar.childH == 48
                && bar.selfW == 1080 && bar.selfH == 48,
            "self=" + bar.selfW + "x" + bar.selfH
                + " child=" + bar.childW + "x" + bar.childH
                + " want self=1080x48 child=1080x48");

        // ── P2: horizontal subclass, wrap x wrap, explicit-size child ──
        // AOSP horizontal LinearLayout: self = max child height, sum of
        // child widths. Child 100x50 → self 100x50 at AT_MOST specs.
        MyRow rowV = new MyRow(this);
        rowV.setOrientation(LinearLayout.HORIZONTAL);
        View child2 = new View(this);
        rowV.addView(child2, new LinearLayout.LayoutParams(100, 50));
        int ws2 = View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.AT_MOST);
        int hs2 = View.MeasureSpec.makeMeasureSpec(1920, View.MeasureSpec.AT_MOST);
        rowV.measure(ws2, hs2);
        row("P2-HORIZONTAL-WRAP", rowV.selfW == 100 && rowV.selfH == 50
                && rowV.childW == 100 && rowV.childH == 50,
            "self=" + rowV.selfW + "x" + rowV.selfH
                + " child=" + rowV.childW + "x" + rowV.childH
                + " want self=100x50 child=100x50");

        // ── P3: EXACTLY height wins over the children total ──
        // The AOSP law: EXACTLY spec → the self answers the SPEC size even
        // when the children sum is smaller (the appbar EXACTLY face).
        MyBar bar2 = new MyBar(this);
        bar2.setOrientation(LinearLayout.VERTICAL);
        View child3 = new View(this);
        bar2.addView(child3, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 48));
        int ws3 = View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.EXACTLY);
        int hs3 = View.MeasureSpec.makeMeasureSpec(1920, View.MeasureSpec.EXACTLY);
        bar2.measure(ws3, hs3);
        row("P3-EXACTLY-SPEC", bar2.selfW == 1080 && bar2.selfH == 1920
                && bar2.childH == 48,
            "self=" + bar2.selfW + "x" + bar2.selfH
                + " child=" + bar2.childW + "x" + bar2.childH
                + " want self=1080x1920 childH=48");

        // ── N1: negative/sanity — the child IS in the tree ──
        row("N1-TREE-SANITY", bar.getChildCount() == 1 && child != null,
            "children=" + bar.getChildCount());
    }
}
