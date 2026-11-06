package com.probe.c7act;

/** CODER7 WAVE-3 activity probe — the cross-activity evidence recorder.
 *  Statics survive the whole task chain; the final step flushes
 *  act_results.jsonl. String.concat law (no StringBuilder.setLength). */
public class Rec {
    public static String out = "";

    public static void ok(String op, String detail) {
        line("PASS", op, detail);
    }
    public static void fail(String op, String detail) {
        line("FAIL", op, detail);
    }
    private static void line(String v, String op, String d) {
        String row = "C7|".concat(op).concat("|").concat(v)
                .concat("|").concat(d == null ? "null" : d).concat("\n");
        out = out.concat(row);
    }
}
