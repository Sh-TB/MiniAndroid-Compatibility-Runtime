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
#include <execinfo.h>
#include <csetjmp>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cerrno>
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

// S200-T03 F-NEW-622 — ONE-IDENTITY DIRECT-BUFFER LAW (declaration in
// dlopen_exec.h): the f590 hook sets this when the answered addr is the
// buffer's REAL memory; GetDirectBufferAddress then answers it verbatim.
thread_local bool f590_served_real_identity = false;

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
    // GP-JNI-003 (issue #582): one process-global sigjmp_buf + one global
    // g_guard_active meant a fault on thread B while thread A held the
    // guard longjmp'd on A's context — cross-thread siglongjmp is UB and
    // corrupts execution state. The guard context is per-thread now: the
    // signal handler runs on the faulting thread and jumps on THAT
    // thread's own setjmp context. The deterministic single-thread engine
    // keeps its existing behavior.
    static thread_local sigjmp_buf jb;
    return jb;
}
volatile thread_local sig_atomic_t g_guard_active = 0;
// F-NEW-593 (W10): the honest reason of the last guard landing (exception
// text or signal) — surfaced in call_native's fault detail.
std::string g_guard_last_reason;

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
        // F-NEW-593 (W10): the thunk now carries .eh_frame CFI, so a C++
        // exception thrown inside the real native unwinds HERE instead of
        // hitting std::terminate in the unwinder (the abort face that
        // killed queens' RunBundle dispatch). The catch is the honest JNI
        // boundary: call_ok=false + the exception text as the error.
        try {
            fn();
        } catch (const std::exception& e) {
            g_guard_active = 0;
            faulted = true;
            g_guard_last_reason = std::string("C++ exception in native: ") +
                                  (e.what() ? e.what() : "(no message)");
            // F-NEW-593 diag (bounded): WHERE the exception was thrown —
            // the unwind stopped here, so the stack IS the throw chain.
            if (std::getenv("MINIANDROID_W10_JNI_TRACE")) {
                void* bt[24];
                int n = backtrace(bt, 24);
                char** syms = backtrace_symbols(bt, n);
                fprintf(stderr, "[W10-THROW] %s — throw chain:\n",
                        g_guard_last_reason.c_str());
                for (int i = 0; i < n && i < 24; ++i)
                    fprintf(stderr, "[W10-THROW]   [%d] %s\n", i,
                            syms ? syms[i] : "?");
                free(syms);
            }
        } catch (...) {
            g_guard_active = 0;
            faulted = true;
            g_guard_last_reason =
                "unknown C++ exception (uncaught inside the library)";
        }
        if (!faulted) g_guard_active = 0;
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
    if (g_loader_poisoned) {
        fprintf(stderr,
                "[DLOPEN-PHASE] fork-probe skipped: loader poisoned "
                "(pid=%d)\n",
                (int)getpid());
        return ProbeVerdict::FAULTED;
    }
    pid_t p = fork();
    if (p < 0) return ProbeVerdict::SAFE;  // fork unavailable: direct dlopen
    if (p == 0) {
        // Probe child: dlopen then _exit — never unwind, never run parent
        // atexit handlers, never touch the parent's state.
        // F-C4-595 (W10): DEEPBIND in the probe too (mirrors the real
        // open — the probe must observe the same binding the real dlopen
        // will produce).
        // W15: phase rows — the child prints its own pid BEFORE the dlopen
        // so a forensics block from the child is attributable (the
        // S100-CRASH-FORENSICS row carries pid but the caller used to have
        // no marker distinguishing child-from-parent faults).
        fprintf(stderr,
                "[DLOPEN-PHASE] fork-probe child begin pid=%d path=%s\n",
                (int)getpid(), host_path);
        fflush(stderr);
        void* h = dlopen(host_path,
                         RTLD_NOW | RTLD_LOCAL | RTLD_DEEPBIND);
        fprintf(stderr, "[DLOPEN-PHASE] fork-probe child done pid=%d ok=%d\n",
                (int)getpid(), h ? 1 : 0);
        fflush(stderr);
        _exit(h ? 0 : 2);
    }
    int st = 0;
    // GP-APK-010 (issue #582): EINTR must be retried (the old loop broke on
    // the first error leaving st=0, which WIFEXITED/WEXITSTATUS decode as
    // exit 0 → the probe classified an UNKNOWN wait state as SAFE). A
    // genuine waitpid failure now forces verdict REFUSED, never SAFE.
    bool wait_failed = false;
    while (waitpid(p, &st, 0) < 0) {
        if (errno == EINTR) continue;
        wait_failed = true;  // genuine error: child unreaped
        break;
    }
    g_probe_status = st;
    {
        // W15: honest verdict row — settles WHICH process faulted and the
        // raw waitpid status, evidence instead of inference.
        const char* v = wait_failed ? "REFUSED"
                      : WIFSIGNALED(st) ? "FAULTED"
                      : (WIFEXITED(st) && WEXITSTATUS(st) == 0) ? "SAFE"
                                                                : "REFUSED";
        fprintf(stderr,
                "[DLOPEN-PHASE] fork-probe verdict=%s status=0x%x child=%d "
                "parent=%d\n",
                v, (unsigned)st, (int)p, (int)getpid());
        fflush(stderr);
    }
    if (!wait_failed && WIFSIGNALED(st)) return ProbeVerdict::FAULTED;
    if (!wait_failed && WIFEXITED(st) && WEXITSTATUS(st) == 0)
        return ProbeVerdict::SAFE;
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
// F-NEW-594 (W10): registry accesses from multiple threads — guarded.
static std::mutex g_obj_array_mu;
static NativeObjArray* as_obj_array(void* ref) {
    if (!ref) return nullptr;
    std::lock_guard<std::mutex> lk(g_obj_array_mu);
    for (NativeObjArray* b : obj_array_boxes())
        if (b == ref) return b;
    return nullptr;
}

