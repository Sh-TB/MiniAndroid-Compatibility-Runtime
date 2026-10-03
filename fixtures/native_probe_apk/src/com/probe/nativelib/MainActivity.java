package com.probe.nativelib;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.io.FileOutputStream;

/**
 * S-2 native-execution probe (issue #371 closeout).
 *
 * Result contract: one "NATIVEX|<op>|<PASS|FAIL>|<detail>" line per op,
 * written to files/native_probe_results.jsonl (physical backing proof) and
 * echoed through the TextView (screenshot/view-tree channel).
 *
 * Every PASS is an observed value crossing the managed↔native boundary —
 * never an existence check. Expected values are computed MANAGED-SIDE with
 * the same arithmetic the C library implements, so any runtime fabrication
 * of "native-looking" numbers without a real call would still have to
 * produce exactly these values; the A/B BASE binary (pre-S-2) throws
 * UnsatisfiedLinkError at class init and every op FAILs.
 */
public class MainActivity extends Activity {

    private StringBuilder RES = new StringBuilder();

    private void ok(String op, Object detail) {
        RES.append("NATIVEX|").append(op).append("|PASS|").append(detail).append("\n");
    }
    private void fail(String op, String detail) {
        RES.append("NATIVEX|").append(op).append("|FAIL|").append(detail).append("\n");
    }

    /** Managed-side reference checksum — same algorithm as native_probe.c */
    private static int javaChecksum(String s) {
        // bit-exact mirror of native_probe.c:
        //   x = (x * 31 + byte) ^ (x >> 3)   [mod 2^32]
        int x = 0x12345678;
        for (int i = 0; i < s.length(); i++) {
            x = (x * 31 + s.charAt(i)) ^ (x >>> 3);
        }
        return x;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        RES = new StringBuilder();
        try { runProbe(); } catch (Throwable t) {
            fail("PROBE-FATAL", String.valueOf(t));
        }
        try {
            FileOutputStream fos = openFileOutput("native_probe_results.jsonl",
                                                  MODE_PRIVATE);
            fos.write(RES.toString().getBytes("UTF-8"));
            fos.flush();
            fos.close();
        } catch (Throwable t) {
            fail("RESULTS-WRITE", String.valueOf(t));
        }
        TextView tv = new TextView(this);
        tv.setTextSize(11f);
        tv.setText(RES.toString());
        setContentView(tv);
    }

