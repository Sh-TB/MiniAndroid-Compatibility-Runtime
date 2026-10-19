package com.probe.c106a;

import android.app.Activity;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Bundle;

/**
 * CONT-106 F-NEW-446 probe — S123-CLINIT-MAT must NOT defeat the
 * "null = not-yet-factory-initialized" static sentinel law (JVMS 5.5 +
 * AOSP ClassLinker behavior).
 *
 * Real-APK oracle (run/cont105/tg_pre.log, telegram classes3.dex disasm):
 *   o6.&lt;clinit&gt; completed OK (1736 sputs) and does NOT assign k0/m0/u1 —
 *   the lazy factory o6.P(Context) owns them (single u1 writer; callers
 *   o6.R / r4.&lt;init&gt; / CheckBoxSquare.&lt;init&gt;).
 *   o6.k() starts with `sget k0; if-nez k0, +3; return-void` — on ART,
 *   before P() runs, k0 == null → k() early-returns, NO NPE.
 *   Engine pre-fix: [S123-CLINIT-MAT] materialized o6.k0/m0 on first
 *   sget (gate `attempted || stored_null` fired on a HEALTHY clinit) →
 *   guard fell through → iput-boolean xj0.Y:Z on the never-factory u1
 *   → uncaught NPE @o6.k pc=46.
 *
 * Rows (all deterministic):
 *  [C106-SENTINEL]  guardEscaped=false expected POST (AOSP: sget of a
 *      never-assigned static Paint of a HEALTHY class returns null →
 *      null-sentinel guard takes the early-return branch).
 *      PRE (bug face): guardEscaped=true.
 *  [C106-FACTORY]   factory-first ordering: after the factory assigns the
 *      field, the guard proceeds and setColor works (no materialization
 *      needed, AOSP-faithful).
 *  [C106-CLINITFAIL] a &lt;clinit&gt; that THROWS leaves the class erroneous
 *      (JVMS 5.5): first active use answers NCDFE/EIIE-family, and a later
 *      sget does NOT silently invent objects (F-NEW-215 honesty law).
 *      Informational parity row — the exact wrapped type is recorded.
 *  [C106-INVOKE]    unguarded invoke on a never-assigned static Paint:
 *      AOSP NPE parity (negative row — the engine must NOT silently
 *      materialize a receiver at invoke time either).
 */
public class MainActivity extends Activity {

    /** Healthy class: clinit OK; k0 is owned by the P() factory. */
    public static class Lazy {
        public static Paint k0;               // NEVER assigned in <clinit>
        public static boolean guardEscaped;
        public static boolean factoryRan;
        public static boolean invoked;

        public static void P() {              // lazy factory (o6.P analogue)
            k0 = new Paint();
            factoryRan = true;
        }
        public static void k() {              // o6.k analogue (null sentinel)
            if (k0 != null) { guardEscaped = true; return; }
        }
    }

    /** Clinit throws midway (JVMS 5.5 → class is erroneous). */
    public static class Broken {
        public static int ok = 1;
        public static RectF rectTmp;          // declared after the throw point
        static {
            if (ok >= 0) throw new IllegalStateException("c106 mid-clinit abort");
            rectTmp = new RectF();            // never reached
        }
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);

        // ROW 1: null sentinel must hold on a HEALTHY class
        Lazy.k();
        System.err.println("[C106-SENTINEL] guardEscaped=" + Lazy.guardEscaped);

        // ROW 2: factory-first ordering (the AOSP-correct lifecycle)
        Lazy.P();
        Lazy.k();
        System.err.println("[C106-FACTORY] factoryRan=" + Lazy.factoryRan
                + " guardEscaped2=" + Lazy.guardEscaped);

        // ROW 3: throwing clinit → erroneous class (honest, no invention)
        String forNameRes, sgetRes;
        try {
            Class.forName("com.probe.c106a.MainActivity$Broken");
            forNameRes = "NO-EXC";
        } catch (Throwable t) {
            forNameRes = t.getClass().getSimpleName();
        }
        try {
            sgetRes = "nonnull=" + (Broken.rectTmp != null);
        } catch (Throwable t) {
            sgetRes = "sget-throw=" + t.getClass().getSimpleName();
        }
        System.err.println("[C106-CLINITFAIL] forName=" + forNameRes
                + " " + sgetRes);

        // ROW 4: unguarded invoke on a never-assigned static Paint
        String r4;
        try {
            Lazy.k0.setColor(0xFF00FF00);     // k0 is null again? NO — row 2
            r4 = "NO-EXC";
        } catch (NullPointerException e) {
            r4 = "NPE";
        }
        // NOTE: row 2 assigned k0 via the factory, so this row exercises the
        // REAL reference; the AOSP-parity negative for a NULL receiver is
        // covered by the second class below.
        System.err.println("[C106-INVOKE] result=" + r4);

        // ROW 5: unguarded invoke on a never-assigned static of a SECOND
        // healthy class (the true null-receiver negative).
        String r5;
        try {
            Never.k0b.setStrokeWidth(3f);
            r5 = "NO-EXC";
        } catch (NullPointerException e) {
            r5 = "NPE";
        }
        System.err.println("[C106-INVOKE2] result=" + r5);
    }

    /** Second healthy class: k0b never assigned anywhere. */
    public static class Never {
        public static Paint k0b;              // NEVER assigned
    }
}
