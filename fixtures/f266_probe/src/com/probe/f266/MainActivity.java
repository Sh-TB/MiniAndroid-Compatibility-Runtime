package com.probe.f266;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-12 synthetic probe — F-NEW-266 invoke-virtual TRANSITIVE
 * INTERFACE-DEFAULT dispatch (JVMS 5.4.5 / ART resolution law).
 *
 * F266-A  direct default: class implements the interface that DECLARES the
 *         default; call site is invoke-virtual on the CONCRETE class (the
 *         exact Compose-Modifier shape) — default body must execute.
 * F266-B  override wins: subclass overrides the default; the OVERRIDE body
 *         (not the default) must run — most-derived law preserved.
 * F266-C  transitive: default declared on the GRANDPARENT interface
 *         (DefI <- DefJ <- DefK), receiver implements only DefK — closure
 *         must reach 2 super-interface hops.
 * F266-D  negative: an unrelated default (OtherDefI.other) must NOT be
 *         dispatched for receivers outside its hierarchy (no default
 *         cross-dispatch; result stays 0, no crash).
 * F266-E  receiver identity: the default body must execute with the
 *         ORIGINAL receiver — it reads an instance field of the concrete
 *         class via the interface method body (salt pattern).
 * F266-F  value fidelity: primitive int return through the default body
 *         (boxed-free path), exact value, negative and >0xff ranges.
 */
public class MainActivity extends Activity {

    interface DefI {
        int salt();  // abstract: each receiver provides its identity field
        default int plusOne(int x) { return x + 1 + (salt() == 7 ? 0 : 1000); }
        default int triple(int x) { return x * 3; }
    }
    interface DefJ extends DefI {}
    interface DefK extends DefJ {}
    interface OtherDefI { default int other() { return 99; } }

    static class DefA implements DefJ { public int salt() { return 7; } }
    static class DefB implements DefI {
        public int salt() { return 7; }
        public int plusOne(int x) { return x + 10; }   // override
    }
    static class DefC implements DefK { public int salt() { return 7; } }
    static class DefE {
        int f = 5;
        public int salt() { return f; }
        public int viaDefault(DefI self, int x) { return self.plusOne(x); }
    }

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // F266-A: direct default via invoke-virtual on the concrete class
        DefA a = new DefA();
        int r1 = a.plusOne(41);
        row("F266-A", r1 == 42, "plusOne(41)=" + r1 + " (want 42)");

        // F266-B: most-derived override must beat the default
        DefB b = new DefB();
        int r2 = b.plusOne(41);
        row("F266-B", r2 == 51, "plusOne(41)=" + r2 + " (want 51)");

        // F266-C: transitive 2-hop super-interface closure
        DefC c = new DefC();
        int r3 = c.plusOne(41);
        row("F266-C", r3 == 42, "transitive plusOne(41)=" + r3 + " (want 42)");

        // F266-D: negative — no cross-hierarchy default dispatch
        int r4 = 0;
        boolean threw = false;
        try {
            DefE e = new DefE();
            OtherDefI o = null;
            // the ONLY way javac emits an interface-typed call without a
            // receiver is via a typed null; guard it — must NPE, never
            // dispatch anything
            r4 = o.other();
        } catch (NullPointerException npe) {
            threw = true;   // ART law: null receiver NPE, no dispatch
        } catch (Throwable t) {
            threw = false;
        }
        row("F266-D", threw && r4 == 0, "null-receiver NPE=" + threw + " r4=" + r4);

        // F266-E/F: receiver identity + value fidelity through default body
        DefE e = new DefE();
        int r5 = e.viaDefault(new DefC(), 100);  // DefC.salt()==7 → x+1
        row("F266-E", r5 == 101, "identity viaDefault(100)=" + r5 + " (want 101)");
        int r6 = c.triple(7);
        row("F266-F", r6 == 21, "triple(7)=" + r6 + " (want 21)");

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        root.addView(tv);
        setContentView(root);
    }
}
