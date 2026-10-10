package com.probe.s106exc;

/**
 * S106 probe — three law fixtures on one screen (dooz v23 post-ROOT-010 chain).
 *
 * Stage A (ROOT-011 ENUM-VALUEOF): the dooz theme read is
 *   prefs("theme"|"System") -> ThemeOption.valueOf(String) -> Enum.valueOf
 *   -> mutableStateOf(...) -> composition reads Enum.ordinal().
 *   Law: Enum.valueOf(Class, String) returns THE constant with that name
 *   (identity), ordinal() matches creation order, and an unknown name is
 *   an IllegalArgumentException — NEVER null (old bridge: null -> null
 *   state -> ordinal-on-null NPE -> APP BOUNDARY).
 *
 * Stage B (ROOT-012 THROWABLE-SUPPRESSED): libcore Throwable law —
 *   getSuppressed() NEVER returns null (EMPTY_THROWABLE_ARRAY when no
 *   suppression); addSuppressed() round-trips by identity. Old bridge:
 *   null -> getClass-on-null NPE inside the dooz cancellation handler.
 *
 * Stage C (ROOT-013 EXC-ACCOUNTING): inner frame throws, MID frames have
 *   no handler, OUTER frame catches — the app's own error handling
 *   (dooz: typed CancellationException catch). Semantics: the value flows
 *   (rc 0 = caught, value preserved); the ACCOUNTING claim (0 crash rows
 *   for caught exceptions) is asserted by the gate script on crash.log.
 *
 * On-screen verdict: "S106EXC-PROBE valueOf=A suppressed=B unwind=C
 * values=N" — 0/0/0/3 is ALL-PASS. The gate greps this exact line.
 */
public class ExcProbeActivity extends android.app.Activity {

    enum Mode { LIGHT, DARK, SYSTEM }

    static int valueOfRoundTrip() {
        Mode m = Mode.valueOf("SYSTEM");
        if (m != Mode.SYSTEM) return 1;          // identity law broken
        if (m.ordinal() != 2) return 2;          // ordinal law broken
        Mode d = Mode.valueOf("DARK");
        if (d != Mode.DARK || d.ordinal() != 1) return 3;
        try {
            Mode.valueOf("NOPE");                // libcore: IAE, never null
            return 4;                            // returned null / no throw
        } catch (IllegalArgumentException e) {
            return 0;                            // PASS
        }
    }

    static int suppressedLaw() {
        Throwable t = new Throwable("root");
        Throwable[] s0 = t.getSuppressed();
        if (s0 == null) return 1;                // THE ROOT: never null
        if (s0.length != 0) return 2;            // empty-array law
        Throwable x = new Throwable("sup");
        t.addSuppressed(x);
        Throwable[] s1 = t.getSuppressed();
        if (s1 == null || s1.length != 1) return 3;
        if (s1[0] != x) return 4;                // identity round-trip
        return 0;
    }

    static void thrower() { throw new IllegalStateException("deep"); }

    static String unwindCatch() {
        try {
            thrower();                           // two handler-less frames
            return "no-throw";
        } catch (IllegalStateException e) {
            return "caught:" + e.getMessage();
        }
    }

    @Override protected void onCreate(android.os.Bundle b) {
        super.onCreate(b);
        int a = valueOfRoundTrip();
        int c = suppressedLaw();
        String d = unwindCatch();
        android.widget.TextView tv = new android.widget.TextView(this);
        tv.setText("S106EXC-PROBE valueOf=" + a + " suppressed=" + c
                + " unwind=" + d + " values=" + Mode.values().length);
        setContentView(tv);
    }
}
