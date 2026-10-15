package com.probe.tsp;

import android.app.Activity;
import android.content.res.TypedArray;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        android.util.TypedValue tv = new android.util.TypedValue();
        TypedArray ta = obtainStyledAttributes(R.styleable.TspTest);
        int n = ta.getIndexCount();
        // walk the styleable ARRAY directly so every slot is probed
        int[] sa = R.styleable.TspTest;
        // F1 child precedence: nearest writer (TspMidB) beats the root
        int inherited = ta.getColor(R.styleable.TspTest_tspInherited, 0);
        System.out.println("[TSPROBE] F1 tspInherited=" + hex(inherited)
                + " want=ff445566 (nearest-writer, not root ff112233)");
        // F1b deep chain through 10 parent hops + an EMPTY grandparent
        int deep = ta.getInt(R.styleable.TspTest_tspDeepAttr, -1);
        System.out.println("[TSPROBE] F6 deepAttr=" + deep + " want=-1 "
                + "(TspThemeA chain does not include TspDeepChain1)");
        // F3 PRESENT-false vs absent
        boolean pf = ta.getBoolean(R.styleable.TspTest_tspPresentFalse, true);
        boolean pfPresent = hasSlot(ta, R.styleable.TspTest_tspPresentFalse);
        System.out.println("[TSPROBE] F3 presentFalse value=" + pf
                + " present=" + pfPresent + " want=false/true (PRESENT false)");
        boolean oo = hasSlot(ta, R.styleable.TspTest_tspOverlayOnly);
        System.out.println("[TSPROBE] F3b overlayOnly present-before-apply="
                + oo + " want=false (truly absent)");
        // F4 framework attr vs app attr with distinct ids
        Object noTitle = getThemeValue(android.R.attr.windowNoTitle);
        System.out.println("[TSPROBE] F4 android:windowNoTitle=" + noTitle
                + " want=ok type=18 data=1 (INT_BOOLEAN true, framework 0x01010056)");
        ta.recycle();
        // F2 applyStyle-only attr (normal apply fills missing)
        getTheme().applyStyle(R.style.TspOverlayOne, false);
        TypedArray t2 = obtainStyledAttributes(R.styleable.TspTest);
        int ov = t2.getColor(R.styleable.TspTest_tspOverlayOnly, 0);
        System.out.println("[TSPROBE] F2 tspOverlayOnly=" + hex(ov)
                + " want=ff000001 (overlay-only, force=false fills)");
        t2.recycle();
        // F5 force + ordering: force=true #2 overwrites #1; force=false #3 cannot
        getTheme().applyStyle(R.style.TspOverlayTwo, true);
        getTheme().applyStyle(R.style.TspOverlayThree, false);
        TypedArray t3 = obtainStyledAttributes(R.styleable.TspTest);
        int ov2 = t3.getColor(R.styleable.TspTest_tspOverlayOnly, 0);
        int fv = t3.getInt(R.styleable.TspTest_tspForcedValue, -1);
        System.out.println("[TSPROBE] F5 tspOverlayOnly=" + hex(ov2)
                + " want=ff000002 (force=true Two over One)");
        System.out.println("[TSPROBE] F5b tspForcedValue=" + fv
                + " want=2 (force=true wins over later force=false Three)");
        t3.recycle();
        // F6: apply the 10-hop chain style (child attr=1 must beat hop-10 attr=10)
        getTheme().applyStyle(R.style.TspDeepChain1, false);
        TypedArray t4 = obtainStyledAttributes(R.styleable.TspTest);
        int deep2 = t4.getInt(R.styleable.TspTest_tspDeepAttr, -1);
        System.out.println("[TSPROBE] F6b deepAttr-after-fill=" + deep2
                + " want=77 (force=false fills only — attr already present)");
        t4.recycle();
        // F6c: force=true apply of the 10-hop chain: the CHILD value wins
        getTheme().applyStyle(R.style.TspDeepChain1, true);
        TypedArray t5 = obtainStyledAttributes(R.styleable.TspTest);
        int deep3 = t5.getInt(R.styleable.TspTest_tspDeepAttr, -1);
        System.out.println("[TSPROBE] F6c deepAttr-after-force=" + deep3
                + " want=1 (force=true + child precedence over 10-hop ancestor, empty style mid-chain)");
        t5.recycle();
        System.out.println("[TSPROBE] F6d done-no-crash (deep chain + empty style walked safely)");
        // F7 isolation: launch the second activity — its theme (TspThemeB)
        // must NOT carry any of this activity's applyStyle overlay state.
        startActivity(new android.content.Intent(this, SecondActivity.class));
    }

    private static String hex(int c) {
        return String.format("%08x", c);
    }

    private boolean hasSlot(TypedArray ta, int index) {
        return ta.hasValue(index);
    }

    /** resolve a framework attr through the theme (F4). */
    private Object getThemeValue(int attr) {
        android.util.TypedValue v = new android.util.TypedValue();
        boolean ok = getTheme().resolveAttribute(attr, v, true);
        return ok ? ("ok type=" + v.type + " data=" + v.data
                     + "/resid=" + v.resourceId)
                  : "MISS";
    }
}
