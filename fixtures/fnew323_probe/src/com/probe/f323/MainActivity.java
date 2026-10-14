package com.probe.f323;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * F-NEW-322/323 probe — asserts the AOSP ViewGroup detach/attach
 * IDENTITY laws by VALUE. AOSP ViewGroup.java: detachViewFromParent
 * removes the child from mChildren (childCount decrements) but KEEPS
 * child.mParent (detachment is a transient state inside one layout
 * traversal); attachViewToParent re-inserts the child at the given
 * index and REPLACES child.mLayoutParams; removeDetachedView removes
 * for good (mParent cleared). RecyclerView's ChildHelper drives exactly
 * these three through real DEX — any missing bridge left the children
 * table UNSHRUNK after a detach and the second detachAndScrap hit the
 * DEX-side isTmpDetached defense: solitaire IAE "called detach on an
 * already detached child" at GameSelector.onCreate.
 *
 * Rows print as F323|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F323|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Detacher box = new Detacher(this);
        TextView c1 = new TextView(this);
        c1.setText("one");
        TextView c2 = new TextView(this);
        c2.setText("two");
        box.addView(c1);
        box.addView(c2);
        setContentView(box);

        // P1 — detach(0): childCount decrements (the AOSP children-table
        // shrink — the law whose absence made the second detachAndScrap
        // re-catch the detached child).
        box.detachIdx(0);
        row("P1-DETACH-COUNT", box.getChildCount() == 1,
            "count=" + box.getChildCount() + " want 1");

        // P2 — the remaining child at slot 0 is c2 (array compaction).
        View slot = box.getChildAt(0);
        row("P2-DETACH-SLOT", slot == c2,
            "slot0==" + (slot == c2 ? "c2" : (slot == c1 ? "c1" : "null"))
            + " want c2");

        // P3 — AOSP detach KEEPS child.mParent (transient state).
        row("P3-DETACH-KEEPS-PARENT", c1.getParent() == box,
            "c1.parent==" + (c1.getParent() == box ? "box" : "other/null")
            + " want box");

        // P4 — attachViewToParent(c1, 0, lp) re-inserts at index 0.
        ViewGroup.LayoutParams lp = c1.getLayoutParams();
        box.attachIdx(c1, 0, lp);
        row("P4-ATTACH-ROUNDTRIP",
            box.getChildCount() == 2 && box.getChildAt(0) == c1,
            "count=" + box.getChildCount() + " slot0=="
            + (box.getChildAt(0) == c1 ? "c1" : "other") + " want 2/c1");

        // P5 — attachViewToParent REPLACES mLayoutParams with the params
        // argument (AOSP View.mLayoutParams single-slot law, F-NEW-322
        // cooperation): the new object round-trips through getLayoutParams.
        LinearLayout.LayoutParams nlp = new LinearLayout.LayoutParams(50, 60);
        box.attachIdx(c2, 1, nlp);
        ViewGroup.LayoutParams back = c2.getLayoutParams();
        row("P5-ATTACH-LP-IDENTITY", back == nlp,
            "back==" + (back == nlp ? "nlp" : "other") + " want nlp");

        // N1 — removeDetachedView removes FOR GOOD (mParent cleared).
        box.removeDet(c1);
        row("N1-REMOVEDETACHED",
            box.getChildCount() == 1 && c1.getParent() == null,
            "count=" + box.getChildCount() + " c1.parent=="
            + (c1.getParent() == null ? "null" : "kept") + " want 1/null");
    }
}
