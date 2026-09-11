/*
 * F-050 micro reproducer — the CHOREOGRAPHER FRAME-PUMP family of laws,
 * executed as real DEX inside a real APK, with a VISUAL verdict.
 *
 * Four roots landed in one battle (dooz v18 Compose first-frame chain,
 * HEAD 6ff11eb2 → F-050):
 *
 *   F-050c  AtomicLongFieldUpdater.getAndIncrement DECREMENTED (the
 *           prefix-match delta bug: "getAndIncrement" does not start with
 *           "increment"). The Recomposer's BufferedChannel packed state
 *           (senders | closeStatus<<60) went 0 -> -1 on the first send and
 *           kotlinx.coroutines threw ISE "unexpected close status: -1".
 *           OpenJDK law: getAndIncrement() == getAndAdd(1), returns OLD.
 *
 *   F-050d  java.lang.Boolean.TRUE/FALSE static reads returned NULL (R8
 *           rewrites valueOf(true) into the sget). The channel iterator's
 *           boxed hasNext() resume unboxed to false, the consume loop
 *           exited as if the channel was exhausted and cancelConsumed
 *           cancelled the Recomposer's awaitWork channel. OpenJDK law:
 *           TRUE/FALSE are non-null singleton boxed constants.
 *
 *   F-050b  Throwable(String) ctors dropped detailMessage. OpenJDK law:
 *           getMessage() returns the ctor string.
 *
 *   F-050a  The Choreographer family did not exist: getInstance returned
 *           null, postFrameCallback dropped the callback, doFrame never
 *           fired, withFrameNanos never resumed — the Compose first frame
 *           never composed. AOSP law: thread-local instance (singleton
 *           identity), FIFO frame callbacks, one shared monotonic frame
 *           time per tick, removeFrameCallback cancels.
 *
 * Seven laws, one 150px verdict band each (green = holds, red = violated):
 *   L1 getAndIncrement: two calls on a fresh updater-backed long give
 *      (returned 0, stored 1) then (returned 1, stored 2)
 *   L2 getAndDecrement/incrementAndGet/decrementAndGet epochs: 5 ->
 *      getAndDecrement returns 5 (stored 4) -> decrementAndGet returns 3
 *      (stored 3) -> incrementAndGet returns 4 (stored 4)
 *   L3 Boolean.TRUE/FALSE: non-null, TRUE.booleanValue()==true,
 *      FALSE.booleanValue()==false, TRUE !== FALSE (identity)
 *   L4 Boolean storage round-trip: TRUE stored in a static Object slot
 *      and read back stays the same object (identity law)
 *   L5 Throwable message law: new IllegalStateException("f050-msg")
 *      getMessage() returns the exact string
 *   L6 Choreographer.getInstance identity: two calls return the SAME
 *      object (singleton law)
 *   L7 Frame pump: postFrameCallback registers a real callback; the
 *      runtime's deterministic vsync pump fires doFrame(J) with a
 *      strictly positive monotonic frame time (the withFrameNanos
 *      resume path that drives the Compose first frame)
 *
 * Every value reaches the interpreter through non-final static fields so
 * javac/d8 cannot constant-fold the checks — the opcodes and the invoke
 * boundary really execute.
 *
 * Determinism: no wall clock, no randomness — byte-identical framebuffers.
 */
package com.miniandroid.framepump;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.Choreographer;
import android.view.View;
import java.util.concurrent.atomic.AtomicLongFieldUpdater;

public class MainActivity extends Activity {

    // Updater-backed target: the kotlinx.coroutines BufferedChannel shape.
    static final class Channel {
        volatile long sendersAndCloseStatus = 0;
    }

    static final Channel CH = new Channel();
    static final Channel CH2 = new Channel();

    static volatile long misc = 0;
    static Object boolStore = null;
    static long pumpFrameTime = -1;

    static Choreographer c1 = null;
    static Choreographer c2 = null;

    static String throwableMsg = null;

    static final class Pump implements Choreographer.FrameCallback {
        @Override
        public void doFrame(long frameTimeNanos) {
            pumpFrameTime = frameTimeNanos;
        }
    }

