package com.probe.f084;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {
    static List<String> out = new ArrayList<String>();

    static void rec(String line) { out.add(line); }

    // N1 helper: the spin lives in a CALLEE frame so the engine's
    // deferred VirtualMachineError is raised at the invoke site INSIDE
    // onCreate's try range — the app-level catch must observe it.
    // (ECJ compiles `while (k == 5) { k = 5; }` to a branch-free
    // nop/goto self-loop; the frame-level guard halts that frame and
    // the deferred VME unwinds to the caller's catch.)
    static void stalledSpin() {
        int k = 5;
        while (k == 5) {
            k = 5;  // constant decision inputs — a true spin
        }
    }

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // P1 — PROGRESSING long loop: 60,000 iterations of an if-ge
        // back-edge whose operands (i, limit) CHANGE every visit.
        // The old raw-visit cap halted this at 50,001; the forward-progress
        // law must let it complete. Expected sum of (i & 1) over [0,60000)
        // = 30,000.
        long s = 0;
        for (int i = 0; i < 60000; i++) {
            s += (i & 1);
        }
        rec(s == 30000
            ? "GATEA|F084-P1-PROGRESS-COMPLETES|PASS|sum=" + s
            : "GATEA|F084-P1-PROGRESS-COMPLETES|FAIL|sum=" + s);

        // P2 — PROGRESSING nested loop: outer 40 × inner 1250 (the exact
        // fairymahjong shape: 40 tiles × 1254-pixel rows). Branch operands
        // evolve on every visit of both back-edges.
        int total = 0;
        for (int t = 0; t < 40; t++) {
            for (int p = 0; p < 1250; p++) {
                total += (p & 0xFF);
            }
        }
        rec("GATEA|F084-P2-NESTED-50K|PASS|total=" + total);

        // N1 — STALLED spin: the comparison operands NEVER change
        // (k is reassigned the same constant), so the decision inputs are
        // constant forever. The frame-level forward-progress law halts
        // the spinning frame (VirtualMachineError raised at the invoke
        // site) and the catch records it honestly.
        try {
            stalledSpin();
            rec("GATEA|F084-N1-STALLED-HALTED|FAIL|spin exited (guard did not fire)");
        } catch (Throwable t) {
            String n = t.getClass().getName();
            rec("GATEA|F084-N1-STALLED-HALTED|PASS|halted via " + n);
        }

        TextView tv = new TextView(this);
        StringBuilder sb = new StringBuilder();
        for (String line : out) sb.append(line).append('\n');
        tv.setText(sb.toString());
        setContentView(tv);
    }
}
