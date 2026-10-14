package com.probe.f295;

import android.app.Activity;
import android.os.Bundle;
import android.text.Layout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-295 probe — FRAMEWORK ENUM values()/valueOf() TABLE LAW
 * (android.text.Layout$Alignment).
 *
 * The 371-CLOSEOUT wave added the generic framework-enum static-accessor
 * law: values()/valueOf() enumerate the kOrdinals table rows for the class
 * (same table the sget constant law uses → identity coherent). The law is
 * GENERIC but table-driven — an enum class with NO rows still answers NULL
 * for values(), and every consumer of the enumeration then dies on the
 * null array. The reproducing consumer is composeStopwatch's R8-inlined
 * text-layout alignment resolver (Ljd1;.<clinit>, androidx Compose
 * ui-text): it calls Layout.Alignment.values(), searches the array for
 * "ALIGN_LEFT"/"ALIGN_RIGHT" names (API-26-era members that do NOT exist
 * on the toolchain's API level — the AOSP android-34.jar clinit decodes
 * exactly three constants: ALIGN_NORMAL=0, ALIGN_OPPOSITE=1,
 * ALIGN_CENTER=2) and falls back to the ALIGN_NORMAL sget. Pre-fix the
 * values() arm answered NULL → "Attempt to get length of null array" at
 * Ljd1;.<clinit> pc=6 → uncaught, aborting the text pass.
 *
 * Rows:
 *   LA-VALUES-SIZE   Layout.Alignment.values().length == 3
 *   LA-VALUES-ORDER  values()[0..2].name() == ALIGN_NORMAL/ALIGN_OPPOSITE/
 *                    ALIGN_CENTER (the decoded AOSP declaration order)
 *   LA-VALUES-ITER   the exact Ljd1;.<clinit> consumer shape: iterate
 *                    values() searching ALIGN_LEFT/ALIGN_RIGHT, fall back
 *                    to ALIGN_NORMAL (pre-fix: NPE at the array-length)
 *   LA-SGET          Layout.Alignment.ALIGN_NORMAL != null and identity
 *                    with values()[0] (sget law coherence)
 *   LA-VALUEOF       Layout.Alignment.valueOf("ALIGN_CENTER") == the
 *                    values()[2] constant (valueOf law)
 *   LA-VALUEOF-NEG   valueOf("NO_SUCH") throws IllegalArgumentException
 *                    (j.l.Enum.valueOf law, honest negative arm)
 *   SUMMARY          PASS iff all rows pass
 *
 * Hygiene: activity class "Main" carries no substring that any name-gated
 * engine arm matches (the CONT-32 probe-hygiene find).
 */
public class Main extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F295|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);

        // LA-VALUES-SIZE — the enumeration itself (pre-fix: NPE "Attempt
        // to get length of null array" at the array-length).
        try {
            Layout.Alignment[] vs = Layout.Alignment.values();
            row("LA-VALUES-SIZE", vs != null && vs.length == 3,
                "len=" + (vs == null ? "null-arr" : vs.length) + " want=3");
        } catch (Throwable t) {
            row("LA-VALUES-SIZE", false,
                "threw " + t.getClass().getName() + " (" + t.getMessage() + ")");
        }

        // LA-VALUES-ORDER — the decoded AOSP declaration order.
        try {
            Layout.Alignment[] vs = Layout.Alignment.values();
            boolean ok = vs.length == 3
                && "ALIGN_NORMAL".equals(vs[0].name())
                && "ALIGN_OPPOSITE".equals(vs[1].name())
                && "ALIGN_CENTER".equals(vs[2].name());
            row("LA-VALUES-ORDER", ok,
                "got=" + (ok ? "NORMAL,OPPOSITE,CENTER" : vs[0].name() + ","
                    + vs[1].name() + "," + vs[2].name()));
        } catch (Throwable t) {
            row("LA-VALUES-ORDER", false,
                "threw " + t.getClass().getName());
        }

        // LA-VALUES-ITER — the EXACT Ljd1;.<clinit> consumer shape:
        // scan for ALIGN_LEFT/ALIGN_RIGHT (absent on this API level), fall
        // back to ALIGN_NORMAL.
        try {
            Layout.Alignment left = Layout.Alignment.ALIGN_NORMAL;
            Layout.Alignment right = Layout.Alignment.ALIGN_NORMAL;
            for (Layout.Alignment v : Layout.Alignment.values()) {
                if ("ALIGN_LEFT".equals(v.name())) left = v;
                else if ("ALIGN_RIGHT".equals(v.name())) right = v;
            }
            row("LA-VALUES-ITER",
                left == Layout.Alignment.ALIGN_NORMAL
                    && right == Layout.Alignment.ALIGN_NORMAL,
                "fallback-law holds=" + (left == right));
        } catch (Throwable t) {
            row("LA-VALUES-ITER", false,
                "threw " + t.getClass().getName() + " (" + t.getMessage() + ")");
        }

        // LA-SGET — the constant the clinit falls back to; identity with
        // the values() enumeration element (same-table coherence).
        try {
            Layout.Alignment s = Layout.Alignment.ALIGN_NORMAL;
            Layout.Alignment v0 = Layout.Alignment.values()[0];
            row("LA-SGET", s != null && s == v0,
                "sget-nonnull=" + (s != null) + " identity=" + (s == v0));
        } catch (Throwable t) {
            row("LA-SGET", false, "threw " + t.getClass().getName());
        }

        // LA-VALUEOF — valueOf returns the same constant object.
        try {
            Layout.Alignment c = Layout.Alignment.valueOf("ALIGN_CENTER");
            row("LA-VALUEOF",
                c != null && c == Layout.Alignment.values()[2],
                "identity=" + (c == Layout.Alignment.values()[2]));
        } catch (Throwable t) {
            row("LA-VALUEOF", false, "threw " + t.getClass().getName());
        }

        // LA-VALUEOF-NEG — unknown name must throw (j.l.Enum.valueOf law).
        try {
            Layout.Alignment.valueOf("NO_SUCH_ALIGNMENT");
            row("LA-VALUEOF-NEG", false, "no exception (want IAE)");
        } catch (IllegalArgumentException e) {
            row("LA-VALUEOF-NEG", true, "IAE as specified");
        } catch (Throwable t) {
            row("LA-VALUEOF-NEG", false,
                "threw " + t.getClass().getName() + " (want IAE)");
        }

        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F295|SUMMARY|"
                + (fail == 0 && pass >= 6 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f295_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
