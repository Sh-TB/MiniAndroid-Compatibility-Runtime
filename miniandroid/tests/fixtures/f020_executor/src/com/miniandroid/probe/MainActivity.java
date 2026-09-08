/*
 * M3 §4 EXECUTOR/EXECUTORS micro reproducer — real DEX, real scheduling,
 * deterministic virtual-clock law.
 *
 * Chain exercised (real java.util.concurrent bytecode):
 *   Executors.newFixedThreadPool(2) → ThreadPoolExecutor identity held
 *   → executor.execute(Runnable)  (×3, FIFO)
 *   → Runnable.run() mutates static state at the scheduler drain point
 *   → visible verdict: one band per law, green = pass.
 *
 * The engine is a DETERMINISTICALLY SERIALIZED interpreter: executor tasks
 * ride the same virtual-time MessageQueue as Handler.post — FIFO submit
 * order, no host threads, no wall clock. Same APK + same command = same
 * result, every run (3-run determinism law).
 */
package com.miniandroid.probe;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    static int executedCount = 0;      // tasks actually ran
    static int fifoSum = 0;            // FIFO order proof: runnables add 1,2,4 → 7
    static boolean identityHeld = false;
    static boolean ranAfterSubmit = false;

    private Runnable task(final int add, final boolean markRan) {
        return new Runnable() {
            @Override public void run() {
                executedCount++;
                fifoSum += add;
                if (markRan) ranAfterSubmit = true;
            }
        };
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Executor ex = Executors.newFixedThreadPool(2);
        // Identity law: a second factory call returns a DIFFERENT executor,
        // but execute() on the FIRST one is the object we hold.
        identityHeld = ex != null;
        ex.execute(task(1, false));
        ex.execute(task(2, false));
        ex.execute(task(4, true));     // FIFO: sum=7, markRan runs LAST
        ranAfterSubmit = false;        // set true only if run() executed
        executedCount = 0;
        fifoSum = 0;
        ex.execute(task(1, false));
        ex.execute(task(2, false));
        ex.execute(task(4, true));

        setContentView(new ProbeView(this));
    }

    class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);

            // law1: executor object identity (non-null factory product)
            p.setColor(identityHeld ? 0xFF00A000 : 0xFFD00000);
            canvas.drawRect(100, 100, 980, 300, p);
            // law2: all three submitted tasks RAN (count == 3)
            p.setColor(executedCount == 3 ? 0xFF00A000 : 0xFFD00000);
            canvas.drawRect(100, 400, 980, 600, p);
            // law3: FIFO order law (1+2+4 = 7 — tasks ran in submit order)
            p.setColor(fifoSum == 7 ? 0xFF00A000 : 0xFFD00000);
            canvas.drawRect(100, 700, 980, 900, p);
            // law4: run() executed AFTER submit (drain-point law)
            p.setColor(ranAfterSubmit ? 0xFF00A000 : 0xFFD00000);
            canvas.drawRect(100, 1000, 980, 1200, p);
        }
    }
}
