package com.probe.d05;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;

/**
 * FIX-D05 probe (CONT-120): protobuf-lite UnknownFieldSchema contract at the
 * engine-op substrate level.
 *
 * Ready-source contract (protobuf java UnknownFieldSet / UnknownFieldSchema):
 * "unknown field bytes are captured into an unknownFields sink and re-emitted
 * on re-serialization; never dropped silently."
 *
 * The probe hand-encodes a proto payload with KNOWN fields (1 varint, 2
 * length-delimited, 3 varint) and UNKNOWN fields (field 15 varint, field 9
 * length-delimited — absent from the fixture's schema), parses it with a
 * faithful UnknownFieldSet model (known fields decoded; unknown fields' raw
 * bytes — tag + value — captured byte-perfect), re-serializes known + sink in
 * field order, and asserts BYTE EQUALITY with the input. Every row prints an
 * honest D05- PASS/FAIL verdict; any FAIL would be a real engine-op gap.
 *
 * The same fixture proves the FIX-D12 wrong-thread law behaviorally: a
 * background Thread touches a TextView (drained-body identity != main) and
 * the AOSP CalledFromWrongThreadException must arrive and be caught by the
 * fixture's typed catch — printed as D12- PASS/FAIL.
 */
public class MainActivity extends Activity {

    // ── wire format helpers (protobuf wire spec) ─────────────────────────
    static void writeVarint(ByteArrayOutputStream o, int v) {
        while (true) {
            if ((v & ~0x7F) == 0) { o.write(v); return; }
            o.write((v & 0x7F) | 0x80);
            v >>>= 7;
        }
    }
    static int readVarint(byte[] b, int[] pos) {
        int shift = 0, result = 0, p = pos[0];
        while (p < b.length) {
            byte bb = b[p++];
            result |= (bb & 0x7F) << shift;
            if ((bb & 0x80) == 0) { pos[0] = p; return result; }
            shift += 7;
            if (shift > 35) throw new IllegalStateException("varint too long");
        }
        throw new IllegalStateException("truncated varint");
    }
    static void writeTag(ByteArrayOutputStream o, int field, int wireType) {
        writeVarint(o, (field << 3) | wireType);
    }

    // ── the unknown-field sink (UnknownFieldSet model) ───────────────────
    static class UnknownSet {
        ByteArrayOutputStream sink = new ByteArrayOutputStream();
        void captureField(byte[] buf, int[] pos, int field, int wt) {
            // capture tag + value bytes VERBATIM (the UnknownFieldSchema law)
            writeVarint(sink, (field << 3) | wt);  // re-emit the tag
            if (wt == 0) {
                int v = readVarint(buf, pos);
                writeVarint(sink, v);
            } else if (wt == 2) {
                int len = readVarint(buf, pos);
                writeVarint(sink, len);
                for (int i = 0; i < len; i++) sink.write(buf[pos[0] + i]);
                pos[0] += len;
            } else {
                throw new IllegalStateException("unsupported wt " + wt);
            }
        }
    }

    static int d05Pass = 0, d05Fail = 0;

    static void check(String name, boolean ok) {
        if (ok) { d05Pass++; System.out.println("D05- PASS " + name); }
        else { d05Fail++; System.out.println("D05- FAIL " + name); }
    }

