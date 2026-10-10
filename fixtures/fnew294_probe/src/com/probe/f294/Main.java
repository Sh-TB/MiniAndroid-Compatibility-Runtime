package com.probe.f294;

import android.app.Activity;
import android.graphics.Typeface;
import android.os.Bundle;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-294 probe — AOSP TYPEFACE STATIC-CONSTANT / CREATE LAW.
 *
 * AOSP frameworks/base/graphics/java/android/graphics/Typeface.java:
 *   public static final Typeface DEFAULT       = create((String) null, 0);
 *   public static final Typeface DEFAULT_BOLD  = create((String) null, BOLD);
 *   public static final Typeface SANS_SERIF    = create("sans-serif", 0);
 *   public static final Typeface SERIF         = create("serif", 0);
 *   public static final Typeface MONOSPACE     = create("monospace", 0);
 * and create(familyName, style) / create(family, style) /
 * create(family, weight, italic) (API 28+) / defaultFromStyle(style) are
 * specified to NEVER return null — an unknown or null family falls back to
 * the default family. The pre-fix engine had NO Typeface law at all:
 * sget-object Typeface.DEFAULT hit [SGET-MISS] and answered NULL, and every
 * create/defaultFromStyle static fell to the typed-default stub (also NULL).
 *
 * The reproducing consumer is composeStopwatch's R8-inlined font resolution
 * (Lk6;.<init> = AndroidParagraphIntrinsics): FontListFontFamilyTypeface
 * Adapter.resolve wraps the platform typeface into TypefaceResult(value,
 * immediate) — Luh1;(e=Object, f=Z) — and the consumer does the Kotlin
 * platform-type null check `value!!` compiled as invoke-virtual getClass()
 * BEFORE check-cast Typeface (Lk6;.<init> pc=409). With a NULL DEFAULT the
 * result value is null → NPE "getClass on a null object reference" → the
 * text pass churns and the Compose stopwatch view (Lh4;) stays ops=0.
 *
 * Rows (no identity contracts beyond same-request stability — not part of
 * the documented API; the load-bearing law is NON-NULL):
 *
 *   TF-DEFAULT        Typeface.DEFAULT != null                      (THE row)
 *   TF-CONST-FAMILY   DEFAULT_BOLD/SANS_SERIF/SERIF/MONOSPACE all non-null
 *   TF-CONSUMER-SHAPE wrapper(e=DEFAULT).e.getClass() then cast — the exact
 *                     Lk6;.<init> pc=409 Kotlin !! shape (NPE pre-fix)
 *   TF-CREATE-STR     create("no-such-family-probe", 1) != null
 *   TF-CREATE-NULLFAM create((String) null, 0) != null
 *   TF-CREATE-EMPTY   create("", 0) != null  (the Lzv;.k empty-name arm)
 *   TF-CREATE-TF      create(Typeface.DEFAULT, 2) != null
 *   TF-CREATE-3ARG    create(Typeface.DEFAULT, 400, false) != null
 *                     (the androidx Ly0;.b shape, API 28+ overload)
 *   TF-DFS            defaultFromStyle(1) != null
 *   TF-CREATE-IDEM    create("sans-serif", 0) == create("sans-serif", 0)
 *                     (same-request stability inside one process)
 *   SUMMARY           PASS iff all rows pass
 *
 * Hygiene: activity class "Main" carries no substring that any name-gated
 * engine arm matches (the CONT-32 probe-hygiene find).
 */
