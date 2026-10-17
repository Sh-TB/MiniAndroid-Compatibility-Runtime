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
                    if (std::strcmp(name, "LIBC") == 0)
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
