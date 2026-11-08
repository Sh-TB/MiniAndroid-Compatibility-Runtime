// CONT-83 F-NEW-387 implementation — see native_dep.h for the law.
#include "native_dep.h"
#include "../diagnostics/gfx_trace.h"

#include <dlfcn.h>

#include <cstdint>
#include <cstring>
#include <fstream>
#include <unistd.h>

namespace miniandroid {
namespace jni {

namespace {

#pragma pack(push, 1)
struct Elf64Ehdr {
    uint8_t  e_ident[16];
    uint16_t e_type, e_machine;
    uint32_t e_version;
    uint64_t e_entry, e_phoff, e_shoff;
    uint32_t e_flags;
    // ELF64 halves: e_ehsize/e_phentsize/e_phnum/e_shentsize/e_shnum/
    // e_shstrndx are 2-byte fields (declaring them 4-byte shifted every
    // later field and made every header read garbage).
    uint16_t e_ehsize, e_phentsize, e_phnum;
    uint16_t e_shentsize, e_shnum, e_shstrndx;
};
struct Elf64Phdr {
    uint32_t p_type, p_flags;
    uint64_t p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align;
};
struct Elf64Dyn {
    int64_t d_tag;
    uint64_t d_val;
};
struct Elf64Shdr {
    uint32_t sh_name, sh_type;
    uint64_t sh_flags, sh_addr, sh_offset, sh_size;
    uint32_t sh_link, sh_info;
    uint64_t sh_addralign, sh_entsize;
};
struct Verneed {
    uint16_t vn_version, vn_cnt;
    uint32_t vn_file, vn_aux, vn_next;
};
struct Vernaux {
    uint32_t vna_hash;
    uint16_t vna_flags, vna_other;
    uint32_t vna_name, vna_next;
};
#pragma pack(pop)

constexpr uint16_t ET_DYN = 3;
constexpr uint16_t EM_X86_64 = 62;
constexpr uint32_t PT_DYNAMIC = 2;
constexpr uint32_t PT_LOAD = 1;
constexpr int64_t DT_NULL = 0, DT_NEEDED = 1, DT_STRTAB = 5, DT_STRSZ = 10;
constexpr uint32_t SHT_STRTAB = 3;
constexpr uint32_t SHT_GNU_versym = 0x6fffffff;
constexpr uint32_t SHT_GNU_verneed = 0x6ffffffe;
constexpr uint16_t VER_NDX_GLOBAL = 1;

bool read_file(const std::string& path, std::vector<uint8_t>& buf) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    const std::streamoff n = f.tellg();
    if (n <= 0 || n > (1 << 30)) return false;  // >1GiB: not a dep candidate
    f.seekg(0, std::ios::beg);
    buf.resize((size_t)n);
    return (bool)f.read(reinterpret_cast<char*>(buf.data()), n);
}

// Locate the three ELF structures the two laws need. Returns false when
// any is missing/bounded-out.
bool locate_sections(const std::vector<uint8_t>& buf, std::string& why,
                     const Elf64Shdr** versym, const Elf64Shdr** verneed,
                     const Elf64Shdr** dynstr) {
    Elf64Ehdr e;
    std::memcpy(&e, buf.data(), sizeof e);
    if (e.e_shoff == 0 || e.e_shentsize < sizeof(Elf64Shdr) ||
        e.e_shoff + (uint64_t)e.e_shnum * e.e_shentsize > buf.size()) {
        why = "no section headers";
        return false;
    }
    static thread_local Elf64Shdr vs, vn, ds;
    bool has_vs = false, has_vn = false, has_ds = false;
    for (uint16_t i = 0; i < e.e_shnum; ++i) {
        Elf64Shdr s;
        std::memcpy(&s, buf.data() + e.e_shoff + (size_t)i * e.e_shentsize,
                    sizeof s);
        if (s.sh_type == SHT_GNU_versym) { vs = s; has_vs = true; }
        else if (s.sh_type == SHT_GNU_verneed) { vn = s; has_vn = true; }
        else if (s.sh_type == SHT_STRTAB && !has_ds) { ds = s; has_ds = true; }
    }
    if (!has_vs || !has_vn || !has_ds) {
        why = "missing versym/verneed/dynstr";
        return false;
    }
    *versym = &vs;
    *verneed = &vn;
    *dynstr = &ds;
    return true;
}

}  // namespace

bool is_real_elf64_dyn(const std::string& path, std::string& why) {
    std::vector<uint8_t> buf;
    if (!read_file(path, buf) || buf.size() < sizeof(Elf64Ehdr)) {
        why = "unreadable or truncated";
        return false;
    }
    Elf64Ehdr e;
    std::memcpy(&e, buf.data(), sizeof e);
    if (e.e_ident[0] != 0x7f || e.e_ident[1] != 'E' || e.e_ident[2] != 'L' ||
        e.e_ident[3] != 'F') {
        // GNU ld scripts (text "GROUP ( ... )") and archives ("!<arch>")
        // masquerading as Android sonames — the exact trap this law rejects.
        why = "not an ELF object (ld-script/archive?)";
        return false;
    }
    if (e.e_ident[4] != 2) { why = "not ELF64 (EI_CLASS!=2)"; return false; }
    if (e.e_ident[5] != 1) { why = "not little-endian"; return false; }
    if (e.e_machine != EM_X86_64) {
        why = "wrong machine (expected x86-64)";
        return false;
    }
    if (e.e_type != ET_DYN && e.e_type != 2) {
        why = "not ET_DYN/ET_EXEC";
        return false;
    }
    return true;
}

bool list_dt_needed(const std::string& path,
                    std::vector<std::string>& out, std::string& why) {
    std::vector<uint8_t> buf;
    if (!read_file(path, buf) || buf.size() < sizeof(Elf64Ehdr)) {
        why = "unreadable";
        return false;
    }
    Elf64Ehdr e;
    std::memcpy(&e, buf.data(), sizeof e);
    if (e.e_phentsize < sizeof(Elf64Phdr) || e.e_phoff == 0 ||
        e.e_phoff + (uint64_t)e.e_phnum * e.e_phentsize > buf.size()) {
        why = "no program headers";
        return false;
    }
    const Elf64Dyn* dyn = nullptr;
    size_t dyn_n = 0;
    for (uint32_t i = 0; i < e.e_phnum; ++i) {
        Elf64Phdr p;
        std::memcpy(&p, buf.data() + e.e_phoff + (size_t)i * e.e_phentsize,
                    sizeof p);
        if (p.p_type != PT_DYNAMIC) continue;
        if (p.p_offset + p.p_filesz > buf.size()) { why = "bad PT_DYNAMIC"; return false; }
        dyn = reinterpret_cast<const Elf64Dyn*>(buf.data() + p.p_offset);
        dyn_n = p.p_filesz / sizeof(Elf64Dyn);
        break;
    }
    if (!dyn) { why = "no PT_DYNAMIC"; return false; }
    uint64_t strtab_off = 0, strsz = 0;
    for (size_t i = 0; i < dyn_n && dyn[i].d_tag != DT_NULL; ++i) {
        if (dyn[i].d_tag == DT_STRTAB) strtab_off = dyn[i].d_val;
        if (dyn[i].d_tag == DT_STRSZ) strsz = dyn[i].d_val;
    }
    // The file view of .dynstr: for the first LOAD segment of typical
    // pre-linked .so files vaddr == file offset, so DT_STRTAB's d_val is
    // used directly as the .dynstr FILE offset; every access is bounded
    // to the buffer + DT_STRSZ regardless.
    auto cstr_at = [&](uint64_t str_off) -> const char* {
        if (strtab_off == 0 || strsz == 0) return nullptr;
        const uint64_t rel = str_off;   // offset INSIDE .dynstr
        if (rel >= strsz) return nullptr;
        if (strtab_off + rel >= buf.size()) return nullptr;
        const uint64_t max = std::min<uint64_t>(strsz - rel,
                                                buf.size() - strtab_off - rel);
        const char* s = reinterpret_cast<const char*>(buf.data() +
                                                      strtab_off + rel);
        return memchr(s, '\0', (size_t)max) ? s : nullptr;
    };
    for (size_t i = 0; i < dyn_n && dyn[i].d_tag != DT_NULL; ++i) {
        if (dyn[i].d_tag != DT_NEEDED) continue;
        const char* s = cstr_at(dyn[i].d_val);
        out.push_back(s ? std::string(s) : std::string("<unprintable>"));
    }
    return true;
}

std::string anchor_dir() {
    const char* env = std::getenv("MINIANDROID_ANCHOR_DIR");
    if (env && *env) return env;
    // Default: beside the runtime binary (build/anchor_libs).
    char exe[4096];
    const ssize_t n = readlink("/proc/self/exe", exe, sizeof exe - 1);
    if (n <= 0) return "anchor_libs";
    exe[n] = '\0';
    std::string dir(exe);
    const auto slash = dir.rfind('/');
    return (slash == std::string::npos ? std::string(".")
                                       : dir.substr(0, slash)) +
           "/anchor_libs";
}

// CONT-83 F-NEW-387 (bionic version tags): Android libs reference their C
// symbols as `name@LIBC` (the bionic version tag). glibc rejects the
// versioned lookup — its definitions carry GLIBC_* versions. The bounded,
// recorded transform: in the RUNTIME-OWNED EXTRACTED COPY (never the APK),
// rewrite the .gnu.version indexes of symbols whose required version is
// "LIBC" to VER_NDX_GLOBAL (unversioned reference). The glibc loader then
// resolves the symbol by name against its REAL definitions (the
// documented "no version information available" warning is the record of
// the hop). Rewrites are counted; the caller lands the trace row.
bool strip_bionic_version_tags(const std::string& path, int& rewritten,
                               std::string& why) {
    rewritten = 0;
    std::vector<uint8_t> buf;
    if (!read_file(path, buf) || buf.size() < sizeof(Elf64Ehdr)) {
        why = "unreadable";
        return false;
    }
    const Elf64Shdr *versym = nullptr, *verneed = nullptr, *dynstr = nullptr;
    if (!locate_sections(buf, why, &versym, &verneed, &dynstr)) return false;
    // Version indexes the "LIBC" tag requires.
    std::vector<uint16_t> libc_idx;
    {
        uint64_t off = verneed->sh_offset;
        for (uint32_t n = 0; n < verneed->sh_info; ++n) {
            if (off + sizeof(Verneed) > buf.size()) {
                why = "verneed bounds";
                return false;
            }
            Verneed v;
            std::memcpy(&v, buf.data() + off, sizeof v);
            uint64_t aoff = off + v.vn_aux;
            for (uint16_t k = 0; k < v.vn_cnt; ++k) {
                if (aoff + sizeof(Vernaux) > buf.size()) {
                    why = "vernaux bounds";
                    return false;
                }
                Vernaux a;
                std::memcpy(&a, buf.data() + aoff, sizeof a);
                if (a.vna_name < dynstr->sh_size &&
                    dynstr->sh_offset + a.vna_name < buf.size()) {
                    const char* name = reinterpret_cast<const char*>(
                        buf.data() + dynstr->sh_offset + a.vna_name);
                    // CONT-113 F-NEW-461: bionic tags the C ABI per API
                    // level — LIBC plus per-letter variants (LIBC_N/O/P/Q/
                    // R/S...). __cxa_pure_virtual (the C++ ABI thunk every
                    // NDK C++ lib needs) is tagged LIBC_O, so an exact
                    // "LIBC" match left every LIBC_* symbol versioned and
                    // glibc rejected the lookup ("undefined symbol ...,
                    // version LIBC_O"). The family test (exact LIBC or the
                    // LIBC_ prefix) covers the whole bionic tag family;
                    // GLIBC_* host tags never match the prefix.
                    if (std::strcmp(name, "LIBC") == 0 ||
                        std::strncmp(name, "LIBC_", 5) == 0)
                        libc_idx.push_back(a.vna_other);
                }
                if (!a.vna_next) break;
                aoff += a.vna_next;
            }
            if (!v.vn_next) break;
            off += v.vn_next;
        }
    }
    if (libc_idx.empty()) return true;   // nothing to strip
    const size_t nsyms = versym->sh_size / 2;
    for (size_t i = 0; i < nsyms; ++i) {
        uint16_t idx;
        std::memcpy(&idx, buf.data() + versym->sh_offset + i * 2, 2);
        for (uint16_t want : libc_idx) {
            if (idx == want) {
                const uint16_t g = VER_NDX_GLOBAL;
                std::memcpy(buf.data() + versym->sh_offset + i * 2, &g, 2);
                ++rewritten;
                break;
            }
        }
    }
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) { why = "write failed"; rewritten = 0; return false; }
    f.write(reinterpret_cast<const char*>(buf.data()),
            (std::streamsize)buf.size());
    return true;
}

