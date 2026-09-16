/*
 * R-NEW-361 micro probe — ScatterMap metadata write/extract laws, S49.
 *
 * WHY: dooz v18+v23 die in androidx.collection ScatterMap probing with
 * garbage metadata words (bytes 0x00/0xFF where only EMPTY 0x80, DELETED
 * 0xFE or h2 <= 0x7F are legal). The upstream write law:
 *
 *     writeRawMetadata(data, slot, h2):
 *         i = slot >> 3 ; b = (slot & 7) << 3
 *         data[i] = (data[i] & ~(0xFFL << b)) | (h2L << b)
 *
 * If the clear mask ~(0xFFL << b) mis-executes in the engine, the old
 * EMPTY byte (0x80) survives and ORs with h2 -> 0xFF; if the OR lands
 * wrong the byte stays 0x00 — exactly the corruption observed in the
 * live dooz trace ([METHOD-TRACE] Lh/r;.c register dumps, S49).
 *
 * LAWS under proof (every case = one verdict band, green = holds):
 *   L1  writeRawMetadata over one EMPTY-filled word, slots 0..7, 8 h2
 *       values (incl. 0x7F — the 0x80|h2 == 0xFF collision shape).
 *   L2  sequential half-fill (dooz real shape): slots {1,6,3,4} with
 *       h2 {0x38,0x7F,0x56,0x0F} — full-word byte law.
 *   L3  group() straddle extraction at every byte offset 0..56:
 *       g = (w0 >>> bit) | ((w1 << (64-bit)) & ((1L<<bit)-1))
 *   L4  SWAR match/empty tricks on the half table:
 *       match(0x38) = (x - bc) & ~x & 0x8080..80 with x = g ^ h2*bc
 *       empty       = ~g & (g << 6) & 0x8080..80
 *
 * INDEPENDENT ORACLE: expected 64-bit values are assembled from expected
 * BYTES with pure INT arithmetic (int shifts/masks — the proven surface),
 * then compared against the actual long's two halves extracted with
 * v >>> 32 and (int) v. No long->string, no BigInteger, no folds: all
 * inputs flow through non-final static fields/arrays.
 *
 * Determinism: no time, no randomness, no collections.
 */