public class Main extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F294|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    /** TypefaceResult shape: Luh1;(e=Object value, f=immediate). */
    static class Res { Object e; boolean f; }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);

        // TF-DEFAULT — THE law row (the exact [SGET-MISS] site).
        try {
            Typeface d = Typeface.DEFAULT;
            row("TF-DEFAULT", d != null,
                "got=" + (d == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-DEFAULT", false, "threw " + t.getClass().getName());
        }

        // TF-CONST-FAMILY — the whole documented constant family non-null.
        try {
            Typeface[] cs = { Typeface.DEFAULT_BOLD, Typeface.SANS_SERIF,
                              Typeface.SERIF, Typeface.MONOSPACE };
            boolean all = true;
            for (Typeface c : cs) if (c == null) all = false;
            row("TF-CONST-FAMILY", all,
                "DEFAULT_BOLD/SANS_SERIF/SERIF/MONOSPACE non-null=" + all);
        } catch (Throwable t) {
            row("TF-CONST-FAMILY", false, "threw " + t.getClass().getName());
        }

        // TF-CONSUMER-SHAPE — the exact Lk6;.<init> pc=409 Kotlin !!
        // shape: read the result's Object value, getClass() on it, then
        // check-cast to Typeface. Pre-fix the DEFAULT sget feeds null into
        // the wrapper and getClass() throws the recorded NPE.
        try {
            Res r = new Res();
            r.e = Typeface.DEFAULT;   // resolve() wraps the platform typeface
            r.f = true;               // immediate
            Object v = r.e;
            Class<?> cls = v.getClass();        // pc=409 twin — NPE pre-fix
            Typeface tf = (Typeface) v;         // check-cast twin
            row("TF-CONSUMER-SHAPE", tf != null && cls != null,
                "getClass=" + cls.getName() + " cast-ok=" + (tf != null));
        } catch (Throwable t) {
            row("TF-CONSUMER-SHAPE", false,
                "threw " + t.getClass().getName() + " (" + t.getMessage() + ")");
        }

        // TF-CREATE-STR — unknown family: AOSP falls back, never null.
        try {
            Typeface t = Typeface.create("no-such-family-probe", 1);
            row("TF-CREATE-STR", t != null,
                "got=" + (t == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-CREATE-STR", false, "threw " + t.getClass().getName());
        }

        // TF-CREATE-NULLFAM — null family: AOSP create(null, style) is the
        // DEFAULT initializer path itself; never null.
        try {
            Typeface t = Typeface.create((String) null, 0);
            row("TF-CREATE-NULLFAM", t != null,
                "got=" + (t == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-CREATE-NULLFAM", false, "threw " + t.getClass().getName());
        }

        // TF-CREATE-EMPTY — the Lzv;.k empty-name arm shape.
        try {
            Typeface t = Typeface.create("", 0);
            row("TF-CREATE-EMPTY", t != null,
                "got=" + (t == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-CREATE-EMPTY", false, "threw " + t.getClass().getName());
        }

        // TF-CREATE-TF — create(Typeface, style).
        try {
            Typeface t = Typeface.create(Typeface.DEFAULT, 2);
            row("TF-CREATE-TF", t != null,
                "got=" + (t == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-CREATE-TF", false, "threw " + t.getClass().getName());
        }

        // TF-CREATE-3ARG — create(Typeface, weight, italic) (API 28+), the
        // androidx Ly0;.b shape the resolver's weight path calls.
        try {
            Typeface t = Typeface.create(Typeface.DEFAULT, 400, false);
            row("TF-CREATE-3ARG", t != null,
                "got=" + (t == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-CREATE-3ARG", false, "threw " + t.getClass().getName());
        }

        // TF-DFS — defaultFromStyle.
        try {
            Typeface t = Typeface.defaultFromStyle(1);
            row("TF-DFS", t != null,
                "got=" + (t == null ? "null" : "Typeface obj"));
        } catch (Throwable t) {
            row("TF-DFS", false, "threw " + t.getClass().getName());
        }

        // TF-CREATE-IDEM — same request twice in one process: stable object
        // (AOSP caches created typefaces; identity for identical requests).
        try {
            Typeface a = Typeface.create("sans-serif", 0);
            Typeface c = Typeface.create("sans-serif", 0);
            row("TF-CREATE-IDEM", a != null && a == c,
                "same-instance=" + (a == c));
        } catch (Throwable t) {
            row("TF-CREATE-IDEM", false, "threw " + t.getClass().getName());
        }

        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F294|SUMMARY|"
                + (fail == 0 && pass >= 10 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f294_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
