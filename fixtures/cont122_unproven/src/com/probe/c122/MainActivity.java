package com.probe.c122;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.util.SparseArray;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileInputStream;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * CONT-122 UNPROVEN probe battery — one tiny app, sixteen probes, every
 * claim decided by LIVE behavior (never by inventory mentions).
 *
 * Rows probed (root_cause_registry UNPROVEN):
 *  U01 R-NEW-010  aput-object ArrayStoreException store-check (AOSP HandleAPutObject)
 *  U02 R-NEW-010b System.arraycopy component-type mismatch → ArrayStoreException
 *  U03 R-NEW-169  new-array absurd size → OutOfMemoryError (ART throw law)
 *  U04 R-NEW-282  Collections.singletonMap / unmodifiableMap / singletonList / emptyList
 *  U05 R-NEW-284  check-cast register preservation (null cast legal, receiver use after)
 *  U06 R-NEW-032  View.invalidate / postInvalidate / requestLayout exercised live
 *  U07 R-NEW-192  View.scrollTo / scrollBy / getScrollX / getScrollY
 *  U08 R-NEW-193  View.setTranslationX / setRotation / getMatrix / getTranslationX
 *  U09 R-NEW-097  IntentFilter.addAction / matchAction / getCategoryCount
 *  U10 R-NEW-283  Intent.setClassName / getComponent identity round-trip
 *  U11 R-NEW-161  /proc/self/cmdline passthrough in the app sandbox
 *  U12 R-NEW-083  PackageManager GET_SIGNATURES signature array
 *  U13 R-NEW-151  androidx FileProvider presence (Class.forName)
 *  U14 R-NEW-055  Bundle putSparseParcelableArray / getSparseParcelableArray round-trip
 *  U15 R-NEW-094  manifest exported flag parse via getActivityInfo
 *  U16 R-NEW-132  multi-dex enumeration: a class living in classes2.dex
 *
 * Every probe prints an honest C122- U## PASS/FAIL <detail> line; a probe
 * whose claim needs a CONFIRMED GAP prints FAIL with the observed behavior —
 * both outcomes are real evidence.
 */
public class MainActivity extends Activity {

    static int pass = 0, fail = 0;

    static void verdict(boolean ok, String id, String detail) {
        if (ok) { pass++; System.out.println("C122- " + id + " PASS " + detail); }
        else    { fail++; System.out.println("C122- " + id + " FAIL " + detail); }
    }

    // ── U01: aput-object store-check ────────────────────────────────────
    static boolean u01Raised = false;
    static void u01() {
        Object[] a = new String[3];
        try {
            a[0] = Integer.valueOf(7);   // wrong component type — MUST raise
            System.out.println("C122- U01-STORED no-exception value=" + a[0]);
        } catch (ArrayStoreException e) {
            u01Raised = true;
            System.out.println("C122- U01-RAISED " + e.getClass().getName());
        }
    }

    // ── U02: arraycopy component mismatch ───────────────────────────────
    static boolean u02Raised = false;
    static void u02() {
        Integer[] src = new Integer[] { 1, 2 };
        String[] dst = new String[2];
        try {
            System.arraycopy(src, 0, dst, 0, 2);
            System.out.println("C122- U02-COPIED no-exception dst0=" + dst[0]);
        } catch (ArrayStoreException e) {
            u02Raised = true;
            System.out.println("C122- U02-RAISED " + e.getClass().getName());
        }
    }

    // ── U03: absurd new-array → OutOfMemoryError ────────────────────────
    static boolean u03Raised = false;
    static int[] bigHolder;   // defeats ECJ dead-code elimination (the
                              // compiler folded away an unused allocation)
    static void u03() {
        try {
            bigHolder = new int[Integer.MAX_VALUE - 2];
            int n = bigHolder.length;
            System.out.println("C122- U03-ALLOCATED size=" + n);
        } catch (OutOfMemoryError e) {
            u03Raised = true;
            System.out.println("C122- U03-RAISED " + e.getClass().getName()
                + " msg=" + e.getMessage());
        } catch (NegativeArraySizeException e) {
            System.out.println("C122- U03-NEG " + e.getClass().getName());
        }
    }

