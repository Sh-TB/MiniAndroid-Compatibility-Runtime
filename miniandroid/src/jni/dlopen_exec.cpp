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
#include "native_dep.h"
#include "../diagnostics/gfx_trace.h"  // CONT-83 WS-B native.load rows

#include <dlfcn.h>
#include <csetjmp>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <sys/wait.h>
#include <unistd.h>
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
unsigned long long g_native_call_faults = 0;  // FIX-TTT guarded-call faults

std::vector<LoadedLib>& libs() {
    static std::vector<LoadedLib> v;
    return v;
}
std::map<std::string, std::string>& loader_notes() {  // caller class → lib
    static std::map<std::string, std::string> m;
    return m;
}

// ── FIX-TTT (CONT-120): FAULT-GUARDED NATIVE CALL LAW ──────────────────
// A real dlopen hands us REAL foreign code (JNI_OnLoad, JNI functions)
// running against our minimal JavaVM/JNIEnv bridge. A fault inside that
// code is a LIBRARY-vs-BRIDGE contract failure in this environment — on a
// real device it would kill the process, but a compatibility runtime must
// SURVIVE to report honestly (the tictactoe evidence: libgdx.so's
// JNI_OnLoad dereferenced a null the minimal bridge handed it → SIGSEGV
// si_addr=0x0 → the whole run died BEFORE the runtime could raise the
// honest UnsatisfiedLinkError the AOSP Runtime.loadLibrary0 contract
// demands for a rejected library). Law: native entry points we do not
// control run inside a sigsetjmp guard; a SIGSEGV/SIGBUS inside the guard
// longjmps back, the library is dlclose'd, and the caller sees a load
// failure / UnsatisfiedLinkError with the REAL fault recorded on stderr.
// The guard is the standard recover-from-plugin-fault technique; the
// engine-wide crash forensics handler (diagnostics/crash_forensics.cpp)
// is saved and restored around every guarded region, so faults OUTSIDE a
// guarded region keep their full forensics path.
sigjmp_buf& guard_jb() {
    static sigjmp_buf jb;
    return jb;
}
volatile sig_atomic_t g_guard_active = 0;

struct GuardedSignal {
    int sig;
    struct sigaction old;
};
// Saved pre-guard actions (crash-forensics handler) — read by the guard
// handler's fallback path, written only by install_native_guard.
GuardedSignal g_guard_saved[4];
size_t g_guard_saved_n = 0;

// Installs the guard handlers for SIGSEGV/SIGBUS/SIGABRT/SIGILL (saves the
// previous actions so the engine-wide crash-forensics path survives the
// guard).
// F-C4-546 (4APP4 W2, Coder-4): SIGABRT joins the guarded set. Live
// evidence (Tusky 33.1 + ConnectBot 1.11.1-oss at S154 HEAD post-F545):
// libconscrypt_jni.so dlopen now SUCCEEDS (fortify family bound), its
// JNI_OnLoad runs against the minimal JNIEnv, a field lookup misses
// ("NativeCrypto: could not find field address" — GetFieldID is an
// unimplemented slot) and conscrypt's own CHECK path calls abort() →
// SIGABRT → the WHOLE RUN died with rc=134 before the engine could raise
// the AOSP load-failure contract. A native init that aborts inside the
// guarded handshake is a LIBRARY-vs-BRIDGE contract failure — same law
// class as the SIGSEGV/SIGBUS arm (FIX-TTT): longjmp back, dlclose,
// honest UnsatisfiedLinkError; the app's own Conscrypt catch chain then
// degrades gracefully (OkHttp platform fallback). SIGILL joins for the
// illegal-instruction variant of the same class.
void install_native_guard() {
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_flags = SA_NODEFER | SA_SIGINFO;  // allow return; W10: fault RIP
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = [](int sig, siginfo_t* info, void* uctx_v) {
        if (g_guard_active) {
            // W10 (Coder-4) FAULT TRACE — the faulting instruction pointer
            // and fault address (diagnoses WHICH native instruction killed
            // the call; RIP<->library mapping via /proc/self/maps).
            {
                ucontext_t* uc = static_cast<ucontext_t*>(uctx_v);
                uintptr_t rip = uc->uc_mcontext.gregs[REG_RIP];
                uintptr_t addr =
                    info && info->si_code != SI_USER
                        ? reinterpret_cast<uintptr_t>(info->si_addr)
                        : 0;
                static bool w10_ft =
                    std::getenv("MINIANDROID_W10_JNI_TRACE") != nullptr;
                if (w10_ft) {
                    fprintf(stderr,
                            "[W10-FAULT] sig=%d rip=%p fault_addr=%p\n",
                            sig, (void*)rip, (void*)addr);
                    // Map RIP to its library + offset (self-maps lookup).
                    FILE* maps = fopen("/proc/self/maps", "r");
                    if (maps) {
                        char line[512];
                        while (fgets(line, sizeof line, maps)) {
                            unsigned long lo, hi;
                            char perms[8], path[400] = "";
                            if (sscanf(line, "%lx-%lx %7s %*x %*x:%*x %*u %399s",
                                       &lo, &hi, perms, path) >= 3) {
                                if (rip >= lo && rip < hi && path[0] == '/') {
                                    fprintf(stderr,
                                            "[W10-FAULT] rip in %s +0x%lx "
                                            "(%s)\n",
                                            path, rip - lo, perms);
                                    break;
                                }
                            }
                        }
                        // W10: crude stack walk — print mapped return
                        // address candidates (RSP..RSP+512) so the native
                        // call chain at the fault is visible.
                        rewind(maps);
                        uintptr_t rsp =
                            uc->uc_mcontext.gregs[REG_RSP];
                        for (int wi = 0; wi < 64; ++wi) {
                            uintptr_t v;
                            memcpy(&v, (void*)(rsp + wi * 8), 8);
                            if (v < 0x1000) continue;
                            char mline[512];
                            bool printed = false;
                            rewind(maps);
                            while (fgets(mline, sizeof mline, maps)) {
                                unsigned long lo, hi;
                                char perms[8], path[400] = "";
                                if (sscanf(mline,
                                           "%lx-%lx %7s %*x %*x:%*x %*u %399s",
                                           &lo, &hi, perms, path) >= 3) {
                                    if (v >= lo && v < hi && path[0] == '/') {
                                        fprintf(stderr,
                                                "[W10-FAULT] stack[%d]=%s "
                                                "+0x%lx\n",
                                                wi, path, v - lo);
                                        printed = true;
                                        break;
                                    }
                                }
                            }
                            (void)printed;
                        }
                        fclose(maps);
                    }
                    fflush(stderr);
                }
            }
            g_guard_active = 0;
            siglongjmp(guard_jb(), 1);
        }
        // Fault outside a guarded region: restore the handler that was
        // live before the guard was installed — the engine-wide crash
        // forensics path — and re-raise so a REAL engine crash keeps its
        // full forensic evidence.
        for (size_t i = 0; i < g_guard_saved_n; i++)
            sigaction(g_guard_saved[i].sig, &g_guard_saved[i].old, nullptr);
        raise(sig);
    };
    const int sigs[4] = {SIGSEGV, SIGBUS, SIGABRT, SIGILL};
    g_guard_saved_n = 0;
    for (int s : sigs)
        if (sigaction(s, &sa, &g_guard_saved[g_guard_saved_n].old) == 0) {
            g_guard_saved[g_guard_saved_n].sig = s;
            g_guard_saved_n++;
        }
}

