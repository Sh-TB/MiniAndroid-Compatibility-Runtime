package com.probe.fclk;

import android.app.Activity;
import android.os.Bundle;
import android.view.Choreographer;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-40 Phase-4 discriminating probe — the Compose frame-clock loop and
 * the View.getWindowToken contract, replicated as real plain-Java DEX
 * (real aapt2/ECJ/D8 toolchain; no Compose classes needed). Every row is a
 * generic platform contract.
 *
 * FC-01..04 + FC-06: the Choreographer frame-pump loop — the exact law the
 * Compose AndroidUiFrameClock (withFrameNanos) rides (F-050): getInstance
 * identity, registration → delivery with the virtual vsync, the
 * RE-REGISTRATION loop (doFrame re-posts itself — the composition loop
 * shape), state mutation across frames, and cancellation.
 *
 * FC-05: View.getWindowToken — null before attach, non-null and identity-
 * stable after attach, ONE token per window (two views share it). This is
 * the friend-claim audit row: AbstractComposeView stores it raw with zero
 * null-gates (DEX-decoded Lr;->c), so null cannot gate composition.
 *
 * FC-07: the visible-render control (white on black, runner-side pixels).
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static synchronized void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    private static TextView tv;
    private static long firstFrameNanos = -1;
    private static long[] frameTimes = new long[8];
    private static int loopDeliveries = 0;
    private static int stateAcrossFrames = 0;
    private static int removedCbFired = 0;
    private static Choreographer choreo;

    private static void refresh() {
        if (tv != null) {
            tv.setText("FCLKPROBE " + countPass() + "/" + countTotal() + "\n" + report);
        }
    }

    private static synchronized int countPass() {
        int p = 0;
        for (String line : report.split("\n"))
            if (line.contains("|PASS|")) p++;
        return p;
    }

    private static synchronized int countTotal() {
        int t = 0;
        for (String line : report.split("\n"))
            if (line.contains("|PASS|") || line.contains("|FAIL|")) t++;
        return t;
    }

    // ── the re-registration loop callback (the Compose frame-loop shape) ──
    private static final class LoopCallback implements Choreographer.FrameCallback {
        public void doFrame(long frameTimeNanos) {
            loopDeliveries++;
            stateAcrossFrames += loopDeliveries;  // mutation each frame
            if (loopDeliveries <= frameTimes.length)
                frameTimes[loopDeliveries - 1] = frameTimeNanos;
            if (loopDeliveries == 1) {
                firstFrameNanos = frameTimeNanos;
                row("FC-02", frameTimeNanos >= 1000000000L,
                    "first doFrame frameTimeNanos=" + frameTimeNanos
                    + " (virtual base 1e9)");
            }
            if (loopDeliveries < 3) {
                choreo.postFrameCallback(this);   // the re-registration law
            } else {
                // final delivery: evaluate the loop + cancellation rows
                boolean mono = frameTimes[1] > frameTimes[0]
                    && frameTimes[2] > frameTimes[1];
                long q01 = frameTimes[1] - frameTimes[0];
                long q12 = frameTimes[2] - frameTimes[1];
                row("FC-03", mono && q01 == 16666667L && q12 == 16666667L,
                    "3 deliveries strictly monotonic q=" + q01 + "/" + q12);
                row("FC-04", stateAcrossFrames == 6,
                    "state mutation across frames=" + stateAcrossFrames);
                row("FC-06", removedCbFired == 0,
                    "removed callback fired=" + removedCbFired);
                refresh();
            }
        }
    }

    // ── a callback that is posted then immediately removed ──
    private static final class RemovedCallback implements Choreographer.FrameCallback {
        public void doFrame(long frameTimeNanos) {
            removedCbFired++;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // FC-05a: BEFORE any attach — the token must be null (AOSP
        // mAttachInfo.mWindowToken is null for a never-attached view).
        TextView detached = new TextView(this);
        Object preToken = detached.getWindowToken();
        row("FC-05a", preToken == null,
            "pre-attach token=" + (preToken == null ? "null" : preToken.toString()));

        choreo = Choreographer.getInstance();

        // FC-01: identity-stable singleton
        Choreographer again = Choreographer.getInstance();
        row("FC-01", choreo == again,
            "getInstance identity stable=" + (choreo == again));

        // FC-06 setup: post then remove immediately
        RemovedCallback rc = new RemovedCallback();
        choreo.postFrameCallback(rc);
        choreo.removeFrameCallback(rc);

        // FC-02/03/04: the re-registration loop
        choreo.postFrameCallback(new LoopCallback());

        LinearLayout root = rootView = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF000000);
        tv = new TextView(this);
        tv.setText("FCLKPROBE boot\n" + report);
        tv.setTextColor(0xFFFFFFFF);
        tv.setTextSize(24f);
        root.addView(tv);
        setContentView(root);
        refresh();
    }

    private static LinearLayout rootView;

    @Override
    protected void onResume() {
        super.onResume();
        // FC-05b: AFTER attach (attach precedes onResume in the AOSP order).
        // The audited shape is the CONTENT view (dooz's Lho; — the
        // ComposeView inside the content tree), not the decor: the engine's
        // attach dispatch marks the content tree (the R347 wave); the decor
        // node is outside it and answers the detached state honestly.
        if (tv != null) {
            Object tk1 = tv.getWindowToken();
            Object tk2 = tv.getWindowToken();
            row("FC-05b", tk1 != null,
                "post-attach content token=" + (tk1 == null ? "null" : ("oid:" + tk1)));
            row("FC-05c", tk1 != null && tk1 == tk2,
                "two calls same identity=" + (tk1 != null && tk1 == tk2));
            Object tkRoot = rootView != null ? rootView.getWindowToken() : null;
            row("FC-05d", tk1 != null && tk1 == tkRoot,
                "second tree view same window token=" + (tk1 == tkRoot));
        }
        refresh();
    }
}
