package com.probe.r1;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * S211 A-R1 native-tail probe — the #576 R1 finding as an executable row.
 * A REAL host .so (lib/x86_64/libr1probe.so) registers two natives through
 * RegisterNatives:
 *
 *   throwThenReturn42  — ThrowNew(IllegalStateException, "r1-probe") then
 *                        returns 42. JNI spec: on native return with a
 *                        pending exception the VM DISCARDS the return value
 *                        and throws at the call site. Pre-fix (A-R1 absent)
 *                        the DEX saw 42 and no exception — the silent
 *                        typed-default pattern on the native tail (#576 R1,
 *                        P0). Post-fix: IllegalStateException propagates,
 *                        the catch runs, 42 never escapes.
 *
 *   clearThenReturn7   — ThrowNew then ExceptionCheck+ExceptionClear (the
 *                        native CONSUMES its own pending exception), returns
 *                        7. Law: no pending exception at return → the DEX
 *                        sees 7 and no throw. Regression guard on both
 *                        sides (the channel must not over-raise).
 */
public class MainActivity extends Activity {

    static {
        System.loadLibrary("r1probe");
    }

    private static native int throwThenReturn42();

    private static native int clearThenReturn7();

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int v42 = 0;
        boolean caught = false;
        String msg = "";
        try {
            v42 = throwThenReturn42();
        } catch (IllegalStateException e) {
            caught = true;
            msg = e.getMessage();
        }
        row("R1-01", caught && v42 == 0,
                "ThrowNew discards native ret 42 → ISE caught, msg=" + msg);

        int v7 = 0;
        boolean caught7 = false;
        try {
            v7 = clearThenReturn7();
        } catch (Throwable t) {
            caught7 = true;
        }
        row("R1-02", !caught7 && v7 == 7,
                "native ExceptionCheck+Clear consumes pending → 7, no throw");

        // ── visible render: runner-side pixel gate reads the frame ──
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF000000);
        TextView tv = new TextView(this);
        tv.setText("R1PROBE " + countPass() + "/" + countTotal() + "\n"
                + report);
        tv.setTextColor(0xFFFFFFFF);
        tv.setTextSize(24f);
        root.addView(tv);
        TextView marker = new TextView(this);
        marker.setText("S211R1PROBE");
        marker.setTextColor(0xFFFFFFFF);
        marker.setTextSize(24f);
        root.addView(marker);
        setContentView(root);
    }

    private static int countPass() {
        int p = 0;
        for (String line : report.split("\n"))
            if (line.contains("|PASS|")) p++;
        return p;
    }

    private static int countTotal() {
        int t = 0;
        for (String line : report.split("\n"))
            if (line.contains("|PASS|") || line.contains("|FAIL|")) t++;
        return t;
    }
}