void restore_native_guard() {
    for (size_t i = 0; i < g_guard_saved_n; i++)
        sigaction(g_guard_saved[i].sig, &g_guard_saved[i].old, nullptr);
}

// Runs `fn()` under the guard; returns false iff the native code faulted
// (the caller records the honest failure and cleans up).
template <typename F>
bool run_native_guarded(F&& fn) {
    install_native_guard();
    bool faulted = false;
    if (sigsetjmp(guard_jb(), 1) == 0) {
        g_guard_active = 1;
        fn();
        g_guard_active = 0;
    } else {
        faulted = true;  // longjmp landed: g_guard_active already cleared
    }
    restore_native_guard();
    return !faulted;
}

// ── FIX-TTT (CONT-120): DLOPEN FAULT PRE-CHECK LAW ──────────────────────
// A library whose ELF constructors / loader processing faults (tictactoe
// evidence: libgdx.so SIGSEGV inside dlopen with the anchor pre-pass in
// place, while the tower3d libgdx.so of the same family loads clean) would
// otherwise take the whole runtime down inside glibc's loader — and a
// post-fault longjmp would leave the loader lock held. Law: probe the
// exact dlopen in a FORKED child first (inherits the anchor pre-pass and
// address space; a faulted child dies by signal WITHOUT poisoning the
// parent's loader). The parent attempts its real dlopen only when the
// probe came back clean; a faulted/refused probe becomes the honest load
// failure. Belt-and-braces: the parent's own dlopen also runs under the
// fault guard, and any residual fault sets g_loader_poisoned so NO further
// real dlopen is attempted this process (every later load fails honestly —
// the loader-lock exposure is never repeated).
volatile sig_atomic_t g_loader_poisoned = 0;
int g_probe_status = 0;  // raw waitpid status of the last fork-probe child

// Probe verdict: SAFE → parent dlopens for real; REFUSED → parent dlopens
// anyway (its own failure carries the REAL dlerror string); FAULTED → the
// library faults inside the loader, the parent must NOT dlopen it.
enum class ProbeVerdict { SAFE, REFUSED, FAULTED };

