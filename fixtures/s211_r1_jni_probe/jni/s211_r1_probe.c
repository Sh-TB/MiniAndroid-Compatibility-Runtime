/*
 * s211_r1_probe.c — A-R1 (S211) native-tail probe library (host x86_64).
 *
 * Minimal SPEC-EXACT JNI declarations — no jni.h needed (JRE-only host):
 * the slots are pinned by jni.h JNINativeInterface layout and by the
 * runtime's own F-C4-581 objdump proof (RegisterNatives 215, GetJavaVM
 * 219, ExceptionCheck 228; FindClass 6, Throw 13, ThrowNew 14,
 * ExceptionOccurred 15, ExceptionClear 17; JavaVM GetEnv 6).
 */
#include <stdint.h>
#include <string.h>

typedef struct { const char* name; const char* sig; void* fnPtr; } JNM;

/* raw slot access: env → functions table → slot i */
#define ENV_SLOT(env, i) (((void**)(*(void**)(env)))[(i)])

typedef int32_t (*GetEnv_t)(void* vm, void** env, int32_t version);
typedef void* (*FindClass_t)(void* env, const char* name);
typedef int32_t (*ThrowNew_t)(void* env, void* clazz, const char* msg);
typedef void (*ExceptionClear_t)(void* env);
typedef unsigned char (*ExceptionCheck_t)(void* env);
typedef int32_t (*RegisterNatives_t)(void* env, void* clazz,
                                     const JNM* methods, int32_t n);

static int32_t throwThenReturn42_impl(void* env, void* thiz) {
    (void)thiz;
    FindClass_t fc = (FindClass_t)ENV_SLOT(env, 6);
    ThrowNew_t tn = (ThrowNew_t)ENV_SLOT(env, 14);
    void* cls = fc(env, "java/lang/IllegalStateException");
    if (cls) tn(env, cls, "r1-probe native ThrowNew");
    /* JNI spec: this 42 must NEVER reach the DEX — the pending exception
     * owns the call site (the A-R1 law the probe discriminates). */
    return 42;
}

static int32_t clearThenReturn7_impl(void* env, void* thiz) {
    (void)thiz;
    FindClass_t fc = (FindClass_t)ENV_SLOT(env, 6);
    ThrowNew_t tn = (ThrowNew_t)ENV_SLOT(env, 14);
    ExceptionCheck_t ec = (ExceptionCheck_t)ENV_SLOT(env, 228);
    ExceptionClear_t cl = (ExceptionClear_t)ENV_SLOT(env, 17);
    void* cls = fc(env, "java/lang/IllegalStateException");
    if (cls) tn(env, cls, "clear-me");
    if (ec(env)) cl(env);   /* the native CONSUMES its own exception */
    /* no pending exception at return → the DEX sees 7, no throw */
    return 7;
}

/* JavaVM table: GetEnv is spec slot 6 (F-C4-581-exact on this runtime). */
int32_t JNI_OnLoad(void* vm, void* reserved) {
    (void)reserved;
    GetEnv_t get_env = (GetEnv_t)((void**)(*(void**)(vm)))[6];
    void* env = 0;
    if (!get_env) return -1;  /* JNI_EVERSION family failure */
    if (get_env(vm, &env, 0x00010006) != 0 || !env) return -1;
    FindClass_t fc = (FindClass_t)ENV_SLOT(env, 6);
    RegisterNatives_t rn = (RegisterNatives_t)ENV_SLOT(env, 215);
    void* clazz = fc(env, "com/probe/r1/MainActivity");
    if (!clazz || !rn) return -1;
    JNM methods[2] = {
        {"throwThenReturn42", "()I", (void*)&throwThenReturn42_impl},
        {"clearThenReturn7", "()I", (void*)&clearThenReturn7_impl},
    };
    if (rn(env, clazz, methods, 2) != 0) return -1;
    return 0x00010006;
}
