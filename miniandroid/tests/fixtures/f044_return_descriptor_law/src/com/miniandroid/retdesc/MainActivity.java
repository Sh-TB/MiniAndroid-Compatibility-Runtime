/*
 * M7 (MASTER CAMPAIGN 4) F-044 micro reproducer — the PER-FRAME RETURN
 * DESCRIPTOR LAW, executed as real DEX inside a real APK, visual verdict.
 *
 * Single law family under proof (Dalvik return model, CHAR-PROBE law
 * completion):
 *     A method's `return` opcode defines the returned value's
 *     interpretation by the method's OWN return descriptor, regardless of
 *     which descriptors the methods it CALLED had. An int-returning
 *     method must yield its full 32-bit value even after calling
 *     boolean/void/Object-returning methods: the per-frame descriptor
 *     context must not leak across recursive invoke frames.
 *
 * Historical defect class (pre-F-044): the engine kept ONE global
 * `current_method_descriptor_`, set at frame entry but never restored
 * after a nested call returned. A caller whose last callee returned
 * boolean therefore executed `return vAA` with the CALLEE's ")Z"
 * descriptor current, and the signature-aware return typing
 * re-interpreted the int bits as a boolean (non-zero -> 1). Every int
 * return value collapsed to 0/1 whenever the method called anything
 * boolean-returning last.
 *
 * First real-APK hit: dooz Compose DerivedSnapshotState version scan
 * (LF/F$a.d) — computes ((7*31 + identityHashCode)*31 + recordId) = 6729,
 * calls SnapshotIdSet.contains (")Z") last, then returns. The 6729 came
 * back as BOOLEAN(1), so the record-validity compare (cached version vs
 * re-scanned version) matched 1 == 1 forever: the dependency-change
 * detection could NEVER fire, the derived state was permanently stale,
 * AndroidComposeView.getViewTreeOwners() read back the pre-write null,
 * and the Intrinsics checkNotNull threw the NPE that killed
 * MainActivity.onCreate at the dooz app boundary (rc=1, blank frame).
 *
 * Seven laws, one 150px verdict band each (green = holds, red = violated):
 *   L1 int return after a boolean callee (the exact dooz .d shape):
 *        versionHash() calls zCallee() then returns 6729 — must read 6729
 *   L2 int return after an Object callee: 6729 preserved
 *   L3 int return after a void callee, NEGATIVE value: -5 preserved
 *   L4 boolean return after an int callee: boolean semantics intact in
 *        the reverse direction (no cross-corruption either way)
 *   L5 the dooz nested .c -> .d -> q shape: I-method calls Z-method that
 *        calls I-method; outer still returns its own full 6729
 *   L6 the dooz dependency-change law: the scanned version differs when
 *        the record id changes (6729 -> 6731) — pre-F-044 both collapsed
 *        to boolean 1, so a dependency write was permanently invisible
 *   L7 Object return after a boolean callee: reference identity preserved
 *        (the getValue/move-result-object path)
 *
 * Every value reaches the interpreter through non-final static fields so
 * javac/d8 cannot constant-fold the arithmetic — the return opcodes and
 * the per-frame descriptor context really execute.
 *
 * Determinism: no time, no randomness, no collections — the same 7 bands
 * every run, byte-identical framebuffer.
 */
package com.miniandroid.retdesc;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {

    // Runtime sources — statics so d8 cannot fold the arithmetic.
    static boolean flag = true;
    static int recordId = 2;          // the "record snapshot id" stand-in
    static int hashSeed = 7;          // the version-scan accumulator seed
    static int mulConst = 31;         // the rolling-hash multiplier
    static Object token = new Object();

    static boolean zCallee() { return flag; }                    // )Z
    static Object oCallee() { return token; }                    // )Ljava/lang/Object;
    static void vCallee() { flag = !flag; flag = !flag; }        // )V (net no-op)
    static int iCallee() { return mulConst * 2 + 11; }           // )I (73)

    // L1 — the exact dooz LF/F$a.d shape: boolean callee LAST, then a
    // full int return (6729 — the real dooz version hash magnitude).
    static int versionHash() {
        boolean b = zCallee();
        return ((hashSeed * mulConst) + 0) * mulConst + recordId;
    }

    // L2 — int return after an Object-returning callee.
    static int afterObj() {
        Object o = oCallee();
        return ((hashSeed * mulConst) + 0) * mulConst + recordId;
    }

    // L3 — int return after a void callee; NEGATIVE value keeps all bits.
    static int afterVoid() {
        vCallee();
        return -5;
    }

    // L4 — the reverse direction: boolean return after an int callee.
    static boolean afterInt() {
        int v = iCallee();
        return v > mulConst;
    }

    // L5 — the dooz nested .c -> .d -> contains() shape.
    static int innerInt() { return recordId; }
    static boolean midZ() { return innerInt() > 0; }
    static int outerVersion() {
        boolean b = midZ();
        return ((hashSeed * mulConst) + 0) * mulConst + recordId;
    }

    // L6 — the dependency-change detection law: the scanned version must
    // CHANGE when the record id changes (2 -> 4). Pre-F-044 both scans
    // collapsed to boolean 1 and the write was permanently invisible.
    static int scanVersion() {
        boolean inSet = zCallee();
        return ((hashSeed * mulConst) + 0) * mulConst + recordId;
    }

    // L7 — Object return after a boolean callee: identity preserved.
    static Object afterBoolObj() {
        boolean b = zCallee();
        return token;
    }

    static boolean l1 = false, l2 = false, l3 = false,
                   l4 = false, l5 = false, l6 = false, l7 = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // L1 — int survives a trailing boolean callee (6729, not 1).
            l1 = versionHash() == 6729;

            // L2 — int survives a trailing Object callee.
            l2 = afterObj() == 6729;

            // L3 — int survives a trailing void callee, negative intact.
            l3 = afterVoid() == -5;

            // L4 — boolean return after an int callee stays boolean.
            l4 = afterInt();

            // L5 — the nested .c -> .d -> q shape keeps the outer value.
            l5 = outerVersion() == 6729;

            // L6 — dependency-change detection: version differs when the
            // record id moves 2 -> 4 (the write-invalidates-read law).
            int vBefore = scanVersion();       // 217*31 + 2 = 6729
            recordId = 4;                      // the "write" advances the id
            int vAfter = scanVersion();        // 217*31 + 4 = 6731
            l6 = (vBefore == 6729) && (vAfter == 6731) && (vBefore != vAfter);

            // L7 — reference identity survives a trailing boolean callee.
            Object a = afterBoolObj();
            l7 = (a == token) && (a != null);
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
