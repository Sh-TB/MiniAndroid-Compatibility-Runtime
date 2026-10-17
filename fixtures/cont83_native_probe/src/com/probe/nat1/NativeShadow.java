package com.probe.nat1;

// Negative probe surface: its lib has an unsatisfiable DT_NEEDED
// (libno.so) — System.loadLibrary must throw UnsatisfiedLinkError.
public class NativeShadow {
    static { System.loadLibrary("natprobe_noshadow"); }
    public static native int add3(int a, int b, int c);
}
