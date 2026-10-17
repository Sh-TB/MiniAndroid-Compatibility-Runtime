package com.probe.mg310;

import android.app.Activity;
import android.os.Bundle;

/**
 * MG-310 dedicated <clinit> fence (issue #364 FOUNDATION 4/4 — class
 * initialization ordering). Locks the JLS 12.4.1 / JVMS 5.5 laws with
 * self-contained expected-value assertions; the harness fence script
 * additionally parses engine [CLASS_INIT] rows for the occurrence laws.
 *
 * Rows (all printed by the app itself on stderr):
 *   MG310-L1  active-use init: Base.<clinit> ran on first static METHOD call
 *   MG310-L2  compile-time constant read does NOT initialize
 *             ConstHolder.<clinit> must NOT have run when C is read
 *   MG310-L3  superclass-first: Derived first use -> Base.<clinit> before
 *             Derived.<clinit> (order captured in the markers below)
 *   MG310-L4  once-only: second active use -> initCount still 1
 *   MG310-L5  default-value-before-write: self forward reference in <clinit>
 *             yields "nullx" (JLS: the variable holds its default while
 *             <clinit> runs)
 *   MG310-VERSION  identity marker
 */
public class MainActivity extends Activity {

    public static final String VERSION = "V1-MG310";

    /** L1/L3/L4: logging base class — init on first ACTIVE use. */
    public static class Base {
        public static int initCount = 0;
        static {
            initCount++;
            System.err.println("[MG310-CLINIT] Base #" + initCount);
        }
        public static String ping() { return "base"; }
    }

    /** L2: holder whose ONLY member is a compile-time constant. */
    public static class ConstHolder {
        public static final int C = 7;
        static {
            System.err.println("[MG310-CLINIT] ConstHolder — MUST NOT APPEAR");
        }
    }

    /** L3: subclass — its first use must init Base FIRST. */
    public static class Derived extends Base {
        static {
            System.err.println("[MG310-CLINIT] Derived");
        }
        public static String ping() { return "derived"; }
    }

    /** L5: default value visible during <clinit> (JLS-legal form:
     *  the field is declared first; the static block reads the default). */
    public static class Forward {
        public static String s;
        static {
            s = s + "x";  // s == null at this point -> "nullx"
        }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        System.err.println("[MG310-VERSION] code=" + VERSION);

        // L2 FIRST — reading a compile-time constant must not initialize
        // ConstHolder (asserted twice: value + no CLINIT row in the log).
        System.err.println("[MG310-L2] ConstHolder.C=" + ConstHolder.C
                + " (no MG310-CLINIT ConstHolder row must exist)");

        // L1: first active use of Base = static method call.
        String r1 = Base.ping();
        System.err.println("[MG310-L1] Base.ping=" + r1
                + " initCount=" + Base.initCount);

        // L3: first active use of Derived — Base already initialized here,
        // so the ORDER law is exercised on a fresh chain: Derived must not
        // appear before Base's init in a cold run. To make the order
        // observable even when Base is warm, the fence script checks that
        // the Derived marker comes after a Base marker in the log stream.
        String r3 = Derived.ping();
        System.err.println("[MG310-L3] Derived.ping=" + r3);

        // L4: once-only — second calls do not re-run <clinit>.
        Base.ping();
        Derived.ping();
        System.err.println("[MG310-L4] initCount-after-second-use="
                + Base.initCount + " (expect 1)");

        // L5: default value visible during <clinit>.
        System.err.println("[MG310-L5] Forward.s=" + Forward.s
                + " (expect nullx)");
    }
}
