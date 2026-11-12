// s225m_wave_law_test — regression battery for the S225-M wave (issue #585
// execution-mandate items 2/3/4/6), the diff that was sitting uncommitted in
// the worktree and is now landed + gated.
//
// Laws pinned here:
//
//   PREC (finding 23, jni_bridge.h) — dispatch-precedence: a later
//          HOST_COMPATIBILITY_STUB registration must NEVER shadow an
//          existing REAL_NATIVE_LIBRARY entry (a stub would report success
//          for required initialization that did not occur). The upgrade
//          direction (STUB → REAL) stays allowed; non-stub overwrites stay
//          last-writer-wins with recorded reregistrations.
//
//   MARSH (finding 24, jni_bridge.h) — missing-argument honesty: the legacy
//          synthetic INT(0) face is kept for ABI compatibility but a missing
//          positional arg is now RECORDED (marshal_errors), new handlers get
//          the explicit nullptr face (try_arg) and the one-call arity gate
//          (validate_arity).
//
//   ELF-VA (finding 20, native_dep.cpp) — DT_STRTAB's d_val is a VIRTUAL
//          ADDRESS: list_dt_needed must map it through the PT_LOAD table
//          (VA → file offset) instead of assuming VA == file offset; the
//          legacy layout (VA == offset, no LOAD mapping) still resolves via
//          the bounded fallback face.
//
//   PTHREAD (findings 6+7, pthread_shadow.c) — locked-section registry:
//          every operation is atomic under g_slots_mu; UNKNOWN attr keys
//          answer EINVAL (POSIX semantics) instead of silent success, and
//          exhausted-registry init answers ENOMEM.
//
// The pthread laws link $(BUILDDIR)/jni/pthread_shadow.o (see the Makefile
// rule for s225m_wave_law_test) — the same interposition shape the real
// binary uses.

#include "../src/jni/jni_bridge.h"
#include "../src/jni/native_dep.h"

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>
#include <unistd.h>

#if defined(__unix__) || defined(__APPLE__)
#include <pthread.h>
#define HAVE_PTHREAD 1
#endif

using miniandroid::jni::JNIBridge;
using miniandroid::jni::NativeCallContext;
using miniandroid::jni::NativeImplType;