    @Override public void onCreate(Bundle icicle) {
        super.onCreate(icicle);
        LinearLayout root = new LinearLayout(this);
        TextView tv = new TextView(this);
        tv.setText("c122-probe");
        root.addView(tv);
        setContentView(root);

        // U01 / U02 / U03 (static probes, engine-op level)
        u01(); u02(); u03();
        verdict(u01Raised, "U01", "aput-object String[]<-Integer raised ASE");
        verdict(u02Raised, "U02", "arraycopy Integer[]->String[] raised ASE");
        verdict(u03Raised, "U03", "new int[MAX-2] raised OutOfMemoryError");

        // U04: Collections singletons/unmodifiable
        try {
            Map<String, Integer> sm = Collections.singletonMap("k", 1);
            boolean ok = sm.size() == 1 && sm.get("k").intValue() == 1
                && sm.containsKey("k");
            Map<String, Integer> um = Collections.unmodifiableMap(new HashMap<String, Integer>());
            um.put("x", 2);   // in modifiable map first? no — um wraps empty map; skip mutation
            Map<String, Integer> um2 = Collections.unmodifiableMap(sm);
            boolean ok2 = um2.get("k").intValue() == 1;
            verdict(ok && ok2, "U04", "singletonMap+unmodifiableMap round-trip");
        } catch (Throwable t) {
            verdict(false, "U04", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        // U05: check-cast register preservation
        try {
            String s = null;
            Object o = s;
            String t = (String) o;           // null cast: legal, no NPE here
            boolean nullCastOk = (t == null);
            String real = "abc";
            Object o2 = real;
            String r2 = (String) o2;         // cast preserves the register
            verdict(nullCastOk && r2.length() == 3,
                "U05", "null-cast legal + cast preserves receiver");
        } catch (Throwable th) {
            verdict(false, "U05", "threw " + th.getClass().getName() + ": " + th.getMessage());
        }

        // U06: invalidate family exercised
        try {
            tv.invalidate();
            tv.postInvalidate();
            root.requestLayout();
            verdict(true, "U06", "invalidate+postInvalidate+requestLayout no-crash");
        } catch (Throwable t) {
            verdict(false, "U06", "threw " + t.getClass().getName());
        }

        // U07: scroll laws
        try {
            View sv = new View(this);
            sv.scrollTo(10, 20);
            int x = sv.getScrollX(), y = sv.getScrollY();
            sv.scrollBy(5, -5);
            int x2 = sv.getScrollX(), y2 = sv.getScrollY();
            verdict(x == 10 && y == 20 && x2 == 15 && y2 == 15,
                "U07", "scrollTo(10,20)=" + x + "," + y + " scrollBy→" + x2 + "," + y2);
        } catch (Throwable t) {
            verdict(false, "U07", "threw " + t.getClass().getName());
        }

        // U08: transform laws
        try {
            View mv = new View(this);
            mv.setTranslationX(5.0f);
            mv.setRotation(30.0f);
            float tx = mv.getTranslationX();
            boolean hasMatrix = mv.getMatrix() != null;
            verdict(tx == 5.0f && hasMatrix,
                "U08", "translationX=" + tx + " matrix=" + (hasMatrix ? "yes" : "null"));
        } catch (Throwable t) {
            verdict(false, "U08", "threw " + t.getClass().getName());
        }

        // U09: IntentFilter matching
        try {
            IntentFilter f = new IntentFilter("com.probe.c122.ACT");
            f.addCategory(Intent.CATEGORY_DEFAULT);
            boolean m = f.matchAction("com.probe.c122.ACT");
            boolean m2 = f.matchAction("com.probe.c122.NOPE");
            int cc = f.countCategories();
            verdict(m && !m2 && cc == 1,
                "U09", "matchAction true/false cats=" + cc);
        } catch (Throwable t) {
            verdict(false, "U09", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        // U10: intent component identity
        try {
            Intent in = new Intent();
            in.setClassName("com.probe.c122", "com.probe.c122.MainActivity");
            ComponentName cn = in.getComponent();
            boolean ok = cn != null
                && "com.probe.c122".equals(cn.getPackageName())
                && "com.probe.c122.MainActivity".equals(cn.getClassName());
            in.setComponent(new ComponentName("a.b", "a.b.C"));
            boolean ok2 = "a.b.C".equals(in.getComponent().getClassName());
            verdict(ok && ok2, "U10", "component round-trip identity");
        } catch (Throwable t) {
            verdict(false, "U10", "threw " + t.getClass().getName());
        }

        // U11: /proc passthrough
        try {
            File proc = new File("/proc/self/cmdline");
            boolean can = proc.canRead() && proc.exists();
            String head = "";
            if (can) {
                FileInputStream fis = new FileInputStream(proc);
                byte[] buf = new byte[64];
                int n = fis.read(buf);
                fis.close();
                if (n > 0) head = new String(buf, 0, n).trim();
            }
            System.out.println("C122- U11-DETAIL canRead=" + can + " head=" + head);
            verdict(can, "U11", "/proc/self/cmdline canRead=" + can);
        } catch (Throwable t) {
            verdict(false, "U11", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        // U12: package signatures
        try {
            android.content.pm.PackageInfo pi = getPackageManager()
                .getPackageInfo(getPackageName(), PackageManager.GET_SIGNATURES);
            int n = (pi.signatures != null) ? pi.signatures.length : -1;
            verdict(n >= 0, "U12", "GET_SIGNATURES signatures=" + n
                + (n > 0 ? " sig0len=" + pi.signatures[0].toCharsString().length() : ""));
        } catch (Throwable t) {
            verdict(false, "U12", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        // U13: FileProvider presence
        try {
            Class<?> fc = Class.forName("androidx.core.content.FileProvider");
            verdict(fc != null, "U13", "FileProvider resolvable: " + fc.getName());
        } catch (ClassNotFoundException cnfe) {
            verdict(false, "U13", "ClassNotFoundException androidx.core.content.FileProvider");
        } catch (Throwable t) {
            verdict(false, "U13", "threw " + t.getClass().getName());
        }

        // U14: Bundle sparse round-trip
        try {
            Bundle b = new Bundle();
            SparseArray<Bundle> sa = new SparseArray<Bundle>();
            Bundle inner = new Bundle();
            inner.putString("in", "v");
            sa.put(3, inner);
            b.putSparseParcelableArray("sa", sa);
            SparseArray<Bundle> out = b.getSparseParcelableArray("sa");
            boolean ok = out != null && out.size() == 1
                && out.get(3) != null && "v".equals(out.get(3).getString("in"));
            verdict(ok, "U14", "SparseArray<Bundle> round-trip");
        } catch (Throwable t) {
            verdict(false, "U14", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        // U15: exported flag parse
        try {
            ComponentName comp = new ComponentName(this, MainActivity.class);
            android.content.pm.ActivityInfo ai = getPackageManager()
                .getActivityInfo(comp, 0);
            System.out.println("C122- U15-DETAIL exported=" + ai.exported
                + " name=" + ai.name);
            verdict(ai.exported, "U15", "manifest exported parsed =" + ai.exported);
        } catch (Throwable t) {
            verdict(false, "U15", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        // U16: classes2.dex companion class (multi-dex enumeration)
        try {
            Class<?> c2 = Class.forName("com.probe.c122.Companion");
            Object inst = c2.newInstance();
            verdict(inst instanceof Companion2Marker, "U16",
                "classes2.dex Companion loaded: " + c2.getName());
        } catch (Throwable t) {
            verdict(false, "U16", "threw " + t.getClass().getName() + ": " + t.getMessage());
        }

        System.out.println("C122- VERDICT pass=" + pass + " fail=" + fail);
    }

    /** Marker interface resolved against the classes2.dex class. */
    public interface Companion2Marker {}
}
