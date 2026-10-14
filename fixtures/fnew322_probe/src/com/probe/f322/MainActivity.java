package com.probe.f322;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * F-NEW-322 probe — asserts the AOSP View.mLayoutParams IDENTITY law by
 * VALUE. AOSP: View stores ONE mLayoutParams reference; setLayoutParams
 * writes it, getLayoutParams reads the SAME object back (View.java
 * L~20500: mLayoutParams = params / return mLayoutParams). ViewGroup
 * code downstream (RecyclerView.getChildViewHolderInt family) reads the
 * holder back from THE object it attached the holder to — any identity
 * split (getLayoutParams answering a fresh fallback object) silently
 * drops every field the app wrote between set and get.
 *
 * Solitaire face (CONT-51 decode): ay$o.a (tryGetViewHolderForPosition)
 * wrote ay$i.c = holder on obj#1802 via setLayoutParams; ay.e
 * (getChildViewHolderInt) later read .c on obj#1805 — the ROOT-055
 * fallback allocated a FRESH object because the setLayoutParams bridge
 * never recorded the object identity.
 *
 * Rows print as F322|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F322|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    static String describe(ViewGroup.LayoutParams lp) {
        if (lp == null) return "null";
        String cls = lp.getClass().getSimpleName();
        String tag = (lp instanceof LpTag && ((LpTag) lp).tag != null)
                     ? ((LpTag) lp).tag : "<no-tag>";
        return cls + "/" + tag + "/" + lp.width + "x" + lp.height;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        LinearLayout root = (LinearLayout) findViewById(R.id.root);
        TextView plain = (TextView) findViewById(R.id.plain);

        // P1 — programmatic set → get returns the SAME object with the
        // field the app wrote BEFORE the set still attached (the
        // mViewHolder face).
        LpTag lp1 = new LpTag(100, 200);
        lp1.tag = "held-1";
        root.setLayoutParams(lp1);
        ViewGroup.LayoutParams back1 = root.getLayoutParams();
        boolean p1 = back1 instanceof LpTag && "held-1".equals(((LpTag) back1).tag);
        row("P1-LP-IDENTITY", p1,
            "back=" + describe(back1) + " want LpTag/held-1");

        // P2 — a second set REPLACES the stored identity (AOSP overwrite).
        LpTag lp2 = new LpTag(300, 400);
        lp2.tag = "held-2";
        root.setLayoutParams(lp2);
        ViewGroup.LayoutParams back2 = root.getLayoutParams();
        boolean p2 = back2 instanceof LpTag && "held-2".equals(((LpTag) back2).tag);
        row("P2-LP-OVERWRITE", p2,
            "back=" + describe(back2) + " want LpTag/held-2");

        // N1 — a view that was NEVER given params still answers non-null
        // (ROOT-055 fallback law kept intact for the inflate world).
        ViewGroup.LayoutParams dfb = plain.getLayoutParams();
        row("N1-NOSET-NONNULL", dfb != null, "back=" + describe(dfb));

        // N2 — width/height round-trip through the identity (the
        // pre-existing semantic face must hold THROUGH the same object).
        boolean n2 = back2 != null && back2.width == 300 && back2.height == 400;
        row("N2-WH-ROUNDTRIP", n2, "wh=" + (back2 == null ? "null" : (back2.width + "x" + back2.height)) + " want 300x400");

        // N3 — the fallback object for the never-set view answers the
        // layout XML width (wrap_content = -2): the ROOT-055 semantic
        // width face must not regress.
        boolean n3 = dfb != null && dfb.width == -2;
        row("N3-NOSET-SEMANTIC", n3, "width=" + (dfb == null ? "null" : dfb.width) + " want -2");
    }
}
