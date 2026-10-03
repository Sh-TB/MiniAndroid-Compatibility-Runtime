/*
 * dlopen_exec.h — S-2 native execution layer (issue #371 closeout).
 *
 * AOSP law (art/runtime/java_vm_ext.cc + native_loader_libc.cc):
 *   System.loadLibrary → Runtime.loadLibrary0 → dlopen(extracted path)
 *   → JNI_OnLoad(vm, NULL) version handshake → class linker marks the
 *   library live → native methods resolve via dlsym(JNI mangling) or
 *   RegisterNatives → invocation with JNIEnv* + receiver + args.
 *
 * This layer makes the runtime's extracted-native-lib tree genuinely
 * executable for the ABI the host can run (x86_64). Arm-only APKs get the
 * REAL dlopen refusal string (wrong ELF class / ABI mismatch) — the same
 * honest answer a real x86_64 Android device without binary translation
 * gives — never a fabricated success.
 *
 * Generic by construction: no package/app knowledge anywhere; every call
 * is keyed by (class descriptor, method name, DEX signature) exactly like
 * JNI symbol resolution.
 */
#ifndef MINIANDROID_DLOPEN_EXEC_H
#define MINIANDROID_DLOPEN_EXEC_H

#include <string>
#include <vector>
#include <cstdint>

namespace miniandroid {
namespace nativeexec {

// One loaded native library (AOSP LibraryEntry: path + handle).
struct LoadedLib {
    std::string name;        // short name ("probe" for libprobe.so)
    std::string host_path;   // extracted file path handed to dlopen
    std::string logical_path;// Android-visible path (nativeLibraryDir/…)
    void* handle = nullptr;  // dlopen handle
    bool jni_on_load_ran = false;
    int jni_on_load_version = 0;  // e.g. 0x00010006
};

// Load-result detail for diagnostics / UnsatisfiedLinkError messages.
struct LoadOutcome {
    bool ok = false;
    std::string detail;      // human-readable, includes real dlerror
    std::string sha16;       // extracted file identity
    unsigned long long size = 0;
    int jni_version = 0;
};

// JNI-spec argument value (positional, full precision).
struct JArg {
    enum class Kind { INT, LONG, FLOAT, DOUBLE, BOOLEAN, CHAR, SHORT, BYTE,
                      STRING, OBJECT, NULLREF } kind = Kind::INT;
    int32_t i32 = 0;
    int64_t i64 = 0;
    float f32 = 0.0f;
    double f64 = 0.0;
    std::string str;         // STRING kind
    uint32_t object_id = 0;  // OBJECT kind (engine heap id)
    static JArg of_int(int32_t v) { JArg a; a.kind = Kind::INT; a.i32 = v; return a; }
    static JArg of_long(int64_t v) { JArg a; a.kind = Kind::LONG; a.i64 = v; return a; }
    static JArg of_float(float v) { JArg a; a.kind = Kind::FLOAT; a.f32 = v; return a; }
    static JArg of_double(double v) { JArg a; a.kind = Kind::DOUBLE; a.f64 = v; return a; }
    static JArg of_bool(bool v) { JArg a; a.kind = Kind::BOOLEAN; a.i32 = v ? 1 : 0; return a; }
    static JArg of_char(int32_t v) { JArg a; a.kind = Kind::CHAR; a.i32 = v; return a; }
    static JArg of_short(int32_t v) { JArg a; a.kind = Kind::SHORT; a.i32 = v; return a; }
    static JArg of_byte(int32_t v) { JArg a; a.kind = Kind::BYTE; a.i32 = v; return a; }
    static JArg of_string(std::string s) { JArg a; a.kind = Kind::STRING; a.str = std::move(s); return a; }
    static JArg of_object(uint32_t id) { JArg a; a.kind = Kind::OBJECT; a.object_id = id; return a; }
    static JArg null() { JArg a; a.kind = Kind::NULLREF; return a; }
};

// Invocation result (return type per DEX descriptor).
struct JOutcome {
    enum class Kind { VOID, INT, LONG, FLOAT, DOUBLE, BOOLEAN, CHAR, SHORT,
                      BYTE, STRING, OBJECT } kind = Kind::VOID;
    int64_t i = 0;           // INT/LONG/BOOLEAN/CHAR/SHORT/BYTE
    double d = 0.0;          // FLOAT/DOUBLE
    std::string str;         // STRING (materialized from the native side)
    uint32_t object_id = 0;  // OBJECT
    std::string provenance;  // symbol + lib that actually executed
};

// ── Library lifecycle (System.loadLibrary / System.load) ──────────────
// Attempts REAL dlopen + JNI_OnLoad. On success the handle stays live for
// symbol resolution; on failure outcome.detail carries the REAL dlerror.
LoadOutcome load_library(const std::string& libname,
                         const std::string& host_path,
                         const std::string& logical_path);

// Records which caller class requested a load (AOSP per-classloader lib
// list law) — find_symbol walks this list first.
void note_loader(const std::string& caller_class, const std::string& libname);

bool has_loaded_libs();
std::vector<LoadedLib> loaded_libs_snapshot();

// ── Symbol resolution (JNI short + long mangling, RegisterNatives) ────
// Returns the function pointer for Java_<class>_<method> or the registered
// native. `tried` lists every symbol name attempted (AOSP "No
// implementation found" evidence).
void* find_symbol(const std::string& class_desc, const std::string& method,
                  const std::string& dex_sig, std::string& tried);

// ── Invocation (System V call via function pointer + JNIEnv bridge) ───
// sig: the DEX descriptor "(args)ret". static_call: JNI receiver slot is
// jclass instead of jobject.
bool call_native(void* fn, bool static_call, const std::string& sig,
                 const std::vector<JArg>& args, JOutcome& out,
                 std::string& error);

// ── Diagnostics counters (pkginspect runtime section) ─────────────────
unsigned long long load_attempts();
unsigned long long load_successes();
unsigned long long native_calls();
unsigned long long native_call_failures();

}  // namespace nativeexec
}  // namespace miniandroid

#endif  // MINIANDROID_DLOPEN_EXEC_H
