package com.probe.f320;

import android.app.Activity;
import android.os.Bundle;

/**
 * F-NEW-320/321 probe — asserts two generic interpreter laws by VALUE:
 *
 * F-NEW-321 (shadowed-field slot identity, the c$b/ay$a family):
 *   P1  sub ctor's write to SubA.a survives the super ctor's later mirror
 *       write — outer() answers the EXACT Outer instance (slot identity)
 *   P2  the super slot still holds the super ctor's Inner (superA())
 *   P3  two SubA instances do not cross-contaminate (per-instance slots)
 *   N1  non-shadowed field round-trip (write-then-read through both
 *       accessors lands where it was written)
 *   N2  super-slot writer round-trip (setSuperA then superA identity)
 *
 * F-NEW-320 (per-frame instance dispatch must bind the receiver):
 *   P4  computeScroll() runs with a BOUND receiver — the Flinger row
 *       prints from inside the override (printed by the view itself;
 *       MainActivity only reports the static verdict after layout).
 *
 * Rows print as F320|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F320|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        Outer o1 = new Outer("outer-1");
        Outer o2 = new Outer("outer-2");
        SubA s1 = new SubA(o1);
        SubA s2 = new SubA(o2);

        // P1 — the sub slot holds the sub ctor's value (solitaire face).
        Outer r1 = s1.outer();
        row("P1-SUB-SLOT", r1 == o1,
            "s1.outer()==" + (r1 == null ? "null" : r1.tag)
            + " want outer-1");

        // P2 — the super slot keeps the super ctor's value.
        Inner i1 = s1.superA();
        row("P2-SUPER-SLOT", i1 != null && "super-slot".equals(i1.tag),
            "s1.superA()==" + (i1 == null ? "null" : i1.tag)
            + " want super-slot");

        // P3 — per-instance slot identity.
        Outer r2 = s2.outer();
        row("P3-SECOND-INSTANCE", r2 == o2,
            "s2.outer()==" + (r2 == null ? "null" : r2.tag)
            + " want outer-2");

        // N1 — non-shadowed round-trip (unique name).
        Inner fresh = new Inner("fresh");
        s1.setSuperA(fresh);
        Inner back = s1.superA();
        row("N1-ROUNDTRIP", back == fresh,
            "setSuperA->superA identity=="
            + (back == null ? "null" : back.tag));

        // N2 — the super writer does not leak into the sub slot.
        Outer after = s1.outer();
        row("N2-SUB-UNTOUCHED", after == o1,
            "s1.outer() after super write=="
            + (after == null ? "null" : after.tag) + " want outer-1");

        // P4 — computeScroll's receiver binding is gated BY THE OVERRIDE
        // ITSELF: Flinger.computeScroll prints F320|P4-CS-RECV rows from
        // inside the DEX body during the frame passes (after onCreate
        // returns, so a static read here would measure too early — the
        // first draft's P4-CS-VERDICT row was that design artifact and is
        // removed; the in-override rows are the law's gate).
    }
}
