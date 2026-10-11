package com.probe.f260;

import android.app.Activity;
import android.os.Bundle;
import java.lang.reflect.Modifier;

/**
 * CONT-46 Phase-1 — F-NEW-260 revalidation probe: Class.getModifiers()
 * for MEMBER (nested) classes must answer the SYSTEM
 * dalvik.annotation.InnerClass accessFlags (the JVMS InnerClasses
 * attribute law), NOT the class_def access_flags (which never carry
 * ACC_STATIC in DEX).
 *
 * Positive rows: the compiled inner-class zoo — public/protected/package/
 * private x static/non-static members, a nested interface (implicitly
 * static), an anonymous class, a top-level class.
 * Negative rows: a framework shadow token class (Handler) must NOT answer
 * typed-zero (the F-NEW-260 pre-fix failure shape) and must not throw.
 *
 * Ground truth per row = what javac emits + OpenJDK Class.getModifiers:
 *   public static member     -> PUBLIC|STATIC           (0x9)
 *   package static member    -> STATIC                  (0x8)
 *   protected static member  -> PUBLIC|PROTECTED|STATIC (0xd? — javac emits
 *                               protected static = 0x4|0x8 = 0xc)
 *   private static member    -> PRIVATE|STATIC          (0xc)
 *   public non-static member -> PUBLIC                  (0x1)
 *   protected non-static     -> PROTECTED               (0x4)
 *   private non-static       -> PRIVATE                 (0x2)
 *   nested interface         -> PUBLIC|STATIC|INTERFACE (0x209)
 *   anonymous                -> (compiler) — assert isAnonymousClass only
 *   top-level public class   -> PUBLIC (0x1), !isMemberClass, !isStatic
 *
 * Rows print via System.out as ID|PASS|detail.
 */
public class MainActivity extends Activity {

    static final StringBuilder REPORT = new StringBuilder();
    static void row(String id, boolean pass, String detail) {
        REPORT.append(id).append('|').append(pass ? "PASS" : "FAIL")
              .append('|').append(detail).append('\n');
    }

    public static class PublicStatic { }
    static class PackageStatic { }
    protected static class ProtectedStatic { }
    private static class PrivateStatic { }

    public class PublicInner { }
    protected class ProtectedInner { }
    private class PrivateInner { }

    public interface NestedInterface { }

    // NOTE: the OpenJDK 21 oracle (host JVM, empirically verified) answers:
    //   anonymous -> 0x0 (InnerClasses attr access_flags verbatim)
    //   top-level -> its class_def flags (PUBLIC), isMemberClass=false
    //   member    -> InnerClass accessFlags

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // ── positive: static members carry ACC_STATIC ───────────────
            int m = PublicStatic.class.getModifiers();
            row("M-1", (m & Modifier.PUBLIC) != 0 && (m & Modifier.STATIC) != 0,
                "public static member mods=" + hex(m)
                + " (InnerClass law: PUBLIC|STATIC)");

            m = PackageStatic.class.getModifiers();
            row("M-2", (m & Modifier.STATIC) != 0 && (m & Modifier.PUBLIC) == 0,
                "package static member mods=" + hex(m)
                + " (STATIC, not public)");

            m = ProtectedStatic.class.getModifiers();
            row("M-3", (m & Modifier.STATIC) != 0
                     && (m & Modifier.PROTECTED) != 0,
                "protected static member mods=" + hex(m));

            m = PrivateStatic.class.getModifiers();
            row("M-4", (m & Modifier.STATIC) != 0
                     && (m & Modifier.PRIVATE) != 0,
                "private static member mods=" + hex(m));

            // ── positive: non-static members carry NO ACC_STATIC ────────
            m = PublicInner.class.getModifiers();
            row("M-5", (m & Modifier.PUBLIC) != 0 && (m & Modifier.STATIC) == 0,
                "public non-static member mods=" + hex(m)
                + " (PUBLIC, not static)");

            m = ProtectedInner.class.getModifiers();
            row("M-6", (m & Modifier.PROTECTED) != 0
                     && (m & Modifier.STATIC) == 0,
                "protected non-static member mods=" + hex(m));

            m = PrivateInner.class.getModifiers();
            row("M-7", (m & Modifier.PRIVATE) != 0
                     && (m & Modifier.STATIC) == 0,
                "private non-static member mods=" + hex(m));

            // ── nested interface: PUBLIC|STATIC|INTERFACE ───────────────
            m = NestedInterface.class.getModifiers();
            row("M-8", (m & Modifier.INTERFACE) != 0
                     && (m & Modifier.STATIC) != 0,
                "nested interface mods=" + hex(m));

            // ── member-class predicates ─────────────────────────────────
            row("M-9", PublicStatic.class.isMemberClass()
                     && !MainActivity.class.isMemberClass()
                     && (MainActivity.class.getModifiers()
                           & Modifier.STATIC) == 0,
                "isMemberClass member=true top-level=false; "
                + "top-level isStatic=false");

            // ── anonymous class ─────────────────────────────────────────
            Runnable anon = new Runnable() {
                @Override public void run() { }
            };
            m = anon.getClass().getModifiers();
            row("M-10", anon.getClass().isAnonymousClass() && m == 0,
                "anonymous mods=" + hex(m)
                + " (OpenJDK law: InnerClasses access_flags=0 verbatim)");

            // ── top-level class ─────────────────────────────────────────
            m = MainActivity.class.getModifiers();
            row("M-11", (m & Modifier.PUBLIC) != 0
                     && !MainActivity.class.isMemberClass(),
                "top-level public class mods=" + hex(m));

            // ── negative: framework token class must not typed-zero ────
            m = android.os.Handler.class.getModifiers();
            row("N-1", m != 0 && (m & Modifier.PUBLIC) != 0,
                "framework token Handler.class mods=" + hex(m)
                + " (public default, never typed-zero)");
            m = String.class.getModifiers();
            row("N-2", m != 0 && (m & Modifier.PUBLIC) != 0,
                "framework token String.class mods=" + hex(m));
        } catch (Throwable t) {
            row("FATAL", false, "threw " + t);
        }
    }

    static String hex(int v) { return "0x" + Integer.toHexString(v); }

    @Override
    protected void onResume() {
        super.onResume();
        java.io.PrintStream out = System.out;
        for (String line : REPORT.toString().split("\n")) {
            if (!line.isEmpty()) out.println(line);
        }
        out.println("F260-PROBE-END");
    }
}
