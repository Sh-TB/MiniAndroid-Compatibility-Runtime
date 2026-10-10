package com.probe.f296;

import android.app.Activity;
import android.graphics.text.LineBreakConfig;
import android.os.Bundle;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-296 probe — AOSP LINEBREAKCONFIG BUILDER OBJECT LAW (API 33+).
 *
 * AOSP frameworks/base/graphics/java/android/graphics/text/LineBreakConfig
 * .java: Builder() constructs a mutable builder with the AOSP defaults
 * (LINE_BREAK_STYLE_NONE=0, LINE_BREAK_WORD_STYLE_NONE=0);
 * setLineBreakStyle(int)/setLineBreakWordStyle(int) are FLUENT (return
 * this, declared @NonNull); build() returns a non-null LineBreakConfig.
 * The Compose text pipeline (R8'd into Llw;.i / Lb1; in composeStopwatch)
 * gates on SDK >= 33 and runs
 *   new LineBreakConfig$Builder().setLineBreakStyle(s)
 *       .setLineBreakWordStyle(w).build()
 * then applies it to the StaticLayout Builder. With no ctor law the
 * engine's new-instance answered NULL and the first fluent setter NPE'd
 * ("setLineBreakWordStyle on a null object reference", Lb1;.n pc=0) —
 * the recorded post-F-NEW-295 face.
 *
 * Rows:
 *   LBC-CHAIN     the EXACT Llw;.i shape: new Builder().setLineBreakStyle
 *                 (0).setLineBreakWordStyle(0).build() != null (pre-fix:
 *                 NPE at the first setter)
 *   LBC-BUILD     build() returns a non-null LineBreakConfig
 *   LBC-FLUENT    each setter returns the SAME builder instance (AOSP
 *                 fluent law; the whole chain is identity-welded)
 *   LBC-CONSTS    LINE_BREAK_STYLE_NONE == 0 and
 *                 LINE_BREAK_WORD_STYLE_NONE == 0 (the AOSP constants the
 *                 app's SDK-gated defaults compare against)
 *   LBC-NEG       a fresh Builder is NOT the same object as a second one
 *                 (per-instance state law; no hidden singleton)
 *   SUMMARY       PASS iff all rows pass
 *
 * Hygiene: activity class "Main" carries no substring that any name-gated
 * engine arm matches (the CONT-32 probe-hygiene find).
 */
public class Main extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F296|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);

        // LBC-CHAIN — THE law row: the exact Llw;.i consumer shape.
        // Pre-fix this threw NPE at the FIRST fluent setter (the builder
        // itself was null), recorded at Lb1;.n pc=0.
        try {
            LineBreakConfig cfg = new LineBreakConfig.Builder()
                    .setLineBreakStyle(LineBreakConfig.LINE_BREAK_STYLE_NONE)
                    .setLineBreakWordStyle(
                        LineBreakConfig.LINE_BREAK_WORD_STYLE_NONE)
                    .build();
            row("LBC-CHAIN", cfg != null,
                "got=" + (cfg == null ? "null" : "LineBreakConfig obj"));
        } catch (Throwable t) {
            row("LBC-CHAIN", false,
                "threw " + t.getClass().getName() + " (" + t.getMessage() + ")");
        }

        // LBC-BUILD — build() non-null.
        try {
            LineBreakConfig cfg = new LineBreakConfig.Builder().build();
            row("LBC-BUILD", cfg != null,
                "got=" + (cfg == null ? "null" : "LineBreakConfig obj"));
        } catch (Throwable t) {
            row("LBC-BUILD", false, "threw " + t.getClass().getName());
        }

        // LBC-FLUENT — setters return THIS (the identity-welded chain).
        try {
            LineBreakConfig.Builder fb = new LineBreakConfig.Builder();
            LineBreakConfig.Builder fb1 = fb.setLineBreakStyle(0);
            LineBreakConfig.Builder fb2 = fb1.setLineBreakWordStyle(0);
            row("LBC-FLUENT", fb == fb1 && fb1 == fb2,
                "identity-welded=" + (fb == fb1 && fb1 == fb2));
        } catch (Throwable t) {
            row("LBC-FLUENT", false,
                "threw " + t.getClass().getName() + " (" + t.getMessage() + ")");
        }

        // LBC-CONSTS — the AOSP defaults the pipeline compares against.
        try {
            boolean ok = LineBreakConfig.LINE_BREAK_STYLE_NONE == 0
                && LineBreakConfig.LINE_BREAK_WORD_STYLE_NONE == 0;
            row("LBC-CONSTS", ok,
                "STYLE_NONE=0:" + (LineBreakConfig.LINE_BREAK_STYLE_NONE == 0)
                + " WORD_STYLE_NONE=0:"
                + (LineBreakConfig.LINE_BREAK_WORD_STYLE_NONE == 0));
        } catch (Throwable t) {
            row("LBC-CONSTS", false, "threw " + t.getClass().getName());
        }

        // LBC-NEG — two Builders are distinct objects (per-instance state).
        try {
            LineBreakConfig.Builder a = new LineBreakConfig.Builder();
            LineBreakConfig.Builder c = new LineBreakConfig.Builder();
            row("LBC-NEG", a != null && a != c,
                "distinct=" + (a != c));
        } catch (Throwable t) {
            row("LBC-NEG", false, "threw " + t.getClass().getName());
        }

        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F296|SUMMARY|"
                + (fail == 0 && pass >= 5 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f296_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
