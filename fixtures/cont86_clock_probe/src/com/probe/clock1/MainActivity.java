package com.probe.clock1;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;

// CONT-86 virtual-clock fixture (CONT-85 T10 residual closure): asserts the
// clock-semantics laws the runtime claims:
//   1. SystemClock.uptimeMillis() monotonic, and Thread.sleep(120) advances
//      it by a plausible wall delta (sleep yield law),
//   2. SystemClock.elapsedRealtime() >= uptimeMillis (includes deep sleep),
//   3. System.currentTimeMillis() on the real host clock (bridge law,
//      CONT-85 T10) within a 2020..2030 sanity window,
//   4. System.nanoTime() monotonic across the same sleep,
//   5. SystemClock.currentThreadTimeMillis() recorded honestly (CPU-time
//      semantics; a 0/REC-MISS is a NAMED residual, not a pass).
// Evidence lives in the [CLOCK1-*] stderr rows + the verdict canvas band.
public class MainActivity extends Activity {
    private static long up1, up2, dtUp, elapsed, wall, n1, n2, dtNano;
    private static long threadTime;
    private static int checksPassed = 0, checksTotal = 0;
    private static String verdict = "PENDING";
    private static String detail = "";

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        System.out.println("[CLOCK1-VERSION] pkg=com.probe.clock1 wave=CONT-86");
        runChecks();
        setContentView(new ProbeView(this));
        System.out.println("[CLOCK1-DONE] checksPassed=" + checksPassed
            + "/" + checksTotal + " verdict=" + verdict);
    }

    private static void chk(String name, boolean ok, long v) {
        checksTotal++;
        if (ok) checksPassed++;
        System.out.println("[CLOCK1-CHK] " + name + " ok=" + ok + " v=" + v);
    }

    private static void runChecks() {
        up1 = SystemClock.uptimeMillis();
        try { Thread.sleep(120); } catch (InterruptedException ie) { }
        up2 = SystemClock.uptimeMillis();
        dtUp = up2 - up1;
        // Thread.sleep(120) must advance uptime by a plausible amount: the
        // sleep-yield law suspends the thread body; the virtual clock must
        // not be frozen (0) nor wildly overshooting (>2s for a 120ms sleep).
        chk("uptime-monotonic-sleep-120ms", dtUp >= 100 && dtUp <= 2000, dtUp);

        elapsed = SystemClock.elapsedRealtime();
        // elapsedRealtime includes deep sleep: always >= uptime.
        chk("elapsedRealtime>=uptime", elapsed >= up2, elapsed);

        wall = System.currentTimeMillis();
        // Host-clock bridge law (CONT-85 T10): 2020-09-01 .. 2030-01-01.
        chk("currentTimeMillis-host-window",
            wall > 1598918400000L && wall < 1893456000000L, wall);

        n1 = System.nanoTime();
        try { Thread.sleep(60); } catch (InterruptedException ie) { }
        n2 = System.nanoTime();
        dtNano = n2 - n1;
        chk("nanoTime-monotonic-sleep-60ms", dtNano > 0, dtNano);

        threadTime = SystemClock.currentThreadTimeMillis();
        // Honest row: CPU-time semantics. Recorded, not asserted.
        System.out.println("[CLOCK1-THREADTIME] v=" + threadTime
            + " (recorded honestly; 0 = named residual)");

        verdict = (checksPassed == checksTotal)
            ? ("PASS " + checksPassed + "/" + checksTotal)
            : ("FAIL " + checksPassed + "/" + checksTotal);
        detail = "dtUp=" + dtUp + " elapsed=" + elapsed + " wall=" + wall;
        System.out.println("[CLOCK1-VERDICT] " + verdict + " " + detail);
    }

    static class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }
        @Override public void onDraw(Canvas cv) {
            cv.drawColor(Color.WHITE);
            Paint p = new Paint();
            p.setColor(Color.BLACK);
            p.setTextSize(28);
            cv.drawText("uptime dt=" + dtUp + "ms (sleep 120)", 20, 60, p);
            cv.drawText("elapsed=" + elapsed + " uptime2=" + up2, 20, 105, p);
            cv.drawText("wall=" + wall, 20, 150, p);
            cv.drawText("nanoDt=" + dtNano, 20, 195, p);
            cv.drawText("threadTime=" + threadTime, 20, 240, p);
            cv.drawText("checks=" + checksPassed + "/" + checksTotal,
                        20, 285, p);
            p.setColor(verdict.startsWith("PASS") ? Color.rgb(0,128,0)
                                                  : Color.rgb(180,0,0));
            p.setTextSize(34);
            cv.drawText(verdict, 20, 350, p);
        }
    }
}
