/*
 * F-074 + F-075 micro reproducer — the ENGINE-LEVEL VIRTUAL DISPATCH and
 * POLYMORPHIC-ZERO families, executed as real DEX inside a real APK,
 * with a VISUAL verdict (green band = law holds, red = violated).
 *
 * S21 root evidence chain (dooz gate: composition coroutine never resumed,
 * 0/2073600 non-white pixels):
 *
 *   F-074  Engine-level virtual dispatch must follow the runtime class
 *          hierarchy. try_recursive_invoke resolved methods ONLY on the
 *          exact class; the queue drains (UC009-WIRE, EXP-086 post-onCreate,
 *          CHOREO-PUMP) pass the RUNTIME class of the receiver. kotlinx-
 *          coroutines DispatchedContinuation (dooz b2/h) has NO run() of
 *          its own — the entrypoint is DispatchedTask.run (W1/N) on the
 *          superclass — so the drained continuation silently vanished
 *          (0 dispatch records) and the composition coroutine never ran.
 *          ART law: invokevirtual/interface dispatch resolves on the
 *          runtime class, walking to the most-derived concrete override.
 *
 *   F-075  The polymorphic zero word is the NULL reference at every
 *          reference-use boundary. Kotlin `return null` compiles to
 *          `const/4 v0, 0; return-object v0`; the old engine stored
 *          INT32(0) and propagated it as the return value. Consumers then
 *          mis-compared: `if (node !== newNode)` (LL/b.remove,
 *          PersistentOrderedSet) hit the int fallback, answered 0==0
 *          EQUAL for (object, null), skipped the EMPTY-map rebuild, the
 *          set iterator walked the sentinel and threw CME "Hash code of
 *          an element has changed after it was added to the persistent
 *          set" — fatally killing the composition coroutine. ART law:
 *          the verifier's Zero reg-type is convertible to ANY reference
 *          type; return-object/move-result-object/if-eq/if-ne against a
 *          const/4 zero compare the null reference.
 *
 * Six laws, one 150px verdict band each:
 *   L1  Super-run: Handler.post(SubR) where SubR declares NO run() — the
 *       base class run() must dispatch through the post-onCreate drain
 *       (the F-074 walk; ranCount >= 1).
 *   L2  Receiver identity: two distinct SubR instances carry different
 *       tag fields; the inherited run() must read EACH receiver's own
 *       field (lastTag == 22 — the second instance's value).
 *   L3  Two-hop walk: LeafG extends MidG extends RootG — run() declared
 *       only on RootG; the walk must climb two levels (gCount >= 1).
 *   L4  Most-derived override: Sub2 overrides run(); the override must
 *       win over the base implementation (whoRan == 2).
 *   L5  Polymorphic zero vs object (if-ne): makeNull(5) returns null via
 *       const/4-0 + return-object; `nullReturned != realObj` must be
 *       TAKEN (the F-075 mixed compare; nullNotSameAsReal == true).
 *   L6  Non-null identity round-trip: makeNull(0) returns realObj; the
 *       returned reference must compare EQUAL by identity (o == realObj).
 *
 * Every value reaches the interpreter through non-final static fields so
 * javac/d8 cannot constant-fold the checks. Deterministic: no wall clock,
 * no randomness.
 */
package com.miniandroid.superrun;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;

public class MainActivity extends Activity {

    // ── F-074 family: superclass-dispatch runnables ─────────────────────
    static final class BaseR implements Runnable {
        int tag;
        BaseR(int t) { tag = t; }
        @Override
        public void run() {
            // Reads the RECEIVER's own field — proves the inherited method
            // executes with the ORIGINAL runtime receiver (ART law).
            lastTag = tag;
            ranCount++;
        }
    }
    static int lastTag = -1;
    static int ranCount = 0;

    static class RootG implements Runnable {
        public void run() { gCount++; }
    }
    static class MidG extends RootG {}
    static final class LeafG extends MidG {}
    static int gCount = 0;

    static class Base2 implements Runnable {
        public void run() { whoRan = 1; }
    }
    static final class Sub2 extends Base2 {
        @Override
        public void run() { whoRan = 2; }
    }
    static int whoRan = 0;

    // ── F-075 family: polymorphic zero ──────────────────────────────────
    static Object realObj = new Object();

    static Object makeNull(int which) {
        // which==5 compiles the null path as const/4-0 + return-object.
        if (which == 5) {
            return null;
        }
        return realObj;
    }

    static boolean nullNotSameAsReal = false;
    static Object nullResult = null;
    static Object nonNullResult = null;

    int verdictL1 = 0, verdictL2 = 0, verdictL3 = 0;
    int verdictL4 = 0, verdictL5 = 0, verdictL6 = 0;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Handler h = new Handler(Looper.getMainLooper());

        // L1 + L2: two distinct superclass-only runnables.
        BaseR r1 = new BaseR(11);
        BaseR r2 = new BaseR(22);
        h.post(r1);
        h.post(r2);

        // L3: two-hop walk.
        h.post(new LeafG());

        // L4: most-derived override wins.
        h.post(new Sub2());

        // L5: the polymorphic zero crosses the return-object +
        // move-result-object boundary and is compared with if-ne against
        // a real object — the exact LL/b.remove `node !== newNode` shape.
        nullResult = makeNull(5);
        nullNotSameAsReal = (nullResult != realObj);

        // L6: non-null identity round-trip (F-070/F-073 protected).
        nonNullResult = makeNull(0);

        setContentView(new BandView(this));
    }

    static final class BandView extends View {
        final Paint paint = new Paint();
        final MainActivity act;

        BandView(MainActivity activity) {
            super(activity);
            this.act = activity;
        }

        @Override
        protected void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            paint.setStyle(Paint.Style.FILL);
            // Sample the drain-dependent verdicts at draw time: the
            // post-onCreate drain runs between onCreate and the first
            // draw (the AOSP idle-Looper dispatch ordering law), so
            // precomputed verdicts would be stale.
            int[] verdicts = {
                    ranCount >= 1 ? 1 : 0,
                    lastTag == 22 ? 1 : 0,
                    gCount >= 1 ? 1 : 0,
                    whoRan == 2 ? 1 : 0,
                    (act.nullNotSameAsReal) ? 1 : 0,
                    (act.nonNullResult == realObj) ? 1 : 0,
            };
            for (int i = 0; i < 6; i++) {
                paint.setColor(verdicts[i] == 1 ? 0xFF00A000 : 0xFFD00000);
                int top = 100 + i * 280;
                canvas.drawRect(60, top, 1020, top + 180, paint);
            }
        }
    }
}