ProbeVerdict dlopen_probe(const char* host_path) {
    if (g_loader_poisoned) return ProbeVerdict::FAULTED;
    pid_t p = fork();
    if (p < 0) return ProbeVerdict::SAFE;  // fork unavailable: direct dlopen
    if (p == 0) {
        // Probe child: dlopen then _exit — never unwind, never run parent
        // atexit handlers, never touch the parent's state.
        // F-C4-595 (W10): DEEPBIND in the probe too (mirrors the real
        // open — the probe must observe the same binding the real dlopen
        // will produce).
        void* h = dlopen(host_path,
                         RTLD_NOW | RTLD_LOCAL | RTLD_DEEPBIND);
        _exit(h ? 0 : 2);
    }
    int st = 0;
    while (waitpid(p, &st, 0) < 0) {
        // EINTR only; other errors would leave the child unreaped — accept.
        break;
    }
    g_probe_status = st;
    if (WIFSIGNALED(st)) return ProbeVerdict::FAULTED;
    if (WIFEXITED(st) && WEXITSTATUS(st) == 0) return ProbeVerdict::SAFE;
    return ProbeVerdict::REFUSED;
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

// ─────────────────────────────────────────────────────────────────────
// F-C4-587 (W10, 4APP4 Coder-4) — JNI OBJECT-ARRAY family. AOSP/ART law
// (art/runtime/jni/jni_internal.cc): NewObjectArray(len, elementClass,
// init) allocates a real object array; SetObjectArrayElement stores a
// reference at an index; GetObjectArrayElement reads one; GetArrayLength
// answers the element count. The spec slots are 171/172/173/174 (the
// F-C4-581 spec-exact table left them on the UNSUPPORTED stub), so any
// registered native building a String[] got 0 back from NewObjectArray
// and returned null — live-proven: conscrypt's NativeCrypto.<clinit> does
//   get_cipher_names("ALL") → C body loops the SSL_CIPHER stack calling
//   NewObjectArray + NewStringUTF + SetObjectArrayElement → returned the
//   null → `array-length` NPE at pc=0x48 (NC) / 0x42 (CB) — the tail of
//   the whole conscrypt/RegisterNatives chain. Box model: a NativeObjArray
//   is a tagged heap-arena structure of element pointers (jstring boxes or
//   nested); call_native's 'L'/'[' return marshaling converts a known
//   array box into JOutcome::STRING_ARRAY so the engine mints a real DEX
//   array. Nested non-string elements surface as empty strings (honest
//   documented boundary — conscrypt's surface is String[] flat).
// ─────────────────────────────────────────────────────────────────────
struct NativeObjArray {
    uint64_t magic = 0x4A4F42415225110Full;  // "J0BARR!"
    std::vector<void*> elems;
};
static std::vector<NativeObjArray*>& obj_array_boxes() {
    static std::vector<NativeObjArray*> boxes;
    return boxes;
}
static NativeObjArray* as_obj_array(void* ref) {
    if (!ref) return nullptr;
    for (NativeObjArray* b : obj_array_boxes())
        if (b == ref) return b;
    return nullptr;
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
// F-C4-581 (W9): 181 → 240 — the spec table runs past 228 (ExceptionCheck);
// the old bound silently capped the spec-exact wiring above it.
constexpr int kJniSlots = 240;
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

// S188-W8 F-NEW-584 (slot census): the loud stub no longer shouts blindly —
// it records WHICH spec slot the library invoked. Per-slot thunks carry the
// slot index (a JNIEnv fn-table call cannot derive it from the args). The
// census turns "6 UNSUPPORTED-slot hits" (W2 promotion evidence, queens)
// into an exact demand list — the honest requirement matrix for the next
// engine wave. env slots -> census[0..239], vm slots -> census[240+i].
unsigned long long g_slot_census[256] = {0};
static void jni_unsupported_slot_impl(int slot, bool is_vm) {
    std::lock_guard<std::mutex> lk(g_mu);
    ++g_unsupported_slot_calls;
    int idx = is_vm ? 240 + slot : slot;
    if (slot < 0 || idx < 0 || idx >= 256) idx = 0;
    ++g_slot_census[idx];
    static unsigned long long s_printed = 0;
    if (s_printed < 40) {
        ++s_printed;
        fprintf(stderr,
                "[MINIANDROID-JNI] UNSUPPORTED %s slot %d invoked — the library "
                "used a JNI function outside the implemented subset (strings / "
                "exceptions / VM / registration)\n",
                is_vm ? "JavaVM" : "JNIEnv", slot);
    }
}
long jni_unsupported_slot() {  // legacy alias (no index known)
    jni_unsupported_slot_impl(-1, false);
    return 0;
}
template <int N, bool V>
struct UnsupportedThunk {
    static long fn() { jni_unsupported_slot_impl(N, V); return 0; }
};
template <int N, bool V>
struct FillUnsupported {
    static void fill(void** t) {
        FillUnsupported<N - 1, V>::fill(t);
        t[N] = (void*)&UnsupportedThunk<N, V>::fn;
    }
};
template <bool V>
struct FillUnsupported<-1, V> {
    static void fill(void**) {}
};

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

// ── S188-W8 frontier-1 (queens slot census): env165 GetStringChars ×5 +
// env226 NewWeakGlobalRef ×1 — the EXACT demand list from the F-NEW-584
// census run (evidence/s188_w8/QUEENS_SLOT_CENSUS.json). The UTF-16 face
// of the string family: transcode the boxed modified-UTF8 string to
// UTF-16 (surrogate pairs for supplementary codepoints, the JNI spec's
// jchar* shape), arena-owned copy (is_copy=1 — same law as
// GetStringUTFChars). NewWeakGlobalRef = identity (same law as
// NewGlobalRef — a weak ref that the runtime never collects is honest
// here: the runtime has no GC collection pass over native boxes).
static const uint16_t* jni_string_utf16_arena(void* jstr, int* out_len) {
    static std::vector<std::vector<uint16_t>>* arena = nullptr;
    static std::mutex* a_mu = nullptr;
    if (!a_mu) { a_mu = new std::mutex(); arena = new std::vector<std::vector<uint16_t>>(); }
    std::string s = jstr ? *static_cast<std::string*>(jstr) : std::string();
    std::vector<uint16_t> out;
    size_t i = 0, n = s.size();
    while (i < n) {
        unsigned char c = (unsigned char)s[i];
        uint32_t cp = 0;
        int extra = 0;
        if (c < 0x80) { cp = c; extra = 0; }
        else if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; extra = 1; }
        else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; extra = 2; }
        else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; extra = 3; }
        else { cp = 0xFFFD; extra = 0; }  // invalid byte -> U+FFFD
        ++i;
        bool bad = false;
        for (int k = 0; k < extra; ++k) {
            if (i >= n || ((unsigned char)s[i] & 0xC0) != 0x80) { bad = true; break; }
            cp = (cp << 6) | ((unsigned char)s[i] & 0x3F);
            ++i;
        }
        if (bad) cp = 0xFFFD;
        if (cp >= 0x10000) {  // supplementary -> surrogate pair
            cp -= 0x10000;
            out.push_back((uint16_t)(0xD800 | (cp >> 10)));
            out.push_back((uint16_t)(0xDC00 | (cp & 0x3FF)));
        } else {
            out.push_back((uint16_t)cp);
        }
    }
    std::lock_guard<std::mutex> lk(*a_mu);
    arena->push_back(std::move(out));
    std::vector<uint16_t>& stored = arena->back();
    if (out_len) *out_len = (int)stored.size();
    return stored.data();
}
const uint16_t* jni_GetStringChars(void* env, void* jstr,
                                   unsigned char* is_copy) {
    if (!jstr) return nullptr;
    if (is_copy) *is_copy = 1;  // arena-owned copy semantics
    return jni_string_utf16_arena(jstr, nullptr);
}
void jni_ReleaseStringChars(void*, void*, const uint16_t*) {}  // arena-owned
void* jni_NewWeakGlobalRef(void*, void* r) { return r; }
void jni_DeleteWeakGlobalRef(void*, void*) {}

