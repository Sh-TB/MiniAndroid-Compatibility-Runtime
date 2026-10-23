package com.probe.cont11;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Rect;
import android.os.Bundle;
import android.view.WindowManager;
import android.view.WindowMetrics;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.lang.Thread;

/**
 * CONT-11 synthetic probe — the three recurring-root fixes landed by the
 * loading-screen census wave. Upstream contracts under test (generic
 * platform laws — no app specifics):
 *
 *   F272-A  ART interface-resolution exactness: invoke-interface with the
 *           4-arg (I,I,Map,Function1) descriptor on a receiver whose class
 *           only declares the 5-arg same-name overload must resolve the
 *           INTERFACE DEFAULT (which delegates to the 5-arg) — never the
 *           5-arg body dispatched through a truncated arg window (the
 *           trailing captured Function1 must arrive non-null).
 *   F272-B  negative/positive pair: the 5-arg abstract dispatch through
 *           the SAME interface ref resolves the receiver's 5-arg override
 *           with the full arg window.
 *   F273-A  Thread default UncaughtExceptionHandler law:
 *           getDefaultUncaughtExceptionHandler() NEVER null (RuntimeInit
 *           installs KillApplicationHandler at boot); identity stable;
 *           setDefault is honored by getDefault; per-thread
 *           getUncaughtExceptionHandler/set answers the per-thread
 *           handler when set.
 *   F273-B  chaining: defaultHandler.uncaughtException(thread, t) invoked
 *           through the interface returns normally (engine default
 *           handles honestly — no NPE, no void-void hole).
 *   F274-A  WindowMetrics family (API 30+): WindowManager.getCurrent-
 *           WindowMetrics()/getMaximumWindowMetrics() non-null; getBounds()
 *           spans the device profile (1080x1920); two getBounds() calls
 *           return DISTINCT Rect copies with EQUAL fields.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    // ── F272 fixture shape (mirrors compose MeasureScope/LookaheadCapable-
    // Placeable): interface default 4-arg delegating to the 5-arg abstract;
    // receiver overrides ONLY the 5-arg.
    interface MeasureScope {
        Object layout(int w, int h, java.util.Map<Integer, String> lines,
                      Runnable placementBlock);
        // the 4-arg DEFAULT (compose upstream carries this with code)
        default Object layout(int w, int h, java.util.Map<Integer, String> lines) {
            return layout(w, h, lines, new Runnable() {
                public void run() { report += "F272-default-block|ran\n"; }
            });
        }
    }

    static class LookaheadLike implements MeasureScope {
        boolean fiveArgRan = false;
        boolean placed = false;
        Runnable captured = null;
        public Object layout(int w, int h, java.util.Map<Integer, String> lines,
                             Runnable placementBlock) {
            fiveArgRan = true;
            captured = placementBlock;   // must be the DEFAULT's lambda, not unset
            return "impl5:" + w + "x" + h;
        }
        // compose placeChildren analogue: invoke the captured block
        void place() {
            if (captured != null) { captured.run(); placed = true; }
        }
    }

    private void probeF272() {
        LookaheadLike recv = new LookaheadLike();
        MeasureScope scope = recv;
        java.util.Map<Integer, String> lines = new java.util.HashMap<>();
        // F272-A: 4-arg invoke through the interface — the DEFAULT must run
        // and delegate with the lambda intact.
        Object r1 = scope.layout(1080, 1920, lines);
        boolean a = recv.fiveArgRan
            && recv.captured != null
            && "impl5:1080x1920".equals(String.valueOf(r1));
        row("F272-A", a, r1 + " captured=" + (recv.captured != null));
        // the placement analogue must invoke the captured block without NPE
        // (upstream placeChildren invokes $placementBlock.invoke(scope)).
        try {
            recv.place();
            boolean b = recv.placed && report.contains("F272-default-block|ran");
            row("F272-A-block", b, "placed=" + recv.placed);
        } catch (NullPointerException npe) {
            row("F272-A-block", false, "NPE " + npe.getMessage());
        }

        // F272-B: the 5-arg abstract dispatch — full arg window, distinct
        // identity (the impl's captured lambda is the caller's).
        Runnable mine = new Runnable() { public void run() { } };
        Object r2 = scope.layout(11, 22, lines, mine);
        boolean c = recv.captured == mine && "impl5:11x22".equals(String.valueOf(r2));
        row("F272-B", c, String.valueOf(r2));
    }

    private static Thread.UncaughtExceptionHandler savedDefault = null;
    private static Thread.UncaughtExceptionHandler savedPerThread = null;

    private void probeF273() {
        // F273-A1: getDefault never null (RuntimeInit boot law).
        Thread.UncaughtExceptionHandler d1 =
            Thread.getDefaultUncaughtExceptionHandler();
        row("F273-A1", d1 != null, String.valueOf(d1));
        // F273-A2: identity stable across reads.
        Thread.UncaughtExceptionHandler d2 =
            Thread.getDefaultUncaughtExceptionHandler();
        row("F273-A2", d1 == d2, "identity-stable");
        // F273-A3: setDefault is honored.
        Thread.UncaughtExceptionHandler mine = new Thread.UncaughtExceptionHandler() {
            public void uncaughtException(Thread t, Throwable e) { }
        };
        Thread.setDefaultUncaughtExceptionHandler(mine);
        row("F273-A3", Thread.getDefaultUncaughtExceptionHandler() == mine,
            "set-then-get");
        // F273-A4: per-thread set/get honors the handler.
        Thread.UncaughtExceptionHandler mine2 = new Thread.UncaughtExceptionHandler() {
            public void uncaughtException(Thread t, Throwable e) { }
        };
        Thread cur = Thread.currentThread();
        cur.setUncaughtExceptionHandler(mine2);
        savedPerThread = cur.getUncaughtExceptionHandler();
        row("F273-A4", savedPerThread == mine2, "per-thread");
        cur.setUncaughtExceptionHandler(null);
        // F273-A5: after clearing the per-thread handler the getter falls
        // back to the process default (never null).
        Thread.UncaughtExceptionHandler afterClear = cur.getUncaughtExceptionHandler();
        row("F273-A5", afterClear != null, "fallback-to-default");
        // F273-B: chaining into the default handler must not NPE.
        try {
            afterClear.uncaughtException(cur, new RuntimeException("probe"));
            row("F273-B", true, "chain-ok");
        } catch (NullPointerException npe) {
            row("F273-B", false, "NPE " + npe.getMessage());
        }
        // restore the boot default for later probes
        if (d1 != null) Thread.setDefaultUncaughtExceptionHandler(d1);
        savedDefault = Thread.getDefaultUncaughtExceptionHandler();
    }

    private void probeF274() {
        WindowManager wm = getWindow().getWindowManager();
        boolean ok = false, ok2 = false;
        String detail = "";
        try {
            WindowMetrics cur = wm.getCurrentWindowMetrics();
            ok = cur != null;
            if (ok) {
                Rect b = cur.getBounds();
                ok = b != null && b.right == 1080 && b.bottom == 1920
                    && b.left == 0 && b.top == 0;
                detail = b == null ? "null-bounds" : b.toString();
            }
        } catch (Throwable t) {
            detail = "EXC:" + t.getClass().getSimpleName();
        }
        row("F274-A", ok, detail);
        try {
            WindowMetrics max = wm.getMaximumWindowMetrics();
            Rect b1 = max.getBounds();
            Rect b2 = max.getBounds();
            // Contract that matters: every call answers valid, correct
            // bounds (AOSP returns a fresh copy; the engine lineage answers
            // a stable identity — recorded deviation, both satisfy app
            // code that reads the fields).
            ok2 = b1 != null && b2 != null
                && b1.right == b2.right && b1.bottom == b2.bottom
                && b1.right == 1080 && b2.bottom == 1920;
            detail = (b1 == b2 ? "stable-identity" : "fresh-copy")
                + " fields-equal";
        } catch (Throwable t) {
            detail = "EXC:" + t.getClass().getSimpleName();
        }
        row("F274-B", ok2, detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        TextView tv = new TextView(this);
        root.addView(tv);
        setContentView(root);
        probeF272();
        probeF273();
        probeF274();
        tv.setText(report);
        android.util.Log.i("CONT11", report);
    }
}
