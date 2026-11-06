package com.probe.c7runtime;

/** CODER7 probe: shared delivery-order recorder.
 *  WAVE-2 NOTE: reset/append were switched from StringBuilder to String —
 *  the runtime does not implement StringBuilder.setLength (a silent no-op:
 *  appends worked, truncation never happened, so the recorder accumulated
 *  across ops). String.concat/isEmpty are implemented and side-effect
 *  free. The StringBuilder.setLength gap is recorded as an OBSERVED
 *  core-lib frontier in the issue (not this domain's fix). */
public class Order {
    public static String seq = "";
    public static void append(String who) {
        if (seq.isEmpty()) seq = who;
        else seq = seq.concat(",").concat(who);
    }
    public static void reset() { seq = ""; }
}
