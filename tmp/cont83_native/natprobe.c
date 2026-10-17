#include <math.h>
#include <stdint.h>
typedef struct _JavaVM _JavaVM;
typedef struct _JNIEnv _JNIEnv;
typedef int32_t jint;
typedef int64_t jlong;
typedef void* jclass;
#define JNIEXPORT __attribute__((visibility("default")))
#define JNICALL
jint JNI_OnLoad(_JavaVM* vm, void* reserved) { return 0x00010006; }
JNIEXPORT jint JNICALL Java_com_probe_nat1_NativeProbe_add3(
        _JNIEnv* e, jclass c, jint a, jint b, jint c2) {
    // Real libm use: the result folds a sin()-derived zero so the DT_NEEDED
    // libm dependency is a real symbol requirement, not decoration.
    double s = sin((double)(a + b + c2));
    return a + b + c2 + (jint)s;
}
JNIEXPORT jint JNICALL Java_com_probe_nat1_NativeProbe_mathCheck(
        _JNIEnv* e, jclass c, jint v) {
    // sqrt+pow chain: returns ((int)sqrt(pow(v,2))) — v when libm resolves.
    return (jint)sqrt(pow((double)v, 2.0));
}
