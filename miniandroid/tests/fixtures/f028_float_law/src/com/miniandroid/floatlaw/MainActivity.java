/*
 * M3 F-028 micro reproducer — the UNTYPED-REGISTER CONVERSION LAW,
 * executed as real DEX inside a real APK, with a VISUAL verdict.
 *
 * Single law family under proof (Dalvik register model):
 *     Registers are UNTYPED 32-bit slots; the OPCODE — not a runtime
 *     value tag — defines the source interpretation. A register holding
 *     the raw bits of 115.0f (0x42E60000), produced by const/high16 and
 *     stored through a float static, MUST read as 115 via float-to-int
 *     (bit reinterpretation), not as 1120702464 (numeric conversion of
 *     the int-tagged word).
 *
 * Historical defect class (pre-F-028): the conversion/comparison/float
 * arithmetic sites numeric-converted INT32-tagged raw float bits. First
 * real-APK hit: Material3 LG0/b.<clinit> in Dooz builds FontScaleConverter
 * table keys via const/high16 float bits + float-to-int and threw
 * IllegalStateException "You should only apply non-linear scaling to font
 * scales > 1". No app special-casing anywhere.
 *
 * Seven laws, one 150px verdict band each (green = holds, red = violated):
 *   L1 const/high16 float literal -> float static -> float-to-int:
 *        (int) sKey == 115                     (the exact dooz pattern)
 *   L2 int-to-float of a real int: (float) i180 == 180.0f, cmp vs
 *        const/high16 180.0f
 *   L3 the dooz arithmetic chain: ((float)200 / sHundred - sTwo) > sOne
 *        (div-float/2addr + sub-float/2addr + cmpg-float on const/high16
 *        and const operands)
 *   L4 round-toward-zero: (int)-2.5f == -2, (int)0.9f == 0,
 *        (int)1.9f == 1
 *   L5 NaN->0 and saturation: (int)(0.0f/0.0f) == 0,
 *        (int)1e30f == Integer.MAX_VALUE
 *   L6 float identity through call paths: static method, virtual
 *        method, interface DEFAULT method — 1.0f preserved exactly
 *   L7 float bits through storage: float static + float[] element
 *        round-trips (sput/sget, aput/aget) preserve -2.5f/115.0f
 *
 * Every float constant reaches the interpreter through NON-FINAL static
 * fields (sget) or arrays so javac/d8 cannot constant-fold the checks —
 * the opcodes really execute.
 *
 * Determinism: no time, no randomness, no collections — the same 7 bands
 * every run, byte-identical framebuffer.
 */
package com.miniandroid.floatlaw;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {

    // Non-final statics: every read is a real sget/iget at runtime.
    static float sKey = 115.0f;      // const/high16 0x42e6 — the dooz key
    static float sHundred = 100.0f;  // const/high16 0x42c8 — dooz divisor
    static float sTwo = 0.02f;       // const 0x3ca3d70a — dooz subtrahend
    static float sOne = 1.0f;        // const/high16 0x3f80 — dooz bound
    static float sNeg = -2.5f;       // const/high16 0xc020
    static float s09 = 0.9f;         // const 0x3f666666
    static float s19 = 1.9f;         // const 0x3ff33333
    static float sBig = 1.0e30f;     // const 0x7d21dc40 — saturates f2i
    static float sZero = 0.0f;       // const/high16 0x0000
    static int i180 = 180;           // real int for int-to-float
    static int key;
    static float fRound1, fRound2;   // storage round-trip slots
    static float[] fArr = new float[3];

    static boolean l1 = false, l2 = false, l3 = false,
                   l4 = false, l5 = false, l6 = false, l7 = false;

    interface FloatId {
        default float id(float x) { return x; }   // default method, F path
    }
    static class FloatIdImpl implements FloatId { }

    static float ident(float x) { return x; }     // static F->F path

    static class Holder {
        float viaVirtual(float x) { return x; }   // virtual F->F path
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // L1 — the exact dooz G0/b pattern: const/high16 float bits
            // travel const/high16 -> sput :F -> sget -> float-to-int.
            key = (int) sKey;
            l1 = (key == 115);

            // L2 — int-to-float of a real int + cmp against const/high16.
            float f180 = (float) i180;
            l2 = (f180 == 180.0f) && (f180 > 179.0f);

            // L3 — the dooz arithmetic chain: 200/100.0f - 0.02f = 1.98,
            // compared > 1.0f. Every operand arrives via the laws above.
            float v = (float) key /* 115 */ ;
            float w = ((float) i180 + 20.0f);          // 200.0f, arith law
            float chain = w / sHundred - sTwo;         // 2.0 - 0.02 = 1.98
            l3 = (chain > sOne) && (chain < sKey / 50.0f /* 2.3 */);

            // L4 — round-toward-zero (truncate) law on negative/fractional.
            l4 = ((int) sNeg == -2) && ((int) s09 == 0) && ((int) s19 == 1);

            // L5 — NaN -> 0 and saturation laws (f2i/f2l spec behavior).
            float nan = sZero / sZero;
            l5 = ((int) nan == 0) && ((int) sBig == Integer.MAX_VALUE);

            // L6 — float identity through static + virtual + interface
            // default-method dispatch; 1.0f must survive every path.
            float a = ident(sOne);
            float b = new Holder().viaVirtual(sOne);
            float c = new FloatIdImpl().id(sOne);
            l6 = (a == sOne) && (b == sOne) && (c == sOne) && (a == 1.0f);

            // L7 — float bits through storage: sput/sget and aput/aget.
            fRound1 = sKey;          // sput of the 115.0f bit pattern
            fArr[1] = sNeg;          // aput into a float[] element
            fRound2 = fArr[1];       // aget back
            l7 = (fRound1 == sKey) && (fRound2 == sNeg) && (fArr[1] == -2.5f);
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
