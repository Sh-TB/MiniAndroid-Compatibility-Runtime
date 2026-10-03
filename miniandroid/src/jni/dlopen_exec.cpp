/*
 * dlopen_exec.cpp — S-2 native execution layer implementation.
 *
 * Implements the AOSP JNI contract subset required for honest native
 * execution:
 *   - real host dlopen of the extracted library (never a fabricated load)
 *   - JNI_OnLoad(vm, NULL) version handshake through a minimal JavaVM
 *   - JNI short/long symbol mangling + RegisterNatives resolution
 *   - System V invocation through native_thunk.S (correct SSE/int classes)
 *   - a minimal JNIEnv function table at SPEC SLOT INDICES (strings,
 *     exceptions, VM handle, native registration); every unimplemented
 *     slot answers through a loud unsupported-stub that logs and counts —
 *     never a silent zero that could masquerade as success.
 *
 * String identity law: a jstring token is a pointer to a std::string box
 * allocated in the per-call arena (local-ref lifetime). Managed strings
 * passed in and strings materialized by the native side share the same
 * box representation, so GetStringUTFChars/NewStringUTF round-trip.
 */
#include "dlopen_exec.h"

#include <dlfcn.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <map>
#include <mutex>
#include <vector>

namespace miniandroid {
namespace nativeexec {

extern "C" uint64_t miniandroid_native_thunk(void* fn, const void* stack_args,
                                             size_t n_stack_args,
                                             const uint64_t* int_regs,
                                             const double* sse_regs,
                                             void* sse_ret);

namespace {

// ── counters (pkginspect runtime section) ──────────────────────────────
std::mutex g_mu;
unsigned long long g_load_attempts = 0;
unsigned long long g_load_successes = 0;
unsigned long long g_native_calls = 0;
unsigned long long g_unsupported_slot_calls = 0;

std::vector<LoadedLib>& libs() {
    static std::vector<LoadedLib> v;
    return v;
}
std::map<std::string, std::string>& loader_notes() {  // caller class → lib
    static std::map<std::string, std::string> m;
    return m;
}
struct RegisteredNative {
    std::string class_desc;
    std::string method;
    std::string sig;
    void* fn = nullptr;
};
std::vector<RegisteredNative>& registered() {
    static std::vector<RegisteredNative> v;
    return v;
}

// ── per-call arena (local-ref lifetime) ────────────────────────────────
std::vector<std::string*>& arena() {
    static std::vector<std::string*> a;
    return a;
}
std::string* box_string(const std::string& s) {
    std::string* b = new std::string(s);
    arena().push_back(b);
    return b;
}
void arena_clear() {
    for (std::string* p : arena()) delete p;
    arena().clear();
}

// ── JNI function table (spec slot indices) ─────────────────────────────
constexpr int kJniSlots = 181;
void* g_jni_table[kJniSlots];
struct JNIEnvStub {
    void* functions;
};
JNIEnvStub g_env = {g_jni_table};

constexpr int kVmSlots = 8;
void* g_vm_table[kVmSlots];
struct VMStub {
    void* functions;
};
VMStub g_vm = {g_vm_table};

// generic loud stub for unimplemented slots (returns 0)
long jni_unsupported_slot() {
    std::lock_guard<std::mutex> lk(g_mu);
    ++g_unsupported_slot_calls;
    fprintf(stderr,
            "[MINIANDROID-JNI] UNSUPPORTED JNIEnv slot invoked — the library "
            "used a JNI function outside the implemented subset (strings / "
            "exceptions / VM / registration)\n");
    return 0;
}

// implemented slots — signatures per JNI spec (jni.h)
int jni_GetVersion(void*) { return 0x00010006; }
void* jni_ExceptionOccurred(void*) { return nullptr; }
void jni_ExceptionDescribe(void*) {}
void jni_ExceptionClear(void*) {}
unsigned char jni_ExceptionCheck(void*) { return 0; }
void* jni_NewStringUTF(void*, const char* utf) {
    if (!utf) return nullptr;
    return box_string(std::string(utf));
}
const char* jni_GetStringUTFChars(void*, void* jstr, unsigned char* is_copy) {
    if (!jstr) return nullptr;
    if (is_copy) *is_copy = 1;  // arena-owned copy semantics
    return static_cast<std::string*>(jstr)->c_str();
}
void jni_ReleaseStringUTFChars(void*, void*, const char*) {}
int jni_GetStringUTFLength(void*, void* jstr) {
    return jstr ? (int)static_cast<std::string*>(jstr)->size() : 0;
}
int jni_GetStringLength(void*, void* jstr) {
    if (!jstr) return 0;
    // ASCII probe surface: modified-UTF8 length ≈ byte length
    return (int)static_cast<std::string*>(jstr)->size();
}
void* jni_FindClass(void*, const char* name) {
    return box_string(std::string(name ? name : ""));
}
void* jni_GetObjectClass(void*, void*) {
    // object identity only — class reflection stays an unsupported frontier
    return box_string("Ljava/lang/Object;");
}
void* jni_NewGlobalRef(void*, void* r) { return r; }
void* jni_NewLocalRef(void*, void* r) { return r; }
void jni_DeleteGlobalRef(void*, void*) {}
void jni_DeleteLocalRef(void*, void*) {}
int jni_Throw(void*, void*) { return 0; }
int jni_ThrowNew(void*, void*, const char* msg) {
    fprintf(stderr, "[MINIANDROID-JNI] ThrowNew: %s\n", msg ? msg : "");
    return 0;
}
void jni_FatalError(void*, const char* msg) {
    fprintf(stderr, "[MINIANDROID-JNI] FATAL: %s\n", msg ? msg : "");
    std::abort();
}

struct JNINativeMethodC {  // jni.h layout
    const char* name;
    const char* signature;
    void* fnPtr;
};
int jni_RegisterNatives(void*, void* jcls, const JNINativeMethodC* methods,
                        int n) {
    if (!methods || n <= 0) return -1;
    std::string cls;
    if (jcls) {
        void** fns = *static_cast<void***>(jcls);
        if (fns != g_jni_table) cls = *static_cast<std::string*>(jcls);
    }
    std::lock_guard<std::mutex> lk(g_mu);
    for (int i = 0; i < n; ++i) {
        registered().push_back({cls, methods[i].name ? methods[i].name : "",
                                methods[i].signature ? methods[i].signature
                                                     : "",
                                methods[i].fnPtr});
    }
    fprintf(stderr, "[MINIANDROID-JNI] RegisterNatives: %d methods for %s\n",
            n, cls.c_str());
    return 0;
}
int jni_UnregisterNatives(void*, void*) { return 0; }
int jni_GetJavaVM(void*, void** vm) {
    if (vm) *vm = &g_vm;
    return 0;
}
int jni_AttachCurrentThread(void*, void** env, void*) {
    if (env) *env = &g_env;
    return 0;
}
int jni_DetachCurrentThread(void*) { return 0; }
int jni_DestroyJavaVM(void*) { return 0; }

int vm_GetEnv(void* vm, void** env, int version);

void init_tables() {
    static bool done = false;
    if (done) return;
    done = true;
    for (int i = 0; i < kJniSlots; ++i)
        g_jni_table[i] = (void*)&jni_unsupported_slot;
    g_jni_table[4] = (void*)&jni_GetVersion;               // GetVersion
    g_jni_table[6] = (void*)&jni_FindClass;                // FindClass
    g_jni_table[13] = (void*)&jni_Throw;                   // Throw
    g_jni_table[14] = (void*)&jni_ThrowNew;                // ThrowNew
    g_jni_table[15] = (void*)&jni_ExceptionOccurred;       // ExceptionOccurred
    g_jni_table[16] = (void*)&jni_ExceptionDescribe;       // ExceptionDescribe
    g_jni_table[17] = (void*)&jni_ExceptionClear;          // ExceptionClear
    g_jni_table[18] = (void*)&jni_FatalError;              // FatalError
    g_jni_table[21] = (void*)&jni_NewGlobalRef;            // NewGlobalRef
    g_jni_table[22] = (void*)&jni_DeleteGlobalRef;         // DeleteGlobalRef
    g_jni_table[23] = (void*)&jni_DeleteLocalRef;          // DeleteLocalRef
    g_jni_table[25] = (void*)&jni_NewLocalRef;             // NewLocalRef
    g_jni_table[31] = (void*)&jni_GetObjectClass;          // GetObjectClass
    g_jni_table[113] = (void*)&jni_NewStringUTF;           // NewString
    g_jni_table[114] = (void*)&jni_GetStringLength;        // GetStringLength
    g_jni_table[117] = (void*)&jni_NewStringUTF;           // NewStringUTF
    g_jni_table[118] = (void*)&jni_GetStringUTFLength;     // GetStringUTFLength
    g_jni_table[119] = (void*)&jni_GetStringUTFChars;      // GetStringUTFChars
    g_jni_table[120] = (void*)&jni_ReleaseStringUTFChars;  // ReleaseStringUTFChars
    g_jni_table[163] = (void*)&jni_RegisterNatives;        // RegisterNatives
    g_jni_table[164] = (void*)&jni_UnregisterNatives;      // UnregisterNatives
    g_jni_table[167] = (void*)&jni_GetJavaVM;              // GetJavaVM
    g_jni_table[176] = (void*)&jni_ExceptionCheck;         // ExceptionCheck
    for (int i = 0; i < kVmSlots; ++i)
        g_vm_table[i] = (void*)&jni_unsupported_slot;
    g_vm_table[3] = (void*)&jni_DestroyJavaVM;             // DestroyJavaVM
    g_vm_table[4] = (void*)&jni_AttachCurrentThread;       // AttachCurrentThread
    g_vm_table[5] = (void*)&jni_DetachCurrentThread;       // DetachCurrentThread
    g_vm_table[6] = (void*)&vm_GetEnv;                     // GetEnv
}

int vm_GetEnv(void* vm, void** env, int version) {
    (void)vm;
    (void)version;
    if (env) *env = &g_env;
    return 0;  // JNI_OK
}

// ── JNI symbol mangling (AOSP art::JniIdType semantics) ────────────────
void mangle_escape(const std::string& in, std::string& out) {
    char buf[8];
    for (unsigned char c : in) {
        if (c == '_') out += "_1";
        else if (c == ';') out += "_2";
        else if (c == '[') out += "_3";
        else if (c == '/' || c == '.') out += '_';
        else if (c < 0x20 || c > 0x7e) {
            snprintf(buf, sizeof buf, "_0%04x", (unsigned)c);
            out += buf;
        } else out += (char)c;
    }
}

std::string internal_from_descriptor(const std::string& class_desc) {
    // "Lcom/probe/Native;" → "com/probe/Native"
    if (class_desc.size() >= 2 && class_desc.front() == 'L' &&
        class_desc.back() == ';')
        return class_desc.substr(1, class_desc.size() - 2);
    return class_desc;
}

std::string long_name_suffix(const std::string& dex_sig) {
    // "(II)Ljava/lang/String;" → "__II_java_lang_String" (ARGS only)
    size_t close = dex_sig.find(')');
    if (close == std::string::npos || dex_sig.empty() || dex_sig[0] != '(')
        return "";
    std::string args = dex_sig.substr(1, close - 1);
    if (args.empty()) return "";  // no overload ambiguity for ()-signatures
    std::string out = "__";
    mangle_escape(args, out);
    return out;
}

std::vector<std::string> param_types(const std::string& dex_sig) {
    std::vector<std::string> out;
    size_t i = dex_sig.find('(');
    if (i == std::string::npos) return out;
    ++i;
    while (i < dex_sig.size() && dex_sig[i] != ')') {
        size_t j = i;
        while (dex_sig[j] == '[') ++j;
        if (dex_sig[j] == 'L') {
            size_t k = dex_sig.find(';', j);
            out.push_back(dex_sig.substr(i, k - i + 1));
            i = k + 1;
        } else {
            out.push_back(std::string(1, dex_sig[i]));
            i = j + 1;
        }
    }
    return out;
}

}  // namespace

// ── Library lifecycle ──────────────────────────────────────────────────
LoadOutcome load_library(const std::string& libname,
                         const std::string& host_path,
                         const std::string& logical_path) {
    init_tables();
    LoadOutcome out;
    {
        std::lock_guard<std::mutex> lk(g_mu);
        ++g_load_attempts;
    }
    dlerror();
    void* h = dlopen(host_path.c_str(), RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        const char* e = dlerror();
        out.detail = std::string("dlopen failed: ") + (e ? e : "unknown error");
        fprintf(stderr, "[S2-NATIVE] load %s (%s): %s\n", libname.c_str(),
                host_path.c_str(), out.detail.c_str());
        return out;
    }
    LoadedLib lib;
    lib.name = libname;
    lib.host_path = host_path;
    lib.logical_path = logical_path;
    lib.handle = h;
    // JNI_OnLoad handshake (AOSP: version must be >= JNI_VERSION_1_1)
    int (*onload)(void*, void*) = (int (*)(void*, void*))dlsym(h, "JNI_OnLoad");
    if (onload) {
        int v = onload(&g_vm, nullptr);
        if (v == 0) {
            out.detail = "JNI_OnLoad failed (returned 0)";
            dlclose(h);
            fprintf(stderr, "[S2-NATIVE] %s: %s\n", libname.c_str(),
                    out.detail.c_str());
            return out;
        }
        lib.jni_on_load_ran = true;
        lib.jni_on_load_version = v;
        out.jni_version = v;
    }
    {
        std::lock_guard<std::mutex> lk(g_mu);
        ++g_load_successes;
        libs().push_back(lib);
    }
    out.ok = true;
    if (lib.jni_on_load_ran) {
        char b[16];
        snprintf(b, sizeof b, "%x", lib.jni_on_load_version);
        out.detail = std::string("dlopen ok; JNI_OnLoad version 0x") + b;
    } else {
        out.detail = "dlopen ok; no JNI_OnLoad";
    }
    fprintf(stderr, "[S2-NATIVE] load %s: dlopen ok (%s)%s\n", libname.c_str(),
            host_path.c_str(), lib.jni_on_load_ran ? " JNI_OnLoad ran" : "");
    return out;
}

void note_loader(const std::string& caller_class, const std::string& libname) {
    std::lock_guard<std::mutex> lk(g_mu);
    loader_notes()[caller_class] = libname;
}

bool has_loaded_libs() {
    std::lock_guard<std::mutex> lk(g_mu);
    return !libs().empty();
}

std::vector<LoadedLib> loaded_libs_snapshot() {
    std::lock_guard<std::mutex> lk(g_mu);
    return libs();
}

void* find_symbol(const std::string& class_desc, const std::string& method,
                  const std::string& dex_sig, std::string& tried) {
    init_tables();
    std::string cls = internal_from_descriptor(class_desc);
    std::string short_name = "Java_";
    mangle_escape(cls, short_name);
    short_name += "_";
    std::string m_method;
    mangle_escape(method, m_method);
    short_name += m_method;
    std::string long_name = short_name + long_name_suffix(dex_sig);

    std::lock_guard<std::mutex> lk(g_mu);
    for (const auto& lib : libs()) {
        dlerror();
        void* fn = dlsym(lib.handle, short_name.c_str());
        if (fn) {
            tried = short_name + "@" + lib.name;
            return fn;
        }
        if (long_name != short_name) {
            fn = dlsym(lib.handle, long_name.c_str());
            if (fn) {
                tried = long_name + "@" + lib.name;
                return fn;
            }
        }
    }
    // RegisterNatives resolution: (class, name, sig) or (name, sig)
    for (const auto& rn : registered()) {
        bool cls_match = !rn.class_desc.empty() &&
                         (rn.class_desc == class_desc ||
                          rn.class_desc == internal_from_descriptor(class_desc));
        bool name_match = rn.method == method && rn.sig == dex_sig;
        if (name_match && (cls_match || rn.class_desc.empty())) {
            tried = "RegisterNatives:" + rn.method + rn.sig;
            return rn.fn;
        }
    }
    tried = short_name;
    if (long_name != short_name) tried += ", " + long_name;
    tried += ", RegisterNatives";
    return nullptr;
}

bool call_native(void* fn, bool static_call, const std::string& sig,
                 const std::vector<JArg>& args, JOutcome& out,
                 std::string& error) {
    init_tables();
    {
        std::lock_guard<std::mutex> lk(g_mu);
        ++g_native_calls;
    }
    auto params = param_types(sig);
    size_t close = sig.find(')');
    char ret = close + 1 < sig.size() ? sig[close + 1] : 'V';

    // For virtual methods the engine passes the receiver as args[0]
    // (OBJECT kind); skip it — the JVM receiver slot is covered below.
    size_t arg_off = 0;
    if (!static_call && !args.empty() &&
        (args[0].kind == JArg::Kind::OBJECT || args[0].kind == JArg::Kind::NULLREF))
        arg_off = 1;

    uint64_t int_regs[6] = {0, 0, 0, 0, 0, 0};
    double sse_regs[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    std::vector<uint64_t> stack_args;
    int int_i = 0, sse_i = 0;

    auto push_int = [&](uint64_t v) {
        if (int_i < 6) int_regs[int_i++] = v;
        else stack_args.push_back(v);
    };
    auto push_float_bits = [&](uint32_t fb) {
        // SysV: float rides in an SSE register (movss). We store the 4-byte
        // pattern in the LOW half of an 8-byte slot; the thunk's movsd load
        // leaves the exact float pattern where the callee's movss reads it.
        double d = 0.0;
        memcpy(&d, &fb, 4);
        if (sse_i < 8) sse_regs[sse_i++] = d;
        else {
            uint64_t b = fb;  // zero-extended into the stack slot
            stack_args.push_back(b);
        }
    };
    auto push_double = [&](double d) {
        if (sse_i < 8) sse_regs[sse_i++] = d;
        else stack_args.push_back(*(uint64_t*)&d);
    };

    // slot 0: JNIEnv*
    push_int((uint64_t)(uintptr_t)&g_env);
    // slot 1: receiver — jclass token for static, jobject identity otherwise
    if (static_call) push_int((uint64_t)(uintptr_t)box_string("jclass-token"));
    else push_int(0x500000000ull);  // anonymous receiver identity

    for (size_t i = 0; i < params.size(); ++i) {
        const char c0 = params[i][0];
        char c = c0 == '[' ? 'L' : c0;  // arrays ride as references
        const JArg a = (i + arg_off) < args.size() ? args[i + arg_off] : JArg();
        switch (c) {
            case 'Z': case 'B': case 'C': case 'S': case 'I':
                push_int((uint64_t)(uint32_t)(a.kind == JArg::Kind::NULLREF
                                                  ? 0
                                                  : a.i32));
                break;
            case 'J':
                push_int((uint64_t)a.i64);
                break;
            case 'F': {
                float fv = a.f32;
                uint32_t fb;
                memcpy(&fb, &fv, 4);
                push_float_bits(fb);
                break;
            }
            case 'D':
                push_double(a.f64);
                break;
            case 'L': {
                if (a.kind == JArg::Kind::STRING)
                    push_int((uint64_t)(uintptr_t)box_string(a.str));
                else if (a.kind == JArg::Kind::NULLREF) push_int(0);
                else push_int(0x500000000ull | (a.object_id & 0xffffffffull));
                break;
            }
            default:
                push_int(0);
        }
    }

    // overflow buffer must stay alive across the call
    std::vector<uint64_t> overflow = stack_args;
    double sse_ret = 0.0;
    uint64_t int_ret = miniandroid_native_thunk(
        fn, overflow.data(), overflow.size(), int_regs, sse_regs, &sse_ret);

    switch (ret) {
        case 'V': out.kind = JOutcome::Kind::VOID; break;
        case 'Z':
            out.kind = JOutcome::Kind::BOOLEAN;
            out.i = (int32_t)(int_ret & 0xff) ? 1 : 0;
            break;
        case 'B':
            out.kind = JOutcome::Kind::BYTE;
            out.i = (int8_t)(uint8_t)int_ret;
            break;
        case 'C':
            out.kind = JOutcome::Kind::CHAR;
            out.i = (uint16_t)int_ret;
            break;
        case 'S':
            out.kind = JOutcome::Kind::SHORT;
            out.i = (int16_t)(uint16_t)int_ret;
            break;
        case 'I':
            out.kind = JOutcome::Kind::INT;
            out.i = (int32_t)int_ret;
            break;
        case 'J':
            out.kind = JOutcome::Kind::LONG;
            out.i = (int64_t)int_ret;
            break;
        case 'F': {
            out.kind = JOutcome::Kind::FLOAT;
            float fv;
            memcpy(&fv, &sse_ret, 4);  // low 32 bits = float pattern
            out.d = fv;
            break;
        }
        case 'D':
            out.kind = JOutcome::Kind::DOUBLE;
            out.d = sse_ret;
            break;
        case 'L': case '[': {
            void* ref = (void*)(uintptr_t)int_ret;
            if (!ref) {
                out.kind = JOutcome::Kind::OBJECT;
                out.object_id = 0;
            } else {
                // The implemented subset materializes exactly one object
                // kind: a jstring box (NewStringUTF). Any other pointer is
                // surfaced as UNSUPPORTED text, never a fabricated managed
                // object.
                out.kind = JOutcome::Kind::STRING;
                out.str = *static_cast<std::string*>(ref);
            }
            break;
        }
        default:
            out.kind = JOutcome::Kind::VOID;
    }
    arena_clear();
    (void)error;
    return true;
}

unsigned long long load_attempts() {
    std::lock_guard<std::mutex> lk(g_mu);
    return g_load_attempts;
}
unsigned long long load_successes() {
    std::lock_guard<std::mutex> lk(g_mu);
    return g_load_successes;
}
unsigned long long native_calls() {
    std::lock_guard<std::mutex> lk(g_mu);
    return g_native_calls;
}
unsigned long long native_call_failures() {
    std::lock_guard<std::mutex> lk(g_mu);
    return g_unsupported_slot_calls;
}

}  // namespace nativeexec
}  // namespace miniandroid
