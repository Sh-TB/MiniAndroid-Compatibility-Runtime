package com.probe.f289;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-289 probe — MAIN-QUEUE DELIVERY IDENTITY LAW.
 *
 * AOSP law (Looper/Handler model): code delivered by the main Looper's
 * MessageQueue ALWAYS executes on the main thread — inside every
 * main-queue Runnable,
 *     Thread.currentThread() == Looper.getMainLooper().getThread()
 * must hold (the DefaultTaskExecutor.isMainThread contract that androidx
 * LiveData.assertMainThread enforces; a violation throws
 * IllegalStateException "Cannot invoke setValue on a background thread").
 *
 * Discriminating scenario: a WORKER thread (Thread subclass — the
 * composeStopwatch/DataStore executor shape) posts the probe Runnable to
 * the main handler FROM INSIDE its run() body. On ART the worker returns
 * and the main Looper delivers the Runnable on the main thread. A
 * deterministic engine that drains the queue nested inside the worker's
 * run-to-completion body (F-110d worker identity) must RE-BIND the main
 * identity for the delivery — this probe isolates exactly that handoff.
 *
 * Rows (appended by the runnables; the FINAL posted runnable renders the
 * summary into the TextView + the results file so the whole handshake is
 * captured by the engine's drain):
 *   BODY-WORKER  inside the thread body: currentThread != main  (F-110d law;
 *                must stay TRUE — the body runs on the worker)
 *   QUEUE-MAIN   inside the main-queue Runnable: currentThread == main
 *                (the F-NEW-289 law under test)
 *   LOP-MAIN     inside the Runnable: Looper.myLooper() == main Looper
 *   SUMMARY      PASS iff all rows pass
 */
public class MainActivity extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;
    static TextView tv = null;
    static String summary = "F289|SUMMARY|FAIL|rows did not complete";

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F289|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        tv = new TextView(this);
        setContentView(tv);

        final Handler main = new Handler(Looper.getMainLooper());
        final Thread mainRef = Looper.getMainLooper().getThread();

        // Worker = Thread subclass (self-run law; the kotlinx worker shape).
        // The body posts to the main handler, THEN parks — the coroutines
        // "post continuation, park worker" shape. The engine's park law
        // (R-NEW-345) drains the main queue at the park point, NESTED inside
        // the worker's run-to-completion body: exactly the delivery whose
        // thread identity is under test.
        Thread worker = new Thread() {
            @Override public void run() {
                Thread self = Thread.currentThread();
                row("BODY-WORKER", self != mainRef,
                    "body currentThread!=main: " + (self != mainRef));
                main.post(new Runnable() {
                    @Override public void run() {
                        Thread cur = Thread.currentThread();
                        boolean isMain = (cur == mainRef);
                        row("QUEUE-MAIN", isMain,
                            "queue currentThread==main: " + isMain);
                        boolean lopMain =
                            Looper.myLooper() == Looper.getMainLooper();
                        row("LOP-MAIN", lopMain,
                            "queue myLooper==mainLooper: " + lopMain);
                        // Final link: render + persist AFTER all rows exist.
                        main.post(new Runnable() {
                            public void run() { finishProbe(); }
                        });
                    }
                });
                // kotlinx worker park: the deterministic engine drains the
                // main MessageQueue at this park boundary (R-NEW-345 law).
                java.util.concurrent.locks.LockSupport.parkNanos(1000000L);
            }
        };
        try {
            worker.start();   // deterministic engine: body drains inline
        } catch (Throwable t) {
            row("HARNESS", false, t.getClass().getName() + ": " + t.getMessage());
            finishProbe();
        }
    }

    static synchronized void finishProbe() {
        summary = "F289|SUMMARY|" + (fail == 0 && pass >= 3 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        sb.append(summary);
        String text = sb.toString();
        if (tv != null) tv.setText(text);
        try {
            java.io.FileOutputStream fos =
                tv.getContext().openFileOutput("f289_results.txt", MODE_PRIVATE);
            fos.write(text.getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t) { }
    }
}