package com.miniandroid.r361probe;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {

    static long EMPTY = 0x8080808080808080L;   // the 0x80 x8 marker
    static long BC = 0x0101010101010101L;      // broadcast constant
    static long HIGH = 0x8080808080808080L;    // msb-per-byte constant
    static int[] H2S = new int[] { 0x7F, 0x01, 0x38, 0x56, 0x22, 0x66, 0x0F, 0x4C };
    static int[] FILL_SLOTS = new int[] { 1, 6, 3, 4 };
    static int[] FILL_H2S = new int[] { 0x38, 0x7F, 0x56, 0x0F };

    // verdicts: 8 + 1 + 8 + 2 = 19 bands
    static boolean[] bands = new boolean[19];

    // expected half-table bytes after L2 (shared oracle state)
    static int[] halfBytes = new int[8];

    // assemble two ints from 8 expected BYTES (pure int ops)
    static int hiFromBytes(int b7, int b6, int b5, int b4) {
        return (b7 << 24) | (b6 << 16) | (b5 << 8) | b4;
    }
    static int loFromBytes(int b3, int b2, int b1, int b0) {
        return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try { run6_sentinel(); } catch (Throwable t) { bands[0] = false; }
        try { run7_mirror(); } catch (Throwable t) { bands[1] = false; }
        try { run5_copyalias(); } catch (Throwable t) { bands[2] = false; }
        try { run1_writeRaw(); } catch (Throwable t) { bands[0] = false; }
        try { run2_halffill(); } catch (Throwable t) { bands[8] = false; }
        try { run3_group(); } catch (Throwable t) { bands[9] = false; }
        try { run4_swar(); } catch (Throwable t) { bands[17] = false; }
        setContentView(new VerdictView(this));
    }

    // L6 — sentinel law: initializeMetadata writes Sentinel (0xFF) at
    // slot = capacity (7 for a mask-7 table) => word0 byte7 == 0xFF.
    static long SENTINEL = 0xFFL;
    void run6_sentinel() {
        long[] m = new long[2];
        m[0] = EMPTY; m[1] = EMPTY;
        int slot = 7;                 // capacity
        int b = (slot & 7) << 3;
        m[0] = (m[0] & ~(0xFFL << b)) | (SENTINEL << b);
        actuals[0] = m[0];            // expect 0xFF80808080808080 (row0)
    }

    // L7 — mirror law: writeMetadata mirrors slot writes into the cloned
    // tail region: cloneIndex = ((slot - 7) and capacity) + (7 and capacity)
    // for capacity 7, slot 0 -> cloneIndex 8 => word1 byte0 = h2.
    void run7_mirror() {
        long[] m = new long[2];
        m[0] = EMPTY; m[1] = EMPTY;
        int cap = 7;
        int slot = 0;
        int h2 = 0x38;
        int b = (slot & 7) << 3;
        m[0] = (m[0] & ~(0xFFL << b)) | (((long) h2) << b);
        int cloneIndex = ((slot - 7) & cap) + (7 & cap);
        int cb = (cloneIndex & 7) << 3;
        m[1] = (m[1] & ~(0xFFL << cb)) | (((long) h2) << cb);
        actuals[1] = m[1];            // expect 0x8080808080808038 (row1)
    }

    // L5 — long[] copy independence law (Compose snapshot clone shape):
    // b = a.clone(); b[0] modified => a[0] MUST be untouched. Also
    // System.arraycopy(a, 0, c, 0, len) and manual element copy.
    // static int[] mirrorSrc = new int[8];
    void run5_copyalias() {
        long[] a = new long[1];
        a[0] = EMPTY;
        long[] b = a.clone();
        b[0] = (b[0] & ~(0xFFL << 8)) | (0x7FL << 8);   // b gets byte1=0x7F
        // a[0] must STILL be 0x8080808080808080
        actuals[2] = a[0];
        // System.arraycopy independence
        long[] c = new long[2];
        c[0] = EMPTY; c[1] = EMPTY;
        long[] d = new long[2];
        java.lang.System.arraycopy(c, 0, d, 0, 2);
        d[1] = 0x00000000000000FEL;
        actuals[3] = c[1];   // must still be EMPTY (0x80..80)
        // manual element-wise copy independence (the R-NEW-360 family shape)
        long[] e = new long[2];
        e[0] = EMPTY; e[1] = EMPTY;
        long[] f = new long[2];
        for (int i = 0; i < 2; i++) f[i] = e[i];
        f[0] = 0L;
        actuals[4] = e[0];   // must still be EMPTY
    }

    // L1 — writeRawMetadata over one word, every slot
    void run1_writeRaw() {
        long[] data = new long[1];
        data[0] = EMPTY;
        for (int slot = 0; slot < 8; slot++) {
            int h2 = H2S[slot];
            int i = slot >> 3;
            int b = (slot & 7) << 3;
            long clear = 0xFFL << b;
            long inv = ~clear;
            long masked = data[i] & inv;
            long orv = ((long) h2) << b;
            data[i] = masked | orv;

            // oracle: expected bytes = 0x80 everywhere except slot -> h2
            int[] eb = new int[8];
            for (int k = 0; k < 8; k++) eb[k] = 0x80;
            eb[slot] = h2;
            int ehi = hiFromBytes(eb[7], eb[6], eb[5], eb[4]);
            int elo = loFromBytes(eb[3], eb[2], eb[1], eb[0]);
            actuals[5 + slot] = data[0];
            int ahi = (int) (data[0] >>> 32);
            int alo = (int) data[0];
            bands[slot] = (ahi == ehi) && (alo == elo);
        }
    }

    // L2 — sequential half fill (dooz shape)
    void run2_halffill() {
        long[] d2 = new long[2];
        d2[0] = EMPTY;
        d2[1] = EMPTY;
        for (int k = 0; k < 8; k++) halfBytes[k] = 0x80;
        for (int k = 0; k < 4; k++) {
            int s = FILL_SLOTS[k];
            int h2 = FILL_H2S[k];
            int b = (s & 7) << 3;
            d2[0] = (d2[0] & ~(0xFFL << b)) | (((long) h2) << b);
            halfBytes[s] = h2;
        }
        int ehi = hiFromBytes(halfBytes[7], halfBytes[6], halfBytes[5], halfBytes[4]);
        int elo = loFromBytes(halfBytes[3], halfBytes[2], halfBytes[1], halfBytes[0]);
        actuals[13] = d2[0];
        int ahi = (int) (d2[0] >>> 32);
        int alo = (int) d2[0];
        bands[8] = (ahi == ehi) && (alo == elo);
    }

    // L3 — group() straddle extraction, offsets 0..56 (8 cases)
    void run3_group() {
        long[] d2 = new long[2];
        for (int k = 0; k < 8; k++) {
            int b = k << 3;
            d2[0] = (d2[0] & ~(0xFFL << b)) | (((long) halfBytes[k]) << b);
        }
        for (int k = 0; k < 8; k++) {
            int b = k << 3;
            d2[1] = (d2[1] & ~(0xFFL << b)) | (((long) halfBytes[k]) << b);
        }
        // d2 = halfBytes mirrored (what upstream's metadata mirror produces)
        for (int off = 0; off < 64; off += 8) {
            int w = off >> 6;               // off is a BIT offset: word 0 for all <64
            int bit = off & 0x3F;           // bit shift inside the straddle window
            long w0 = d2[w];
            long w1 = d2[w + 1];
            long g0 = w0 >>> bit;
            long g1 = w1 << (64 - bit);
            long mask;
            if (bit == 0) {
                mask = -1L;
            } else {
                mask = (1L << bit) - 1L;
            }
            long g = g0 | (g1 & mask);
            // oracle: 8 expected bytes starting at byte offset off (mod 8 window)
            int start = (off >> 3) * 8 + (off & 7) / 8; // off is byte-granular
            // off in {0,8,...,56}: word boundary aligned -> window = bytes [off/8 .. off/8+7]
            int s0 = off >> 3;
            int eb0 = halfBytes[s0 & 7];
            int eb1 = halfBytes[(s0 + 1) & 7];
            int eb2 = halfBytes[(s0 + 2) & 7];
            int eb3 = halfBytes[(s0 + 3) & 7];
            int eb4 = halfBytes[(s0 + 4) & 7];
            int eb5 = halfBytes[(s0 + 5) & 7];
            int eb6 = halfBytes[(s0 + 6) & 7];
            int eb7 = halfBytes[(s0 + 7) & 7];
            int ehi = hiFromBytes(eb7, eb6, eb5, eb4);
            int elo = loFromBytes(eb3, eb2, eb1, eb0);
            actuals[14 + (off >> 3)] = g;
            int ahi = (int) (g >>> 32);
            int alo = (int) g;
            bands[9 + (off >> 3)] = (ahi == ehi) && (alo == elo);
        }
    }

    // L4 — SWAR match/empty on the half table
    void run4_swar() {
        // rebuild the half-table word through the write law
        long g = EMPTY;
        for (int k = 0; k < 4; k++) {
            int s = FILL_SLOTS[k];
            int b = (s & 7) << 3;
            g = (g & ~(0xFFL << b)) | (((long) FILL_H2S[k]) << b);
        }
        // match(0x38) — decomposed for op-level attribution
        long mulbc = 0x38L * BC;
        long x = g ^ mulbc;
        long xsub = x - BC;
        long nx = ~x;
        long m = xsub & nx & HIGH;
        actuals[22] = mulbc;   // expect 0x3838383838383838
        actuals[23] = x;       // expect 0xB847B8376EB800B8
        actuals[24] = xsub;    // expect 0xB746B7366DB7FFB7
        actuals[25] = nx;      // expect 0x41B847C89148FF47
        // oracle: first byte equal to 0x38 in halfBytes (slot 1) -> bit 1
        // m must have exactly one msb set at the FIRST matching byte.
        int firstMatch = -1;
        for (int k = 0; k < 8; k++) {
            if (halfBytes[k] == 0x38) { firstMatch = k; break; }
        }
        boolean matchOk;
        if (firstMatch < 0) {
            matchOk = m == 0L;
        } else {
            int mh = (firstMatch >= 4) ? (0x80 << (firstMatch - 4)) : 0;
            int ml = (firstMatch >= 4) ? 0 : (0x80 << firstMatch);
            int ahi = (int) (m >>> 32);
            int alo = (int) m;
            matchOk = (ahi == mh) && (alo == ml);
            actuals[26] = m;
        }
        bands[17] = matchOk;

        // empty = ~g & (g << 6) & HIGH — first byte that is 0x80 (slot 0)
        long e = ~g & (g << 6) & HIGH;
        int firstEmpty = -1;
        for (int k = 0; k < 8; k++) {
            if (halfBytes[k] == 0x80) { firstEmpty = k; break; }
        }
        boolean emptyOk;
        if (firstEmpty < 0) {
            emptyOk = e == 0L;
        } else {
            int eh = (firstEmpty >= 4) ? (0x80 << (firstEmpty - 4)) : 0;
            int el = (firstEmpty >= 4) ? 0 : (0x80 << firstEmpty);
            int ahi = (int) (e >>> 32);
            int alo = (int) e;
            emptyOk = (ahi == eh) && (alo == el);
            actuals[27] = e;
        }
        bands[18] = emptyOk;
    }

    static long[] actuals = new long[28];

    class VerdictView extends View {
        VerdictView(android.content.Context c) { super(c); }
        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);
            // rows: 64 bits each, LSB left; bit set -> green stripe
            for (int r = 0; r < 28; r++) {
                long v = actuals[r];
                int top = 12 + r * 56;
                for (int b = 0; b < 64; b++) {
                    long bit = (v >>> b) & 1L;
                    p.setColor(bit == 1L ? 0xFF00A000 : 0xFF303030);
                    int left = 30 + b * 16;
                    canvas.drawRect(left, top, left + 14, top + 48, p);
                }
            }
        }
    }
}