namespace {

int g_rows = 0, g_fail = 0;

void check(bool ok, const char* name) {
    ++g_rows;
    if (ok) std::printf("[PASS] %s\n", name);
    else { ++g_fail; std::printf("[FAIL] %s\n", name); }
}

const auto kNoop = [](const NativeCallContext&, int32_t&, int64_t&,
                      float&, double&, std::string&, uint32_t&, bool&) {};

// ── synthetic ELF64 builders ─────────────────────────────────────────────
struct Elf64EhdrT {
    uint8_t  e_ident[16];
    uint16_t e_type, e_machine;
    uint32_t e_version;
    uint64_t e_entry, e_phoff, e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize, e_phentsize, e_phnum;
    uint16_t e_shentsize, e_shnum, e_shstrndx;
};
struct Elf64PhdrT {
    uint32_t p_type, p_flags;
    uint64_t p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align;
};
struct Elf64DynT {
    int64_t d_tag;
    uint64_t d_val;
};

void put16(std::vector<uint8_t>& d, size_t o, uint16_t v) {
    d[o] = v & 0xFF; d[o + 1] = v >> 8;
}
void put32(std::vector<uint8_t>& d, size_t o, uint32_t v) {
    d[o] = v & 0xFF; d[o+1] = (v >> 8) & 0xFF;
    d[o+2] = (v >> 16) & 0xFF; d[o+3] = (v >> 24) & 0xFF;
}
void put64(std::vector<uint8_t>& d, size_t o, uint64_t v) {
    for (int i = 0; i < 8; ++i) d[o + i] = (v >> (8 * i)) & 0xFF;
}

// Layout (file offsets):  ehdr@0, phdr table@64, dynamic@0x200,
// strtab@0x260 ("libva.so"), DT entries at 0x200.
// VA bias: the PT_LOAD segment maps vaddr 0x4000 → offset 0, so the
// strtab VA (0x4260) deliberately differs from its file offset (0x260).
std::vector<uint8_t> elf_with_strtab_va(bool load_bias) {
    std::vector<uint8_t> d(0x400, 0);
    const uint8_t id[16] = {0x7f,'E','L','F', 2, 1, 1, 0, 0,0,0,0, 0,0,0,0};
    std::memcpy(d.data(), id, 16);
    put16(d, 16, 3);           // ET_DYN
    put16(d, 18, 62);          // EM_X86_64
    put32(d, 20, 1);           // e_version
    put64(d, 24, 0);           // e_entry
    put64(d, 32, 64);          // e_phoff
    put64(d, 40, 0);           // e_shoff
    put32(d, 48, 0);           // e_flags
    put16(d, 52, 64);          // e_ehsize
    put16(d, 54, 56);          // e_phentsize
    put16(d, 56, load_bias ? 2 : 1);  // e_phnum
    put16(d, 58, 0);           // e_shentsize
    put16(d, 60, 0);           // e_shnum
    put16(d, 62, 0);           // e_shstrndx

    const uint64_t strtab_file_off = 0x260;
    const uint64_t load_vaddr = 0x4000;
    const uint64_t strtab_va = load_bias ? load_vaddr + strtab_file_off
                                         : strtab_file_off;
    // PT_LOAD (only when testing the mapping face)
    if (load_bias) {
        put32(d, 64, 1);            // PT_LOAD
        put32(d, 68, 5);            // PF_R|PF_X
        put64(d, 72, 0);            // p_offset
        put64(d, 80, load_vaddr);   // p_vaddr
        put64(d, 88, load_vaddr);   // p_paddr
        put64(d, 96, 0x400);        // p_filesz (whole file image)
        put64(d, 104, 0x400);       // p_memsz
        put64(d, 112, 0x1000);      // p_align
    }
    // PT_DYNAMIC at phdr slot 1 (or 0 when no LOAD)
    const size_t dyn_ph = load_bias ? 64 + 56 : 64;
    put32(d, dyn_ph, 2);        // PT_DYNAMIC
    put32(d, dyn_ph + 4, 6);    // PF_R|PF_W
    put64(d, dyn_ph + 8, 0x200);      // p_offset
    put64(d, dyn_ph + 16, 0x200);     // p_vaddr (unmapped — irrelevant here)
    put64(d, dyn_ph + 24, 0x200);     // p_paddr
    put64(d, dyn_ph + 32, 0x60);      // p_filesz (6 entries × 16)
    put64(d, dyn_ph + 40, 0x60);      // p_memsz
    put64(d, dyn_ph + 48, 8);         // p_align

    // dynamic table: NEEDED → "libva.so" at strtab+1 (keep slot 0 = NUL)
    const size_t dt = 0x200;
    auto dyn_entry = [&](size_t idx, int64_t tag, uint64_t val) {
        put64(d, dt + idx * 16, static_cast<uint64_t>(tag));
        put64(d, dt + idx * 16 + 8, val);
    };
    dyn_entry(0, 1, 1);                    // DT_NEEDED offset 1
    dyn_entry(1, 5, strtab_va);            // DT_STRTAB (the VA under test)
    dyn_entry(2, 10, 0x20);                // DT_STRSZ
    dyn_entry(3, 0, 0);                    // DT_NULL
    // strtab[0] stays NUL (buffer is zero-filled); the soname begins at
    // offset 1 — the DT_NEEDED d_val points there (DYNSTR offset 1).
    const char name[] = "libva.so";
    std::memcpy(d.data() + strtab_file_off + 1, name, sizeof name);
    return d;
}

bool write_tmp(const std::vector<uint8_t>& d, std::string& path) {
    path = "/tmp/s225m_elf_" + std::to_string(getpid()) + ".so";
    std::ofstream f(path, std::ios::binary);
    return (bool)f.write(reinterpret_cast<const char*>(d.data()),
                         (std::streamsize)d.size());
}

}  // namespace

