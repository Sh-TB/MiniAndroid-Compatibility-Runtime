/*
 * M6 F-040 micro reproducer — the java.util.Arrays.fill FAMILY LAW,
 * executed as real DEX inside a real APK, with a VISUAL verdict.
 *
 * Single law family under proof (OpenJDK/AOSP ojluni Arrays.java):
 *     Arrays.fill(a, v) assigns the SAME reference/bits to EVERY element;
 *     Arrays.fill(a, from, to, v) does a[from..to) after rangeCheck:
 *         fromIndex > toIndex -> IllegalArgumentException
 *         fromIndex < 0       -> ArrayIndexOutOfBoundsException
 *         toIndex > a.length  -> ArrayIndexOutOfBoundsException
 *     Reference identity is preserved for Object arrays (every element
 *     is the identical object), and the WIDE (long/double) value must
 *     survive the invoke boundary as a full 64-bit tagged value.
 *
 * Historical defect class (pre-F-040): MiniAndroid had NO Arrays.fill
 * handler, so the call was a silent no-op. Kotlin stdlib compiles its
 * scatter-map metadata initialization (ArraysKt.fill with the EMPTY
 * 0x8080808080808080 marker) down to `Ljava/util/Arrays;.fill([J I I J)V`
 * — freshly-allocated hash tables stayed all-zero and the SWAR probe
 * loop could never observe an EMPTY control byte. First real-APK hit:
 * dooz Compose DerivedSnapshotState dependency table — Lh/u;.a probe
 * spun forever (38,000+ Object.equals calls, rc=124 timeout, blank
 * framebuffer).
 *
 * Seven laws, one 150px verdict band each (green = holds, red = violated):
 *   L1 the dooz metadata init law: new long[8] + Arrays.fill(range 0..len,
 *        0x8080808080808080) — every 64-bit window equals the EMPTY marker
 *   L2 range fill + rangeCheck law: fill middle with 0L, boundaries intact;
 *        from>to throws IAE; to>len throws AIOOBE (both caught)
 *   L3 int[] whole + range fill (4-arg and 2-arg variants)
 *   L4 Object[] fill: null fill reads back null; token fill reads back the
 *        IDENTICAL reference at every slot (a[i] == token reference law)
 *   L5 byte[]/short[]/char[]/boolean[] fills (the whole primitive family)
 *   L6 float[]/double[] fill (wide-tagged values through the invoke)
 *   L7 the ScatterMap probe-readback simulation: after EMPTY fill every
 *        control byte (meta[i>>3] >>> ((i&7)<<3)) & 0xFF is 0x80; after the
 *        insert-commit shape writes the H2 tag at slot 5, slot 5 reads tag
 *        and slot 0 still reads EMPTY — the exact marker-window law that
 *        made the Lh/u;.a probe spin when fill was missing
 *
 * Every value reaches the interpreter through non-final static fields or
 * arrays so javac/d8 cannot constant-fold the checks — Arrays.fill really
 * executes through the API dispatch boundary.
 *
 * Determinism: no time, no randomness, no collections — the same 7 bands
 * every run, byte-identical framebuffer.
 */
package com.miniandroid.filllaw;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import java.util.Arrays;

public class MainActivity extends Activity {

    static long EMPTY_MARKER = 0x8080808080808080L;  // the ScatterMap Empty byte x8
    static long TAG_H2 = 0x3F;                        // a 7-bit H2 control tag
    static int lenSrc = 8;                            // runtime length source

    static long[] meta = new long[8];
    static long[] rangeArr = new long[6];
    static int[] ints = new int[5];
    static Object[] objs = new Object[4];
    static Object token = new Object();
    static byte[] bytes = new byte[3];
    static short[] shorts = new short[3];
    static char[] chars = new char[3];
    static boolean[] bools = new boolean[4];
    static float[] floats = new float[3];
    static double[] doubles = new double[3];

    static boolean l1 = false, l2 = false, l3 = false,
                   l4 = false, l5 = false, l6 = false, l7 = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            // L1 — the exact dooz Lh/r;.d -> Ln/a;.r -> Arrays.fill([J I I J)
            // shape: metadata windows initialized to the EMPTY marker.
            meta = new long[lenSrc];
            Arrays.fill(meta, 0, meta.length, EMPTY_MARKER);
            boolean all = meta.length == lenSrc;
            for (int i = 0; i < meta.length; i++) all &= meta[i] == EMPTY_MARKER;
            l1 = all;

