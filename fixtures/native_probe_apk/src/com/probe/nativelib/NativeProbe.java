package com.probe.nativelib;

/**
 * S-2 native-execution probe (issue #371 closeout).
 *
 * Every method declared here is ACC_NATIVE and must be resolved against the
 * REAL extracted libprobe.so (x86_64 primary ABI) through the runtime's
 * dlopen + dlsym + System V dispatch layer. The library's implementations
 * are deterministic (fixtures/native_probe/native_probe.c):
 *
 *   fibNative(15)   -> 610            (loop arithmetic, jlong)
 *   addNative(2,3,4)-> 9              (jint)
 *   tagNative()     -> "S2-NATIVE-OK" (jstring materialized natively)
 *   checksumNative(byte[]) -> C-side XOR/XOR-shift checksum (jint)
 *   mixNative(int,float,double,long) -> exercises ALL JNI arg register
 *                                       classes (I/F/D/J) in one call
 */
public final class NativeProbe {
    static { System.loadLibrary("probe"); }

    public static native long fibNative(int n);
    public static native int addNative(int a, int b, int c);
    public static native String tagNative();
    public static native int checksumNative(String s);
    public static native double mixNative(int a, float b, double c, long d);

    private NativeProbe() {}
}
