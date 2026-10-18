package com.probe.c102c;

import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import android.os.Bundle;

/**
 * CONT-102 Batch C — #364 CONT-98 T8 (permission checks + app-private
 * boundary) + T9 (configuration/resource selection coherence) +
 * T10 (process death / restart / durable state recovery).
 *
 * T10 protocol (two harness invocations of the SAME apk):
 *   GEN1: seeds SharedPreferences c102.counter=41 and
 *         files/durable.txt="gen1"; prints GEN rows.
 *   GEN2: verifies SharedPreferences == 41, durable.txt == gen1, and that
 *         process-local static state reset to its default (fresh gen).
 */
public class MainActivity extends Activity {
    static int processLocal = 0;

    void row(String tag, Object v) {
        System.err.println("[C102-" + tag + "] " + v);
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // T10 protocol (durable-state-driven): the generation is decided
            // by the durable state itself — absent prefs counter ⇒ GEN1
            // (seed); present ⇒ GEN2 (verify). Two harness invocations of
            // the SAME apk + data-root are two process generations.
            int existing = getSharedPreferences("c102", Context.MODE_PRIVATE)
                    .getInt("counter", -1);
            if (existing >= 0) runGen2();
            else runGen1();
            System.err.println("[C102-C-DONE] existing=" + existing);
        } catch (Throwable t) {
            System.err.println("[C102-C-ERR] " + t);
        }
    }

    void runGen1() throws Exception {
        // ── T8: permission laws ──────────────────────────────────────
        row("R-SELF-DECL",
                checkSelfPermission("com.probe.c102c.PERM"));   // 0 GRANTED
        row("R-SELF-UNDECL",
                checkSelfPermission("android.permission.CAMERA")); // -1 DENIED
        row("R-CHECKPERM-DECL",
                checkPermission("com.probe.c102c.PERM",
                        android.os.Process.myPid(), android.os.Process.myUid()));
        // sandbox: own files dir writable, foreign app dir NOT
        java.io.File own = new java.io.File(getFilesDir(), "own.txt");
        java.io.FileWriter w = new java.io.FileWriter(own);
        w.write("C102-OWN-BYTES");
        w.close();
        row("R-OWN-WRITE", own.length() == 14);   // "C102-OWN-BYTES" = 14 bytes
        java.io.File foreign = new java.io.File(
                "/data/data/com.other.pkg/files/x.txt");
        row("R-FOREIGN-EXISTS", foreign.exists());   // false (no leak)

        // ── T9: configuration coherence (cold == warm selection) ─────
        Configuration cfg = getResources().getConfiguration();
        row("C-CONFIG", cfg == null ? "null" : "non-null");
        row("C-DENSITY-DPI", cfg == null ? -1 : cfg.densityDpi);
        float d1 = getResources().getDisplayMetrics().density;
        float d2 = getResources().getDisplayMetrics().density;
        row("C-DENSITY-STABLE", d1 == d2 && d1 > 0f);

        // ── T10 gen1: seed durable state ─────────────────────────────
        getSharedPreferences("c102", Context.MODE_PRIVATE)
                .edit().putInt("counter", 41).commit();
        java.io.File df = new java.io.File(getFilesDir(), "durable.txt");
        java.io.FileWriter dw = new java.io.FileWriter(df);
        dw.write("gen1");
        dw.close();
        row("GEN1-SEEDED", "counter=41 durable=gen1");
        row("T10-PROCESS-LOCAL", processLocal);      // 0 fresh gen
    }

    void runGen2() throws Exception {
        // ── T10 gen2: durable state survived process death ──────────
        int c = getSharedPreferences("c102", Context.MODE_PRIVATE)
                .getInt("counter", -1);
        row("T10-PREFS-SURVIVED", c);                // exp 41
        java.io.File df = new java.io.File(getFilesDir(), "durable.txt");
        java.io.FileReader fr = new java.io.FileReader(df);
        char[] buf = new char[8];
        int n = fr.read(buf);
        fr.close();
        row("T10-FILE-SURVIVED", n == 4 ? new String(buf, 0, 4) : "short:" + n);
        row("T10-PROCESS-LOCAL", processLocal);      // 0 (new generation)
        row("R-OWN2-EXISTS",
                new java.io.File(getFilesDir(), "own.txt").exists());
    }
}
