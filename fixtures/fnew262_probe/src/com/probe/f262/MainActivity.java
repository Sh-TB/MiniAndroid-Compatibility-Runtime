package com.probe.f262;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.view.Window;

/**
 * CONT-46 Phase-3 — F-NEW-262 discriminator probe (bridge <-> DEX
 * object-flow contract). Every row asserts OBJECT IDENTITY / VALUE, not
 * merely absence of exceptions (the #375 contract).
 *
 * Shape families under test:
 *   BR-*  framework shadow-bridge invoke -> move-result-(object) -> DEX
 *         register -> field/arg use (the solitaire getCallback and notes
 *         createController shape).
 *   NI-*  new-instance -> invoke-direct <init> -> iput-object -> iget-object
 *         (the BMI FragmentActivity.mHandler shape; NI-3/4 add the
 *         DEX-subclass-of-shadow super-ctor hop — FragmentActivity$1).
 *   AM-*  argument marshalling DEX->DEX.
 *   MR-*  move-result-object after a value-returning DEX static.
 *   WV-*  wide / primitive / void bridge returns.
 *   EX-*  DEX-thrown exception path with move-exception identity.
 *
 * Rows print via System.out as ID|PASS|detail (engine println -> stdout law).
 */
public class MainActivity extends Activity {

    static final StringBuilder REPORT = new StringBuilder();
    static void row(String id, boolean pass, String detail) {
        REPORT.append(id).append('|').append(pass ? "PASS" : "FAIL")
              .append('|').append(detail).append('\n');
    }

    /** DEX-only box: ctor-arg -> field -> read identity. */
    static class Box {
        Object v;
        final Object fin;
        Box(Object v) { this.v = v; this.fin = v; }
    }

    /** DEX subclass of a framework shadow class (the FragmentActivity$1 shape). */
    static class MyHandler extends Handler { }

    /**
     * Preconditions-shaped identity helper (the R-NEW-365 law surface):
     * the descriptor contains "Preconditions", so it exercises the exact
     * engine-side name-gate family the BMI FragmentHostCallback.mHandler
     * loss flows through. check* helpers are IDENTITY on non-null input
     * and must throw on null — a stub that refuses the DEX body breaks
     * the value-return contract and poisons move-result-object with
     * <unset>.
     */
    static class Preconditions {
        static Object checkNotNull(Object v, String msg) {
            if (v == null) throw new NullPointerException(msg);
            return v;
        }
    }

    /** DEX static chain returning an object. */
    static Object a(Object x) { return b(x); }
    static Object b(Object x) { return c(x); }
    static Object c(Object x) { return x; }

    Window storedWindow;
    Handler storedHandler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // ── BR family: bridge returns into DEX registers ────────────
            Window w = getWindow();
            row("BR-1", w != null,
                "getWindow() non-null bridge return=" + (w != null));

            storedWindow = w;
            row("BR-2", storedWindow == w && getWindow() == w,
                "window identity survives field roundtrip + re-invoke");

            android.content.Intent it = getIntent();
            row("BR-3", it != null,
                "getIntent() non-null bridge return=" + (it != null));

            android.content.ComponentName cn = getCallingActivity();
            row("BR-4", cn == null,
                "getCallingActivity() intentional-null bridge -> register "
                + "is null (not <unset> poison)");

            // ── NI family: new-instance -> ctor -> iput -> iget ─────────
            Handler h1 = new Handler();
            row("NI-1", h1 != null,
                "new Handler() allocates non-null (direct shadow ctor)");
            storedHandler = h1;
            row("NI-2", storedHandler == h1,
                "Handler identity survives field roundtrip");

            MyHandler h2 = new MyHandler();
            row("NI-3", h2 != null,
                "new MyHandler() (DEX subclass of shadow) non-null");
            storedHandler = h2;
            row("NI-4", storedHandler == h2 && storedHandler instanceof MyHandler,
                "MyHandler identity survives field roundtrip + instanceof");

            Box box = new Box(w);
            row("NI-5", box.v == w && box.fin == w,
                "DEX ctor arg -> field -> read identity (v + final)");

            // ── AM family: argument marshalling ─────────────────────────
            Object thru = a(w);
            row("AM-1", thru == w,
                "object through 3-hop DEX static chain identity intact");
            row("AM-2", b(box) == box,
                "object receiver through DEX static chain identity intact");

            // ── WV family: primitive / wide / void bridge returns ───────
            int tid = getTaskId();
            row("WV-1", tid >= 0,
                "primitive bridge return getTaskId()=" + tid);
            long now = SystemClock.elapsedRealtime();
            row("WV-2", now >= 0,
                "wide bridge return elapsedRealtime()=" + now);
            int ori = getRequestedOrientation();
            setRequestedOrientation(ori);
            int ori2 = getRequestedOrientation();
            row("WV-3", ori2 == ori,
                "void bridge + int bridge roundtrip " + ori + "->" + ori2);

            // ── MR family: move-result-object after DEX static ─────────
            Object direct = c(box);
            row("MR-1", direct == box,
                "move-result-object after value-returning DEX static");

            // ── CK family: check* identity law (R-NEW-365) ─────────────
            Box checked = (Box) Preconditions.checkNotNull(box, "must not be null");
            row("CK-1", checked == box,
                "checkNotNull(nonNull) returns the SAME reference (identity law)");

            Object ck2 = Preconditions.checkNotNull(w, "m");
            row("CK-2", ck2 == w,
                "checkNotNull result survives move-result-object + use");

            boolean threw = false;
            try {
                Preconditions.checkNotNull(null, "ck-npe");
            } catch (NullPointerException e) {
                threw = "ck-npe".equals(e.getMessage());
            }
            row("CK-3", threw,
                "checkNotNull(null) throws NPE with the message (negative)");

            // ── EX family: throw + move-exception identity ──────────────
            boolean npeCaught = false;
            Throwable kept = null;
            try {
                Object dead = null;
                dead.toString();
            } catch (NullPointerException npe) {
                npeCaught = true;
                kept = npe;
            }
            row("EX-1", npeCaught && kept != null,
                "NPE thrown+caught, move-exception object non-null="
                + (kept != null));
        } catch (Throwable t) {
            row("FATAL", false, "threw " + t);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        java.io.PrintStream out = System.out;
        for (String line : REPORT.toString().split("\n")) {
            if (!line.isEmpty()) out.println(line);
        }
        out.println("F262-PROBE-END");
    }
}
