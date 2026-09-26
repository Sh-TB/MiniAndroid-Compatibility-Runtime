package com.probe.s105park;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.concurrent.locks.LockSupport;

/**
 * S105 ROOT-010 WORKER-PARK-DEPTH minimal probe.
 *
 * Models the kotlinx.coroutines CoroutineScheduler.Worker.runLoop shape
 * (upstream law for the dooz v23 Lsr;.run F084 spin):
 *
 *   while (running) {
 *       Runnable t = poll();          // findNextTaskAndExecute
 *       if (t != null) { t.run(); continue; }
 *       parks++;                      // queue empty -> IDLE
 *       LockSupport.parkNanos(...);   // the worker must PARK, never spin
 *   }
 *
 * Deterministic claim set (engine law, single serialized thread):
 *   1. worker ACTIVE      : task1 executes exactly once
 *   2. worker IDLE/PARKED : empty queue -> park (PARK-YIELD in engine log;
 *                           pre-fix this spun park-scan until F084 halt)
 *   3. worker AWAKENED    : task2 (posted delayed on the main queue while
 *                           the worker is parked) becomes observable at the
 *                           next scheduler boundary re-drain (F-150)
 *   4. executes EXACTLY ONCE, then worker returns to idle and TERMINATES
 *      (worker-exit log line) - no repeated polling, no lost wakeup, no
 *      duplicate execution, no infinite spin.
 *
 * Engine-law note: park wake = the NEXT scheduler boundary (wake_at = 0,
 * immediately-due F-150 registry entry); the parkNanos timeout value does
 * not drive engine scheduling. This is the serialized counterpart of
 * unpark-on-arrival (AOSP LockSupport.park contract).
 */
public class ParkProbeActivity extends Activity {
    private static final int CAP = 16;
    private static final Object[] Q = new Object[CAP];
    private static int qHead = 0;
    private static int qTail = 0;
    private static volatile boolean running = true;
    private static int executed = 0;
    private static int parks = 0;
    private static TextView tv;

    private static void enqueue(Runnable r) { Q[qTail % CAP] = r; qTail++; }

    private static Runnable poll() {
        if (qHead >= qTail) return null;
        Runnable r = (Runnable) Q[qHead % CAP];
        Q[qHead % CAP] = null;
        qHead++;
        return r;
    }

    private static void note(String tag) {
        executed++;
        String text = "executed=" + executed + " parks=" + parks
                + " running=" + running + " last=" + tag;
        android.util.Log.i("S105-PARK", text);
        if (tv != null) tv.setText(text);
    }

    private final class Worker extends Thread {
        @Override public void run() {
            while (running) {
                Runnable t = poll();
                if (t != null) {
                    t.run();
                    if (executed >= 2) running = false;
                    continue;
                }
                parks++;
                LockSupport.parkNanos(2000);
            }
            android.util.Log.i("S105-PARK", "worker-exit executed=" + executed
                    + " parks=" + parks);
        }
    }

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout box = new LinearLayout(this);
        tv = new TextView(this);
        tv.setText("park-probe-start");
        box.addView(tv);
        setContentView(box);

        new Worker().start();

        // Task 1: queued before the worker's first slice - the ACTIVE leg.
        enqueue(new Runnable() { public void run() { note("task1"); } });

        // Task 2: arrives LATE (2.5s virtual) while the worker is parked -
        // the AWAKEN leg via the boundary re-drain.
        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            public void run() {
                enqueue(new Runnable() { public void run() { note("task2"); } });
            }
        }, 2500);
    }
}