// ── per-call arena (local-ref lifetime) ────────────────────────────────
// F-NEW-594 (W10): the arena is touched from every thread that mints
// boxes (NewStringUTF etc.) — mutex-guarded. Distinct mutex from the
// interner's (box_string is called while holding the interner lock).
std::mutex g_arena_mu;
std::vector<std::string*>& arena() {
    static std::vector<std::string*> a;
    return a;
}
std::string* box_string(const std::string& s) {
    std::string* b = new std::string(s);
    std::lock_guard<std::mutex> lk(g_arena_mu);
    arena().push_back(b);
    return b;
}
// F-NEW-596 (W12) — the lifetime contract was violated: box_string
// registered EVERY box in the per-call arena, and arena_clear() (the
// local-ref sweep at the end of every native dispatch) DELETED them —
// including the interner's ids and the class tokens the DEX side caches
// across calls. Live face (queens RunBundle): batch 1 of the
// refreshRateFPS reads answered fine; an arena sweep between calls
// freed the interned "SF:...|refreshRateFPS|F" box; the platform-message
// state reused the 32-byte chunk ({1, ptr, 39, 39, JSON bytes}); the
// next read copied a std::string whose length field was a heap pointer
// -> _Znwm(0x7ff...) -> std::bad_alloc. Evidence:
// evidence/s188_w12/w12_f596_2.console.log (same id=0x...b7580:
// box_len=38 healthy at :1140, box_len=0x7ff...d19d20 smashed at :1160).
// Contract: interned ids and class tokens are GLOBAL-scope handles our
// runtime retains across calls — they must be allocated OUTSIDE the
// per-call arena. Local refs (NewStringUTF etc.) stay arena-scoped
// (JNI-spec local-ref lifetime).
std::string* box_string_permanent(const std::string& s) {
    return new std::string(s);
}
void arena_clear() {
    std::lock_guard<std::mutex> lk(g_arena_mu);
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

// ── A-R1 (S211): the JNI pending-exception channel ─────────────────────
// Before this channel the four exception slots were unconditional no-ops
// (Occurred→null, Clear→{}, Check→0) and Throw/ThrowNew were log-only —
// the native tail of the UC-CM-001 silent-zero pattern: a library that
// signalled failure via ThrowNew returned its typed default and the DEX
// continued on a wrong value. JNI spec law: ThrowNew/Throw "record the
// pending exception"; ExceptionCheck "returns JNI_TRUE if there is a
// pending exception"; on native return with a pending exception the VM
// DISCARDS the return value and throws at the call site (AOSP
// art_jni.cc). One process-wide channel (the runtime's minimal bridge
// serves one JNIEnv, g_env); the engine consumes it once per native call
// via take_pending_jni_exception (declaration in dlopen_exec.h).
std::mutex g_exc_mu;
bool g_exc_pending = false;
std::string g_exc_class = "Ljava/lang/Exception;";
std::string g_exc_msg;

void record_pending_exc(std::string cls, std::string msg) {
    std::lock_guard<std::mutex> lk(g_exc_mu);
    // First raise wins within one native call (JNI: a second throw while
    // an exception is pending is ignored by the VM).
    if (!g_exc_pending) {
        g_exc_pending = true;
        g_exc_class = std::move(cls);
        g_exc_msg = std::move(msg);
    }
}

// F-NEW-596 interned class tokens (defined below; forward-declared so
// ExceptionOccurred can answer a non-null jthrowable marker).
static void* intern_class_token(const std::string& name);

void* jni_ExceptionOccurred(void*) {
    std::lock_guard<std::mutex> lk(g_exc_mu);
    if (!g_exc_pending) return nullptr;
    // Non-null jthrowable marker: the interned class token box. The call
    // boundary consumes the channel (take_pending_jni_exception), so the
    // marker only needs identity ≠ null for in-native polling code.
    return intern_class_token(g_exc_class);
}
void jni_ExceptionDescribe(void*) {}  // loud describe stays a no-op (stderr
                                      // already carries the ThrowNew row)
void jni_ExceptionClear(void*) {
    std::lock_guard<std::mutex> lk(g_exc_mu);
    g_exc_pending = false;
    g_exc_class = "Ljava/lang/Exception;";
    g_exc_msg.clear();
}
unsigned char jni_ExceptionCheck(void*) {
    std::lock_guard<std::mutex> lk(g_exc_mu);
    return g_exc_pending ? 1 : 0;
}
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
    // F-NEW-594 (W10): magic statics (C++11 thread-safe init) — the old
    // `if (!a_mu)` lazy-init raced when two threads hit the first call.
    static std::mutex a_mu_instance;
    static std::vector<std::vector<uint16_t>> arena_instance;
    std::mutex* a_mu = &a_mu_instance;
    std::vector<std::vector<uint16_t>>* arena = &arena_instance;
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
// F-NEW-596 forward decl (defined in the reflection-ID block below)
static void* jni_intern_id(const std::string& key);

// F-NEW-596 (W12) — class-token interner: the payload MUST stay the plain
// binary class name (the DEX side reads the box as the name — a "C:" key
// prefix leaked into payloads and broke the FlutterJNI reflection path,
// live face: GetFieldID(C:io/flutter/... instead of the plain name). The
// pool key carries the prefix; the payload does not. Permanent storage,
// pointer identity per name — the arena sweep can never free a token.
static void* intern_class_token(const std::string& name) {
    static std::mutex mu;
    static std::map<std::string, std::string*> pool;
    std::lock_guard<std::mutex> lk(mu);
    auto it = pool.find(name);
    if (it == pool.end()) {
        std::string* p = box_string_permanent(name);
        it = pool.emplace(name, p).first;
    }
    return it->second;
}
void* jni_FindClass(void*, const char* name) {
    // F-NEW-596: class tokens are INTERNED PERMANENT boxes (plain-name
    // payload) — the DEX side caches them across calls; the per-call
    // arena sweep must never free one.
    return intern_class_token(std::string(name ? name : ""));
}
void* jni_GetObjectClass(void*, void*) {
    // object identity only — class reflection stays an unsupported frontier
    return intern_class_token("Ljava/lang/Object;");
}
void* jni_NewGlobalRef(void*, void* r) { return r; }
void* jni_NewLocalRef(void*, void* r) { return r; }
void jni_DeleteGlobalRef(void*, void*) {}
void jni_DeleteLocalRef(void*, void*) {}
int jni_Throw(void*, void* throwable) {
    // A-R1 (S211): the pending-exception channel. The throwable jobject
    // rides as a tagged-oid handle the engine owns; the channel carries
    // the generic Throwable family here (ThrowNew is the classified arm —
    // it knows the FindClass token). The [MINIANDROID-JNI] row stays loud.
    record_pending_exc("Ljava/lang/Throwable;", "");
    fprintf(stderr, "[MINIANDROID-JNI] Throw recorded (pending)\n");
    return 0;
}
int jni_ThrowNew(void*, void* jclass, const char* msg) {
    // A-R1 (S211): log AND record. The jclass token is an interned box
    // whose payload is the plain binary name ("java/lang/IllegalStateException",
    // F-NEW-596) — normalized to the L-form the engine's deferred-raise
    // machinery dispatches on. An unresolvable token falls to the generic
    // Exception family (never a fabricated class name).
    std::string cls = "Ljava/lang/Exception;";
    if (jclass) {
        std::string name = *static_cast<std::string*>(jclass);
        if (!name.empty() && name.front() == 'L' && name.back() == ';')
            cls = name;  // already L-form
        else if (!name.empty() && name.front() != '[')
            cls = "L" + name + ";";
    }
    std::string m = msg ? msg : "";
    fprintf(stderr, "[MINIANDROID-JNI] ThrowNew: %s%s%s\n", cls.c_str(),
            m.empty() ? "" : ": ", m.c_str());
    record_pending_exc(std::move(cls), std::move(m));
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
    {
        std::lock_guard<std::mutex> lk(g_obj_array_mu);  // F-NEW-594
        obj_array_boxes().push_back(b);
    }
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
    // F-NEW-594 (W10): MUTEX-GUARDED INTERNING — the JNI env surface now
    // serves REAL threads (queens: platform + raster + io task runners —
    // the W9 thread pool), and libflutter interns field/method ids from
    // MORE THAN ONE thread concurrently. The unguarded static map raced:
    // two interning threads rehashed the pool simultaneously and a later
    // GetStaticFloatField copied a garbage std::string* — the
    // length_error("basic_string::_M_create") that landed in the guard at
    // libflutter modoff 0x532b1a (slot 152 call site, refreshRateFPS).
    // The interned payload is permanent (never freed) — the lock costs one
    // uncontended futex per lookup.
    static std::mutex id_mu;
    static std::map<std::string, std::string*> id_pool;
    std::lock_guard<std::mutex> lk(id_mu);
    auto it = id_pool.find(key);
    if (it == id_pool.end()) {
        // F-NEW-596: the interned payload is permanent — NOT an arena
        // box (the arena sweep must never free an id the pool hands out).
        std::string* p = box_string_permanent(key);
        it = id_pool.emplace(key, p).first;
    }
    return it->second;
}
// F-NEW-596 forward decls (definitions below the F-NEW-590 block)
static bool f590_box_len_of(void* box, size_t* len_out);
static std::string f590_field_name_of_safe(void* fieldID, const char* who);
static std::string jni_class_name_of(void* jcls) {
    if (!jcls) return std::string();
    // box_string jclass: the payload IS the binary class name.
    // F-NEW-596: the same corrupt-box boundary (a smashed jclass box
    // must not _Znwm a pointer-length string).
    size_t len = 0;
    if (!f590_box_len_of(jcls, &len) || len > 512) {
        static std::mutex cmu; static uint64_t cn = 0;
        std::lock_guard<std::mutex> lk(cmu);
        if (cn++ < 8)
            fprintf(stderr,
                    "[F-NEW-596] corrupt jclass box: ptr=%p head_len=%zu "
                    "(0x%zx) — answering empty\n", jcls, len, len);
        return std::string();
    }
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
    void* id = jni_intern_id("SF:" + jni_class_name_of(jcls) + "|" + name +
                             "|" + sig);
    // F-NEW-596 attribution: what the slot-152 reader receives must be
    // THIS pointer — if it differs, the arg lane between slot 144 and
    // slot 152 is broken, not the box.
    static thread_local uint64_t f596_sf = 0;
    if (f596_sf < 12) { ++f596_sf;
        size_t blen = 0;
        f590_box_len_of(id, &blen);
        fprintf(stderr, "[F-NEW-596] GetStaticFieldID -> id=%p box_len=%zu\n",
                id, blen); }
    return id;
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

// ─────────────────────────────────────────────────────────────────────
// F-NEW-590 (W10) — the static-field read family (spec slots 146/150/151/
// 152/153) + the direct-Buffer family (229/230/231).
// ROOT (live, queens W9 exit census: env152=8, env230=4 — evidence/
// s188_w9/w9_gl2.console.log [MINIANDROID-JNI] UNSUPPORTED slot census):
//   • GetStaticFloatField: libflutter's registered UpdateDisplayMetrics
//     native resolved refreshRateFPS / displayWidth / displayHeight /
//     displayDensity ("F") via GetStaticFieldID — whose jclass our
//     GetObjectClass identity law degraded to Ljava/lang/Object; — then
//     read them ×8 (2 rounds of 4). The JNI TU cannot see the DEX static
//     store, so the ENGINE answers through the F-NEW-590 hooks (set at
//     engine construction): name-keyed DEX static first (the app's own
//     values when its FlutterView code ran), the REAL display
//     configuration second. Spec law (jni.h): a resolvable field read
//     never answers via the loud UNSUPPORTED stub.
//   • GetDirectBufferAddress: DartMessenger#send builds the platform
//     message as a DEX heap ByteBuffer (S108 ROOT-022 shape: lazy
//     __bb_b<i>__ byte fields) and libflutter's registered
//     nativeDispatchPlatformMessage reads its address — without it the
//     message bytes never reach the engine side (the calls at
//     w9_gl2.console.log:1065/1143/1217 landed right after each
//     dispatchPlatformMessage). The engine snapshots the bytes into REAL
//     malloc memory; the box registry serves the address/capacity
//     getters. NewDirectByteBuffer covers the reverse direction
//     (native-built buffers).
// Tagged-oid law (call_native marshal): DEX objects ride as
// 0x500000000|oid — GetDirectBufferAddress decodes that exact pattern
// and asks the engine hook; anything else is a box this layer minted
// itself (NewDirectByteBuffer) or an honest NULL (non-direct buffer).
// ─────────────────────────────────────────────────────────────────────
static nativeexec::EngineHooks g_f590_hooks;

struct DirectBufferBox {
    void* addr;
    size_t cap;
};
static std::vector<DirectBufferBox*>& direct_buffer_boxes() {
    static std::vector<DirectBufferBox*> v;
    return v;
}
// S188-W18 F-NEW-609: persistent per-oid direct-buffer backing registry —
// GetDirectBufferAddress returns THE SAME malloc for the buffer's lifetime
// (JNI direct buffers are shared memory; per-call snapshots erased native
// writes — the FreeType face face).
struct PersistentDirectBuffer {
    void* addr;
    size_t cap;
};
static std::map<uint32_t, PersistentDirectBuffer>& persistent_direct_buffers() {
    static std::map<uint32_t, PersistentDirectBuffer> m;
    return m;
}
// F-NEW-594 (W10): multi-thread registry law — same as the object-array
// registry (the direct-buffer family is called from the platform AND
// raster threads once the real task runners run).
static std::mutex g_direct_buffer_mu;
static DirectBufferBox* as_direct_buffer_box(void* p) {
    if (!p) return nullptr;
    std::lock_guard<std::mutex> lk(g_direct_buffer_mu);
    for (DirectBufferBox* b : direct_buffer_boxes())
        if (b == p) return b;
    return nullptr;
}

// interned field ids carry "SF:<class>|<name>|<sig>" (F-C4-581) — the
// name is the middle segment.
static std::string f590_field_name_of(void* fieldID) {
    if (!fieldID) return std::string();
    std::string s = *static_cast<std::string*>(fieldID);
    size_t a = s.find('|');
    if (a == std::string::npos) return std::string();
    size_t b = s.find('|', a + 1);
    if (b == std::string::npos) return std::string();
    return s.substr(a + 1, b - a - 1);
}

// F-NEW-596 (W12) — corrupt-fieldID boundary: the interned id box is a
// permanent std::string*, but a heap smash elsewhere (queens RunBundle
// face: the second refreshRateFPS batch read len=0x7f... (a pointer
// value) out of the box and _Znwm'd 0x7f... bytes -> std::bad_alloc)
// can poison ANY box. A corrupt box must not take the run down: read
// the {ptr,len} head safely, verify len against a sane bound, hexdump
// the smashed object for attribution, and answer empty (the callers
// fall back honestly). The huge-allocation face is UNREACHABLE from
// this path afterwards.
static bool f590_box_len_of(void* fieldID, size_t* len_out) {
    if (!fieldID) return false;
    // std::__cxx11::basic_string head: {char* _M_p; size_type _M_len; ...}
    unsigned long raw[2];
    memcpy(raw, fieldID, sizeof raw);
    *len_out = raw[1];
    return true;
}

static std::string f590_field_name_of_safe(void* fieldID, const char* who) {
    size_t len = 0;
    if (!f590_box_len_of(fieldID, &len) || len > 256) {
        static std::mutex diag_mu;
        static uint64_t diag_n = 0;
        {
            std::lock_guard<std::mutex> lk(diag_mu);
            if (diag_n++ < 8) {
                fprintf(stderr,
                        "[F-NEW-596] corrupt id box (%s): ptr=%p head_len=%zu "
                        "(0x%zx) — dumping 48 bytes:\n",
                        who, fieldID, len, len);
                unsigned char* p = (unsigned char*)fieldID;
                for (int row = 0; row < 3; ++row) {
                    fprintf(stderr, "[F-NEW-596]   %04x:", row * 16);
                    for (int k = 0; k < 16; ++k)
                        fprintf(stderr, " %02x", p[row * 16 + k]);
                    fprintf(stderr, "\n");
                }
            }
        }
        return std::string();
    }
    return f590_field_name_of(fieldID);
}

static float jni_GetStaticFloatField(void*, void*, void* fieldID) {
    std::string name = f590_field_name_of_safe(fieldID, "GetStaticFloatField");
    float out = 0.0f;
    if (!name.empty() && g_f590_hooks.static_float) {
        // F-NEW-594: the hook walks the engine's static storage — a
        // corrupt/unreadable storage state must not take the run down
        // (the boundary answers the display-config fallback instead, and
        // the exception text is recorded for the next frontier). Live
        // face: queens' second refreshRateFPS batch inside RunBundle
        // bad_alloc'd while the FIRST batch read the same keys fine —
        // evidence/s188_w10/probe_throw2.console.log.
        try {
            if (g_f590_hooks.static_float("Ljava/lang/Object;", name.c_str(),
                                          &out))
                return out;
        } catch (const std::exception& e) {
            static thread_local uint64_t ne = 0;
            if (ne++ < 8)
                fprintf(stderr,
                        "[F-NEW-590] GetStaticFloatField(%s) hook threw %s — "
                        "answering the display-config fallback\n",
                        name.c_str(), e.what());
        } catch (...) {
        }
    }
    // display-config fallback (the REAL software-target constants — the
    // same law the engine serves every other display consumer).
    if (name == "refreshRateFPS") return 60.0f;
    if (name == "displayWidth") return 1080.0f;
    if (name == "displayHeight") return 1920.0f;
    if (name == "displayDensity") return 2.625f;
    static thread_local uint64_t n = 0;
    if (n++ < 8)
        fprintf(stderr,
                "[F-NEW-590] GetStaticFloatField(%s) unresolvable — answered "
                "0.0f (the engine carries no such static)\n",
                name.c_str());
    return 0.0f;
}
static int32_t jni_GetStaticIntField(void*, void*, void* fieldID) {
    std::string name = f590_field_name_of_safe(fieldID, "GetStaticIntField");
    int32_t out = 0;
    if (!name.empty() && g_f590_hooks.static_int &&
        g_f590_hooks.static_int("Ljava/lang/Object;", name.c_str(), &out))
        return out;
    return 0;
}
static int64_t jni_GetStaticLongField(void*, void*, void* fieldID) {
    std::string name = f590_field_name_of_safe(fieldID, "GetStaticLongField");
    int64_t out = 0;
    if (!name.empty() && g_f590_hooks.static_long &&
        g_f590_hooks.static_long("Ljava/lang/Object;", name.c_str(), &out))
        return out;
    return 0;
}
static uint8_t jni_GetStaticBooleanField(void*, void*, void* fieldID) {
    std::string name = f590_field_name_of_safe(fieldID, "GetStaticBooleanField");
    uint8_t out = 0;
    if (!name.empty() && g_f590_hooks.static_bool &&
        g_f590_hooks.static_bool("Ljava/lang/Object;", name.c_str(), &out))
        return out;
    return 0;
}
static double jni_GetStaticDoubleField(void*, void*, void* fieldID) {
    std::string name = f590_field_name_of_safe(fieldID, "GetStaticDoubleField");
    double out = 0.0;
    if (!name.empty() && g_f590_hooks.static_double &&
        g_f590_hooks.static_double("Ljava/lang/Object;", name.c_str(), &out))
        return out;
    return 0.0;
}

// Direct-Buffer family — the {addr,cap} box registry. The engine-side
// snapshot hook fills the box on first demand; NewDirectByteBuffer boxes
// wrap native memory the library handed us (identity stays stable).
void* jni_NewDirectByteBuffer(void*, void* address, int64_t capacity) {
    // ── S199 W19a F-NEW-615 — ZERO-CAPACITY DIRECT BUFFER VALIDITY law ──
    // AOSP/ART (OpenJDK Bits.reserveMemory / DirectByteBuffer(int, long)):
    // a direct ByteBuffer of capacity 0 is WELL-FORMED (non-null, pos=lim=
    // cap=0) as long as the address is non-null. Live face (tictactoe,
    // S199): the first glyph generated from Roboto-Medium is SPACE (0x20)
    // — an EMPTY outline — FT_Glyph_To_Bitmap succeeds with rows=width=
    // pitch=0; gdx2d_new(0,0) (real libgdx.so, disasm 0x11720: NO w/h
    // validation, pixels=malloc(0) non-NULL) succeeds; newPixmap calls
    // NewDirectByteBuffer(pixels, w*h*bpp = 0) and the old
    // `capacity <= 0 → nullptr` guard answered NULL → Gdx2DPixelPtr null
    // → Gdx2DPixmap.<init> "Error loading pixmap." → taskFailed →
    // GdxRuntimeException at AndroidLauncher.onCreate APP BOUNDARY. Real
    // Android packs the empty space glyph and continues. The same family
    // covers every 0-dimension pixmap/buffer any native mints.
    if (!address || capacity < 0) return nullptr;
    DirectBufferBox* b = new DirectBufferBox{address, (size_t)capacity};
    {
        std::lock_guard<std::mutex> lk(g_direct_buffer_mu);  // F-NEW-594
        direct_buffer_boxes().push_back(b);
    }
    return b;
}
void* jni_GetDirectBufferAddress(void*, void* buf) {
    if (!buf) return nullptr;
    if (DirectBufferBox* b = as_direct_buffer_box(buf)) return b->addr;
    uintptr_t v = (uintptr_t)buf;
    if ((v >> 32) == 5) {  // tagged-oid law: 0x500000000|oid
        uint32_t oid = (uint32_t)(v & 0xffffffffull);
        // ── S188-W18 F-NEW-609 — PERSISTENT DIRECT-BUFFER BACKING law ──
        // The pre-609 hook snapshotted the DEX mirror into a FRESH malloc
        // on EVERY GetDirectBufferAddress call. JNI direct buffers are
        // SHARED memory: a native that WRITES through the address (libgdx
        // BufferUtils.copyJni streaming the 126168B RobotoCondensed TTF
        // into the buffer) expects the NEXT native reader (FreeType
        // newMemoryFace) to see those bytes. Per-call snapshots erased
        // them — FT read zeros → newFace=0 → GdxRuntimeException
        // "Couldn't create face for font" → MainActivity.onCreate APP
        // BOUNDARY. AOSP/ART law: GetDirectBufferAddress returns THE
        // buffer's address for its lifetime. Law here: the FIRST Get
        // allocates the backing malloc and copies the CURRENT DEX mirror
        // in; EVERY later Get returns the SAME pointer (native writes
        // persist; DEX-side bridge writes after the first Get are not
        // re-snapshotted — the documented boundary, the p9/font and
        // pixmap consumers are native-side only).
        {
            std::lock_guard<std::mutex> lk(g_direct_buffer_mu);  // F-NEW-594
            auto& reg = persistent_direct_buffers();
            auto it = reg.find(oid);
            if (it != reg.end()) {
                static thread_local uint64_t hits = 0;
                if (hits++ < 8)
                    fprintf(stderr,
                            "[F-NEW-609] GetDirectBufferAddress(oid=%u) "
                            "persistent hit addr=%p cap=%zu\n",
                            oid, it->second.addr, it->second.cap);
                return it->second.addr;
            }
        }
        void* addr = nullptr;
        size_t cap = 0;
        f590_served_real_identity = false;  // F-NEW-622: per-call reset
        if (g_f590_hooks.direct_buffer &&
            g_f590_hooks.direct_buffer(oid, &addr, &cap)) {
            // ── S200-T03 F-NEW-622 — ONE-IDENTITY DIRECT LAW ────────────
            // When the hook answered the buffer's REAL memory (__bb_addr__
            // native mint / __bb_direct__ engine mint / F-NEW-619 parent
            // chase), answer THAT pointer. The 609 mint-copy captured the
            // buffer at FIRST-GET time and every later reader parsed the
            // copy — for the tictactoe font buffer the first Get happened
            // mid-stream (chunk 1 of 42): the copy held a real head and an
            // uninitialized tail, FreeType parsed a truncated font (cmap
            // garbage → FT_Get_Char_Index=1 for every char → empty
            // outlines → 0×0 bitmaps → white font pages). Stability law
            // (the 609 promise) holds WITHOUT a copy: the real malloc
            // lives for the buffer's lifetime, and now DEX-side bridge
            // writes (copyJni real-mem arm) and native writes share the
            // one address — the old documented boundary closes.
            // The 609 persistent-copy below remains for the DEX-mirror
            // arm only (its snapshot is a fresh malloc per call — only
            // the registry makes that address stable).
            if (f590_served_real_identity) {
                static thread_local uint64_t real_n = 0;
                if (real_n++ < 100)
                    fprintf(stderr,
                            "[F-NEW-622] GetDirectBufferAddress(oid=%u) "
                            "served REAL identity addr=%p cap=%zu "
                            "(no copy, one identity)\n",
                            oid, addr, cap);
                // S200-T03 diag (env-gated): the served memory's content —
                // byte-sum + head/tail vs the real font (sum=13464079,
                // tail=001d0000 for Roboto-Medium) answers whether the
                // engine-side copyJni arm actually filled the real memory.
                if (cap > 0 && std::getenv("MINIANDROID_T03_BUF_DIAG")) {
                    unsigned char* p622 = (unsigned char*)addr;
                    unsigned long long s622 = 0;
                    for (size_t i = 0; i < cap; ++i) s622 += p622[i];
                    fprintf(stderr,
                            "[T03-BUF] real oid=%u cap=%zu sum=%llu head="
                            "%02x%02x%02x%02x %02x%02x%02x%02x tail="
                            "%02x%02x%02x%02x\n",
                            oid, cap, s622, p622[0], p622[1], p622[2],
                            p622[3], p622[4], p622[5], p622[6], p622[7],
                            p622[cap - 4], p622[cap - 3], p622[cap - 2],
                            p622[cap - 1]);
                }
                return addr;
            }
            void* backing = std::malloc(cap ? cap : 1);
            if (!backing) return nullptr;
            if (addr && cap) memcpy(backing, addr, cap);
            {
                // GP-JNI-005 (issue #582): two threads could pass the
                // registry check above simultaneously, each mint its OWN
                // backing, and the two losers/winners returned DIFFERENT
                // pointers for the same buffer oid (last insert wins the
                // registry, the first returner's pointer is orphaned).
                // Re-check under the insert lock: the first insert wins,
                // every other caller frees its own backing and serves the
                // registry pointer — ONE identity per oid.
                std::lock_guard<std::mutex> lk(g_direct_buffer_mu);
                auto& reg5 = persistent_direct_buffers();
                auto it5 = reg5.find(oid);
                if (it5 != reg5.end()) {
                    std::free(backing);  // loser's copy never published
                    static thread_local uint64_t lost5 = 0;
                    if (lost5++ < 8)
                        fprintf(stderr,
                                "[GP-JNI-005] concurrent first-Get on oid=%u "
                                "resolved to the registry pointer %p\n",
                                oid, it5->second.addr);
                    return it5->second.addr;
                }
                DirectBufferBox* b = new DirectBufferBox{backing, cap};
                direct_buffer_boxes().push_back(b);
                reg5[oid] = {backing, cap};
            }
            static thread_local uint64_t n = 0;
            if (n++ < 8)
                fprintf(stderr,
                        "[F-NEW-609] GetDirectBufferAddress(oid=%u) "
                        "persistent backing minted cap=%zu\n",
                        oid, cap);
            // S200-T03 diag (env-gated, zero behavior): WHICH bytes did the
            // persistent mint capture? First-16 hex + byte-sum answer the
            // font-buffer identity split (copyJni real-mem write vs the
            // 609 snapshot taken at first-Get time).
            if (cap > 0 && std::getenv("MINIANDROID_T03_BUF_DIAG")) {
                unsigned char* p609 = (unsigned char*)backing;
                unsigned long long s609 = 0;
                for (size_t i = 0; i < cap; ++i) s609 += p609[i];
                fprintf(stderr,
                        "[T03-BUF] mint oid=%u cap=%zu sum=%llu head=%02x"
                        "%02x%02x%02x %02x%02x%02x%02x tail=%02x%02x%02x%02x\n",
                        oid, cap, s609, p609[0], p609[1], p609[2], p609[3],
                        p609[4], p609[5], p609[6], p609[7], p609[cap - 4],
                        p609[cap - 3], p609[cap - 2], p609[cap - 1]);
            }
            return backing;
        }
    }
    return nullptr;  // JNI spec: non-direct buffer answers NULL
}
int64_t jni_GetDirectBufferCapacity(void*, void* buf) {
    if (!buf) return 0;
    if (DirectBufferBox* b = as_direct_buffer_box(buf)) return (int64_t)b->cap;
    uintptr_t v = (uintptr_t)buf;
    if ((v >> 32) == 5) {
        uint32_t oid = (uint32_t)(v & 0xffffffffull);
        void* addr = nullptr;
        size_t cap = 0;
        if (g_f590_hooks.direct_buffer &&
            g_f590_hooks.direct_buffer(oid, &addr, &cap))
            return (int64_t)cap;
    }
    return 0;
}

// ─────────────────────────────────────────────────────────────────────
// S188-W18 F-NEW-605 — the primitive-array critical family (spec slots
// 222 GetPrimitiveArrayCritical / 223 ReleasePrimitiveArrayCritical).
// LIVE DEMAND (evidence/s188_w18/W18_GDX2DPIXMAP_CONTRACT.json, objdump
// call-face of the APK's own libgdx.so + p9_w17b console faults):
//   • Matrix4.mul/inv/det/mulVec/prj/rot ([F variants): Get on the
//     float[] args, math on the bytes, Release mode 0 WRITES RESULTS
//     back into the arrays (void/boolean out-by-array semantics).
//   • Gdx2DPixmap.load: Get(encodedData byte[]) -> gdx2d_load ->
//     Release(encodedData) -> NewDirectByteBuffer(pixels) -> Get(pdata
//     long[]) -> pdata[0..3] = {pixmap ptr, width, height, format} ->
//     Release(pdata) -> return the ByteBuffer.
//   • Gdx2DPixmap.newPixmap: Get(pdata) + NewDirectByteBuffer.
// LAW (JNI spec): GetPrimitiveArrayCritical may answer a COPY
// (is_copy=JNI_TRUE); between Get and Release the native must not call
// other JNI functions — libgdx honors this. Release mode: 0 → write
// back + free, JNI_COMMIT (1) → write back, JNI_ABORT (2) → free only.
// The array arrives as the tagged-oid 0x500000000|oid (call_native
// marshal); the DEX heap cannot offer contiguous storage, so the
// engine-side primitive_array/primitive_array_write hooks snapshot and
// commit (the memcmp skip avoids pointless writebacks for read-only
// criticals — the load encodedData face).
// ─────────────────────────────────────────────────────────────────────
struct CriticalArrayBox {
    uint32_t oid;
    void* copy;
    size_t len;
};
static std::vector<CriticalArrayBox*>& critical_array_boxes() {
    static std::vector<CriticalArrayBox*> v;
    return v;
}
static std::mutex g_critical_mu;
static CriticalArrayBox* as_critical_box(void* p) {
    if (!p) return nullptr;
    std::lock_guard<std::mutex> lk(g_critical_mu);
    for (CriticalArrayBox* b : critical_array_boxes())
        if (b->copy == p) return b;
    return nullptr;
}
static void* jni_GetPrimitiveArrayCritical(void*, void* arr,
                                           unsigned char* is_copy) {
    if (!arr) return nullptr;  // JNI spec: null array → NULL
    uintptr_t v = (uintptr_t)arr;
    if ((v >> 32) != 5) return nullptr;  // not a tagged DEX heap handle
    uint32_t oid = (uint32_t)(v & 0xffffffffull);
    void* addr = nullptr;
    size_t len = 0;
    if (!g_f590_hooks.primitive_array ||
        !g_f590_hooks.primitive_array(oid, &addr, &len) || !addr) {
        static thread_local uint64_t n = 0;
        if (n++ < 8)
            fprintf(stderr,
                    "[F-NEW-605] GetPrimitiveArrayCritical(oid=%u) not a "
                    "live DEX primitive array — answering NULL (spec)\n",
                    oid);
        return nullptr;
    }
    if (is_copy) *is_copy = 1;  // copy semantics — spec-legal
    CriticalArrayBox* b = new CriticalArrayBox{oid, addr, len};
    {
        std::lock_guard<std::mutex> lk(g_critical_mu);
        critical_array_boxes().push_back(b);
    }
    static thread_local uint64_t n = 0;
    if (n++ < 12)
        fprintf(stderr,
                "[F-NEW-605] GetPrimitiveArrayCritical(oid=%u) snapshot "
                "len=%zu\n", oid, len);
    return addr;
}
static void jni_ReleasePrimitiveArrayCritical(void*, void* arr, void* cdata,
                                              int32_t mode) {
    (void)arr;
    CriticalArrayBox* b = as_critical_box(cdata);
    if (!b) return;  // mismatched release — nothing to commit
    // GP-JNI-001 (issue #582): JNI spec — mode JNI_COMMIT (1) commits the
    // changes but KEEPS the array available for continued native access;
    // the final release (mode 0 / JNI_ABORT) frees it. The old code erased
    // the box and freed the copy for EVERY non-ABORT mode, so a legal
    // Get→COMMIT→use→Release sequence used freed memory. COMMIT now
    // writes back and returns with the box/copy alive.
    if (mode == 1 /* JNI_COMMIT */) {
        if (g_f590_hooks.primitive_array_write)
            g_f590_hooks.primitive_array_write(b->oid, b->copy, b->len);
        return;  // box + copy stay registered for the final release
    }
    if (mode != 2 /* JNI_ABORT */ && g_f590_hooks.primitive_array_write) {
        // The write hook snapshots the CURRENT element content and skips
        // untouched elements (memcmp per element) — the load encodedData
        // face releases unmodified byte[] at near-zero cost, the Matrix4
        // face commits the modified float[] elements.
        g_f590_hooks.primitive_array_write(b->oid, b->copy, b->len);
    }
    {
        std::lock_guard<std::mutex> lk(g_critical_mu);
        auto& v = critical_array_boxes();
        for (size_t i = 0; i < v.size(); ++i)
            if (v[i] == b) { v.erase(v.begin() + (long)i); break; }
    }
    std::free(b->copy);
    delete b;
}

}  // anonymous namespace — JNI internals stay TU-local

// F-NEW-590: engine hook setter — the ONE external symbol of this block
// (dalvik_engine.cpp installs the DEX-storage-backed hooks at ctor time).
void set_engine_hooks(const nativeexec::EngineHooks& hooks) {
    g_f590_hooks = hooks;
}

// F-NEW-608 (S198, C3) DIRECT-BUFFER LOOKUP — the GLES20 bridge's marshal
// fallback asks for the {addr,cap} of an engine-minted direct ByteBuffer
// by oid. INTEGRATION (S195 audit): implemented over THIS line's W18
// engine hook (f590_direct_buffer_snapshot — the persistent direct-buffer
// backing, F-NEW-609); C3's S196 registry and this line's hook registry
// are the same contract — one lookup surface, both mint paths feed it.
bool lookup_direct_buffer(uint32_t oid, void** addr, int32_t* cap) {
    void* a = nullptr;
    size_t c = 0;
    if (!g_f590_hooks.direct_buffer) return false;
    if (!g_f590_hooks.direct_buffer(oid, &a, &c)) return false;
    if (!a) return false;
    if (addr) *addr = a;
    if (cap) *cap = (int32_t)c;
    return true;
}

namespace {

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
    // F-NEW-590 (W10): the static-field READ family — W9 census env152=8
    // (queens UpdateDisplayMetrics; the typed siblings complete the
    // family — one contract, no half-families).
    g_jni_table[146] = (void*)&jni_GetStaticBooleanField;  // 146 GetStaticBooleanField
    g_jni_table[150] = (void*)&jni_GetStaticIntField;      // 150 GetStaticIntField
    g_jni_table[151] = (void*)&jni_GetStaticLongField;     // 151 GetStaticLongField
    g_jni_table[152] = (void*)&jni_GetStaticFloatField;    // 152 GetStaticFloatField (W9 census: queens ×8)
    g_jni_table[153] = (void*)&jni_GetStaticDoubleField;   // 153 GetStaticDoubleField
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
    // F-NEW-590 (W10): the direct-Buffer family — W9 census env230=4
    // (DartMessenger platform messages into libflutter's native
    // dispatch); 229/231 complete the family.
// ── S188-W18 F-NEW-605: the primitive-array critical family — the W16
// census slot (p9 ×N Matrix4 + Gdx2DPixmap.load/newPixmap).
    g_jni_table[222] = (void*)&jni_GetPrimitiveArrayCritical;   // 222 GetPrimitiveArrayCritical
    g_jni_table[223] = (void*)&jni_ReleasePrimitiveArrayCritical; // 223 ReleasePrimitiveArrayCritical
    g_jni_table[229] = (void*)&jni_NewDirectByteBuffer;     // 229 NewDirectByteBuffer
    g_jni_table[230] = (void*)&jni_GetDirectBufferAddress;  // 230 GetDirectBufferAddress (W9 census: queens ×4)
    g_jni_table[231] = (void*)&jni_GetDirectBufferCapacity; // 231 GetDirectBufferCapacity
    FillUnsupported<kVmSlots - 1, true>::fill(g_vm_table);
    // F-NEW-594 diag: the slot-152 identity — the throw-probe chain said
    // libflutter's slot-152 call landed on exe code at 0x676ff7, not on
    // jni_GetStaticFloatField (0x732fe0); verify the wiring is what we
    // think it is (bounded, diag-gated).
    if (std::getenv("MINIANDROID_W10_JNI_TRACE"))
        fprintf(stderr,
                "[F-NEW-594] slot152=&jni_GetStaticFloatField=%p "
                "table=%p jni_GetStaticFieldID=%p\n",
                (void*)&jni_GetStaticFloatField, (void*)g_jni_table[152],
                (void*)&jni_GetStaticFieldID);
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
    // S188-W18 F-NEW-611 — JNI NAME MANGLING law (JNI spec
    // ResolveNativeMethod short/long names): every character that is NOT
    // an ASCII digit/letter/underscore carries a Unicode escape _0xxxx;
    // the explicit / ; [ mappings keep their table entries. The pre-611
    // code passed every printable byte through — '$' (U+0024) survived
    // raw, so dlsym searched "Java_...FreeType$Library_newMemoryFace"
    // while libgdx-freetype.so exports
    // "Java_...FreeType_00024Library_newMemoryFace" (jnigen emits the
    // ART-faithful _00024). Miss → the STUBBED tail answered the typed
    // long default 0 → "Couldn't load font, FreeType error code: 0" →
    // MainActivity.onCreate APP BOUNDARY. Inner-class natives ($-classes)
    // are the whole FreeType/Bitmap/Face/Glyph family — one rule, all of
    // them land. Previously-hit symbols (alnum/_//) are unchanged.
    for (unsigned char c : in) {
        if (c == '_') out += "_1";
        else if (c == ';') out += "_2";
        else if (c == '[') out += "_3";
        else if (c == '/' || c == '.') out += '_';
        else if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                 (c >= '0' && c <= '9')) out += (char)c;
        else {
            snprintf(buf, sizeof buf, "_0%04x", (unsigned)c);
            out += buf;
        }
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
    // W15: phase row BEFORE the pre-pass so a fault inside prepare's own
    // (unguarded) dlopens is attributable by log position alone.
    fprintf(stderr, "[DLOPEN-PHASE] deps-prep begin lib=%s path=%s pid=%d\n",
            libname.c_str(), host_path.c_str(), (int)getpid());
    {
        const auto slash = host_path.rfind('/');
        const std::string lib_dir =
            slash == std::string::npos ? std::string() : host_path.substr(0, slash);
        for (const auto& row : jni::prepare_dependencies(host_path, lib_dir))
            (void)row;   // trace rows already landed inside prepare
    }
    fprintf(stderr, "[DLOPEN-PHASE] deps-prep done pid=%d\n", (int)getpid());
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
    fprintf(stderr,
            "[DLOPEN-PHASE] parent dlopen begin (guarded) pid=%d\n",
            (int)getpid());
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

// ── A-R1 (S211) — the engine-side channel API (dlopen_exec.h) ──────────
bool has_pending_jni_exception() {
    std::lock_guard<std::mutex> lk(g_exc_mu);
    return g_exc_pending;
}
bool take_pending_jni_exception(std::string& out_class,
                                std::string& out_msg) {
    std::lock_guard<std::mutex> lk(g_exc_mu);
    if (!g_exc_pending) return false;
    g_exc_pending = false;
    out_class = std::move(g_exc_class);
    out_msg = std::move(g_exc_msg);
    g_exc_class = "Ljava/lang/Exception;";
    g_exc_msg.clear();
    return true;
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
    // F-NEW-592 (W10): tagged-handle law — a tagged heap handle is ONLY
    // minted for a LIVE oid (>=1). object_id==0 means a JNI null (the
    // engine's null references arrive typed OBJECT_REF with id 0); the
    // anonymous 0x500000000 constant was previously pushed for them and a
    // real native deref'd it as a jstring → SIGSEGV at 0x500000000 inside
    // the env-table string face (queens RunBundle fault, W10 trace).
    auto push_object = [&](uint32_t oid) {
        push_int(oid != 0 ? (0x500000000ull | (oid & 0xffffffffull)) : 0ull);
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
        // GP-JNI-002 (issue #582): `*(uint64_t*)&d` violated strict
        // aliasing (UB; -Wstrict-aliasing diagnostic). memcpy the bit
        // pattern — same instruction on -O2, defined semantics.
        else {
            uint64_t bits_d = 0;
            std::memcpy(&bits_d, &d, sizeof(bits_d));
            stack_args.push_back(bits_d);
        }
    };

    // slot 0: JNIEnv*
    push_int((uint64_t)(uintptr_t)&g_env);
    // slot 1: receiver — jclass token for static, jobject identity otherwise.
    // F-NEW-592: the receiver identity carries the REAL tagged oid when the
    // engine passed one (resolvable by the hooks); the anon constant is the
    // fallback for anonymous receivers.
    if (static_call)
        push_int((uint64_t)(uintptr_t)box_string("jclass-token"));
    else if (!args.empty() && args[0].kind == JArg::Kind::OBJECT &&
             args[0].object_id != 0)
        push_object(args[0].object_id);
    else
        push_int(0x500000000ull);  // anonymous receiver identity

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
                else push_object(a.object_id);  // F-NEW-592: oid==0 → JNI null
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
        // F-NEW-593: the guard reason distinguishes the fault class — a
        // C++ exception landing in the catch (thunk .eh_frame) vs a raw
        // signal landing in the longjmp (FIX-TTT).
        if (!g_guard_last_reason.empty())
            error = "native call faulted (" + g_guard_last_reason +
                    ") — guarded, runtime survived (FIX-TTT)";
        else
            error = "native call faulted (SIGSEGV/SIGBUS inside the "
                    "library) — guarded, runtime survived (FIX-TTT)";
        fprintf(stderr, "[S2-NATIVE] guarded call fault: %s sig=%s\n",
                error.c_str(), sig.c_str());
        g_guard_last_reason.clear();
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
            } else if (DirectBufferBox* db = as_direct_buffer_box(ref)) {
                // S188-W18 F-NEW-605: a native-minted DIRECT ByteBuffer
                // (NewDirectByteBuffer — Gdx2DPixmap.load's pixel surface).
                // Surface the {addr,cap} honestly; the engine mints a DEX
                // ByteBuffer whose __bb_addr__ carries the REAL pointer.
                // (The pre-W18 tail deref'd this box as a std::string* —
                // a fabricated object read that crashed on the first
                // successful pixmap load.)
                out.kind = JOutcome::Kind::BYTE_BUFFER;
                out.bb_addr = (uint64_t)(uintptr_t)db->addr;
                out.bb_cap = (uint64_t)db->cap;
                fprintf(stderr,
                        "[F-NEW-605] native direct-ByteBuffer return: "
                        "addr=%p cap=%zu\n", db->addr, db->cap);
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
