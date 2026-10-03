/*
 * native_probe.c — S-2 native-execution fixture (issue #371 closeout).
 *
 * Built for TWO ABIs from the same deterministic source:
 *   - aarch64 (Android arm64-v8a): extraction/provenance fixture — the host
 *     x86_64 runtime can never execute it, which is exactly the honest
 *     ABI-mismatch failure shape the probe asserts.
 *   - x86_64 (Linux host ABI): the REAL execution target — the runtime
 *     dlopens the extracted file and dispatches native methods through a
 *     minimal JNI bridge.
 *
 * No clocks, no randomness, no environment reads: every function returns a
 * value fully determined by its inputs, so the probe can assert exact
 * results across cold runs.
 */
#include <stdint.h>
#include <stddef.h>

/* ------------------------------------------------------------------ */
/* Minimal JNI types (matches the AOSP jni.h function-table contract)  */
/* ------------------------------------------------------------------ */
struct _JNIEnv;
typedef struct _JNIEnv JNIEnv;
typedef void *jobject;
typedef void *jclass;
typedef void *jstring;
typedef int32_t jint;
typedef int64_t jlong;
typedef uint8_t jboolean;
typedef float jfloat;
typedef double jdouble;

#if defined(__x86_64__) || defined(__aarch64__)
#define JNIEXPORT __attribute__((visibility("default")))
#define JNICALL
#endif

/* JNI true/false */
#define JNI_TRUE 1
#define JNI_FALSE 0
#define JNI_VERSION_1_6 0x00010006

/* ------------------------------------------------------------------ */
/* Plain C entry points (direct dlsym proof, no JNI involved)          */
/* ------------------------------------------------------------------ */

/* fib(15) = 610 — loop arithmetic, deterministic across machines */
static jlong fib(jint n) {
    jlong a = 0, b = 1;
    jint i;
    for (i = 0; i < n; i++) { jlong t = a + b; a = b; b = t; }
    return a;
}

JNIEXPORT jlong JNICALL native_fib15(void) { return fib(15); }

JNIEXPORT jlong JNICALL native_add3(jint a, jint b, jint c) {
    return (jlong)a + (jlong)b + (jlong)c;
}

/* 32-bit checksum over a caller-provided buffer: proves bytes cross the
   boundary in BOTH directions without any fixed host-side value. */
JNIEXPORT jint JNICALL native_checksum(const uint8_t *buf, jint len) {
    uint32_t x = 0x12345678u;
    jint i;
    for (i = 0; i < len; i++) x = (x * 31u + buf[i]) ^ (x >> 3);
    return (jint)x;
}

/* ------------------------------------------------------------------ */
/* JNI entry points (Java_com_probe.nativelib.NativeProbe.*)           */
/* Package com.probe.nativelib, class NativeProbe.                     */
/* ------------------------------------------------------------------ */

/* static native long fibNative(int n); */
JNIEXPORT jlong JNICALL
Java_com_probe_nativelib_NativeProbe_fibNative(JNIEnv *env, jclass cls,
                                               jint n) {
    (void)env; (void)cls;
    return fib(n);
}

/* static native int addNative(int a, int b, int c); */
JNIEXPORT jint JNICALL
Java_com_probe_nativelib_NativeProbe_addNative(JNIEnv *env, jclass cls,
                                               jint a, jint b, jint c) {
    (void)env; (void)cls;
    return a + b + c;
}

/* static native String tagNative(); — proves a string is materialized
   inside the native library and crosses back into managed code. */
JNIEXPORT jstring JNICALL
Java_com_probe_nativelib_NativeProbe_tagNative(JNIEnv *env, jclass cls) {
    (void)cls;
    if (!env) return 0;
    /* NewStringUTF is slot 117 of the JNINativeInterface table. */
    void **ft = *(void ***)env;
    typedef jstring (*NewStringUTF_t)(JNIEnv *, const char *);
    NewStringUTF_t new_string_utf = (NewStringUTF_t)ft[117];
    if (!new_string_utf) return 0;
    return new_string_utf(env, "S2-NATIVE-OK");
}

/* static native int checksumNative(String s); — proves managed bytes reach
   the native side (GetStringUTFChars, slot 119) and an int result crosses
   back. Deterministic XOR/shift checksum over the UTF-8 bytes. */
JNIEXPORT jint JNICALL
Java_com_probe_nativelib_NativeProbe_checksumNative(JNIEnv *env, jclass cls,
                                                    jstring s) {
    (void)cls;
    if (!env || !s) return 0;
    void **ft = *(void ***)env;
    typedef const char *(*GetStringUTFChars_t)(JNIEnv *, void *,
                                               unsigned char *);
    GetStringUTFChars_t get = (GetStringUTFChars_t)ft[119];
    if (!get) return 0;
    unsigned char is_copy = 0;
    const char *utf = get(env, s, &is_copy);
    if (!utf) return 0;
    uint32_t x = 0x12345678u;
    for (const unsigned char *p = (const unsigned char *)utf; *p; ++p)
        x = (x * 31u + *p) ^ (x >> 3);
    return (jint)x;
}

/* static native double mixNative(int, float, double, long); — one call
   exercising EVERY JNI argument register class (I, F, D, J). */
JNIEXPORT jdouble JNICALL
Java_com_probe_nativelib_NativeProbe_mixNative(JNIEnv *env, jclass cls,
                                               jint a, jfloat b, jdouble c,
                                               jlong d) {
    (void)env; (void)cls;
    return (jdouble)a + (jdouble)b * 2.0 + c * 3.0 + (jdouble)d * 4.0;
}

/* JNI_OnLoad — optional on Android; returning a valid version proves the
   library initialization path ran inside the runtime. */
JNIEXPORT jint JNICALL JNI_OnLoad(void *vm, void *reserved) {
    (void)vm; (void)reserved;
    return JNI_VERSION_1_6;
}
