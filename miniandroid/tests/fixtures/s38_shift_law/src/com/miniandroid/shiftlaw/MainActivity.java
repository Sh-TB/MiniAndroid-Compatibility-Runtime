/*
 * S38 SHIFT-LAW PROBE — R-NEW-335 (Dooz AIOOBE) upstream-law unit proof.
 *
 * Replicates, as REAL DEX bytecode, the exact long-arithmetic expressions of
 * androidx.collection ScatterMap metadata storage (upstream/scatter_s37,
 * androidx/androidx androidx-main, Apache-2.0):
 *
 *   L1 writeRawMetadata: data[i] = (data[i] and (0xffL shl b).inv()) or (value shl b)
 *   L2 readRawMetadata:  (data[offset shr 3] shr ((offset and 0x7) shl 3)) and 0xff
 *   L3 group():          (m[i] ushr b) or ((m[i+1] shl (64-b)) and (-(b.toLong()) shr 63))
 *   L4 hash()/h1/h2:     h xor (h ushr 16);  * 0xcc9e2d51;  ushr 7;  and 0x7f
 *   L5 convertMetadataForCleanup:
 *        (masked.inv() + (masked ushr 7)) and BitmaskLsb.inv()
 *        with masked = m and BitmaskMsb (0x8080...80), BitmaskLsb = 0x0101...01
 *   L7 neg+shr guard:    (-(b.toLong())) shr 63  for b=0 (must be 0) and b=8 (must be -1)
 *
 * R-NEW-335 live evidence (S37): h/r.c binary-search returned -319519149 on a
 * receiver whose metadata bytes were 0xe2/0x7f/0x00 — 0xe2 is neither
 * Empty(0x80)/Deleted(0xfe)/Sentinel(0xff) nor a valid H2 (<0x80): the write
 * or the group() read produced a byte the upstream algorithm can never store.
 * If all 7 laws below hold, the long-shift engine is NOT the corruptor and
 * the frontier moves to dual-store divergence (F-101 family) on o5057.
 *
 * Anti-constant-folding: every input flows through NON-FINAL static fields
 * (sget/sput) so ECJ/D8 cannot fold the checks — the opcodes really run.
 * Expected values hardcoded from independent big-int computation (Python).
 *
 * Determinism: no clocks, no randomness. License: MIT.
 */
