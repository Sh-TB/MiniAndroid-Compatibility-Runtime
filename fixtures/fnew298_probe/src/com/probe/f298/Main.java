package com.probe.f298;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-298 probe — FRAME-HONESTY LAW (the P1-6 extension, CONT-36 §6
 * recorded PENDING): an in-draw F084 budget halt means the app's frame
 * NEVER COMPLETED — under ART/SurfaceFlinger an unfinished frame is never
 * presented; the display keeps the LAST COMPLETE frame.
 *
 * Shape: a custom View whose FIRST onDraw paints the whole canvas GREEN
 * (the marker frame) and completes; whose SECOND onDraw enters a long DEX
 * busy loop that cannot finish before the engine's wall-clock budget — the
 * interpreter halts mid-draw (F084), the draw window unwinds with 0 extra
 * ops, and the frame never completes.
 *
 * Pre-law face (the wipe): the compositor clears the framebuffer with the
 * window background EVERY frame and presents the result — frame 2's
 * background erase DESTROYS frame 1's green marker; the final screenshot
 * is the bare theme background (the exact face that hid composeStopwatch's
 * cards+text behind the (13,15,18) fill and dooz's boot content behind the
 * (250,250,250) fill).
 *
 * Post-law: the presentation is SKIPPED for the halted frame ([F298-KEEP]);
 * the framebuffer_ keeps frame 1 — the final screenshot is GREEN.
 *
 * Rows (in-log, state-driven):
 *   F298|F1-DRAWN      first onDraw completed with the green fill (guard)
 *   F298|F2-ENTERED    second onDraw entered the busy loop (guard)
 *   F298|SUMMARY       PASS iff both guards
 * Harness discriminator (runner-side, cont30w_probe_pkg.sh precedent):
 *   the FINAL screenshot's top-left 8x8 block is the frame-1 green
 *   0xFF00FF00 — emitted as "F298|KEEP-CORNER|PASS|..." appended to the
 *   run log by the runner after a pixel readback.
 *
 * Hygiene: activity class "Main" carries no substring any name-gated
 * engine arm matches (CONT-32 find).
 */
public class Main extends Activity {
    static boolean f1Drawn = false, f2Entered = false;
    static long busySink = 0;
    static boolean reported = false;

    static class BusyView extends View {
        Paint tp = new Paint();
        int onDrawCalls = 0;
        BusyView(Context c) { super(c); }
        @Override protected void onDraw(Canvas cv) {
            onDrawCalls++;
            if (onDrawCalls == 1) {
                // FRAME 1 — the marker frame: full-canvas green, completes.
                cv.drawColor(0xFF00FF00);
                f1Drawn = true;
                return;
            }
            // FRAME 2+ — the never-completing frame: a DEX busy loop far
            // beyond the interpreter's per-frame loop guard. The guard
            // halts mid-loop; the draw window unwinds with 0 extra ops.
            // Pre-law the compositor presents the wiped background;
            // post-law the presentation is skipped and frame 1 survives.
            f2Entered = true;
            report();
            long acc = 0;
            final long N = 2000000000L;
            for (long i = 0; i < N; i++) {
                acc += i;
                if (acc == -123456789012345L) busySink = acc; // never true
            }
            busySink = acc; // unreachable within the budget
        }
    }

    static TextView reportView;

    static synchronized void report() {
        if (reported) return;
        reported = true;
        List<String> out = new ArrayList<String>();
        int pass = 0, fail = 0;
        out.add("F298|F1-DRAWN|" + (f1Drawn ? "PASS" : "FAIL")
                + "|first onDraw completed with the green fill=" + f1Drawn);
        if (f1Drawn) pass++; else fail++;
        out.add("F298|F2-ENTERED|" + (f2Entered ? "PASS" : "FAIL")
                + "|second onDraw entered the busy loop=" + f2Entered);
        if (f2Entered) pass++; else fail++;
        out.add("F298|SUMMARY|" + (fail == 0 && pass >= 2 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail"
                + " (the KEEP-CORNER pixel row is runner-side)");
        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        reportView.setText(sb.toString());
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        BusyView bv = new BusyView(this);
        bv.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT));
        reportView = new TextView(this);
        root.addView(bv);
        root.addView(reportView);
        setContentView(root);
    }
}
