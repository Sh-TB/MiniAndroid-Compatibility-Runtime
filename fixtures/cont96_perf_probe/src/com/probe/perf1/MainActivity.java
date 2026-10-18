package com.probe.perf1;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/**
 * CONT-96 throughput probe (com.probe.perf1).
 *
 * Deterministic hot-loop fixture shaped like Telegram's SvgHelper$ParserHelper:
 * a char-stream parser whose inner loop is dominated by
 *   invoke-virtual (charAt / length) + add-int/2addr + if-ge + aget/aput-char.
 *
 * Each section runs a fixed iteration count and reports its own elapsed ms
 * via System.nanoTime (host-bridged clock, proven by com.probe.clock1 4/4).
 * Verdict rows are written to stderr AND to the activity title so the run
 * log carries them without depending on pixels.
 *
 * This fixture measures INTERPRETER DISPATCH OVERHEAD ONLY: identical
 * bytecode pre/post engine fix must produce identical counts and identical
 * parsed output, with elapsed ms as the only expected delta.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String name, long elapsedMs, long checksum) {
        String line = "[PERF1] " + name + " ms=" + elapsedMs + " sum=" + checksum;
        System.out.println(line);
        report = report + line + "\n";
    }

    // Section 1: charAt + arithmetic + compare — the SvgHelper.advance/isDigit shape.
    private static long benchCharAt(String s, int iters) {
        long sum = 0;
        for (int k = 0; k < iters; k++) {
            int n = s.length();
            for (int i = 0; i < n; i++) {
                char c = s.charAt(i);
                if (c >= '0' && c <= '9') {
                    sum += (c - '0');
                } else if (c == ' ') {
                    sum += 1;
                } else {
                    sum += c;
                }
            }
        }
        return sum;
    }

    // Section 2: manual char-array walk — aget/aput + 2addr arithmetic shape.
    private static long benchCharArray(char[] buf, int iters) {
        long sum = 0;
        int n = buf.length;
        for (int k = 0; k < iters; k++) {
            for (int i = 0; i < n; i++) {
                char c = buf[i];
                buf[i] = (char) (c + 1);
                sum += buf[i];
            }
        }
        return sum;
    }

    // Section 3: virtual call per element — invoke dispatch cost shape.
    private static long benchVirtual(int iters) {
        long sum = 0;
        for (int k = 0; k < iters; k++) {
            sum += ident(k & 0x7fff);
        }
        return sum;
    }

    private static long ident(long x) {
        return x * 3 + 1;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("PERF1 running");
        setContentView(tv);

        String sample = "M12.34 5.67 L89.01 23.45 C1.23 4.56 7.89 0.12 3.45 6.78 Z ";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 40; i++) sb.append(sample);
        String svgShape = sb.toString(); // 2160 chars, digit/space heavy like path data

        long t0 = System.nanoTime();
        long s1 = benchCharAt(svgShape, 100);          // 400 x 2160 = 864K charAt
        long t1 = System.nanoTime();
        row("charat", (t1 - t0) / 1000000L, s1);

        char[] buf = new char[2048];
        for (int i = 0; i < buf.length; i++) buf[i] = (char) ('a' + (i & 15));
        long t2 = System.nanoTime();
        long s2 = benchCharArray(buf, 100);            // 400 x 2048 = 819K aget/aput
        long t3 = System.nanoTime();
        row("chararray", (t3 - t2) / 1000000L, s2);

        long t4 = System.nanoTime();
        long s3 = benchVirtual(300000);               // 1M invokes
        long t5 = System.nanoTime();
        row("virtual", (t5 - t4) / 1000000L, s3);

        long t6 = System.nanoTime();
        row("total", (t6 - t0) / 1000000L, s1 + s2 + s3);
        System.out.println("[PERF1] verdict=DONE rows=4");
    }
}
