package com.probe.nat1;

// F-NEW-387 probe surface: the native lib's DT_NEEDED is the ANDROID
// soname libm.so (host-unresolvable) — the runtime's dependency law must
// serve it through the validated first-party anchor.
public class NativeProbe {
    static { System.loadLibrary("natprobe"); }
    public static native int add3(int a, int b, int c);
    public static native int mathCheck(int v);
}
