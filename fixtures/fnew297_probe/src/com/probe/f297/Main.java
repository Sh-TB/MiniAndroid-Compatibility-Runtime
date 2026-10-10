package com.probe.f297;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.text.StaticLayout;
import android.text.TextPaint;

import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-297 probe — COMPOSE DRAW-DISPATCH IDENTITY + LAYOUT.draw TEXT LAW.
 *
 * TWO coordinated generic points, one semantic family (the draw subtree):
 *
 * POINT 1 — RE-ENTRY IDENTITY (the M3-19/F-098/S122 family): the engine's
 * active-cycle stub keys re-entry on (class.method+descriptor, receiver,
 * FIRST 2 object args, first 2 primitives). composeStopwatch's R8'd
 * CanvasDrawScope (Loc0;.c(Ltf;JLmo0;Luv;Lt40;)V) is a REUSED dispatcher:
 * every nested subtree draw calls it with the SAME canvas/size/transform
 * payload and a DIFFERENT draw block (Lt40;, the 5th arg — BEYOND the
 * 2-object cap, excluded from the key). The nested call is therefore
 * stubbed as "same computation" and the whole subtree — including
 * TextPainter (Lg6;.d → Landroid/text/Layout;.draw) — silently vanishes
 * (observed: Lg6 executes ZERO times in the entire run; the draw walk
 * records only the outer subtree's roundrect/clip ops, ops=64, no text).
 *
 * POINT 2 — LAYOUT.draw TEXT LAW: the framework entry that paints Compose
 * paragraphs is android.text.Layout.draw(Canvas) (AndroidParagraph.paint →
 * layout.paint(nativeCanvas) → Layout.draw; R8'd caller Lg6;.d decodes as
 * save/clip/translate/layout.draw/restore). The engine had NO law for it —
 * a silent void — so even with point 1 fixed no DRAW_TEXT op reaches the
 * canvas op stream.
 *
 * Rows (all state-driven, emitted at the END of onDraw):
 *   F297|OUTER-EXEC    outer block ran                       (guard)
 *   F297|NESTED-EXEC   nested block ran — THE identity row
 *                      (pre-fix: stubbed, false; post-fix: true)
 *   F297|TEXT-CALLED   Canvas.drawText executed inside the
 *                      nested block (pre-fix dead with the block)
 *   F297|SL-BUILD      StaticLayout build non-null           (guard; the
 *                      ROOT-063 field-carrying layout)
 *   F297|SL-DRAW-VOID  layout.draw(canvas) completed normally (guard; the
 *                      point-2 call shape — the op itself is asserted
 *                      harness-side via the canvas op trace:
 *                      TEXT op carrying "F297-LAYOUT-TEXT")
 *   F297|SUMMARY       PASS iff all rows pass
 *
 * Harness discriminator (wave check script, cont30w_probe_pkg.sh precedent):
 *   MINIANDROID_CANVAS_OP_TRACE contains
 *   - a TEXT op with "F297-TEXT"        (point 1 live)
 *   - a TEXT op with "F297-LAYOUT-TEXT" (point 2 live)
 *
 * Hygiene: activity class "Main" carries no substring any name-gated
 * engine arm matches (CONT-32 find).
 */
public class Main extends Activity {
    static boolean outerRan = false, nestedRan = false, textCalled = false;
    static boolean slBuildOk = false, slDrawOk = false;
    static String slDetail = "";

    /** The reused draw dispatcher — the CanvasDrawScope shape: one
     *  instance, (canvas, packedSize, transform, layoutDir, block). */
    static class Scope {
        void draw(Canvas c, long packedSize, Object transform,
                  Object layoutDir, Runnable block) {
            block.run();
        }
    }

    static class DrawView extends View {
        Scope scope = new Scope();   // ONE reused dispatcher
        Paint tp = new Paint();
        boolean reported = false;
        DrawView(Context c) {
            super(c);
            tp.setColor(0xFFCC3333);
            tp.setTextSize(60f);
        }
        @Override protected void onDraw(Canvas cv) {
            cv.drawColor(0xFFFFFFFF);
            // outer-subtree primitive (records; proves the frame canvas)
            cv.drawRoundRect(40, 40, 400, 200, 20, 20, tp);

            final Object transform = new Object();
            final Object layoutDir = new Object();
            final long packed = 10801920L;

            // Outer subtree dispatch — call #1 of the key.
            scope.draw(cv, packed, transform, layoutDir, new Runnable() {
                public void run() {
                    outerRan = true;
                    // NESTED subtree dispatch — same receiver/canvas/
                    // transform payload, DIFFERENT block. Pre-fix the
                    // re-entry stub kills this call: the inner block
                    // (and the text draw it carries) never executes.
                    scope.draw(cv, packed, transform, layoutDir,
                            new Runnable() {
                        public void run() {
                            nestedRan = true;
                            cv.drawText("F297-TEXT", 60, 320, tp);
                            textCalled = true;
                        }
                    });
                }
            });

            // POINT 2 call shape — the Compose paragraph paint entry.
            // TextPaint carries the color the draw must reproduce; the
            // layout is the ROOT-063 field-carrying StaticLayout.
            try {
                TextPaint tp2 = new TextPaint();
                tp2.setColor(0xFF2244CC);
                tp2.setTextSize(72f);
                String s = "F297-LAYOUT-TEXT";
                StaticLayout sl = StaticLayout.Builder
                        .obtain(s, 0, s.length(), tp2, 400).build();
                slBuildOk = sl != null;
                if (sl != null) {
                    sl.draw(cv);
                    slDrawOk = true;
                    slDetail = "completed lines=" + sl.getLineCount();
                } else {
                    slDetail = "build returned null";
                }
            } catch (Throwable t) {
                slDetail = "threw " + t.getClass().getName();
            }

            if (!reported) {
                reported = true;
                report();
            }
        }
    }

    static TextView reportView;

    static synchronized void report() {
        List<String> out = new ArrayList<String>();
        int pass = 0, fail = 0;
        out.add("F297|OUTER-EXEC|" + (outerRan ? "PASS" : "FAIL")
                + "|outer block ran=" + outerRan);
        if (outerRan) pass++; else fail++;
        out.add("F297|NESTED-EXEC|" + (nestedRan ? "PASS" : "FAIL")
                + "|nested block ran=" + nestedRan + " (THE identity row)");
        if (nestedRan) pass++; else fail++;
        out.add("F297|TEXT-CALLED|" + (textCalled ? "PASS" : "FAIL")
                + "|nested Canvas.drawText executed=" + textCalled);
        if (textCalled) pass++; else fail++;
        out.add("F297|SL-BUILD|" + (slBuildOk ? "PASS" : "FAIL")
                + "|StaticLayout build non-null=" + slBuildOk);
        if (slBuildOk) pass++; else fail++;
        out.add("F297|SL-DRAW-VOID|" + (slDrawOk ? "PASS" : "FAIL")
                + "|layout.draw " + slDetail);
        if (slDrawOk) pass++; else fail++;
        out.add("F297|SUMMARY|" + (fail == 0 && pass >= 5 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail");
        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        reportView.setText(sb.toString());
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        DrawView dv = new DrawView(this);
        dv.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 600));
        reportView = new TextView(this);
        root.addView(dv);
        root.addView(reportView);
        setContentView(root);
    }
}
