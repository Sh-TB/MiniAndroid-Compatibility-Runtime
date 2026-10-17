package com.probe.c74esc;

import android.app.Activity;
import android.os.Bundle;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;

/**
 * CONT-74 — issue #364 FOUNDATION 7/4 residual-branch escape probe
 * (path containment on the two tail-join branches F-NEW-375 did NOT
 * cover: /system/fonts/<tail> and /storage/emulated/0<tail>).
 *
 * Law under test (F-NEW-375 tail-join containment, natural extension):
 * ANY branch that joins a caller-controlled tail under a virtual backing
 * directory must resolve INSIDE that backing directory. A `..` sequence
 * in the tail must never move the resolved host path out of the app
 * namespace.
 *
 * Self-contained proof: the probe first writes own.txt in its own
 * sandbox, then re-reads ITS OWN bytes through escape spellings. Reading
 * back the marker byte-string through a path that lexically leaves the
 * backing directory proves the fence is missing — no other package, no
 * fixture coupling.
 *
 * Rows:
 *   C74-SELF      own filesDir write (positive base)
 *   C74-VOL-ESC   /storage/emulated/0/../../../data/data/<self>/files/own.txt (expect DENY;
 *                 THREE .. — 0→emulated→storage→<store root> — the volume backing
 *                 EXISTS, so this escape is runtime-REACHABLE today)
 *   C74-VOL-ESC2  /storage/emulated/0/../0/../../../data/data/<self>/files/own.txt (expect DENY)
 *   C74-FONT-ESC  /system/fonts/../../data/data/<self>/files/own.txt (resolve-layer
 *                 allows; currently IO-unreachable only because <store>/system
 *                 does not exist yet — recorded as a law-hygiene row)
 *   C74-VOL-OK    /storage/emulated/0/probe74.txt write+read (positive control — volume law intact)
 *   C74-NEG-ETC   /etc/passwd (expect ABSENT, canonical negative)
 *   C74-VERSION   compiled identity marker
 */
public class MainActivity extends Activity {

    public static final String VERSION = "V1-ESC";
    private static final String SELF = "com.probe.c74esc";
    private static final String MARKER = "C74-OWN-BYTES";

    private void log(String row, boolean ok, String detail) {
        System.err.println("[C74-" + row + "] " + (ok ? "OK" : "LEAK") + " " + detail);
    }

    private String readAll(String path) throws Exception {
        FileInputStream in = new FileInputStream(path);
        try {
            StringBuilder sb = new StringBuilder();
            byte[] buf = new byte[512];
            int n;
            while ((n = in.read(buf)) > 0) sb.append(new String(buf, 0, n, "UTF-8"));
            return sb.toString();
        } finally { in.close(); }
    }

    private void expectAbsent(String row, String path) {
        try {
            String s = readAll(path);
            boolean marker = s.contains(MARKER);
            log(row, !marker, (marker ? "ESCAPE read own marker via " : "read non-marker bytes via ")
                    + path + " len=" + s.length());
        } catch (Throwable t) {
            log(row, true, "denied/absent " + path + " -> " + t.getClass().getSimpleName());
        }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        System.err.println("[C74-VERSION] code=" + VERSION
                + " pkg=" + getPackageName()
                + " filesDir=" + getFilesDir().getAbsolutePath());

        // 1. own-namespace write (positive base — the escape target bytes)
        try {
            FileOutputStream out = openFileOutput("own.txt", MODE_PRIVATE);
            out.write(MARKER.getBytes("UTF-8"));
            out.close();
            log("SELF", true, "wrote own.txt marker");
        } catch (Throwable t) {
            log("SELF", false, "openFileOutput threw " + t);
        }

        // 2. volume tail-join escapes — REACHABLE (backing exists, three ..)
        expectAbsent("VOL-ESC",  "/storage/emulated/0/../../../data/data/" + SELF + "/files/own.txt");
        expectAbsent("VOL-ESC2", "/storage/emulated/0/../0/../../../data/data/" + SELF + "/files/own.txt");

        // 3. font tail-join — resolve layer ALLOWS the escape spelling;
        //    IO-unreachable today only because <store>/system is absent.
        expectAbsent("FONT-ESC",  "/system/fonts/../../data/data/" + SELF + "/files/own.txt");

        // 4. volume positive control — normal virtual-external IO must work
        try {
            File v = new File("/storage/emulated/0/probe74.txt");
            FileOutputStream out = new FileOutputStream(v);
            out.write("C74-VOL-OK".getBytes("UTF-8"));
            out.close();
            String s = readAll(v.getAbsolutePath());
            log("VOL-OK", s.contains("C74-VOL-OK"), "volume round-trip " + v.getAbsolutePath());
        } catch (Throwable t) {
            log("VOL-OK", false, "volume round-trip threw " + t.getClass().getSimpleName());
        }

        // 5. canonical negative control
        expectAbsent("NEG-ETC", "/etc/passwd");

        System.err.println("[C74-DONE] rows complete");
    }
}
