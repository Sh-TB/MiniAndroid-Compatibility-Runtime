/*
 * M5 F-030 micro reproducer — the ZERO-IS-NULL-AT-REFERENCE-USE LAW,
 * executed as real DEX inside a real APK, with a VISUAL verdict.
 *
 * Single law family under proof (Dalvik register model, F-028 extension):
 *     Dalvik registers are UNTYPED 32-bit slots. `const/4 vX, #0` loads
 *     the POLYMORPHIC zero word: int 0 in a primitive context, the NULL
 *     REFERENCE in a reference context. ART's verifier materializes this
 *     as the `Zero` reg-type, convertible to any reference type. The
 *     tagged-union engine must re-type an INT32(0) argument as null when
 *     the callee's declared parameter type is a reference (L...; / [...).
 *
 * Historical defect class (pre-F-030): const/4 #0 crossed the invoke
 * boundary tagged INT32(0); identity-sensitive consumers saw boxed-int-0
 * instead of null. First real-APK hit: dooz LY1/b;.D passes const/4 #0
 * as the `expected` state of the Segment cell CAS (LY1/j;.j over an
 * AtomicReferenceArray) — the CAS can never match (correct F-028h law:
 * null is not boxed Integer 0) and the lock-free coroutine scheduler
 * spins forever (rc=timeout, 99,803+ AtomicReferenceArray.get calls).
 *
 * Seven laws, one 150px verdict band each (green = holds, red = violated):
 *   L1 null-CAS law: AtomicReferenceArray.compareAndSet(1, null, token)
 *        on a fresh cell succeeds — the exact dooz Segment shape
 *        (const/4 #0 as the `expected` Object param through the invoke
 *        boundary into the identity CAS)
 *   L2 null param identity: isNull(Object) called with literal null
 *        returns true (callee sees null, not boxed 0)
 *   L3 null return across boundary: getNull() returns null through
 *        move-result-object and == null holds (the Segment.k() shape)
 *   L4 primitive zero unaffected: an int 0 argument stays int 0 through
 *        the same invoke machinery (Zero law must not corrupt int params)
 *   L5 F-028h identity preserved: CAS with a REAL boxed Integer(0)
 *        against a fresh (null) cell FAILS — null is not boxed Integer 0;
 *        only the unboxed const-zero re-types
 *   L6 queue publication pattern (kotlinx.coroutines LockFreeTaskQueueCore
 *        reserve/publish/consume, single logical thread): state CAS
 *        null->RESERVED succeeds, element published, consumer observes it
 *   L7 null storage round-trip: null in a static Object slot and in an
 *        Object[] element reads back null through sget/sput/aput/aget
 *
 * Every value reaches the interpreter through non-final static fields or
 * arrays so javac/d8 cannot constant-fold the checks — the opcodes and
 * the invoke boundary really execute.
 *
 * Determinism: no time, no randomness, no collections — the same 7 bands
 * every run, byte-identical framebuffer.
 */
package com.miniandroid.zerolaw;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import java.util.concurrent.atomic.AtomicReferenceArray;

public class MainActivity extends Activity {

    static final int RESERVED = 0x52535644;  // 'RSVD' — reservation token

    static AtomicReferenceArray<Object> cells = new AtomicReferenceArray<>(8);
    static Object token = new Object();
    static Object published = new Object();

    static int zeroSrc = 0;         // real int zero source (sget at runtime)
    static int addResult;
    static Object nullSlot;         // L7 static round-trip (defaults null)
    static Object[] objArr = new Object[3];
    static Object boxedZero = Integer.valueOf(0);

    static boolean isNull(Object o) { return o == null; }

    static int addOne(int i) { return i + 1; }

    static Object getNull() { return null; }

    static boolean l1 = false, l2 = false, l3 = false,
                   l4 = false, l5 = false, l6 = false, l7 = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // L1 — the exact dooz LY1/b;.D -> LY1/j;.j shape: const/4 #0
            // travels as an Object-typed argument into compareAndSet and
            // must be seen as null by the identity CAS against the fresh
            // (null) cell.
            l1 = cells.compareAndSet(1, null, token);

            // L2 — null param identity through the invoke boundary.
            l2 = isNull(null);

            // L3 — null return through move-result-object stays null.
            Object back = getNull();
            l3 = (back == null) && isNull(back);

            // L4 — the same zero word in a PRIMITIVE param stays int 0.
            l4 = (addOne(zeroSrc) == 1) && (addOne(0) == 1);

            // L5 — F-028h identity law preserved: a REAL boxed Integer(0)
            // is an object, not null — CAS against the fresh cell fails,
            // and getAndSet still works afterwards.
            boolean casBoxed = cells.compareAndSet(2, boxedZero, token);
            Object prev = cells.getAndSet(2, null);
            l5 = !casBoxed && (prev == null) && isNull(cells.get(2));

            // L6 — queue publication: reserve slot 3 by CAS(null -> token),
            // publish the element, consume it — the reserve/publish/
            // consume triple the coroutine queue machinery relies on.
            boolean reserved = cells.compareAndSet(3, null, token);
            cells.set(3, published);
            Object consumed = cells.get(3);
            Object reservedCell = cells.get(1);
            l6 = reserved && (consumed == published)
                        && (reservedCell == token);

            // L7 — null survives the storage round-trip.
            nullSlot = null;
            objArr[1] = null;
            Object r1 = nullSlot;
            Object r2 = objArr[1];
            l7 = (r1 == null) && (r2 == null) && isNull(r1) && isNull(r2);
        } catch (Throwable t) {
            // any throw = law chain violated; bands render red
        }
        setContentView(new ProbeView(this));
    }

    class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);
            boolean[] laws = { l1, l2, l3, l4, l5, l6, l7 };
            for (int i = 0; i < 7; i++) {
                p.setColor(laws[i] ? 0xFF00A000 : 0xFFD00000);
                int top = 100 + i * 250;
                canvas.drawRect(100, top, 980, top + 150, p);
            }
        }
    }
}