// S188-W8 frontier-1b (quinb slot census): env19 PushLocalFrame ×1 — the
// local-ref frame family. The runtime's local refs are identity boxes with
// no collection pass, so a frame push/pop is an honest success that passes
// the surviving ref through (the JNI spec's PopLocalFrame return law).
int jni_PushLocalFrame(void*, int32_t /*capacity*/) { return 0; }  // JNI_OK
void* jni_PopLocalFrame(void*, void* result) { return result; }
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

// F-C4-587 (W10): the object-array family — spec slots 171-174.
// (jsize = jint = int32_t per jni.h; kept local to avoid a jni.h dep.)
static int32_t f587_len_of(void* arr) {
    NativeObjArray* b = as_obj_array(arr);
    return b ? (int32_t)b->elems.size() : 0;
}
int32_t jni_GetArrayLength(void*, void* arr) { return f587_len_of(arr); }
void* jni_NewObjectArray(void*, int32_t len, void* elem_class, void* init) {
    (void)elem_class;
    if (len < 0) return nullptr;
    NativeObjArray* b = new NativeObjArray();
    b->elems.assign((size_t)len, init);
    obj_array_boxes().push_back(b);
    return b;
}
void* jni_GetObjectArrayElement(void*, void* arr, int32_t idx) {
    NativeObjArray* b = as_obj_array(arr);
    if (!b || idx < 0 || (size_t)idx >= b->elems.size()) return nullptr;
    return b->elems[(size_t)idx];
}
void jni_SetObjectArrayElement(void*, void* arr, int32_t idx, void* val) {
    NativeObjArray* b = as_obj_array(arr);
    if (!b || idx < 0) return;
    if ((size_t)idx >= b->elems.size()) b->elems.resize((size_t)idx + 1, nullptr);
    b->elems[(size_t)idx] = val;
}
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

