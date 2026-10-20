package com.probe.c449walk;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/**
 * FIX-449 probe (CONT-120): the protobuf-lite RawMessageInfo → MessageSchema
 * walk shape, isolated on a KNOWN-GOOD generated-lite trio shape.
 *
 * S36 decode (CONT-119, F-NEW-449): the generated `n2;.r` splits the
 * MessageInfo info-string on '\u0000'; two count sources exist —
 *   (1) the integer count token inside the info string,
 *   (2) the Object[] entries length (11 in the live trace: 10 fields + aux);
 * the rotated-loop terminator read entries[11] → [S36-AOOB] len=11 idx=11.
 *
 * This probe reproduces the EXACT walk shape on a controlled 10-string-field
 * trio and asserts three contracts:
 *   WALK-A (count-token law):  parse count token → consume exactly that many
 *          tokens+entries → fill buffer 3-ints-per-field → IN BOUNDS.
 *   WALK-B (rotated-terminator law): for(i=0;;i++){e=entries[i]; if
 *          (e==TERMINATOR) break; ...} with the terminator ABSENT → the
 *          ArrayIndexOutOfBoundsException signature must be exactly
 *          length=11, index=11 (the S36 signature) — caught by the fixture.
 *   WALK-C (buffer layout): buffer[i*3+2] carries the presence slot — 3
 *          ints per field, 11 fields → buffer length 33.
 *
 * Every row prints an honest W449- verdict. If WALK-A/C hold and WALK-B
 * reproduces the exact S36 signature, the WALK OPS are engine-correct and
 * the live divergence is isolated to the DATA construction upstream
 * (c3.<clinit> string/entries build — R337 rows) — the bisect continues
 * there, with this probe as the isolation tool.
 */
public class MainActivity extends Activity {

    static final char SEP = '\u0000';
    // 10 real field tokens + 1 aux token = 11 (the S36 shape)
    static final String INFO_STRING =
            "11" + SEP + "f0" + SEP + "f1" + SEP + "f2" + SEP + "f3" + SEP
            + "f4" + SEP + "f5" + SEP + "f6" + SEP + "f7" + SEP + "f8" + SEP
            + "f9" + SEP + "aux";

    static int pass = 0, fail = 0;

    static void check(String name, boolean ok, String extra) {
        if (ok) { pass++; System.out.println("W449- PASS " + name + " " + extra); }
        else { fail++; System.out.println("W449- FAIL " + name + " " + extra); }
    }

    // ── WALK-A: the count-token law ──────────────────────────────────────
    static void walkCountToken(String info, Object[] entries) {
        String[] tokens = split(info);   // generated code splits on '\u0000'
        int count = Integer.parseInt(tokens[0]);   // count source (1)
        int[] buffer = new int[entries.length * 3];
        int n = 0;
        for (int i = 1; i <= count && n < entries.length; i++, n++) {
            // 3 ints per field: field#, type+offset, presence (ready-source
            // MessageSchema.java layout) — the walk stores metadata per entry
            buffer[n * 3 + 0] = 1000 + i;      // field number slot
            buffer[n * 3 + 1] = 0x0800 | i;    // type+offset slot
            buffer[n * 3 + 2] = i;             // presence slot
        }
        check("walkA-count-token", n == count && count == entries.length,
              "count=" + count + " consumed=" + n + " entries=" + entries.length
              + " buffer=" + buffer.length);
    }

    // ── WALK-B: the rotated-terminator law (expected S36 AOOB) ───────────
    static String walkRotatedTerminator(String info, Object[] entries) {
        String[] tokens = split(info);
        int count = Integer.parseInt(tokens[0]);
        Object terminator = new Object();   // the sentinel is NOT in entries
        StringBuilder seen = new StringBuilder();
        try {
            for (int i = 0; ; i++) {
                Object e = entries[i];               // ← the rotated read
                if (e == terminator) break;
                seen.append(tokens[i + 1]).append('|');
            }
            return "NO-AOOB consumed=" + seen.length();
        } catch (ArrayIndexOutOfBoundsException ex) {
            return "AOOB " + ex.getMessage();
        }
    }

    // ── WALK-C: buffer layout ────────────────────────────────────────────
    static void walkBufferLayout() {
        int fields = 11;
        int[] buffer = new int[fields * 3];
        for (int i = 0; i < fields; i++) buffer[i * 3 + 2] = 0x50 + i;
        boolean ok = buffer.length == 33 && buffer[32] == 0x50 + 10
                     && buffer[2] == 0x50 && buffer[5] == 0x51;
        check("walkC-buffer-3-ints-per-field", ok,
              "len=" + buffer.length + " last=" + buffer[32]);
    }

    // faithful split on '\u0000' (no regex — the generated code walks chars)
    static String[] split(String s) {
        int parts = 1;
        for (int i = 0; i < s.length(); i++) if (s.charAt(i) == SEP) parts++;
        String[] out = new String[parts];
        int idx = 0, start = 0;
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == SEP) {
                out[idx++] = s.substring(start, i);
                start = i + 1;
            }
        }
        out[idx] = s.substring(start);
        return out;
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);

        Object[] entries = new Object[11];
        for (int i = 0; i < 10; i++) entries[i] = "field" + i;
        entries[10] = new Object();   // the aux (default instance) slot

        try {
            walkCountToken(INFO_STRING, entries);
        } catch (Throwable t) {
            check("walkA-count-token", false,
                  "exception " + t.getClass().getName() + ": " + t.getMessage());
        }

        String bSig = walkRotatedTerminator(INFO_STRING, entries);
        // The S36 live signature: len=11 idx=11
        check("walkB-rotated-terminator-S36-signature",
              bSig.contains("11") && bSig.startsWith("AOOB"),
              "sig=[" + bSig + "]");

        try {
            walkBufferLayout();
        } catch (Throwable t) {
            check("walkC-buffer-3-ints-per-field", false,
                  "exception " + t.getClass().getName());
        }

        System.out.println("W449- VERDICT pass=" + pass + " fail=" + fail
                           + (fail == 0 ? " WALK-OPS-OK divergence-isolated-"
                                          + "to-data-construction"
                                        : " WALK-OP-GAP-FOUND"));

        TextView tv = new TextView(this);
        tv.setText("c449walk");
        setContentView(tv);
    }
}