            // L2 — range fill + the OpenJDK rangeCheck law.
            rangeArr = new long[6];
            Arrays.fill(rangeArr, EMPTY_MARKER);
            Arrays.fill(rangeArr, 2, 4, 0L);
            boolean rangeOk = rangeArr[0] == EMPTY_MARKER
                           && rangeArr[1] == EMPTY_MARKER
                           && rangeArr[2] == 0L && rangeArr[3] == 0L
                           && rangeArr[4] == EMPTY_MARKER
                           && rangeArr[5] == EMPTY_MARKER;
            boolean iae = false, aioobe = false;
            try { Arrays.fill(rangeArr, 4, 2, 1L); }
            catch (IllegalArgumentException e) { iae = true; }
            try { Arrays.fill(rangeArr, 0, 7, 1L); }
            catch (ArrayIndexOutOfBoundsException e) { aioobe = true; }
            l2 = rangeOk && iae && aioobe;

            // L3 — int[] whole (2-arg) and range (4-arg) fills.
            ints = new int[5];
            Arrays.fill(ints, 0x2A);
            boolean intsOk = true;
            for (int i = 0; i < ints.length; i++) intsOk &= ints[i] == 0x2A;
            Arrays.fill(ints, 1, 3, 7);
            intsOk &= ints[0] == 0x2A && ints[1] == 7 && ints[2] == 7
                   && ints[3] == 0x2A && ints[4] == 0x2A;
            l3 = intsOk;

            // L4 — Object[] null fill + identity fill.
            objs = new Object[4];
            Arrays.fill(objs, (Object) null);
            boolean nullOk = objs[0] == null && objs[3] == null;
            Arrays.fill(objs, token);
            boolean identOk = true;
            for (int i = 0; i < objs.length; i++) identOk &= objs[i] == token;
            l4 = nullOk && identOk;

            // L5 — the small primitive family.
            Arrays.fill(bytes, (byte) 0x7F);
            Arrays.fill(shorts, (short) 0x2A2A);
            Arrays.fill(chars, 'Z');
            Arrays.fill(bools, true);
            l5 = bytes[0] == 0x7F && bytes[2] == 0x7F
              && shorts[1] == 0x2A2A
              && chars[0] == 'Z' && chars[2] == 'Z'
              && bools[0] && bools[3];

            // L6 — wide-tagged values (float/double) through the boundary.
            Arrays.fill(floats, 0.5f);
            Arrays.fill(doubles, 6.0);
            boolean fdOk = floats[0] == 0.5f && floats[2] == 0.5f
                        && doubles[0] == 6.0 && doubles[2] == 6.0;
            // the double bits must round-trip EXACTLY (wide law):
            long dBits = Double.doubleToRawLongBits(doubles[1]);
            l6 = fdOk && dBits == 0x4018000000000000L;

            // L7 — the probe-readback simulation (why the spin happened):
            // every control byte of a fresh EMPTY-filled table is 0x80;
            // writing the tag byte at slot 5 leaves slot 0 EMPTY.
            meta = new long[lenSrc];
            Arrays.fill(meta, 0, meta.length, EMPTY_MARKER);
            boolean emptyOk = true;
            for (int i = 0; i < 64; i++) {
                long b = (meta[i >> 3] >>> ((i & 7) << 3)) & 0xFFL;
                emptyOk &= b == 0x80L;
            }
            // insert-commit shape (Lh/r;.c): clear byte 5, write the tag.
            int slot = 5;
            long w = meta[slot >> 3];
            long clear = ~(0xFFL << ((slot & 7) << 3));
            meta[slot >> 3] = (w & clear) | (TAG_H2 << ((slot & 7) << 3));
            long b5 = (meta[0] >>> (5 << 3)) & 0xFFL;
            long b0 = (meta[0] >>> 0) & 0xFFL;
            l7 = emptyOk && b5 == TAG_H2 && b0 == 0x80L;
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
