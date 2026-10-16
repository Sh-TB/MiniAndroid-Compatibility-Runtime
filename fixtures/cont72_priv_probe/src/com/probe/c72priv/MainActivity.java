package com.probe.c72priv;

import android.app.Activity;
import android.os.Bundle;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;

/**
 * CONT-72 — issue #364 FOUNDATION 3 review probe (package identity /
 * canonical path / byte-source contract).
 *
 * Law under test (AOSP ContextImpl + ActivityManager isolation): the
 * running package B must NOT read another package A's private
 * /data/data/<A> bytes through any spelling (absolute, user-0 alias,
 * relative ..); sibling volume names under /storage/emulated must not
 * alias the primary volume; /etc, /proc, /data/local/tmp must be denied;
 * own-namespace CE alias must agree; DE storage must be distinct.
 *
 * Rows (logged by the code whose contract is asserted):
 *   C72-SELF       own filesDir spelling + own write
 *   C72-ALIAS-SELF /data/user/0/<self>/files/own.txt read (positive control)
 *   C72-XPKG-ABS   /data/data/<victim>/files/secret72.txt (expect DENY/absent)
 *   C72-XPKG-U0    /data/user/0/<victim>/files/secret72.txt (expect DENY/absent)
 *   C72-REL-ESC    ../<victim>/files/secret72.txt relative (expect DENY/absent)
 *   C72-REL-ESC2   files/../../<victim>/files/secret72.txt (expect DENY/absent)
 *   C72-MNT-0EVIL  /storage/emulated/0evil/probe72.txt (expect ABSENT: no such volume)
 *   C72-MNT-0123   /storage/emulated/0123/probe72.txt (expect ABSENT)
 *   C72-NEG-ETC    /etc/passwd (expect ABSENT)
 *   C72-NEG-PROC   /proc/self/status (expect ABSENT)
 *   C72-NEG-DLT    /data/local/tmp/probe72.txt (expect ABSENT)
 *   C72-DE-WRITE   /data/user_de/0/<self>/files/de.txt write+read
 *   C72-VERSION    compiled code identity (fault-injection update test)
 */
public class MainActivity extends Activity {

    public static final String VERSION = "V1";
    private static final String SELF = "com.probe.c72priv";
    private static final String VICTIM = "com.dubrowgn.microtimer";

    private void log(String row, boolean ok, String detail) {
        System.err.println("[C72-" + row + "] " + (ok ? "OK" : "FAIL") + " " + detail);
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
            log(row, false, "LEAK read " + path + " len=" + s.length() + " head="
                    + s.substring(0, Math.min(24, s.length())));
        } catch (Throwable t) {
            log(row, true, "denied/absent " + path + " -> " + t.getClass().getSimpleName());
        }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        System.err.println("[C72-VERSION] code=" + VERSION
                + " pkg=" + getPackageName()
                + " filesDir=" + getFilesDir().getAbsolutePath());

        // 1. own-namespace write (positive base)
        try {
            FileOutputStream out = openFileOutput("own.txt", MODE_PRIVATE);
            out.write("C72-OWN".getBytes("UTF-8"));
            out.close();
            log("SELF", true, "wrote own.txt via openFileOutput");
        } catch (Throwable t) {
            log("SELF", false, "openFileOutput threw " + t);
        }

        // 2. CE alias positive control
        try {
            String s = readAll("/data/user/0/" + SELF + "/files/own.txt");
            log("ALIAS-SELF", s.contains("C72-OWN"),
                    "/data/user/0 alias read len=" + s.length());
        } catch (Throwable t) {
            log("ALIAS-SELF", false, "alias read threw " + t.getClass().getSimpleName());
        }

        // 3. cross-package absolute
        expectAbsent("XPKG-ABS", "/data/data/" + VICTIM + "/files/secret72.txt");
        // 4. cross-package user-0 alias
        expectAbsent("XPKG-U0", "/data/user/0/" + VICTIM + "/files/secret72.txt");
        // 5. relative .. escape to sibling package
        expectAbsent("REL-ESC", "../" + VICTIM + "/files/secret72.txt");
        // 6. nested .. escape
        expectAbsent("REL-ESC2", "files/../../" + VICTIM + "/files/secret72.txt");
        // 7. sibling-volume aliases (must NOT alias the primary volume)
        expectAbsent("MNT-0EVIL", "/storage/emulated/0evil/probe72.txt");
        expectAbsent("MNT-0123", "/storage/emulated/0123/probe72.txt");
        // 8. negative controls
        expectAbsent("NEG-ETC", "/etc/passwd");
        expectAbsent("NEG-PROC", "/proc/self/status");
        expectAbsent("NEG-DLT", "/data/local/tmp/probe72.txt");

        // 9. device-protected storage write+read (DE fence)
        try {
            File de = new File("/data/user_de/0/" + SELF + "/files/de.txt");
            FileOutputStream out = new FileOutputStream(de);
            out.write("C72-DE".getBytes("UTF-8"));
            out.close();
            String s = readAll(de.getAbsolutePath());
            log("DE-WRITE", s.contains("C72-DE"), "DE round-trip " + de.getAbsolutePath());
        } catch (Throwable t) {
            log("DE-WRITE", false, "DE write/read threw " + t.getClass().getSimpleName());
        }

        System.err.println("[C72-DONE] rows complete");
    }
}