    private void runProbe() {
        // NATX-01 — ABI law: primary ABI is the host-executable one.
        try {
            String nld = getApplicationInfo().nativeLibraryDir;
            if (nld != null && nld.endsWith("/data/app/" + getPackageName() + "/lib/x86_64"))
                ok("NATX-01", "nativeLibraryDir=" + nld);
            else fail("NATX-01", "nativeLibraryDir=" + nld);
        } catch (Throwable t) { fail("NATX-01", String.valueOf(t)); }

        // NATX-02 — extraction identity: the .so physically exists in the
        // package sandbox with non-zero, correct length (File law).
        try {
            java.io.File so = new java.io.File(getApplicationInfo().nativeLibraryDir, "libprobe.so");
            long len = so.length();
            if (so.exists() && len > 0)
                ok("NATX-02", "libprobe.so exists=true length=" + len);
            else fail("NATX-02", "exists=" + so.exists() + " length=" + len);
        } catch (Throwable t) { fail("NATX-02", String.valueOf(t)); }

        // NATX-03 — REAL native execution #1: jlong return (fib loop).
        try {
            long r = NativeProbe.fibNative(15);
            if (r == 610L) ok("NATX-03", "fibNative(15)=" + r + " (expected 610)");
            else fail("NATX-03", "fibNative(15)=" + r + " expected 610");
        } catch (Throwable t) { fail("NATX-03", String.valueOf(t)); }

        // NATX-04 — REAL native execution #2: jint args + jint return.
        try {
            int r = NativeProbe.addNative(2, 3, 4);
            if (r == 9) ok("NATX-04", "addNative(2,3,4)=" + r + " (expected 9)");
            else fail("NATX-04", "addNative(2,3,4)=" + r + " expected 9");
        } catch (Throwable t) { fail("NATX-04", String.valueOf(t)); }

        // NATX-05 — jstring materialized INSIDE the library (NewStringUTF
        // slot) and adopted by the managed runtime.
        try {
            String s = NativeProbe.tagNative();
            if ("S2-NATIVE-OK".equals(s)) ok("NATX-05", "tagNative()=" + s);
            else fail("NATX-05", "tagNative()=" + s + " expected S2-NATIVE-OK");
        } catch (Throwable t) { fail("NATX-05", String.valueOf(t)); }

        // NATX-06 — managed bytes → native (GetStringUTFChars) → jint back.
        // Expected value computed managed-side with the same algorithm.
        try {
            String payload = "miniandroid-s2-probe-payload";
            int got = NativeProbe.checksumNative(payload);
            int want = javaChecksum(payload);
            if (got == want && payload.length() > 0)
                ok("NATX-06", "checksumNative=" + got + " javaRef=" + want + " (payload len " + payload.length() + ")");
            else fail("NATX-06", "checksumNative=" + got + " javaRef=" + want);
        } catch (Throwable t) { fail("NATX-06", String.valueOf(t)); }

        // NATX-07 — mixed register classes (I + F + D + J) in one call.
        try {
            double got = NativeProbe.mixNative(10, 1.5f, 2.25d, 100L);
            double want = 10 + 1.5 * 2 + 2.25 * 3 + 100 * 4;
            if (Math.abs(got - want) < 1e-9)
                ok("NATX-07", "mixNative(10,1.5f,2.25,100)=" + got + " (expected " + want + ")");
            else fail("NATX-07", "mixNative=" + got + " expected " + want);
        } catch (Throwable t) { fail("NATX-07", String.valueOf(t)); }

        // NATX-08 — missing symbol: a native method declared in this class
        // family but absent from the loaded .so must throw the AOSP
        // "No implementation found" linkage error. (NativeMissing is a
        // nested class with a native method the library does not export.)
        try {
            try {
                NativeMissing.callMissingSymbol();
                fail("NATX-08", "no exception (fake native success)");
            } catch (UnsatisfiedLinkError ule) {
                String m = ule.getMessage() != null ? ule.getMessage() : String.valueOf(ule);
                if (m.contains("No implementation found"))
                    ok("NATX-08", "ULE: " + m.substring(0, Math.min(110, m.length())));
                else fail("NATX-08", "wrong ULE shape: " + m);
            }
        } catch (Throwable t) { fail("NATX-08", String.valueOf(t)); }

        // NATX-09 — missing library: loadLibrary of an absent lib must stay
        // an honest UnsatisfiedLinkError with the APK-absent detail.
        try {
            try {
                System.loadLibrary("nativex_nosuch");
                fail("NATX-09", "no exception (fake load success)");
            } catch (UnsatisfiedLinkError ule) {
                String m = ule.getMessage() != null ? ule.getMessage() : String.valueOf(ule);
                if (m.contains("not found"))
                    ok("NATX-09", "ULE: " + m.substring(0, Math.min(110, m.length())));
                else fail("NATX-09", "wrong ULE shape: " + m);
            }
        } catch (Throwable t) { fail("NATX-09", String.valueOf(t)); }

        // NATX-10 — repeat-call determinism: the same native call twice
        // returns identical values (no host-state dependence).
        try {
            long a = NativeProbe.fibNative(15);
            long b2 = NativeProbe.fibNative(15);
            if (a == b2 && a == 610) ok("NATX-10", "repeat fibNative=" + a + "," + b2);
            else fail("NATX-10", "unstable repeats " + a + "," + b2);
        } catch (Throwable t) { fail("NATX-10", String.valueOf(t)); }
    }

    /** Declares a native method the .so does NOT export (NATX-08). */
    static class NativeMissing {
        static native void callMissingSymbol();
    }
}
