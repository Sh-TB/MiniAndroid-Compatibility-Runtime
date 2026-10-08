package com.probe.f268;

import android.app.Activity;
import android.os.Bundle;
import java.util.regex.Pattern;

/**
 * CONT-18g — F-NEW-268/269 EXCEPTION-SEMANTICS PROBE (issue #381 claims sweep).
 * One row = one #381 face + its ART/JDK law. Each row lives in its OWN method
 * (own frame + try table) so a failure cannot cross-contaminate the next row.
 * Catch handlers use instanceof only (no exception-object method dispatch).
 *
 *   A  new-array negative size  -> NegativeArraySizeException (ART law)
 *   B  aget on CONFIRMED zero-length array -> AIOOBE (recorded len == 0)
 *   C  aget on null array       -> NPE (AOSP HandleAGet; aput had it, aget didn't)
 *   D  aput on CONFIRMED zero-length array -> AIOOBE (mirror of B)
 *   E  iget on null receiver    -> NPE at the access (ART law)
 *   F  aget in-bounds control   -> returns values
 *   G  aput in-bounds control   -> stores
 *   H  split("a,b,,") trailing empties removed (JDK split = limit 0)
 *   I  split("ab", "") per-char zero-length-match law
 *   J  split with Pattern.quote(".") literal delimiter law
 *   K  split("a,b") control
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    private int probeField = 7;

    // F-268 probe: null sources the compiler CANNOT fold (ECJ folds a
    // provable-null dereference into `athrow` of the null itself — that
    // became face L). All nulls reach the opcode through this blackhole.
    private static int[] blackholeArray;
    private static MainActivity blackholeThis;
    private static RuntimeException blackholeRt;

    private static int[] nullArray() { return blackholeArray; }

    private static MainActivity nullThis() { return blackholeThis; }

    private static RuntimeException nullRt() { return blackholeRt; }

    private static void rowA() {
        try {
            int n = -3;
            int[] a = new int[n];
            row("F268-A", false, "no-exception len=" + a.length);
        } catch (Throwable t) {
            boolean nase = t instanceof NegativeArraySizeException;
            row("F268-A", nase, "nase=" + nase);
        }
    }

    private static void rowB() {
        try {
            int[] a = new int[0];
            int v = a[0];
            row("F268-B", false, "no-exception v=" + v);
        } catch (Throwable t) {
            boolean oob = t instanceof ArrayIndexOutOfBoundsException;
            row("F268-B", oob, "aioobe=" + oob);
        }
    }

    private static void rowC() {
        try {
            int[] a = nullArray();
            int v = a[0];
            row("F268-C", false, "no-exception v=" + v);
        } catch (Throwable t) {
            boolean npe = t instanceof NullPointerException;
            row("F268-C", npe, "npe=" + npe);
        }
    }

    private static void rowD() {
        try {
            int[] a = new int[0];
            a[0] = 5;
            row("F268-D", false, "no-exception len=" + a.length);
        } catch (Throwable t) {
            boolean oob = t instanceof ArrayIndexOutOfBoundsException;
            row("F268-D", oob, "aioobe=" + oob);
        }
    }

    private static void rowE() {
        try {
            MainActivity o = nullThis();
            int v = o.probeField;   // probeField is an INSTANCE field here
            row("F268-E", false, "no-exception v=" + v);
        } catch (Throwable t) {
            boolean npe = t instanceof NullPointerException;
            row("F268-E", npe, "npe=" + npe);
        }
    }

    private static void rowF() {
        try {
            int[] a = new int[3];
            a[1] = 5;
            int v = a[1];
            row("F268-F", v == 5, "v=" + v);
        } catch (Throwable t) {
            row("F268-F", false, "unexpected-exception");
        }
    }

    private static void rowG() {
        try {
            int[] a = new int[3];
            a[2] = 9;
            row("F268-G", a[2] == 9, "a2=" + a[2]);
        } catch (Throwable t) {
            row("F268-G", false, "unexpected-exception");
        }
    }

    private static void rowH() {
        try {
            String[] p = "a,b,,".split(",");
            boolean ok = p.length == 2 && "a".equals(p[0]) && "b".equals(p[1]);
            row("F268-H", ok, "len=" + p.length);
        } catch (Throwable t) {
            row("F268-H", false, "unexpected-exception");
        }
    }

    private static void rowI() {
        try {
            String[] p = "ab".split("");
            boolean ok = p.length == 2 && "a".equals(p[0]) && "b".equals(p[1]);
            row("F268-I", ok, "len=" + p.length);
        } catch (Throwable t) {
            row("F268-I", false, "unexpected-exception");
        }
    }

    private static void rowJ() {
        try {
            String[] p = "x.y".split(Pattern.quote("."));
            boolean ok = p.length == 2 && "x".equals(p[0]) && "y".equals(p[1]);
            row("F268-J", ok, "len=" + p.length);
        } catch (Throwable t) {
            row("F268-J", false, "unexpected-exception");
        }
    }

    private static void rowK() {
        try {
            String[] p = "a,b".split(",");
            boolean ok = p.length == 2 && "a".equals(p[0]) && "b".equals(p[1]);
            row("F268-K", ok, "len=" + p.length);
        } catch (Throwable t) {
            row("F268-K", false, "unexpected-exception");
        }
    }

    private static void rowL() {
        // JLS 14.18: `throw null` throws NullPointerException.
        try {
            RuntimeException e = nullRt();
            throw e;
        } catch (Throwable t) {
            boolean npe = t instanceof NullPointerException;
            row("F268-L", npe, "npe=" + npe);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        rowA();
        rowB();
        rowC();
        rowD();
        rowE();
        rowF();
        rowG();
        rowH();
        rowI();
        rowJ();
        rowK();
        rowL();

        android.widget.TextView tv = new android.widget.TextView(this);
        tv.setText(report);
        android.widget.LinearLayout ll = new android.widget.LinearLayout(this);
        ll.addView(tv);
        setContentView(ll);
        System.out.println(report);
    }
}