// ── W15 FOREIGN_LOADER_NULL_CDTOR_LAW ────────────────────────────────────
// Bionic (AOSP linker) call_function/call_array SKIP null and -1 sentinel
// init/fini entries; glibc calls every entry. p9's libgdx.so ships with
// init_array[0]=0x0 (unrelocated) — the probe child's dlopen jumped to
// address 0 (SIGSEGV rip=0x0 fault_addr=0x0, FAULT-IP row 2026-11-08) —
// and fini_array[1]=0x0 would fault dlclose the same way. Device truth:
// the same .so loads on real Android (bionic skips the null entries) —
// this is a FOREIGN LOADER contract difference, not an app defect. Fix
// class: the same runtime-owned extracted-copy surgery as the bionic
// versym strip above (APK bytes untouched). Only TRAILING skip-entries
// are dropped (count shrink — entries never move, so existing RELATIVE
// relocations keep pairing). A slot with ANY relocation on it is never
// dropped (relocated slots are real even when their raw file value is
// small).
bool elide_bionic_skipped_cdtor_entries(const std::string& path,
                                        int& init_dropped, int& fini_dropped,
                                        std::string& why) {
    init_dropped = fini_dropped = 0;
    std::vector<uint8_t> buf;
    if (!read_file(path, buf) || buf.size() < sizeof(Elf64Ehdr)) {
        why = "unreadable";
        return false;
    }
    Elf64Ehdr e;
    std::memcpy(&e, buf.data(), sizeof e);
    if (e.e_phoff == 0 || e.e_phnum == 0 ||
        e.e_phoff + (uint64_t)e.e_phnum * e.e_phentsize > buf.size()) {
        why = "no program headers";
        return false;
    }
    // PT_DYNAMIC + PT_LOAD table for vaddr→file-offset translation.
    Elf64Phdr dyn_ph{};
    bool has_dyn = false;
    std::vector<Elf64Phdr> loads;
    for (uint16_t i = 0; i < e.e_phnum; ++i) {
        Elf64Phdr p;
        std::memcpy(&p, buf.data() + e.e_phoff + (size_t)i * e.e_phentsize,
                    sizeof p);
        if (p.p_type == PT_DYNAMIC) {
            dyn_ph = p;
            has_dyn = true;
        } else if (p.p_type == PT_LOAD) {
            loads.push_back(p);
        }
    }
    if (!has_dyn ||
        dyn_ph.p_offset + dyn_ph.p_filesz > buf.size()) {
        why = "no PT_DYNAMIC";
        return false;
    }
    constexpr int64_t DT_INIT_ARRAYSZ = 27, DT_FINI_ARRAYSZ = 28;
    constexpr int64_t DT_INIT_ARRAY = 25, DT_FINI_ARRAY = 26;
    constexpr uint64_t R_X86_64_RELATIVE = 8;
    constexpr uint32_t SHT_RELA = 4;
    uint64_t off_initsz = 0, off_finisz = 0;
    uint64_t va_init = 0, va_fini = 0, sz_init = 0, sz_fini = 0;
    for (uint64_t o = dyn_ph.p_offset;
         o + sizeof(Elf64Dyn) <= dyn_ph.p_offset + dyn_ph.p_filesz;
         o += sizeof(Elf64Dyn)) {
        Elf64Dyn d;
        std::memcpy(&d, buf.data() + o, sizeof d);
        if (d.d_tag == DT_NULL) break;
        if (d.d_tag == DT_INIT_ARRAY) { va_init = d.d_val; }
        else if (d.d_tag == DT_INIT_ARRAYSZ) { sz_init = d.d_val; off_initsz = o; }
        else if (d.d_tag == DT_FINI_ARRAY) { va_fini = d.d_val; }
        else if (d.d_tag == DT_FINI_ARRAYSZ) { sz_fini = d.d_val; off_finisz = o; }
    }
    if (!sz_init && !sz_fini) {
        why = "no init/fini arrays";
        return true;   // nothing to do (halma's libgdx.so shape)
    }
    // Relocated-slot set: any RELATIVE relocation target. A slot covered
    // by a relocation has a meaningful runtime value — never dropped.
    auto vaddr_to_off = [&loads](uint64_t va, uint64_t& off) -> bool {
        for (const auto& p : loads) {
            if (va >= p.p_vaddr && va < p.p_vaddr + p.p_filesz) {
                off = va - p.p_vaddr + p.p_offset;
                return true;
            }
        }
        return false;
    };
    auto trailing_droppable = [&](uint64_t va, uint64_t sz) -> int {
        if (!va || !sz || sz % 8) return 0;
        uint64_t aoff;
        if (!vaddr_to_off(va, aoff)) return 0;
        int dropped = 0;
        for (int64_t k = (int64_t)(sz / 8) - 1; k >= 0; --k) {
            uint64_t v;
            std::memcpy(&v, buf.data() + aoff + (size_t)k * 8, 8);
            if (v != 0 && v != ~uint64_t(0)) break;   // first non-skip entry
            dropped++;
        }
        // Verify none of the trailing slots is relocated (their vaddrs run
        // from va + sz - dropped*8 up to va + sz - 8).
        for (uint16_t i = 0; i < e.e_shnum && dropped; ++i) {
            Elf64Shdr s;
            std::memcpy(&s, buf.data() + e.e_shoff + (size_t)i * e.e_shentsize,
                        sizeof s);
            if (s.sh_type != SHT_RELA) continue;
            for (uint64_t ro = s.sh_offset;
                 ro + 24 <= s.sh_offset + s.sh_size; ro += 24) {
                uint64_t r_offset, r_info;
                std::memcpy(&r_offset, buf.data() + ro, 8);
                std::memcpy(&r_info, buf.data() + ro + 8, 8);
                if ((r_info & 0xffffffffu) != R_X86_64_RELATIVE) continue;
                for (int k = 0; k < dropped; ++k) {
                    if (r_offset == va + (uint64_t)k * 8 + (sz - dropped * 8))
                        return 0;   // relocation on a trailing slot: keep
                }
            }
        }
        return dropped;
    };
    bool changed = false;
    // Rewrite the WHOLE Elf64Dyn entry (tag kept, d_val updated): writing
    // only 8 bytes at the entry start would clobber d_tag with the new
    // size (0 → DT_NULL stops the loader's dynamic parse mid-table, whose
    // exact downstream face is call_init faulting on a missing
    // l_info[DT_INIT_ARRAYSZ] — W15 live evidence, fixed same day).
    if (sz_init) {
        int d = trailing_droppable(va_init, sz_init);
        if (d > 0) {
            Elf64Dyn dd;
            std::memcpy(&dd, buf.data() + off_initsz, sizeof dd);
            dd.d_val = sz_init - (uint64_t)d * 8;
            std::memcpy(buf.data() + off_initsz, &dd, sizeof dd);
            init_dropped = d;
            changed = true;
        }
    }
    if (sz_fini) {
        int d = trailing_droppable(va_fini, sz_fini);
        if (d > 0) {
            Elf64Dyn dd;
            std::memcpy(&dd, buf.data() + off_finisz, sizeof dd);
            dd.d_val = sz_fini - (uint64_t)d * 8;
            std::memcpy(buf.data() + off_finisz, &dd, sizeof dd);
            fini_dropped = d;
            changed = true;
        }
    }
    if (!changed) {
        why = "no trailing bionic-skip entries (or relocated slots present)";
        return true;
    }
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) { why = "write failed"; init_dropped = fini_dropped = 0; return false; }
    f.write(reinterpret_cast<const char*>(buf.data()),
            (std::streamsize)buf.size());
    return true;
}