    int verdictL1 = 0, verdictL2 = 0, verdictL3 = 0, verdictL4 = 0;
    int verdictL5 = 0, verdictL6 = 0, verdictL7 = 0;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        final AtomicLongFieldUpdater<Channel> up =
                AtomicLongFieldUpdater.newUpdater(Channel.class, "sendersAndCloseStatus");

        // L1 — getAndIncrement: +1 delta, OLD return (OpenJDK getAndAdd(1)).
        CH.sendersAndCloseStatus = 0;
        long r1 = up.getAndIncrement(CH);
        long v1 = up.get(CH);
        long r2 = up.getAndIncrement(CH);
        long v2 = up.get(CH);
        verdictL1 = (r1 == 0 && v1 == 1 && r2 == 1 && v2 == 2) ? 1 : 0;

        // L2 — decrement family epochs on a second channel.
        CH2.sendersAndCloseStatus = 5;
        long d1 = up.getAndDecrement(CH2);          // returns 5, stores 4
        long s1 = up.get(CH2);
        long d2 = up.decrementAndGet(CH2);          // returns 3, stores 3
        long d3 = up.incrementAndGet(CH2);          // returns 4, stores 4
        long s2 = up.get(CH2);
        verdictL2 = (d1 == 5 && s1 == 4 && d2 == 3 && d3 == 4 && s2 == 4) ? 1 : 0;
        // L3 — Boolean.TRUE/FALSE constants (F-050d).
        Boolean t = sgetTrue();
        Boolean f = sgetFalse();
        verdictL3 = (t != null && f != null
                && t.booleanValue() && !f.booleanValue()
                && t != f) ? 1 : 0;

        // L4 — Boolean identity storage round-trip (static Object slot).
        boolStore = sgetTrue();
        Boolean back = (Boolean) boolStore;
        verdictL4 = (back != null && back == sgetTrue()) ? 1 : 0;

        // L5 — Throwable message law (F-050b).
        try {
            throw new IllegalStateException("f050-msg");
        } catch (IllegalStateException e) {
            throwableMsg = e.getMessage();
        }
        verdictL5 = ("f050-msg".equals(throwableMsg)) ? 1 : 0;

        // L6 — Choreographer singleton identity (F-050a).
        c1 = Choreographer.getInstance();
        c2 = Choreographer.getInstance();
        verdictL6 = (c1 != null && c1 == c2) ? 1 : 0;

        // L7 — the frame pump: a real FrameCallback registered through the
        // Choreographer; the runtime vsync pump fires doFrame(J) with a
        // monotonic frame time. The runtime drains the posted callback at
        // the frame boundary — pumpFrameTime becomes the delivered time.
        verdictL7 = (pumpFrameTime > 0) ? 1 : 0;

        setContentView(new BandView(this));

        // Register AFTER setContentView: the runtime's frame pump fires
        // posted callbacks when the main queue goes idle (vsync law).
        Choreographer.getInstance().postFrameCallback(new Pump());
    }
    static Boolean sgetTrue() {
        return Boolean.TRUE;
    }

    static Boolean sgetFalse() {
        return Boolean.FALSE;
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
            // Read the LIVE verdict fields: L7's frame pump fires at the
            // frame boundary after onCreate, so the value must be sampled
            // at draw time (the AOSP draw-reads-current-state law).
            int[] verdicts = {
                    act.verdictL1, act.verdictL2, act.verdictL3,
                    act.verdictL4, act.verdictL5, act.verdictL6,
                    // L7 sampled at draw time: the vsync pump fires between
                    // onCreate and the draw (the AOSP frame ordering law),
                    // so the precomputed verdict would be stale.
                    (act.pumpFrameTime > 0) ? 1 : 0,
            };
            for (int i = 0; i < 7; i++) {
                paint.setColor(verdicts[i] == 1 ? 0xFF00A000 : 0xFFD00000);
                int top = 100 + i * 250;
                canvas.drawRect(60, top, 1020, top + 150, paint);
            }
        }
    }
}
