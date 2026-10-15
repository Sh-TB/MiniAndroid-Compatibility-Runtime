#include <stdint.h>
/* Minimal JNI surface (no jni.h in container): the engine's dlopen bridge
   only needs the symbols to exist with System-V x86_64 calling convention.
   JNI_VERSION_1_6 == 0x00010006. */
typedef struct _JavaVM _JavaVM;
typedef struct _JNIEnv _JNIEnv;
typedef int32_t jint;
typedef int64_t jlong;
typedef void* jclass;
#define JNIEXPORT __attribute__((visibility("default")))
#define JNICALL
jint JNI_OnLoad(_JavaVM* vm, void* reserved) {
    return 0x00010006;
}
JNIEXPORT jlong JNICALL Java_com_probe_gatea_MainActivity_probeFib(_JNIEnv* e, jclass c, jlong n) {
    jlong a = 0, b = 1;
    for (jlong i = 0; i < n; ++i) { jlong t = a + b; a = b; b = t; }
    return a;
}
