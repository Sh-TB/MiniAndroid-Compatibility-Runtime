package com.probe.f291;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * F-NEW-291 probe — STRING.FORMAT LOCALE OVERLOAD LAW.
 *
 * DEX carries two String.format overloads discriminated by arg SHAPE:
 *   format(String, Object...)          → [fmt STRING_REF, Object[]]
 *   format(Locale, String, Object...)  → [Locale OBJECT_REF, fmt STRING_REF, Object[]]
 * AOSP java.lang.String.format(Locale l, String format, Object... args) is
 * specified as equivalent to new Formatter(l).format(format, args) — the
 * format string is ALWAYS args[1] in the Locale overload and the varargs
 * array is args[2]. The pre-fix bridge read args[0] (the Locale object) AS
 * the format string, answered "" for every Locale-overload call, and pushed
 * the real "%02d" + the array into the argument list (the
 * [EXP093-STRFMT] String.format("", n=2) → "" log face). Consumers like
 * composeStopwatch Lwv;.p — format(Locale.US, "%02d", millis%1000) then
 * substring(0, 2) — threw StringIndexOutOfBoundsException (length=0;
 * begin=0; end=2), the composition text pass died in catch-all churn, and
 * the frame stayed DEFAULT_BACKGROUND_ONLY.
 *
 * Discriminating scenario = the exact Lwv;.p shape plus the overload
 * contract edges, with the 2-arg overload as the regression arm:
 *
 *   FMT-LOC-D2     format(Locale.US, "%02d", 7L)   == "07"        (THE law)
 *   FMT-LOC-SUB    format(Locale.US, "%02d", 500L).substring(0, 2) == "50"
 *                  (the exact Lwv;.p consumer shape)
 *   FMT-LOC-2ARG   format(Locale.US, "%02d:%02d", 1L, 2L) == "01:02"
 *   FMT-LOC-S      format(Locale.US, "%s!", "x")   == "x!"
 *   FMT-LOC-DINT   format(Locale.US, "%d", 42)     == "42" (boxed Integer)
 *   FMT-NOLOC-D2   format("%02d", 7)               == "07"  (2-arg regression)
 *   FMT-NOLOC-ARR  format("%s-%s", new Object[]{"a","b"}) == "a-b"
 *   SUMMARY        PASS iff all rows pass
 *
 * Hygiene: activity class "Main" carries no substring that any name-gated
 * engine arm matches (the CONT-32 probe-hygiene find).
 */
public class Main extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F291|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    /** Runs one format call; records the actual value or the thrown type. */
    static String tryFmt(String id, String want, Runnable r) {
        try {
            r.run();
        } catch (Throwable t) {
            row(id, false, "threw " + t.getClass().getName()
                + " (" + t.getMessage() + ") want=" + want);
        }
        return null;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);

        // FMT-LOC-D2 — THE law row (Long boxed exactly like Lwv;.p's
        // Long.valueOf + Arrays.copyOf shape).
        try {
            long v = 7L;
            String s = String.format(Locale.US, "%02d", v);
            row("FMT-LOC-D2", "07".equals(s), "got=\"" + s + "\" want=07");
        } catch (Throwable t) {
            row("FMT-LOC-D2", false, "threw " + t.getClass().getName());
        }

        // FMT-LOC-SUB — the exact Lwv;.p consumer shape (pre-fix this threw
        // StringIndexOutOfBoundsException length=0).
        try {
            long millis = 70500L;
            String s = String.format(Locale.US, "%02d", millis % 1000L);
            String sub = s.substring(0, 2);
            row("FMT-LOC-SUB", "50".equals(sub),
                "got=\"" + sub + "\" want=50 (fmt=\"" + s + "\")");
        } catch (Throwable t) {
            row("FMT-LOC-SUB", false, "threw " + t.getClass().getName()
                + " (" + t.getMessage() + ")");
        }

        // FMT-LOC-2ARG — multi-arg Locale overload.
        try {
            String s = String.format(Locale.US, "%02d:%02d", 1L, 2L);
            row("FMT-LOC-2ARG", "01:02".equals(s),
                "got=\"" + s + "\" want=01:02");
        } catch (Throwable t) {
            row("FMT-LOC-2ARG", false, "threw " + t.getClass().getName());
        }

        // FMT-LOC-S — string conversion through the Locale overload.
        try {
            String s = String.format(Locale.US, "%s!", "x");
            row("FMT-LOC-S", "x!".equals(s), "got=\"" + s + "\" want=x!");
        } catch (Throwable t) {
            row("FMT-LOC-S", false, "threw " + t.getClass().getName());
        }

        // FMT-LOC-DINT — boxed Integer through the Locale overload.
        try {
            int n = 42;
            String s = String.format(Locale.US, "%d", n);
            row("FMT-LOC-DINT", "42".equals(s), "got=\"" + s + "\" want=42");
        } catch (Throwable t) {
            row("FMT-LOC-DINT", false, "threw " + t.getClass().getName());
        }

        // FMT-NOLOC-D2 — the 2-arg overload must stay intact (regression arm;
        // PASSED pre-fix and must keep passing).
        try {
            String s = String.format("%02d", 7);
            row("FMT-NOLOC-D2", "07".equals(s), "got=\"" + s + "\" want=07");
        } catch (Throwable t) {
            row("FMT-NOLOC-D2", false, "threw " + t.getClass().getName());
        }

        // FMT-NOLOC-ARR — explicit array through the 2-arg overload.
        try {
            String s = String.format("%s-%s", new Object[]{"a", "b"});
            row("FMT-NOLOC-ARR", "a-b".equals(s), "got=\"" + s + "\" want=a-b");
        } catch (Throwable t) {
            row("FMT-NOLOC-ARR", false, "threw " + t.getClass().getName());
        }

        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F291|SUMMARY|"
                + (fail == 0 && pass >= 7 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f291_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