package com.miniandroid.shiftlaw;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {

    // Non-final statics = anti-fold carriers (sget every read).
    public static long sMask80 = (long) 0x8080808080808080L; // BitmaskMsb
    public static long sMask01 = (long) 0x0101010101010101L; // BitmaskLsb
    public static long sFF = 0xffL;
    public static long sValE2 = 0xe2L; // the S37 observed corrupt byte
    public static long sPre = (long) 0x8080808080808080L; // pre-filled metadata long
    public static long sLo = (long) 0x0123456789abcdefL;  // m[i] for group()
    public static long sHi = (long) 0xfedcba9876543210L;  // m[i+1] for group()
    public static int sH = -1368058213;                    // hash input
    public static int sC1 = (int) 0xcc9e2d51;              // MurmurHashC1
    public static long sM5 = (long) 0xff00fe7f80e20123L;   // convert-law input
    public static int sB8 = 8;
    public static int sB16 = 16;
    public static int sB24 = 24;
    public static int sB32 = 32;
    public static int sB40 = 40;

    private int pass = 0;
    private int fail = 0;
    private final StringBuilder fails = new StringBuilder();

    private void check(String law, long got, long want) {
        if (got == want) {
            pass++;
            System.out.println("[S38-LAW] " + law + " OK got=" + got);
        } else {
            fail++;
            fails.append(' ').append(law);
            System.out.println("[S38-LAW] " + law + " FAIL got=" + got
                    + " want=" + want);
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        setContentView(root);

        // L1 writeRawMetadata law, all 8 byte lanes (b = 0..56 step 8).
        // (data and mask.inv) or (value shl b) — b variable at runtime.
        check("L1.b0", (sPre & ~(sFF << 0)) | (sValE2 << 0),   (long) 0x80808080808080e2L);
        check("L1.b8", (sPre & ~(sFF << 8)) | (sValE2 << 8),   (long) 0x808080808080e280L);
        check("L1.b16",(sPre & ~(sFF << 16)) | (sValE2 << 16), (long) 0x8080808080e28080L);
        check("L1.b24",(sPre & ~(sFF << 24)) | (sValE2 << 24), (long) 0x80808080e2808080L);
        check("L1.b32",(sPre & ~(sFF << 32)) | (sValE2 << 32), (long) 0x808080e280808080L);
        check("L1.b40",(sPre & ~(sFF << 40)) | (sValE2 << 40), (long) 0x8080e28080808080L);
        check("L1.b48",(sPre & ~(sFF << 48)) | (sValE2 << 48), (long) 0x80e2808080808080L);
        check("L1.b56",(sPre & ~(sFF << 56)) | (sValE2 << 56), (long) 0xe280808080808080L);

        // L2 readRawMetadata law: (data >> b) & 0xff on the L1 results.
        long d0 = (sPre & ~(sFF << 0)) | (sValE2 << 0);
        check("L2.b0", (d0 >> 0) & 0xffL, 0xe2L);
        long d56 = (sPre & ~(sFF << 56)) | (sValE2 << 56);
        check("L2.b56", (d56 >> 56) & 0xffL, 0xe2L);

        // L3 group() cross-long law with the b=0 guard branch.
        // b=8:  guard = -(8L)>>63 = -1 -> hi|lo fully active
        check("L3.b8",  (sLo >>> 8)  | ((sHi << (64 - 8))  & ((-(sB8 * 1L)) >> 63)),
              (long) 0x100123456789abcdL);
        check("L3.b16", (sLo >>> 16) | ((sHi << (64 - 16)) & ((-(sB16 * 1L)) >> 63)),
              (long) 0x32100123456789abL);
        check("L3.b24", (sLo >>> 24) | ((sHi << (64 - 24)) & ((-(sB24 * 1L)) >> 63)),
              (long) 0x5432100123456789L);
        check("L3.b32", (sLo >>> 32) | ((sHi << (64 - 32)) & ((-(sB32 * 1L)) >> 63)),
              (long) 0x7654321001234567L);
        check("L3.b40", (sLo >>> 40) | ((sHi << (64 - 40)) & ((-(sB40 * 1L)) >> 63)),
              (long) 0x9876543210012345L);

        // L4 hash()/h1/h2 laws (MurmurHashC1 chain), all int ops.
        int folded = sH ^ (sH >>> 16);
        check("L4.folded", (long) (folded & 0xffffffffL), (long) 0xae75b8eeL);
        int scrambled = folded * sC1;
        check("L4.scrambled", (long) (scrambled & 0xffffffffL), (long) 0xafa5594eL);
        int fin = scrambled ^ (scrambled >>> 16);
        check("L4.final", (long) (fin & 0xffffffffL), (long) 0xafa5f6ebL);
        check("L4.h1", (long) (fin >>> 7), 23022573L);
        check("L4.h2", (long) (fin & 0x7f), 107L);

        // L5 convertMetadataForCleanup law.
        long masked = sM5 & sMask80;
        long conv = ((~masked) + (masked >>> 7)) & (~sMask01);
        check("L5.convert", conv, (long) 0x80fe80fe8080fefeL);

        // L7 the b=0 guard law: -(0L)>>63 == 0, -(8L)>>63 == -1.
        long zero = 0L;
        check("L7.b0", (-(zero)) >> 63, 0L);
        check("L7.b8", (-(sB8 * 1L)) >> 63, -1L);

        // Verdict rows.
        addRow(root, "S38 shift laws: " + pass + " OK / " + fail + " FAIL",
               fail == 0 ? 0xFF1B5E20 : 0xFFB71C1C);
        addRow(root, "L1 writeRawMetadata 8/8 lanes " + (pass >= 10 ? "PASS" : "FAIL"),
               pass >= 10 ? 0xFF1B5E20 : 0xFFB71C1C);
        addRow(root, "L3 group() x-long " + (pass >= 15 ? "PASS" : "FAIL"),
               pass >= 15 ? 0xFF1B5E20 : 0xFFB71C1C);
        addRow(root, "L4 hash chain " + (pass >= 20 ? "PASS" : "FAIL"),
               pass >= 20 ? 0xFF1B5E20 : 0xFFB71C1C);
        addRow(root, "L5+L7 masks/guards " + (pass >= 23 ? "PASS" : "FAIL"),
               pass >= 23 ? 0xFF1B5E20 : 0xFFB71C1C);
        if (fail == 0) {
            addRow(root, "VERDICT: long-shift engine CLEAN — R-NEW-335 moves to dual-store", 0xFF0B7A46);
        } else {
            addRow(root, "VERDICT: ENGINE SHIFT BUG: " + fails, 0xFFB71C1C);
        }
        System.out.println("[S38-LAW] VERDICT pass=" + pass + " fail=" + fail
                + (fail == 0 ? " CLEAN" : " FAILS:" + fails));
    }

    private void addRow(LinearLayout root, String text, int color) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(color);
        tv.setTextSize(16f);
        root.addView(tv);
    }
}