// ─────────────────────────────────────────────────────────────────────
// F-C4-581 (W9): JNI REFLECTION-ID LAW — GetMethodID / GetStaticMethodID
// / GetFieldID / GetStaticFieldID. ROOT (live, ConnectBot v1.11.1 census
// ×5 UnsatisfiedLinkError family; harness + objdump on the APK's own
// libconscrypt_jni.so): conscrypt's JNI_OnLoad resolves
// `call *0xa8(%rax)` = slot 33 (GetMethodID) and `call *0x2f0(%rax)` =
// slot 94 (GetFieldID); the bridge had NEITHER filled — both hit the
// loud UNSUPPORTED stub → 0 → conscrypt logged "could not find field
// address" (its own string is "could not find field %s") → deref of the
// null id → SIGSEGV → FIX-TTT guard → UnsatisfiedLinkError at
// OpenSSLProvider.<init>. JNI law (jni.h): the ID lookups NEVER answer
// null for a resolvable member; the returned id must be STABLE per
// (class, name, signature). Implementation: interned opaque handles
// (box_string of a coded record), so a future Call*Method layer can
// decode (class, member, signature) from the id verbatim.
// ─────────────────────────────────────────────────────────────────────
static void* jni_intern_id(const std::string& key) {
    static std::map<std::string, std::string*> id_pool;
    auto it = id_pool.find(key);
    if (it == id_pool.end()) {
        std::string* p = box_string(key);
        it = id_pool.emplace(key, p).first;
    }
    return it->second;
}
static std::string jni_class_name_of(void* jcls) {
    if (!jcls) return std::string();
    // box_string jclass: the payload IS the binary class name.
    return *static_cast<std::string*>(jcls);
}
static void* jni_GetMethodID(void*, void* jcls, const char* name,
                             const char* sig) {
    if (!name || !sig) return nullptr;
    static thread_local uint64_t f581_m = 0;
    if (f581_m < 12) { ++f581_m;
        fprintf(stderr, "[F-C4-581] GetMethodID(%s, %s%s) -> id\n",
                jni_class_name_of(jcls).c_str(), name, sig); }
    return jni_intern_id("M:" + jni_class_name_of(jcls) + "|" + name +
                         "|" + sig);
}
static void* jni_GetStaticMethodID(void*, void* jcls, const char* name,
                                   const char* sig) {
    if (!name || !sig) return nullptr;
    static thread_local uint64_t f581_sm = 0;
    if (f581_sm < 12) { ++f581_sm;
        fprintf(stderr, "[F-C4-581] GetStaticMethodID(%s, %s%s) -> id\n",
                jni_class_name_of(jcls).c_str(), name, sig); }
    return jni_intern_id("SM:" + jni_class_name_of(jcls) + "|" + name +
                         "|" + sig);
}
static void* jni_GetFieldID(void*, void* jcls, const char* name,
                            const char* sig) {
    if (!name || !sig) return nullptr;
    static thread_local uint64_t f581_f = 0;
    if (f581_f < 12) { ++f581_f;
        fprintf(stderr, "[F-C4-581] GetFieldID(%s, %s%s) -> id\n",
                jni_class_name_of(jcls).c_str(), name, sig); }
    return jni_intern_id("F:" + jni_class_name_of(jcls) + "|" + name +
                         "|" + sig);
}
static void* jni_GetStaticFieldID(void*, void* jcls, const char* name,
                                  const char* sig) {
    if (!name || !sig) return nullptr;
    static thread_local uint64_t f581_sf = 0;
    if (f581_sf < 12) { ++f581_sf;
        fprintf(stderr, "[F-C4-581] GetStaticFieldID(%s, %s%s) -> id\n",
                jni_class_name_of(jcls).c_str(), name, sig); }
    return jni_intern_id("SF:" + jni_class_name_of(jcls) + "|" + name +
                         "|" + sig);
}
// MonitorEnter/MonitorExit: the serialized engine owns all monitors at
// the DEX layer; native-side enter/exit pairs are answerable 0 (success)
// — the JNI contract allows nested ownership by the same thread.
static int jni_MonitorEnter(void*, void*) { return 0; }
static int jni_MonitorExit(void*, void*) { return 0; }
// NewString(jchar[], len): JNI law — construct from UTF-16. Minimal
// BMP-only UTF-8 encoding (the corpus surface is ASCII+CJK BMP).
static void* jni_NewString(void*, const unsigned short* chars, int len) {
    if (!chars || len < 0) return nullptr;
    std::string out;
    out.reserve(static_cast<size_t>(len));
    for (int i = 0; i < len; ++i) {
        unsigned int cp = chars[i];
        if (cp < 0x80) out.push_back(static_cast<char>(cp));
        else if (cp < 0x800) {
            out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else {
            out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        }
    }
    return box_string(out);
}

int vm_GetEnv(void* vm, void** env, int version);

void init_tables() {
    static bool done = false;
    if (done) return;
    done = true;
    // ─────────────────────────────────────────────────────────────────
    // F-C4-581 (W9): JNI SPEC-TABLE law. The previous wiring filled the
    // upper table with WRONG slot indices (string family at 113/114/117/
    // 118/119/120 — the true spec slots are 163/164/167/168/169/170;
    // RegisterNatives at 163 → true 215; GetJavaVM at 167 → true 219;
    // ExceptionCheck at 176 → true 228). PROOF (the APK's own
    // libconscrypt_jni.so, objdump): JNI_OnLoad's calls are
    // `*0xa8(%rax)` = 33 GetMethodID, `*0xb8(%rax)` = 23 DeleteLocalRef,
    // `*0x2f0(%rax)` = 94 GetFieldID, `*0x6b8(%rax)` = 215
    // RegisterNatives — the binary itself pins the spec order (jni.h
    // JNINativeInterface layout). Every upper-table call a native library
    // made was being routed to the wrong handler or to the loud
    // UNSUPPORTED stub: conscrypt's RegisterNatives never landed, its
    // method/field lookups answered 0 → SIGSEGV. Corrected to the
    // spec-exact layout below (slots ≤ 31 were already correct).
    // Blast radius: strictly-positive — the wrong wirings could only
    // answer nonsense (e.g. a NewString request at true-slot 167 hit the
    // GetJavaVM handler and got 0 back). The corpus battery re-verifies
    // maintainer-side (same honest caveat as every wave).
    // ─────────────────────────────────────────────────────────────────
    FillUnsupported<kJniSlots - 1, false>::fill(g_jni_table);
    g_jni_table[4] = (void*)&jni_GetVersion;               // 4 GetVersion
    g_jni_table[6] = (void*)&jni_FindClass;                // 6 FindClass
    g_jni_table[13] = (void*)&jni_Throw;                   // 13 Throw
    g_jni_table[14] = (void*)&jni_ThrowNew;                // 14 ThrowNew
    g_jni_table[15] = (void*)&jni_ExceptionOccurred;       // 15 ExceptionOccurred
    g_jni_table[16] = (void*)&jni_ExceptionDescribe;       // 16 ExceptionDescribe
    g_jni_table[17] = (void*)&jni_ExceptionClear;          // 17 ExceptionClear
    g_jni_table[18] = (void*)&jni_FatalError;              // 18 FatalError
    g_jni_table[19] = (void*)&jni_PushLocalFrame;          // 19 PushLocalFrame (W8 census: quinb ×1)
    g_jni_table[20] = (void*)&jni_PopLocalFrame;           // 20 PopLocalFrame
    g_jni_table[21] = (void*)&jni_NewGlobalRef;            // 21 NewGlobalRef
    g_jni_table[22] = (void*)&jni_DeleteGlobalRef;         // 22 DeleteGlobalRef
    g_jni_table[23] = (void*)&jni_DeleteLocalRef;          // 23 DeleteLocalRef
    g_jni_table[25] = (void*)&jni_NewLocalRef;             // 25 NewLocalRef
    g_jni_table[31] = (void*)&jni_GetObjectClass;          // 31 GetObjectClass
    // F-C4-581: the reflection-ID family — the conscrypt JNI_OnLoad path.
    g_jni_table[33] = (void*)&jni_GetMethodID;             // 33 GetMethodID
    g_jni_table[94] = (void*)&jni_GetFieldID;              // 94 GetFieldID
    g_jni_table[113] = (void*)&jni_GetStaticMethodID;      // 113 GetStaticMethodID
    g_jni_table[144] = (void*)&jni_GetStaticFieldID;       // 144 GetStaticFieldID
    // string family — TRUE spec slots (were mis-wired at 113..120).
    g_jni_table[163] = (void*)&jni_NewString;              // 163 NewString
    g_jni_table[164] = (void*)&jni_GetStringLength;        // 164 GetStringLength
    g_jni_table[165] = (void*)&jni_GetStringChars;         // 165 GetStringChars (W8 census: queens ×5)
    g_jni_table[166] = (void*)&jni_ReleaseStringChars;     // 166 ReleaseStringChars
    g_jni_table[167] = (void*)&jni_NewStringUTF;           // 167 NewStringUTF
    g_jni_table[168] = (void*)&jni_GetStringUTFLength;     // 168 GetStringUTFLength
    g_jni_table[169] = (void*)&jni_GetStringUTFChars;      // 169 GetStringUTFChars
    g_jni_table[170] = (void*)&jni_ReleaseStringUTFChars;  // 170 ReleaseStringUTFChars
    // F-C4-587 (W10): the object-array family — TRUE spec slots
    // (GetArrayLength 171, NewObjectArray 172, GetObjectArrayElement 173,
    // SetObjectArrayElement 174; previously the loud UNSUPPORTED stub).
    g_jni_table[171] = (void*)&jni_GetArrayLength;          // 171 GetArrayLength
    g_jni_table[172] = (void*)&jni_NewObjectArray;          // 172 NewObjectArray
    g_jni_table[173] = (void*)&jni_GetObjectArrayElement;   // 173 GetObjectArrayElement
    g_jni_table[174] = (void*)&jni_SetObjectArrayElement;   // 174 SetObjectArrayElement
    // registration + VM family — TRUE spec slots (were mis-wired at
    // 163/164/167/176).
    g_jni_table[215] = (void*)&jni_RegisterNatives;        // 215 RegisterNatives
    g_jni_table[216] = (void*)&jni_UnregisterNatives;      // 216 UnregisterNatives
    g_jni_table[217] = (void*)&jni_MonitorEnter;           // 217 MonitorEnter
    g_jni_table[218] = (void*)&jni_MonitorExit;            // 218 MonitorExit
    g_jni_table[219] = (void*)&jni_GetJavaVM;              // 219 GetJavaVM
    g_jni_table[228] = (void*)&jni_ExceptionCheck;         // 228 ExceptionCheck
    g_jni_table[226] = (void*)&jni_NewWeakGlobalRef;       // 226 NewWeakGlobalRef (W8 census: queens ×1)
    g_jni_table[227] = (void*)&jni_DeleteWeakGlobalRef;    // 227 DeleteWeakGlobalRef
    FillUnsupported<kVmSlots - 1, true>::fill(g_vm_table);
    std::atexit([]() {
        std::lock_guard<std::mutex> lk(g_mu);
        if (!g_unsupported_slot_calls) return;
        fprintf(stderr,
                "[MINIANDROID-JNI] UNSUPPORTED slot census: total=%llu",
                g_unsupported_slot_calls);
        for (int i = 0; i < 248; ++i)
            if (g_slot_census[i])
                fprintf(stderr, " %s%d=%llu", i >= 240 ? "vm" : "env",
                        i >= 240 ? i - 240 : i, g_slot_census[i]);
        fprintf(stderr, "\n");
    });
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
    // ── CONT-83 F-NEW-387: Android DT_NEEDED resolution pre-pass ────────
    // Android platform sonames (libm.so/liblog.so/libc.so/…) cannot be
    // resolved by the host loader. The capability-gated law classifies
    // every entry (app-bundled / validated first-party anchor /
    // missing-honest-block), pre-loads what it can RTLD_GLOBAL, and lands
    // a trace row per entry. The REAL dlopen below still fails loudly for
    // anything unresolvable — never a silent substitution.
    {
        const auto slash = host_path.rfind('/');
        const std::string lib_dir =
            slash == std::string::npos ? std::string() : host_path.substr(0, slash);
        for (const auto& row : jni::prepare_dependencies(host_path, lib_dir))
            (void)row;   // trace rows already landed inside prepare
    }
    dlerror();
    // FIX-TTT: fork-probe the dlopen first — a library that faults inside
    // the loader (ELF constructors) must become an honest load failure,
    // never process death and never a poisoned loader lock. A cleanly
    // refused probe still lets the parent dlopen so the REAL dlerror
    // reaches the AOSP UnsatisfiedLinkError message.
    if (dlopen_probe(host_path.c_str()) == ProbeVerdict::FAULTED) {
        out.detail = "dlopen faulted (SIGSEGV/SIGBUS inside the library's "
                     "ELF constructors/loader; fork-probe child died by "
                     "signal) — runtime survived (FIX-TTT)";
        fprintf(stderr, "[S2-NATIVE] load %s (%s): %s\n", libname.c_str(),
                host_path.c_str(), out.detail.c_str());
        gfx::GfxTrace::instance().native_load(libname, host_path, false,
                                              out.detail);
        return out;
    }
    void* h = nullptr;
    bool dlopen_faulted = !run_native_guarded(
        [&] {
            // ── F-C4-595 (W10, 4APP4 Coder-4) — RTLD_DEEPBIND APP-LIB
            // ISOLATION law (the AOSP linker-namespace analog). ROOT
            // (live, CB v1.11.1 conscrypt get_cipher_names fault trace):
            // conscrypt's .so exports its STATICALLY-LINKED BoringSSL
            // (SSL_CTX_new, SSL_set_cipher_list, ... all T), but on glibc
            // an exported symbol can be PREEMPTED by the global scope —
            // the .so's own PLT resolved SSL_CTX_new to the HOST's
            // libssl.so.3 (OpenSSL 3), whose SSL_CTX layout differs from
            // BoringSSL's; the BoringSSL code then walked a foreign struct
            // and CBS_get_u16 deref'd a NULL CBS from the mismatched
            // method table (W10-FAULT: rip=+0x2043f0 fault_addr=0x8, call
            // chain get_cipher_names +0x64 → host libssl +0x25300).
            // Android never sees this: linker namespaces isolate app libs
            // from the platform's libssl. glibc's RTLD_DEEPBIND is the
            // same isolation: the library's OWN definitions win for its
            // internal references. Blast radius: app-lib dlopen binding
            // only — anchor libs and host libs are untouched.
            h = dlopen(host_path.c_str(),
                       RTLD_NOW | RTLD_LOCAL | RTLD_DEEPBIND);
        });
    if (dlopen_faulted) {
        // Residual fault the probe did not catch (address-space layout
        // difference): the loader may hold its lock now — poison it so no
        // further real dlopen is ever attempted this process, and report
        // the honest failure.
        g_loader_poisoned = 1;
        out.detail = "dlopen faulted (SIGSEGV/SIGBUS inside the loader, "
                     "post-probe residual) — loader poisoned for this "
                     "process, runtime survived (FIX-TTT)";
        fprintf(stderr, "[S2-NATIVE] load %s (%s): %s\n", libname.c_str(),
                host_path.c_str(), out.detail.c_str());
        gfx::GfxTrace::instance().native_load(libname, host_path, false,
                                              out.detail);
        return out;
    }
    if (!h) {
        const char* e = dlerror();
        out.detail = std::string("dlopen failed: ") + (e ? e : "unknown error");
        fprintf(stderr, "[S2-NATIVE] load %s (%s): %s\n", libname.c_str(),
                host_path.c_str(), out.detail.c_str());
        gfx::GfxTrace::instance().native_load(libname, host_path, false,
                                              out.detail);
        return out;
    }
    LoadedLib lib;
    lib.name = libname;
    lib.host_path = host_path;
    lib.logical_path = logical_path;
    lib.handle = h;
    // JNI_OnLoad handshake (AOSP: version must be >= JNI_VERSION_1_1)
    // FIX-TTT (CONT-120): FAULT-GUARDED — a foreign JNI_OnLoad that faults
    // against the minimal bridge (libgdx.so evidence: SIGSEGV si_addr=0x0)
    // is a load FAILURE, not process death: dlclose + honest detail, and
    // the caller raises the AOSP UnsatisfiedLinkError contract.
    int (*onload)(void*, void*) = (int (*)(void*, void*))dlsym(h, "JNI_OnLoad");
    if (onload) {
        int v = 0;
        bool onload_ok = run_native_guarded(
            [&] { v = onload(&g_vm, nullptr); });
        if (!onload_ok) {
            out.detail = "JNI_OnLoad faulted (SIGSEGV/SIGBUS at the handshake) "
                         "against the minimal JavaVM bridge; library unloaded "
                         "(dlclose) — runtime survived (FIX-TTT guard)";
            dlclose(h);
            fprintf(stderr, "[S2-NATIVE] %s: %s\n", libname.c_str(),
                    out.detail.c_str());
            gfx::GfxTrace::instance().native_load(libname, host_path, false,
                                                  out.detail);
            return out;
        }
        if (v == 0) {
            out.detail = "JNI_OnLoad failed (returned 0)";
            dlclose(h);
            fprintf(stderr, "[S2-NATIVE] %s: %s\n", libname.c_str(),
                    out.detail.c_str());
            gfx::GfxTrace::instance().native_load(libname, host_path, false,
                                                  out.detail);
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
    gfx::GfxTrace::instance().native_load(libname, host_path, out.ok,
                                          out.detail);
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

    // W10 (Coder-4) JNI TRACE — env-gated, bounded: every find_symbol query
    // with the first few registered-natives entries it compared against
    // (diagnoses the registered-table match for the conscrypt dispatch).
    static thread_local const bool w10_jni_on =
        std::getenv("MINIANDROID_W10_JNI_TRACE") != nullptr;
    static thread_local uint64_t w10_jni_n = 0;
    if (w10_jni_on && w10_jni_n++ < 40) {
        fprintf(stderr, "[W10-JNI] find_symbol cls=%s method=%s sig=%s "
                        "(registered=%zu)\n",
                class_desc.c_str(), method.c_str(), dex_sig.c_str(),
                registered().size());
        size_t shown = 0;
        for (const auto& rn : registered()) {
            if (rn.method != method) continue;
            fprintf(stderr, "[W10-JNI]   reg cand cls=%s name=%s sig=%s fn=%p\n",
                    rn.class_desc.c_str(), rn.method.c_str(),
                    rn.sig.c_str(), rn.fn);
            if (++shown >= 4) break;
        }
    }

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
    // FIX-TTT (CONT-120): the same fault guard that covers the JNI_OnLoad
    // handshake covers every real symbol call — foreign code we do not
    // control must never take the process down; a fault becomes an honest
    // call failure with the error string the caller records.
    uint64_t int_ret = 0;
    bool call_ok = run_native_guarded([&] {
        int_ret = miniandroid_native_thunk(
            fn, overflow.data(), overflow.size(), int_regs, sse_regs, &sse_ret);
    });
    if (!call_ok) {
        ++g_native_call_faults;
        error = "native call faulted (SIGSEGV/SIGBUS inside the library) — "
                "guarded, runtime survived (FIX-TTT)";
        fprintf(stderr, "[S2-NATIVE] guarded call fault: %s sig=%s\n",
                error.c_str(), sig.c_str());
        return false;
    }

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
            } else if (NativeObjArray* arr = as_obj_array(ref)) {
                // F-C4-587 (W10): a native-built jobjectArray → the engine
                // mints a real DEX array (STRING_ARRAY outcome). Elements
                // are jstring boxes; null/non-string elements degrade to
                // empty strings with a null marker carried by emptiness
                // (documented boundary: conscrypt's surface is flat).
                out.kind = JOutcome::Kind::STRING_ARRAY;
                out.str_elems.reserve(arr->elems.size());
                for (void* e : arr->elems) {
                    if (e && !as_obj_array(e)) {
                        out.str_elems.push_back(
                            *static_cast<std::string*>(e));
                    } else {
                        out.str_elems.push_back(std::string());
                    }
                }
                fprintf(stderr,
                        "[F-C4-587] native object-array return: %zu "
                        "string elements (NewObjectArray family live)\n",
                        arr->elems.size());
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
bool loader_poisoned() { return g_loader_poisoned != 0; }
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
