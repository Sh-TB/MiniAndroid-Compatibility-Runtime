package com.probe.f320;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;

/**
 * F-NEW-320 probe shape — a DEX-defined View that OVERRIDES computeScroll
 * (the R-NEW-430 per-frame dispatch family) and reads its OWN field inside
 * the override. On a correctly bound receiver the field read answers the
 * ctor value; on the unbound face (args={} → this=<unset>) the iget
 * silently answers null and the row prints FAIL. The row is printed from
 * INSIDE the override — no runner-side probing needed.
 */
public class Flinger extends View {
    /** Set in the ctor; computeScroll reads it (the mLeftDragger face). */
    public String flingerTag;

    /** Recorded by computeScroll — the receiver-binding verdict. */
    public static String csSeen = "not-called";

    public Flinger(Context c, AttributeSet attrs) {
        super(c, attrs);
        flingerTag = "flinger-bound";
    }

    @Override
    public void computeScroll() {
        if (flingerTag != null && "flinger-bound".equals(flingerTag)) {
            csSeen = "bound";
            System.out.println("F320|P4-CS-RECV|PASS|computeScroll receiver bound, tag="
                               + flingerTag);
        } else {
            csSeen = "unbound";
            System.out.println("F320|P4-CS-RECV|FAIL|computeScroll ran with tag="
                               + flingerTag + " (null = unbound receiver)");
        }
    }
}
