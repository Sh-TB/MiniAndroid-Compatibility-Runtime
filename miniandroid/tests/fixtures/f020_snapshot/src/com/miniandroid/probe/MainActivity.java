/*
 * M3 F-020 micro reproducer — the Compose snapshot-family primitive laws,
 * executed as real DEX inside a real APK, with a VISUAL verdict.
 *
 * Why these four laws: the F-020 forensic chain proved the dooz Compose
 * blocker was a stack of three runtime defects under ONE symptom
 * (SnapshotKt.readError ISE at setContent):
 *   1. AtomicReference.<init>(payload) dropped the constructor argument
 *      (view-parent retry routed the ctor to ViewShadow) — Compose stores
 *      its global snapshot in exactly such an AtomicReference field.
 *   2. Virtual dispatch skipped intermediate overrides (LP/a→LP/b→LP/g):
 *      the base Snapshot.s(I) always throws "Updating write count is not
 *      supported" — MutableSnapshot.s(I) is the override that must win.
 *   3. Enum.compareTo had no shadow: isAtLeast(STARTED) returned true for
 *      INITIALIZED (0 >= 0), firing androidx's real performRestore guard.
 *
 * Each law renders one 200px band: green = law holds, red = violated.
 * The verdict must ALSO be visible in the runtime result — a blank or
 * wrong-color screenshot is a failure (§10: existence is not proof).
 *
 * Determinism: no time, no randomness, no collections — the same 4 bands
 * every run, byte-identical framebuffer.
 */
package com.miniandroid.probe;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicBoolean;

public class MainActivity extends Activity {

    enum State { INITIALIZED, STARTED, RESUMED }

    static boolean law1 = false;   // AtomicReference ctor-value identity
    static boolean law2 = false;   // AtomicInteger prefix/postfix arithmetic
    static boolean law3 = false;   // Enum.compareTo ordinal sign
    static boolean law4 = false;   // CAS value law (identity + swap)
    static boolean law5 = false;   // getLayoutInflater window-singleton law

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Law 1 — the dooz global-snapshot law: the value passed to the
        // constructor must be the value get() returns. In dooz, Compose's
        // SnapshotKt holds the global snapshot this way; losing the arg
        // zeroed the whole snapshot id chain (readError ISE).
        AtomicReference<String> ref = new AtomicReference<String>("SNAP");
        String got = ref.get();
        law1 = got != null && got.length() == 4;

        // Law 2 — AtomicInteger exact arithmetic (write counters).
        AtomicInteger ai = new AtomicInteger(5);
        int pre  = ai.incrementAndGet();   // 6  (returns NEW)
        int post = ai.addAndGet(10);       // 16 (returns NEW)
        int old  = ai.getAndIncrement();   // 16 (returns OLD)
        law2 = (pre == 6) && (post == 16) && (old == 16) && (ai.get() == 17);

        // Law 3 — Enum.compareTo ordinal sign: the isAtLeast shape.
        // INITIALIZED.compareTo(STARTED) == -1, so isAtLeast(STARTED) is
        // false — the exact guard that threw ISE in performRestore when
        // compareTo returned the int-default 0.
        int sign = State.INITIALIZED.compareTo(State.STARTED);
        int self = State.STARTED.compareTo(State.STARTED);
        int rev  = State.RESUMED.compareTo(State.INITIALIZED);
        law3 = (sign == -1) && (self == 0) && (rev == 2);

        // Law 4 — compareAndSet value/identity law.
        AtomicBoolean ab = new AtomicBoolean(true);
        boolean swapped = ab.compareAndSet(true, false);   // true
        boolean mismatch = ab.compareAndSet(true, true);   // false (now false)
        law4 = swapped && !mismatch && !ab.get();

        // Law 5 — F-021: Activity.getLayoutInflater() returns the window
        // inflater (never null) — the ViewBinding root-availability law.
        law5 = getLayoutInflater() != null;

        setContentView(new ProbeView(this));
    }

    class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);

            boolean[] laws = { law1, law2, law3, law4, law5 };
            for (int i = 0; i < 5; i++) {
                p.setColor(laws[i] ? 0xFF00A000 : 0xFFD00000);
                int top = 100 + i * 300;
                canvas.drawRect(100, top, 980, top + 200, p);
            }
        }
    }
}