int main() {
    std::printf("== S225-M wave law battery ==\n");

    // ── PREC: dispatch precedence ────────────────────────────────────────
    {
        JNIBridge b;
        b.register_native("Lcom/test/Loader;", "nativeInit", "(I)Z", kNoop,
                          NativeImplType::REAL_NATIVE_LIBRARY, "real init");
        check(b.impl_type_of("Lcom/test/Loader;", "nativeInit") ==
                  NativeImplType::REAL_NATIVE_LIBRARY,
              "PREC-1 real registration owns the key");
        const size_t before = b.registered_count();
        b.register_native("Lcom/test/Loader;", "nativeInit", "(I)Z", kNoop,
                          NativeImplType::HOST_COMPATIBILITY_STUB, "fake");
        check(b.impl_type_of("Lcom/test/Loader;", "nativeInit") ==
                  NativeImplType::REAL_NATIVE_LIBRARY,
              "PREC-2 stub does NOT shadow the real entry");
        check(b.registered_count() == before,
              "PREC-3 refused registration did not replace the entry");
        check(b.precedence_violations().size() == 1 &&
                  b.precedence_violations()[0].find("stub-shadows-real") !=
                      std::string::npos,
              "PREC-4 violation recorded (stub-shadows-real blocked)");
        // upgrade direction: STUB → REAL stays allowed
        b.register_native("Lcom/test/Up;", "nativeBoot", "()V", kNoop,
                          NativeImplType::HOST_COMPATIBILITY_STUB, "stub");
        b.register_native("Lcom/test/Up;", "nativeBoot", "()V", kNoop,
                          NativeImplType::REAL_NATIVE_LIBRARY, "real");
        check(b.impl_type_of("Lcom/test/Up;", "nativeBoot") ==
                  NativeImplType::REAL_NATIVE_LIBRARY,
              "PREC-5 STUB→REAL upgrade wins");
        // REAL → REAL overwrite: last-writer-wins + recorded
        b.register_native("Lcom/test/Up;", "nativeBoot", "()V", kNoop,
                          NativeImplType::REAL_NATIVE_LIBRARY, "real v2");
        check(b.impl_type_of("Lcom/test/Up;", "nativeBoot") ==
                  NativeImplType::REAL_NATIVE_LIBRARY &&
                  b.reregistrations().size() == 2,
              "PREC-6 REAL→REAL last-writer-wins recorded");
    }

    // ── MARSH: missing-argument honesty ─────────────────────────────────
    {
        NativeCallContext ctx;
        ctx.method_name = "nativeWrite";
        ctx.signature = "(IJ)V";
        ctx.pos.push_back(NativeCallContext::Arg::of_int(7));
        const bool clean_before = !ctx.has_marshal_error();
        const auto& zero = ctx.arg(1);  // missing — synthetic face
        check(zero.kind == NativeCallContext::Arg::Kind::INT &&
                  zero.int_val == 0 && clean_before == true,
              "MARSH-1 legacy synthetic INT(0) face unchanged");
        check(ctx.has_marshal_error() &&
                  ctx.marshal_errors.back().find("synthetic INT(0)") !=
                      std::string::npos,
              "MARSH-2 missing arg RECORDED in marshal_errors");
        check(ctx.try_arg(1) == nullptr && ctx.try_arg(0) != nullptr &&
                  ctx.try_arg(0)->int_val == 7,
              "MARSH-3 try_arg explicit nullptr face");
        // ctx carries ONE positional arg: need 1 OK (min face), need 3
        // fails (shortfall), exact-1 OK, exact-2 fails (exact mismatch);
        // every failure records a structured "arity:" message.
        check(ctx.validate_arity(1) && !ctx.validate_arity(3) &&
                  ctx.validate_arity(1, true) && !ctx.validate_arity(2, true) &&
                  ctx.marshal_errors.back().find("arity:") !=
                      std::string::npos,
              "MARSH-4 validate_arity gate fails on shortfall + records");
        NativeCallContext ok;
        ok.method_name = "f"; ok.signature = "(I)V";
        ok.pos.push_back(NativeCallContext::Arg::of_int(1));
        check(ok.validate_arity(1) && ok.validate_arity(1, true) &&
                  !ok.has_marshal_error(),
              "MARSH-5 validate_arity passes on exact arity");
    }

    // ── ELF-VA: DT_STRTAB VA → PT_LOAD mapping ──────────────────────────
    {
        std::string path, why;
        // mapping face: VA (0x4260) != file offset (0x260)
        auto d1 = elf_with_strtab_va(true);
        check(write_tmp(d1, path), "ELF-VA-0 synthetic ELF written (bias)");
        std::vector<std::string> needed;
        const bool ok1 = miniandroid::jni::list_dt_needed(path, needed, why);
        std::fprintf(stderr, "[dbg VA1] ok=%d n=%zu first=%s why=%s\n", ok1,
                     needed.size(),
                     needed.empty() ? "-" : needed[0].c_str(), why.c_str());
        check(ok1 && needed.size() == 1 && needed[0] == "libva.so",
              "ELF-VA-1 VA mapped through PT_LOAD resolves DT_NEEDED");
        std::remove(path.c_str());
        // fallback face: no LOAD segment, VA == file offset
        auto d2 = elf_with_strtab_va(false);
        check(write_tmp(d2, path), "ELF-VA-0b synthetic ELF written (flat)");
        needed.clear();
        const bool ok2 = miniandroid::jni::list_dt_needed(path, needed, why);
        std::fprintf(stderr, "[dbg VA2] ok=%d n=%zu first=%s why=%s\n", ok2,
                     needed.size(),
                     needed.empty() ? "-" : needed[0].c_str(), why.c_str());
        check(ok2 && needed.size() == 1 && needed[0] == "libva.so",
              "ELF-VA-2 legacy VA==offset layout still resolves (fallback)");
        std::remove(path.c_str());
    }

#ifdef HAVE_PTHREAD
    // ── PTHREAD: POSIX error semantics on the shadow registry ───────────
    {
        pthread_mutexattr_t bogus;
        std::memset(&bogus, 0, sizeof bogus);
        check(pthread_mutexattr_settype(&bogus, 3) == EINVAL,
              "PTH-1 settype on UNKNOWN key answers EINVAL");
        int bogus_type = -1;
        check(pthread_mutexattr_gettype(&bogus, &bogus_type) == EINVAL,
              "PTH-2 gettype on UNKNOWN key answers EINVAL");
        check(pthread_mutexattr_init(&bogus) == 0,
              "PTH-3 init on a fresh key succeeds");
        check(pthread_mutexattr_settype(&bogus, 3) == 0,
              "PTH-4 settype after init succeeds (known key)");
        int t = -1;
        check(pthread_mutexattr_gettype(&bogus, &t) == 0 && t == 3,
              "PTH-5 gettype round-trips the set type");
        check(pthread_mutexattr_destroy(&bogus) == 0,
              "PTH-6 destroy removes the registry entry");
        check(pthread_mutexattr_settype(&bogus, 1) == EINVAL,
              "PTH-7 settype after destroy answers EINVAL (use-after-destroy)");
    }
#endif

    std::printf("BATTERY: rows=%d fail=%d\n", g_rows, g_fail);
    return g_fail == 0 ? 0 : 1;
}