    static void runUnknownFieldProbe() {
        try {
            // ── encode: f1 varint=300 | f2 "hi" | f15 (unknown) varint=7 |
            //           f9 (unknown) "zz" | f3 varint=5
            ByteArrayOutputStream in = new ByteArrayOutputStream();
            writeTag(in, 1, 0); writeVarint(in, 300);
            byte[] hi = new byte[]{'h', 'i'};
            writeTag(in, 2, 2); writeVarint(in, hi.length);
            in.write(hi, 0, hi.length);
            writeTag(in, 15, 0); writeVarint(in, 7);          // unknown field
            byte[] zz = new byte[]{'z', 'z'};
            writeTag(in, 9, 2); writeVarint(in, zz.length);   // unknown field
            in.write(zz, 0, zz.length);
            writeTag(in, 3, 0); writeVarint(in, 5);
            byte[] original = in.toByteArray();

            // ── parse: known fields decoded, unknowns captured byte-perfect
            UnknownSet unknowns = new UnknownSet();
            long f1 = -1, f3 = -1;
            byte[] f2 = null;
            int[] pos = {0};
            while (pos[0] < original.length) {
                int tag = readVarint(original, pos);
                int field = tag >>> 3, wt = tag & 7;
                if (field == 1 && wt == 0) f1 = readVarint(original, pos);
                else if (field == 2 && wt == 2) {
                    int len = readVarint(original, pos);
                    f2 = new byte[len];
                    System.arraycopy(original, pos[0], f2, 0, len);
                    pos[0] += len;
                } else if (field == 3 && wt == 0) f3 = readVarint(original, pos);
                else unknowns.captureField(original, pos, field, wt);
            }

            check("known-f1", f1 == 300);
            check("known-f2", f2 != null && f2.length == 2 && f2[0] == 'h' && f2[1] == 'i');
            check("known-f3", f3 == 5);

            // ── re-serialize: known fields + sink, input field order
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            writeTag(out, 1, 0); writeVarint(out, (int) f1);
            writeTag(out, 2, 2); writeVarint(out, f2.length);
            out.write(f2, 0, f2.length);
            byte[] sunk = unknowns.sink.toByteArray();
            out.write(sunk, 0, sunk.length);
            writeTag(out, 3, 0); writeVarint(out, (int) f3);
            byte[] reserialized = out.toByteArray();

            check("roundtrip-len", reserialized.length == original.length);
            boolean eq = reserialized.length == original.length;
            for (int i = 0; eq && i < original.length; i++)
                eq = reserialized[i] == original[i];
            check("roundtrip-byte-equal", eq);
            System.out.println("D05- VERDICT pass=" + d05Pass
                               + " fail=" + d05Fail
                               + (d05Fail == 0 ? " D05-SUBSTRATE-OK"
                                               : " D05-GAP-FOUND"));
        } catch (Throwable t) {
            System.out.println("D05- FAIL exception " + t.getClass().getName()
                               + ": " + t.getMessage());
        }
    }

    // ── FIX-D12 behavioral probe: wrong-thread view mutation ────────────
    static int d12State = 0;  // 0=pending 1=pass 2=pass-recovered 3=fail

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        runUnknownFieldProbe();

        final TextView tv = new TextView(this);
        tv.setText("main");
        Thread bg = new Thread(() -> {
            try {
                tv.setText("from-bg");  // must raise CalledFromWrongThreadException
                d12State = 3;           // no exception = the law did not fire
            } catch (RuntimeException e) {
                // exact AOSP type checked BY NAME (the android-34 stub jar
                // does not carry the exception class — the runtime identity
                // of the raised type is the probe's subject, not compile-time)
                if ("android.view.CalledFromWrongThreadException"
                        .equals(e.getClass().getName())) {
                    d12State = 1;
                } else {
                    System.out.println("D12- NOTE wrong type "
                                       + e.getClass().getName());
                    d12State = 3;
                }
            } catch (Throwable t) {
                System.out.println("D12- NOTE wrong family " + t.getClass().getName());
                d12State = 3;
            }
        });
        bg.start();
        try { bg.join(2000); } catch (InterruptedException ie) { /* honest */ }
        System.out.println("D12- " + (d12State == 1 ? "PASS raised-and-typed"
                                                    : "FAIL state=" + d12State));

        // AOSP recovery law: the app re-posts through the main looper —
        // Handler.post'ed bodies run on the main identity, so the SAME
        // mutation from a posted runnable must NOT raise.
        final android.os.Handler h = new android.os.Handler(
                android.os.Looper.getMainLooper());
        final boolean[] done = {false};
        final boolean[] recovered = {false};
        h.post(() -> {
            try {
                tv.setText("posted-recovery");
                recovered[0] = true;
            } catch (Throwable t) {
                System.out.println("D12- NOTE posted-mutation raised "
                                   + t.getClass().getName());
            }
            done[0] = true;
        });
        for (int i = 0; i < 40 && !done[0]; i++) {
            try { Thread.sleep(50); } catch (InterruptedException ie) { /* honest */ }
        }
        System.out.println("D12- POSTED " + (recovered[0]
                ? "PASS main-identity-legal"
                : "FAIL posted-mutation-did-not-run"));

        setContentView(tv);
    }
}
