// CONT-83 F-NEW-387 — Android native dependency resolution law.
//
// CONT-84 track 2 / CONT-83 native-engine integration: a real dlopen of an
// extracted Android .so fails on the ANDROID platform sonames (libm.so,
// liblog.so, libc.so, libstdc++.so, libdl.so) — the host loader cannot
// resolve them (Debian libm.so/libc.so are GNU ld scripts; liblog.so does
// not exist). The principled, capability-gated law:
//
//   1. Parse the target ELF64's DT_NEEDED in-process (no readelf).
//   2. Classify each entry:
//      - app-bundled  → present in the app's extracted lib dir
//      - host-anchor  → a first-party anchor object with the ANDROID
//        soname exists in the anchor dir (built by
//        scripts/cont83_build_anchors.sh). The anchor is a REAL ELF64
//        shared object whose own DT_NEEDED pulls the real host library
//        (libm.so.6 …) or implements a small Android surface first-party
//        (liblog.so → stderr rows). Pre-loading it RTLD_GLOBAL satisfies
//        the app's DT_NEEDED by SONAME match; the app's undefined symbols
//        then resolve through the anchor's REAL dependency chain.
//      - missing-honest-block → nothing provides it; the row is recorded
//        and the final dlopen fails with the loader's own error.
//   3. VALIDATION: every anchor/candidate path must be a REAL ELF64
//      little-endian x86-64 ET_DYN object — GNU ld scripts ("GROUP(...)"
//      text), archives ("!<arch>"), and wrong-class objects are REJECTED
//      with an explicit row, never silently substituted.
//
// ABI HONESTY: the anchors bind the app to the HOST C runtime. For the
// layout-free C surface (memcpy/malloc/pow/strtol/…, the measured libgdx
// symbol set) the SysV x86-64 contracts are compatible; bionic-specific
// struct layouts (pthread types, FILE) remain a NAMED RISK recorded in
// evidence/cont83/. Every load lands native.load + native.dep rows — no
// silent substitution. Success is a loader milestone, not a rendered-game
// claim (CONT-83 law).
#ifndef MINIANDROID_NATIVE_DEP_H
#define MINIANDROID_NATIVE_DEP_H

#include <string>
#include <vector>

namespace miniandroid {
namespace jni {

struct DepRow {
    std::string needed;      // the DT_NEEDED soname
    std::string status;      // "app-bundled" | "host-anchor" |
                             // "missing-honest-block" | "elf-invalid"
    std::string resolved;    // path dlopen'd (when applicable)
    std::string note;        // loader/validation detail (bounded)
};

// True when the file is a real ELF64 LE object of the given machine
// (default x86-64 = 62) and ET_DYN/ET_EXEC type. Rejects GNU ld scripts,
// archives, and ELF32/wrong-arch objects with a `why` row.
bool is_real_elf64_dyn(const std::string& path, std::string& why);

// Parse DT_NEEDED entries of an ELF64 shared object in-process.
bool list_dt_needed(const std::string& path,
                    std::vector<std::string>& out, std::string& why);

// Anchor dir: $MINIANDROID_ANCHOR_DIR, else <binary_dir>/anchor_libs.
std::string anchor_dir();

// Bionic version-tag strip (see the law comment in native_dep.cpp):
// rewrites "LIBC"-versioned symbol references to unversioned in the
// runtime-owned extracted copy. `rewritten` counts .gnu.version entries.
bool strip_bionic_version_tags(const std::string& path, int& rewritten,
                               std::string& why);

// Resolve + pre-load the DT_NEEDED chain of `host_path` (the extracted
// app .so). `app_lib_dir` is the extracted lib directory (bundled deps).
// Returns the per-entry plan; dlopen failures per entry land in the row
// note and the caller still attempts the REAL dlopen of the app lib for
// the honest loader error.
std::vector<DepRow> prepare_dependencies(const std::string& host_path,
                                         const std::string& app_lib_dir);

}  // namespace jni
}  // namespace miniandroid

#endif  // MINIANDROID_NATIVE_DEP_H