std::vector<DepRow> prepare_dependencies(const std::string& host_path,
                                         const std::string& app_lib_dir) {
    std::vector<DepRow> plan;
    std::vector<std::string> needed;
    std::string why;
    if (!list_dt_needed(host_path, needed, why)) {
        DepRow r;
        r.needed = "<parse>";
        r.status = "elf-invalid";
        r.note = why;
        plan.push_back(std::move(r));
        gfx::GfxTrace::instance().native_dep("<parse>", "elf-invalid", "", why);
        return plan;
    }
    // Bionic version-tag strip (the extracted copy is runtime-owned).
    {
        int stripped = 0;
        std::string swhy;
        if (strip_bionic_version_tags(host_path, stripped, swhy) &&
            stripped > 0) {
            gfx::GfxTrace::instance().event("native.verstrip",
                [&](nlohmann::json& r) {
                    r["path"] = host_path;
                    r["rewritten"] = stripped;
                    r["law"] = "bionic @LIBC versym indexes -> "
                               "VER_NDX_GLOBAL (unversioned) in the "
                               "extracted copy; APK untouched";
                });
        }
    }
    // W15 FOREIGN_LOADER_NULL_CDTOR_LAW: elide trailing null/-1 init/fini
    // entries in the extracted copy (bionic skips them; glibc calls them —
    // p9 libgdx.so evidence: dlopen jumped to 0x0). Same surgery class as
    // the versym strip; APK bytes untouched.
    {
        int init_dropped = 0, fini_dropped = 0;
        std::string ewhy;
        if (elide_bionic_skipped_cdtor_entries(host_path, init_dropped,
                                               fini_dropped, ewhy) &&
            (init_dropped > 0 || fini_dropped > 0)) {
            gfx::GfxTrace::instance().event("native.nullcdtor",
                [&](nlohmann::json& r) {
                    r["path"] = host_path;
                    r["init_dropped"] = init_dropped;
                    r["fini_dropped"] = fini_dropped;
                    r["law"] = "FOREIGN_LOADER_NULL_CDTOR_LAW: bionic "
                               "call_array skips null/-1 cdtor entries, "
                               "glibc calls them (call-to-0); trailing "
                               "unrelocated skip-entries elided from the "
                               "SZ tags in the extracted copy; APK "
                               "untouched";
                });
        }
    }
    const std::string anchors = anchor_dir();
    for (const auto& soname : needed) {
        DepRow r;
        r.needed = soname;
        // (a) host-native: the HOST loader can resolve this soname itself
        // (glibc sonames like libc.so.6). One dlopen attempt registers it
        // RTLD_GLOBAL for the app's own load; a failure falls through.
        {
            dlerror();
            void* h = dlopen(soname.c_str(), RTLD_LAZY | RTLD_GLOBAL);
            if (h) {
                r.status = "host-native";
                r.resolved = soname;
                plan.push_back(std::move(r));
                gfx::GfxTrace::instance().native_dep(soname,
                                                     plan.back().status,
                                                     plan.back().resolved,
                                                     plan.back().note);
                continue;
            }
        }
        // (b) app-bundled: the extracted lib dir carries the dep itself.
        const std::string bundled = app_lib_dir + "/" + soname;
        std::string vwhy;
        if (app_lib_dir.size() && access(bundled.c_str(), R_OK) == 0) {
            if (is_real_elf64_dyn(bundled, vwhy)) {
                void* h = dlopen(bundled.c_str(), RTLD_LAZY | RTLD_GLOBAL);
                if (h) {
                    r.status = "app-bundled";
                    r.resolved = bundled;
                } else {
                    const char* e = dlerror();
                    r.status = "elf-invalid";
                    r.note = std::string("dlopen: ") + (e ? e : "unknown");
                }
            } else {
                r.status = "elf-invalid";
                r.note = vwhy;
            }
            plan.push_back(std::move(r));
            gfx::GfxTrace::instance().native_dep(soname, plan.back().status,
                                                 plan.back().resolved,
                                                 plan.back().note);
            continue;
        }
        // (c) host-anchor: first-party anchor object with the ANDROID
        // soname (validated ELF64), pre-loaded RTLD_GLOBAL so the app's
        // DT_NEEDED matches by SONAME and its undefined symbols resolve
        // through the anchor's real dependency chain.
        const std::string anchor = anchors + "/" + soname;
        if (access(anchor.c_str(), R_OK) == 0 &&
            is_real_elf64_dyn(anchor, vwhy)) {
            void* h = dlopen(anchor.c_str(), RTLD_LAZY | RTLD_GLOBAL);
            if (h) {
                r.status = "host-anchor";
                r.resolved = anchor;
                r.note = "ABI caveat: binds Android soname to the host C "
                         "runtime (see F-NEW-387 law)";
            } else {
                const char* e = dlerror();
                r.status = "elf-invalid";
                r.note = std::string("dlopen: ") + (e ? e : "unknown");
            }
        } else {
            r.status = access(anchor.c_str(), R_OK) == 0
                           ? "elf-invalid"
                           : "missing-honest-block";
            r.note = access(anchor.c_str(), R_OK) == 0 ? vwhy
                     : "no app-bundled copy and no first-party anchor";
        }
        plan.push_back(std::move(r));
        gfx::GfxTrace::instance().native_dep(soname, plan.back().status,
                                             plan.back().resolved,
                                             plan.back().note);
    }
    return plan;
}

}  // namespace jni
}  // namespace miniandroid
