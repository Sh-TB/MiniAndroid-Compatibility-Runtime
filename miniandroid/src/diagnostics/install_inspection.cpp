// install_inspection.cpp — GATE A (issue #370): INSTALL-ENVIRONMENT
// CAPABILITY inspection surface. See install_inspection.h for the law.
#include "install_inspection.h"

#include "../apk/apk_parser.h"
#include "../apk/manifest_reader.h"
#include "../dex/dex_parser.h"
#include "../resources/arsc_parser.h"

#include <openssl/evp.h>

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <ctime>

namespace fs = std::filesystem;

namespace miniandroid {
namespace gatea {

// ─────────────────────────────────────────────────────────────────────────
// small JSON + hash helpers
// ─────────────────────────────────────────────────────────────────────────
std::string jesc(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 8);
    for (unsigned char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (c < 0x20) {
                    char b[8];
                    snprintf(b, sizeof(b), "\\u%04x", c);
                    out += b;
                } else {
                    out += (char)c;
                }
        }
    }
    return out;
}

static std::string sha256_bytes(const unsigned char* data, size_t len, bool* ok) {
    *ok = false;
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    std::string hex;
    if (ctx && EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) == 1 &&
        EVP_DigestUpdate(ctx, data, len) == 1 &&
        EVP_DigestFinal_ex(ctx, digest, &dlen) == 1) {
        static const char* H = "0123456789abcdef";
        for (unsigned int i = 0; i < dlen; i++) {
            hex += H[digest[i] >> 4];
            hex += H[digest[i] & 0xf];
        }
        *ok = true;
    }
    if (ctx) EVP_MD_CTX_free(ctx);
    return hex;
}

static std::string sha256_file(const std::string& path, bool* ok) {
    *ok = false;
    FILE* f = fopen(path.c_str(), "rb");
    if (!f) return "";
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    std::string hex;
    if (ctx && EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) == 1) {
        char buf[65536];
        size_t n;
        bool stream_ok = true;
        while ((n = fread(buf, 1, sizeof(buf), f)) > 0)
            if (EVP_DigestUpdate(ctx, buf, n) != 1) { stream_ok = false; break; }
        if (stream_ok && !ferror(f) && EVP_DigestFinal_ex(ctx, digest, &dlen) == 1) {
            static const char* H = "0123456789abcdef";
            for (unsigned int i = 0; i < dlen; i++) {
                hex += H[digest[i] >> 4];
                hex += H[digest[i] & 0xf];
            }
            *ok = true;
        }
    }
    if (ctx) EVP_MD_CTX_free(ctx);
    fclose(f);
    return hex;
}

static std::string sha16(const std::string& sha) {
    return sha.size() >= 16 ? sha.substr(0, 16) : sha;
}

// ─────────────────────────────────────────────────────────────────────────
// ZIP central-directory reader (self-contained; no inflation — metadata
// only. Byte access goes through apk::ApkParser::extract_entry).
// ─────────────────────────────────────────────────────────────────────────
struct ZipEntryMeta {
    std::string name;
    uint16_t method = 0;        // 0 stored / 8 deflate
    uint32_t crc32 = 0;
    uint32_t comp_size = 0;
    uint32_t uncomp_size = 0;
    uint32_t local_offset = 0;
};

static bool read_zip_central_directory(const std::string& path,
                                       std::vector<ZipEntryMeta>& out,
                                       std::string& err) {
    std::ifstream f(path, std::ios::binary);
    if (!f) { err = "open-failed"; return false; }
    f.seekg(0, std::ios::end);
    long long size = f.tellg();
    if (size < 22) { err = "too-small"; return false; }
    // Find EOCD (scan back max 64KB + 22).
    long long scan_from = std::max<long long>(0, size - (65536 + 22));
    std::vector<char> tail(size - scan_from);
    f.seekg(scan_from);
    f.read(tail.data(), tail.size());
    long long eocd = -1;
    for (long long i = (long long)tail.size() - 22; i >= 0; i--) {
        uint32_t sig;
        memcpy(&sig, tail.data() + i, 4);
        if (sig == 0x06054b50) { eocd = scan_from + i; break; }
    }
    if (eocd < 0) { err = "no-eocd"; return false; }
    uint16_t cd_count, cd_count2;
    uint32_t cd_size, cd_offset;
    memcpy(&cd_count, tail.data() + (eocd - scan_from) + 10, 2);
    memcpy(&cd_count2, tail.data() + (eocd - scan_from) + 8, 2);
    memcpy(&cd_size, tail.data() + (eocd - scan_from) + 12, 4);
    memcpy(&cd_offset, tail.data() + (eocd - scan_from) + 16, 4);
    uint32_t total = cd_count ? cd_count : cd_count2;
    (void)cd_size;

    f.seekg(cd_offset);
    std::vector<char> cd(cd_size);
    if (cd_size) f.read(cd.data(), cd.size());
    size_t pos = 0;
    for (uint32_t i = 0; i < total && pos + 46 <= cd.size(); i++) {
        uint32_t sig;
        memcpy(&sig, cd.data() + pos, 4);
        if (sig != 0x02014b50) { err = "bad-cd-sig"; return false; }
        ZipEntryMeta e;
        memcpy(&e.method, cd.data() + pos + 10, 2);
        memcpy(&e.crc32, cd.data() + pos + 16, 4);
        memcpy(&e.comp_size, cd.data() + pos + 20, 4);
        memcpy(&e.uncomp_size, cd.data() + pos + 24, 4);
        uint16_t name_len, extra_len, comment_len;
        memcpy(&name_len, cd.data() + pos + 28, 2);
        memcpy(&extra_len, cd.data() + pos + 30, 2);
        memcpy(&comment_len, cd.data() + pos + 32, 2);
        memcpy(&e.local_offset, cd.data() + pos + 42, 4);
        e.name.assign(cd.data() + pos + 46, name_len);
        out.push_back(e);
        pos += 46 + name_len + extra_len + comment_len;
    }
    return true;
}

// ─────────────────────────────────────────────────────────────────────────
// minimal ELF reader (lib/*.so inventory: class, endianness, machine,
// SONAME via .dynamic, exported JNI symbols via .dynsym)
// ─────────────────────────────────────────────────────────────────────────
struct ElfInfo {
    bool valid = false;
    std::string err;
    int bitness = 0;      // 32 / 64
    std::string machine;  // arch string
    std::string soname;
    std::vector<std::string> jni_exports;   // Java_* exported symbols
    std::vector<std::string> all_exports;   // every defined dynsym name
};

static std::string elf_machine_name(uint16_t m) {
    switch (m) {
        case 0x03: return "x86";
        case 0x3e: return "x86_64";
        case 0x28: return "arm";
        case 0xb7: return "aarch64";
        case 0x08: return "mips";
        default: return "machine_0x" + ([](uint16_t v) {
              char b[8]; snprintf(b, sizeof(b), "%x", v); return std::string(b);
          })(m);
    }
}

static ElfInfo parse_elf(const std::vector<uint8_t>& d) {
    ElfInfo info;
    if (d.size() < 64 || d[0] != 0x7f || d[1] != 'E' || d[2] != 'L' || d[3] != 'F') {
        info.err = "not-elf";
        return info;
    }
    bool is64 = d[4] == 2;
    bool le = d[5] == 1;
    if (!le) { info.err = "big-endian-unsupported"; return info; }
    info.bitness = is64 ? 64 : 32;
    auto rd16 = [&](size_t off) {
        uint16_t v; memcpy(&v, d.data() + off, 2); return v;
    };
    auto rd32 = [&](size_t off) {
        uint32_t v; memcpy(&v, d.data() + off, 4); return v;
    };
    auto rd64 = [&](size_t off) {
        uint64_t v; memcpy(&v, d.data() + off, 8); return v;
    };
    uint16_t machine = rd16(18);
    info.machine = elf_machine_name(machine);

    // Section headers.
    uint64_t shoff; uint16_t shentsize, shnum, shstrndx;
    if (is64) {
        shoff = rd64(0x28);
        shentsize = rd16(0x3a);
        shnum = rd16(0x3c);
        shstrndx = rd16(0x3e);
    } else {
        shoff = rd32(0x20);
        shentsize = rd16(0x2e);
        shnum = rd16(0x30);
        shstrndx = rd16(0x32);
    }
    if (!shoff || !shnum || shoff + (uint64_t)shnum * shentsize > d.size()) {
        info.err = "no-section-headers";  // stripped sections: still valid ELF
        info.valid = true;
        return info;
    }
    auto sh = [&](size_t idx, uint32_t& type, uint64_t& offset, uint64_t& size,
                  uint64_t& link, uint64_t& entsize) -> bool {
        if (idx >= shnum) return false;
        size_t b = shoff + idx * shentsize;
        if (b + shentsize > d.size()) return false;
        if (is64) {
            type = rd32(b + 4);
            offset = rd64(b + 24);
            size = rd64(b + 32);
            link = rd32(b + 40);
            entsize = rd64(b + 56);
        } else {
            type = rd32(b + 4);
            offset = rd32(b + 16);
            size = rd32(b + 20);
            link = rd32(b + 24);
            entsize = rd32(b + 36);
        }
        return true;
    };
    uint32_t t; uint64_t o, s, l, e;
    uint64_t strtab_off = 0, strtab_size = 0;
    if (sh(shstrndx, t, o, s, l, e)) { strtab_off = o; strtab_size = s; }
    auto sec_name = [&](uint32_t name_idx) -> std::string {
        if (!strtab_off || name_idx >= strtab_size) return "";
        size_t p = strtab_off + name_idx;
        if (p >= d.size()) return "";
        return std::string((const char*)d.data() + p);
    };
    uint64_t dynsym_off = 0, dynsym_size = 0, dynsym_entsize = 0, dynsym_link = 0;
    uint64_t dynstr_off = 0, dynstr_size = 0;
    uint64_t dynamic_off = 0, dynamic_size = 0, dynamic_link = 0;
    for (size_t i = 0; i < shnum; i++) {
        uint32_t stype; uint64_t soff, ssize, slink, sentsize;
        if (!sh(i, stype, soff, ssize, slink, sentsize)) continue;
        std::string nm = sec_name(rd32(shoff + i * shentsize));
        if (stype == 11 /*SHT_DYNSYM*/) {
            dynsym_off = soff; dynsym_size = ssize;
            dynsym_entsize = sentsize ? sentsize : (is64 ? 24 : 16);
            dynsym_link = slink;
        } else if (nm == ".dynstr") {
            dynstr_off = soff; dynstr_size = ssize;
        } else if (stype == 6 /*SHT_DYNAMIC*/) {
            dynamic_off = soff; dynamic_size = ssize; dynamic_link = slink;
        }
    }
    if (dynsym_link && dynstr_off == 0) {
        uint32_t lt; uint64_t lo, ls, ll, le2;
        if (sh(dynsym_link, lt, lo, ls, ll, le2)) { dynstr_off = lo; dynstr_size = ls; }
    }
    auto cstr = [&](uint64_t off) -> std::string {
        if (!dynstr_off || off >= dynstr_size) return "";
        size_t p = dynstr_off + off;
        if (p >= d.size()) return "";
        return std::string((const char*)d.data() + p);
    };
    // SONAME via .dynamic DT_SONAME (14).
    if (dynamic_off && dynamic_link) {
        uint32_t dt; uint64_t do2, ds, dl, de;
        if (sh(0, dt, do2, ds, dl, de)) {}  // warm sh lambda bounds check
        size_t n = dynamic_size / (is64 ? 16 : 8);
        for (size_t i = 0; i < n; i++) {
            size_t b = dynamic_off + i * (is64 ? 16 : 8);
            if (b + (is64 ? 16 : 8) > d.size()) break;
            int64_t tag = is64 ? (int64_t)rd64(b) : (int32_t)rd32(b);
            uint64_t val = is64 ? rd64(b + 8) : rd32(b + 4);
            if (tag == 0) break;
            if (tag == 14) { info.soname = cstr(val); break; }
        }
    }
    // Exported dynsym symbols (defined, global/weak).
    if (dynsym_off && dynsym_entsize) {
        size_t n = dynsym_size / dynsym_entsize;
        for (size_t i = 0; i < n; i++) {
            size_t b = dynsym_off + i * dynsym_entsize;
            if (b + dynsym_entsize > d.size()) break;
            uint32_t name_off, shndx;
            uint8_t bind;
            if (is64) {
                name_off = rd32(b);
                bind = d[b + 4];
                shndx = rd16(b + 6);
            } else {
                name_off = rd32(b);
                bind = d[b + 12];
                shndx = rd16(b + 14);
            }
            if (shndx == 0) continue;  // undefined (import) — not an export
            if ((bind & 0xf) != 1 /*GLOBAL*/ && (bind & 0xf) != 2 /*WEAK*/) continue;
            std::string nm = cstr(name_off);
            if (nm.empty()) continue;
            info.all_exports.push_back(nm);
            if (nm.rfind("Java_", 0) == 0) info.jni_exports.push_back(nm);
        }
    }
    info.valid = true;
    return info;
}

// ─────────────────────────────────────────────────────────────────────────
// classification + misc
// ─────────────────────────────────────────────────────────────────────────
static std::string classify_entry(const std::string& name) {
    if (name == "AndroidManifest.xml") return "MANIFEST";
    if (name == "resources.arsc") return "ARSC";
    if (name.rfind("classes", 0) == 0 &&
        name.size() > 4 && name.substr(name.size() - 4) == ".dex")
        return "DEX";
    if (name.rfind("lib/", 0) == 0 && name.size() > 3 &&
        name.substr(name.size() - 3) == ".so")
        return "NATIVE_LIB";
    if (name.rfind("assets/", 0) == 0) return "ASSET";
    if (name.rfind("res/", 0) == 0) return "RES";
    if (name.rfind("META-INF/", 0) == 0) return "META_INF";
    return "OTHER";
}

static std::string media_class(const std::string& name) {
    std::string lower;
    for (char c : name) lower += (char)tolower((unsigned char)c);
    auto ends = [&](const char* s) {
        size_t n = strlen(s);
        return lower.size() > n && lower.substr(lower.size() - n) == s;
    };
    if (ends(".png") || ends(".jpg") || ends(".jpeg") || ends(".webp") ||
        ends(".gif"))
        return "IMAGE_RASTER";
    if (ends(".xml") && lower.find("drawable") != std::string::npos)
        return "IMAGE_VECTOR_XML";
    if (ends(".ttf") || ends(".otf")) return "FONT";
    if (ends(".mp3") || ends(".ogg") || ends(".wav") || ends(".m4a") ||
        ends(".aac") || ends(".flac"))
        return "AUDIO";
    if (ends(".mp4") || ends(".webm") || ends(".3gp")) return "VIDEO";
    if (ends(".glb") || ends(".gltf")) return "MODEL_3D";
    return "";
}

static std::string media_decoder(const std::string& cls) {
    if (cls == "IMAGE_RASTER") return "BitmapFactory/Skia (PNG/JPEG/WebP/GIF)";
    if (cls == "IMAGE_VECTOR_XML") return "VectorDrawableInflater / AXML";
    if (cls == "FONT") return "FreeType/HarfBuzz (Typeface)";
    if (cls == "AUDIO") return "MediaPlayer/SoundPool (mpg123/sndfile)";
    if (cls == "VIDEO") return "MediaPlayer (frontier: object-state stub)";
    if (cls == "MODEL_3D") return "app-owned parser (runtime-invisible)";
    return "";
}

static std::string json_esc_pair(const std::string& k, const std::string& v,
                                 bool comma, const char* pad = "    ") {
    std::string out = pad;
    out += "\"";
    out += jesc(k);
    out += "\": \"";
    out += jesc(v);
    out += "\"";
    if (comma) out += ",";
    out += "\n";
    return out;
}

// minimal prefs-XML scanner: AOSP <map> shape emitted by the runtime:
//   <string name="k">v</string> / <int name="k">3</int> / <boolean ..>
//   <long ..> / <float ..> / <set><string>v</string></set>
struct PrefItem { std::string type, key, value; };
static std::vector<PrefItem> parse_prefs_xml(const std::string& xml) {
    std::vector<PrefItem> out;
    static const char* tags[] = {"string", "int", "boolean", "long", "float"};
    for (const char* tag : tags) {
        std::string open = std::string("<") + tag + " ";
        size_t p = 0;
        while ((p = xml.find(open, p)) != std::string::npos) {
            size_t name_at = xml.find("name=\"", p);
            size_t tag_end = xml.find(">", p);
            if (name_at == std::string::npos || tag_end == std::string::npos ||
                name_at > tag_end)
                break;
            size_t kstart = name_at + 6;
            size_t kend = xml.find("\"", kstart);
            if (kend == std::string::npos || kend > tag_end) break;
            PrefItem it;
            it.type = tag;
            it.key = xml.substr(kstart, kend - kstart);
            bool self_closing = tag_end > 0 && xml[tag_end - 1] == '/';
            if (!self_closing) {
                size_t vstart = tag_end + 1;
                std::string close = std::string("</") + tag + ">";
                size_t vend = xml.find(close, vstart);
                if (vend != std::string::npos)
                    it.value = xml.substr(vstart, vend - vstart);
            } else if (std::string(tag) != "string") {
                // <int name="k" value="3" /> alternate shape
                size_t vattr = xml.find("value=\"", p);
                if (vattr != std::string::npos && vattr < tag_end) {
                    size_t vs = vattr + 7;
                    size_t ve = xml.find("\"", vs);
                    if (ve != std::string::npos && ve < tag_end)
                        it.value = xml.substr(vs, ve - vs);
                }
            }
            out.push_back(it);
            p = tag_end + 1;
        }
    }
    return out;
}

} // namespace gatea
} // namespace miniandroid

namespace miniandroid {
namespace gatea {

// ─────────────────────────────────────────────────────────────────────────
// JSONL sink (full-fidelity machine-readable stream, issue #370 §15/§22)
// ─────────────────────────────────────────────────────────────────────────
struct JsonlSink {
    std::ofstream out;
    bool enabled = false;
    std::string package;
    void line(const std::string& section, const std::string& item_json) {
        if (!enabled) return;
        out << "{\"section\":\"" << jesc(section) << "\",\"package\":\""
            << jesc(package) << "\",\"item\":" << item_json << "}\n";
    }
};

// flat package-record field extraction (record JSON is flat, known shape —
// no JSON parser dependency needed for the scalar fields we read)
static std::string record_string(const std::string& body, const char* key) {
    std::string pat = "\"" + std::string(key) + "\": \"";
    size_t p = body.find(pat);
    if (p == std::string::npos) return "";
    size_t s = p + pat.size();
    size_t e = body.find("\"", s);
    if (e == std::string::npos) return "";
    return body.substr(s, e - s);
}

static std::string record_number(const std::string& body, const char* key) {
    std::string pat = "\"" + std::string(key) + "\": ";
    size_t p = body.find(pat);
    if (p == std::string::npos) return "";
    size_t s = p + pat.size();
    size_t e = s;
    while (e < body.size() && (isdigit((unsigned char)body[e]) || body[e] == '-'))
        e++;
    return body.substr(s, e - s);
}

// ═════════════════════════════════════════════════════════════════════════
// SECTION EMITTERS — each writes a JSON fragment to stdout and JSONL items
// ═════════════════════════════════════════════════════════════════════════

static void emit_identity(std::ostream& os, JsonlSink& jl, const std::string& pkg,
                          const fs::path& base_apk, const std::string& record_body,
                          const apk::ApkInfo& info) {
    bool sha_ok = false;
    std::string live_sha = sha256_file(base_apk.string(), &sha_ok);
    std::string rec_sha = record_string(record_body, "apkSha256");
    os << "    \"identity\": {\n";
    os << json_esc_pair("package", pkg, true);
    os << json_esc_pair("logicalCodePath", "/data/app/" + pkg + "/base.apk", true);
    os << json_esc_pair("hostCodePath", base_apk.string(), true);
    os << json_esc_pair("liveBaseApkSha256", live_sha, true);
    os << json_esc_pair("liveBaseApkSha16", sha16(live_sha), true);
    os << json_esc_pair("recordApkSha256", rec_sha, true);
    os << "      \"shaMatch\": " << ((sha_ok && rec_sha == live_sha) ? "true" : "false")
       << ",\n";
    os << json_esc_pair("versionName",
                        record_string(record_body, "versionName").empty()
                            ? info.version_name
                            : record_string(record_body, "versionName"),
                        true);
    os << "      \"versionCode\": "
       << (record_number(record_body, "versionCode").empty()
               ? std::to_string(info.version_code)
               : record_number(record_body, "versionCode"))
       << ",\n";
    os << json_esc_pair("minSdk",
                        record_string(record_body, "minSdk").empty()
                            ? info.min_sdk_version
                            : record_string(record_body, "minSdk"),
                        true);
    os << json_esc_pair("targetSdk",
                        record_string(record_body, "targetSdk").empty()
                            ? info.target_sdk_version
                            : record_string(record_body, "targetSdk"),
                        true);
    os << json_esc_pair("mainActivity",
                        record_string(record_body, "mainActivity").empty()
                            ? info.main_activity_full
                            : record_string(record_body, "mainActivity"),
                        true);
    os << json_esc_pair("installedAt", record_string(record_body, "installedAt"),
                        true);
    os << json_esc_pair("applicationLabel", info.application_label, true);
    os << json_esc_pair("applicationClass", info.application_name, false);
    os << "    }";
    // JSONL: identity item
    std::ostringstream it;
    it << "{\"package\":\"" << jesc(pkg) << "\",\"liveBaseApkSha256\":\""
       << live_sha << "\",\"shaMatch\":" << (rec_sha == live_sha ? "true" : "false")
       << ",\"versionCode\":" << (record_number(record_body, "versionCode").empty()
                                       ? "0"
                                       : record_number(record_body, "versionCode"))
       << "}";
    jl.line("identity", it.str());
}

static void emit_manifest(std::ostream& os, JsonlSink& jl,
                          const std::vector<uint8_t>& manifest_bytes,
                          const apk::ApkInfo& info) {
    apk::ManifestReader mr;
    auto mi = mr.parse(manifest_bytes);
    os << "    \"manifest\": {\n";
    os << "      \"parseSuccess\": " << (mi.parse_success ? "true" : "false")
       << ",\n";
    if (!mi.parse_success)
        os << json_esc_pair("error", mi.error_message, true);
    os << json_esc_pair("package", mi.package_name, true);
    os << json_esc_pair("versionName", mi.version_name, true);
    os << json_esc_pair("applicationClass", mi.application_name, true);
    os << json_esc_pair("mainActivityFull", mi.main_activity_full, true);
    // components
    os << "      \"activities\": [";
    for (size_t i = 0; i < mi.activities.size(); i++) {
        os << (i ? ", " : "");
        os << "{\"name\":\"" << jesc(mi.activities[i].name)
           << "\",\"main\":" << (mi.activities[i].is_main_activity ? "true" : "false")
           << ",\"launcher\":" << (mi.activities[i].is_launcher ? "true" : "false");
        os << ",\"actions\":[";
        for (size_t a = 0; a < mi.activities[i].actions.size(); a++)
            os << (a ? ", " : "") << "\"" << jesc(mi.activities[i].actions[a]) << "\"";
        os << "]}";
    }
    os << "],\n";
    os << "      \"services\": [";
    for (size_t i = 0; i < mi.services.size(); i++) {
        os << (i ? ", " : "");
        os << "{\"name\":\"" << jesc(mi.services[i].name) << "\",\"actions\":[";
        for (size_t a = 0; a < mi.services[i].actions.size(); a++)
            os << (a ? ", " : "") << "\"" << jesc(mi.services[i].actions[a]) << "\"";
        os << "]}";
    }
    os << "],\n";
    os << "      \"receivers\": [";
    for (size_t i = 0; i < mi.receivers.size(); i++) {
        os << (i ? ", " : "");
        os << "{\"name\":\"" << jesc(mi.receivers[i].name) << "\",\"actions\":[";
        for (size_t a = 0; a < mi.receivers[i].actions.size(); a++)
            os << (a ? ", " : "") << "\"" << jesc(mi.receivers[i].actions[a]) << "\"";
        os << "]}";
    }
    os << "],\n";
    os << "      \"providers\": [";
    for (size_t i = 0; i < mi.providers.size(); i++) {
        os << (i ? ", " : "");
        os << "{\"name\":\"" << jesc(mi.providers[i].name)
           << "\",\"authorities\":\"" << jesc(mi.providers[i].authorities) << "\"}";
    }
    os << "],\n";
    os << "      \"requestedPermissions\": [";
    for (size_t i = 0; i < mi.permissions.size(); i++)
        os << (i ? ", " : "") << "\"" << jesc(mi.permissions[i]) << "\"";
    os << "],\n";
    os << "      \"applicationMetaData\": [";
    for (size_t i = 0; i < mi.application_meta_data.size(); i++) {
        os << (i ? ", " : "");
        os << "{\"name\":\"" << jesc(mi.application_meta_data[i].first)
           << "\",\"value\":\"" << jesc(mi.application_meta_data[i].second) << "\"}";
    }
    os << "],\n";
    os << "      \"usesFeatures\": [";
    for (size_t i = 0; i < mi.uses_features.size(); i++)
        os << (i ? ", " : "") << "\"" << jesc(mi.uses_features[i]) << "\"";
    os << "]\n";
    os << "    }";
    // JSONL: one item per component (machine-readable rows)
    for (const auto& a : mi.activities)
        jl.line("manifest_activity",
                "{\"name\":\"" + jesc(a.name) + "\",\"main\":" +
                    std::string(a.is_main_activity ? "true" : "false") + "}");
    for (const auto& s : mi.services)
        jl.line("manifest_service", "{\"name\":\"" + jesc(s.name) + "\"}");
    for (const auto& r : mi.receivers)
        jl.line("manifest_receiver", "{\"name\":\"" + jesc(r.name) + "\"}");
    for (const auto& p : mi.providers)
        jl.line("manifest_provider",
                "{\"name\":\"" + jesc(p.name) + "\",\"authorities\":\"" +
                    jesc(p.authorities) + "\"}");
    for (const auto& p : mi.permissions)
        jl.line("manifest_permission", "{\"name\":\"" + jesc(p) + "\"}");
}

static void emit_entries(std::ostream& os, JsonlSink& jl, const std::string& apk,
                         const std::vector<ZipEntryMeta>& entries) {
    std::map<std::string, int> by_class;
    for (const auto& e : entries) by_class[classify_entry(e.name)]++;
    os << "    \"entries\": {\n";
    os << "      \"count\": " << entries.size() << ",\n";
    os << "      \"byClass\": {";
    bool first = true;
    for (const auto& [c, n] : by_class) {
        os << (first ? "" : ", ") << "\"" << c << "\": " << n;
        first = false;
    }
    os << "},\n";
    os << "      \"items\": [";
    bool first_item = true;
    for (const auto& e : entries) {
        std::ostringstream it;
        it << "{\"name\":\"" << jesc(e.name) << "\",\"method\":\""
           << (e.method == 0 ? "STORED" : e.method == 8 ? "DEFLATE" : "OTHER")
           << "\",\"methodId\":" << e.method
           << ",\"compSize\":" << e.comp_size << ",\"uncompSize\":" << e.uncomp_size
           << ",\"crc32\":\"" << std::hex << e.crc32 << std::dec << "\",\"class\":\""
           << classify_entry(e.name) << "\"}";
        if (!first_item) os << ",";
        first_item = false;
        os << "\n        " << it.str();
        jl.line("entry", it.str());
    }
    os << (entries.empty() ? "" : "\n      ") << "]\n";
    os << "    }";
}

static void emit_dex(std::ostream& os, JsonlSink& jl, const std::string& apk,
                     apk::ApkParser& parser, const std::vector<std::string>& dex_names,
                     size_t class_detail_cap) {
    os << "    \"dex\": {\n";
    os << "      \"dexCount\": " << dex_names.size() << ",\n";
    os << "      \"files\": [";
    uint32_t total_classes = 0, total_native_methods = 0;
    bool first_file = true;
    for (const auto& dname : dex_names) {
        auto bytes = parser.extract_entry(apk, dname);
        dex::DexParser dp;
        auto rep = bytes.empty() ? dex::DexReport{} : dp.parse_data(bytes, dname);
        if (!first_file) os << ", ";
        first_file = false;
        os << "\n        {\"name\":\"" << jesc(dname) << "\",\"valid\":"
           << (rep.is_valid ? "true" : "false");
        if (rep.is_valid) {
            total_classes += rep.classes_count;
            os << ",\"strings\":" << rep.strings_count << ",\"types\":"
               << rep.types_count << ",\"prototypes\":" << rep.prototypes_count
               << ",\"fields\":" << rep.fields_count << ",\"methods\":"
               << rep.methods_count << ",\"classes\":" << rep.classes_count;
            // per-class detail (bounded): name, flags, super, native methods
            uint32_t native_methods = 0;
            size_t shown = 0;
            os << ",\"nativeMethods\":";
            std::ostringstream ncls;
            for (const auto& cls : rep.classes) {
                for (const auto& m : cls.all_methods())
                    if (m.access_flags & 0x100) native_methods++;
            }
            total_native_methods += native_methods;
            os << native_methods;
            os << ",\"classSample\":[";
            for (const auto& cls : rep.classes) {
                if (shown >= class_detail_cap) break;
                if (shown) ncls << ", ";
                ncls << "{\"name\":\"" << jesc(cls.name) << "\",\"flags\":\"0x"
                     << std::hex << cls.access_flags << std::dec << "\",\"super\":\""
                     << jesc(cls.superclass_name) << "\"}";
                shown++;
            }
            os << ncls.str() << "]";
        } else {
            os << ",\"error\":\"" << jesc(rep.validation_error) << "\"";
        }
        os << "}";
        jl.line("dex_file",
                "{\"name\":\"" + jesc(dname) + "\",\"valid\":" +
                    std::string(rep.is_valid ? "true" : "false") +
                    ",\"classes\":" + std::to_string(rep.classes_count) + "}");
    }
    os << (first_file ? "" : "\n      ") << "],\n";
    os << "      \"totalClasses\": " << total_classes << ",\n";
    os << "      \"totalNativeMethods\": " << total_native_methods << "\n";
    os << "    }";
}

static void emit_resources(std::ostream& os, JsonlSink& jl,
                           const std::vector<uint8_t>& arsc_bytes) {
    resources::ArscParser arsc;
    bool parsed = arsc.parse(arsc_bytes);
    os << "    \"resources\": {\n";
    os << "      \"arscPresent\": true,\n";
    os << "      \"arscParseSuccess\": " << (parsed ? "true" : "false") << ",\n";
    if (!parsed)
        os << json_esc_pair("arscError", arsc.last_error(), true);
    if (parsed) {
        auto inv = arsc.inventory();
        size_t total_entries = 0;
        for (const auto& p : inv)
            for (const auto& t : p.types) total_entries += t.entries.size();
        os << "      \"packages\": " << inv.size() << ",\n";
        os << "      \"totalEntries\": " << total_entries << ",\n";
        os << "      \"typeSummary\": {";
        std::map<std::string, size_t> type_counts;
        for (const auto& p : inv)
            for (const auto& t : p.types)
                type_counts[t.type_name] += t.entries.size();
        bool first = true;
        for (const auto& [t, n] : type_counts) {
            os << (first ? "" : ", ") << "\"" << jesc(t) << "\": " << n;
            first = false;
        }
        os << "},\n";
        // full inventory rows (JSONL) + bounded sample on stdout
        os << "      \"sample\": [";
        size_t shown = 0;
        for (const auto& p : inv) {
            for (const auto& t : p.types) {
                for (const auto& e : t.entries) {
                    std::ostringstream it;
                    it << "{\"pkg\":\"" << jesc(p.name) << "\",\"type\":\""
                       << jesc(t.type_name) << "\",\"name\":\"" << jesc(e.name)
                       << "\",\"id\":\"0x" << std::hex << e.id << std::dec
                       << "\",\"configs\":" << e.config_buckets << "}";
                    jl.line("resource", it.str());
                    if (shown < 40) {
                        if (shown) os << ", ";
                        os << it.str();
                    }
                    shown++;
                }
            }
        }
        os << "]\n";
    }
    os << "    }";
}

static void emit_assets(std::ostream& os, JsonlSink& jl,
                        const std::vector<ZipEntryMeta>& entries,
                        apk::ApkParser& parser, const std::string& apk) {
    size_t count = 0;
    unsigned long long total_bytes = 0;
    os << "    \"assets\": {\n";
    os << "      \"items\": [";
    bool first = true;
    for (const auto& e : entries) {
        if (e.name.rfind("assets/", 0) != 0 || e.name.size() <= 7) continue;
        count++;
        total_bytes += e.uncomp_size;
        std::ostringstream it;
        it << "{\"entry\":\"" << jesc(e.name) << "\",\"method\":\""
           << (e.method == 0 ? "STORED" : e.method == 8 ? "DEFLATE" : "OTHER")
           << "\",\"size\":" << e.uncomp_size << "}";
        if (!first) os << ",";
        first = false;
        os << "\n        " << it.str();
        jl.line("asset", it.str());
    }
    os << (count ? "\n      " : "") << "],\n";
    os << "      \"count\": " << count << ",\n";
    os << "      \"uncompressedTotalBytes\": " << total_bytes << "\n";
    os << "    }";
}

static void emit_libs(std::ostream& os, JsonlSink& jl,
                      const std::vector<ZipEntryMeta>& entries,
                      apk::ApkParser& parser, const std::string& apk) {
    std::set<std::string> abis;
    size_t so_count = 0;
    os << "    \"nativeLibs\": {\n";
    os << "      \"items\": [";
    bool first = true;
    for (const auto& e : entries) {
        if (e.name.rfind("lib/", 0) != 0) continue;
        std::string rest = e.name.substr(4);
        auto slash = rest.find('/');
        if (slash == std::string::npos) continue;
        std::string abi = rest.substr(0, slash);
        if (rest.size() <= slash + 1 || rest.substr(rest.size() - 3) != ".so")
            continue;
        abis.insert(abi);
        so_count++;
        auto bytes = parser.extract_entry(apk, e.name);
        bool sha_ok = false;
        std::string sha = sha256_bytes(bytes.data(), bytes.size(), &sha_ok);
        ElfInfo elf = bytes.empty() ? ElfInfo{} : parse_elf(bytes);
        std::ostringstream it;
        it << "{\"entry\":\"" << jesc(e.name) << "\",\"abi\":\"" << jesc(abi)
           << "\",\"size\":" << e.uncomp_size << ",\"sha256\":\"" << sha << "\""
           << ",\"elfValid\":" << (elf.valid ? "true" : "false")
           << ",\"elfBitness\":" << elf.bitness
           << ",\"elfMachine\":\"" << jesc(elf.machine) << "\""
           << ",\"soname\":\"" << jesc(elf.soname) << "\""
           << ",\"jniExports\":" << elf.jni_exports.size()
           << ",\"allExports\":" << elf.all_exports.size() << "}";
        if (!first) os << ",";
        first = false;
        os << "\n        " << it.str();
        jl.line("native_lib", it.str());
        for (const auto& s : elf.jni_exports)
            jl.line("native_lib_symbol",
                    "{\"lib\":\"" + jesc(e.name) + "\",\"symbol\":\"" + jesc(s) +
                        "\"}");
    }
    os << (so_count ? "\n      " : "") << "],\n";
    os << "      \"soCount\": " << so_count << ",\n";
    os << "      \"abis\": [";
    bool first_abi = true;
    for (const auto& a : abis) {
        os << (first_abi ? "" : ", ") << "\"" << jesc(a) << "\"";
        first_abi = false;
    }
    os << "]\n";
    os << "    }";
}

static void emit_media(std::ostream& os, JsonlSink& jl,
                       const std::vector<ZipEntryMeta>& entries) {
    std::map<std::string, int> counts;
    os << "    \"media\": {\n";
    os << "      \"items\": [";
    bool first = true;
    for (const auto& e : entries) {
        std::string cls = media_class(e.name);
        if (cls.empty()) continue;
        counts[cls]++;
        std::ostringstream it;
        it << "{\"entry\":\"" << jesc(e.name) << "\",\"class\":\"" << cls
           << "\",\"size\":" << e.uncomp_size
           << ",\"method\":\"" << (e.method == 0 ? "STORED" : "DEFLATE")
           << "\""
           << ",\"expectedDecoder\":\"" << jesc(media_decoder(cls)) << "\"}";
        if (!first) os << ",";
        first = false;
        os << "\n        " << it.str();
        jl.line("media", it.str());
    }
    os << (first ? "" : "\n      ") << "],\n";
    os << "      \"byClass\": {";
    bool fc = true;
    for (const auto& [c, n] : counts) {
        os << (fc ? "" : ", ") << "\"" << c << "\": " << n;
        fc = false;
    }
    os << "}\n";
    os << "    }";
}


// ─────────────────────────────────────────────────────────────────────────
// data / external / dbs / prefs sections (physical backing inventory)
// ─────────────────────────────────────────────────────────────────────────
struct FileRow {
    std::string logical;   // Android-logical path (e.g. /data/data/<pkg>/files/x)
    std::string physical;  // host backing path
    unsigned long long size = 0;
    std::string sha256;
    bool sha_ok = false;
};

static void walk_tree(const fs::path& root, const std::string& logical_prefix,
                      std::vector<FileRow>& out, size_t cap = 5000) {
    std::error_code ec;
    if (!fs::exists(root, ec)) return;
    for (auto it = fs::recursive_directory_iterator(
             root, fs::directory_options::skip_permission_denied, ec);
         it != fs::recursive_directory_iterator(); it.increment(ec)) {
        if (out.size() >= cap) break;
        std::error_code fe;
        if (it->is_directory(fe)) continue;
        if (!it->is_regular_file(fe)) continue;
        FileRow row;
        row.physical = it->path().string();
        row.logical = logical_prefix +
                      it->path().string().substr(root.string().size());
        row.size = it->file_size(fe);
        row.sha256 = sha256_file(row.physical, &row.sha_ok);
        out.push_back(row);
    }
    std::sort(out.begin(), out.end(),
              [](const FileRow& a, const FileRow& b) { return a.logical < b.logical; });
}

static void emit_file_rows(std::ostream& os, JsonlSink& jl,
                           const std::string& section_name,
                           const std::vector<FileRow>& rows,
                           const std::string& provenance_class) {
    os << "    \"" << section_name << "\": {\n";
    os << "      \"exists\": " << (rows.empty() ? "false" : "true") << ",\n";
    os << "      \"count\": " << rows.size() << ",\n";
    os << "      \"items\": [";
    bool first = true;
    for (const auto& r : rows) {
        std::ostringstream it;
        it << "{\"logical\":\"" << jesc(r.logical) << "\",\"physical\":\""
           << jesc(r.physical) << "\",\"size\":" << r.size << ",\"sha256\":\""
           << r.sha256 << "\",\"provenance\":\"" << provenance_class << "\"}";
        if (!first) os << ",";
        first = false;
        os << "\n        " << it.str();
        jl.line(section_name, it.str());
    }
    os << (rows.empty() ? "" : "\n      ") << "]\n";
    os << "    }";
}

struct DbRow {
    std::string logical, physical, name;
    unsigned long long size = 0;
    std::string sha256;
    bool valid_header = false;
    bool has_wal = false, has_shm = false, has_journal = false;
};

static std::vector<DbRow> inventory_databases(const fs::path& db_dir,
                                              const std::string& logical_prefix) {
    std::vector<DbRow> out;
    std::error_code ec;
    if (!fs::exists(db_dir, ec)) return out;
    for (auto it = fs::directory_iterator(db_dir, ec);
         it != fs::directory_iterator(); ++it) {
        std::error_code fe;
        if (!it->is_regular_file(fe)) continue;
        std::string fn = it->path().filename().string();
        std::string base = fn;
        std::string sidecar;
        for (const char* sfx : {"-wal", "-shm", "-journal"}) {
            size_t n = strlen(sfx);
            if (base.size() > n && base.compare(base.size() - n, n, sfx) == 0) {
                sidecar = sfx + 1;
                base = base.substr(0, base.size() - n);
                break;
            }
        }
        DbRow row;
        row.physical = it->path().string();
        row.logical = logical_prefix + fn;
        row.name = base;
        row.size = it->file_size(fe);
        if (sidecar.empty()) {
            // main db: header magic + sidecar detection
            std::ifstream in(row.physical, std::ios::binary);
            char hdr[16] = {0};
            in.read(hdr, 16);
            in.close();
            row.valid_header = strncmp(hdr, "SQLite format 3", 15) == 0;
            row.has_wal = fs::exists(it->path().string() + "-wal");
            row.has_shm = fs::exists(it->path().string() + "-shm");
            row.has_journal = fs::exists(it->path().string() + "-journal");
            bool sha_ok = false;
            row.sha256 = sha256_file(row.physical, &sha_ok);
        } else {
            row.valid_header = false;
        }
        out.push_back(row);
    }
    std::sort(out.begin(), out.end(),
              [](const DbRow& a, const DbRow& b) { return a.logical < b.logical; });
    return out;
}

static void os_dbs(std::ostream& os, JsonlSink& jl, const std::vector<DbRow>& dbs) {
    os << "    \"databases\": {\n";
    os << "      \"exists\": " << (dbs.empty() ? "false" : "true") << ",\n";
    os << "      \"count\": " << dbs.size() << ",\n";
    os << "      \"items\": [";
    bool first = true;
    for (const auto& d : dbs) {
        std::ostringstream it;
        it << "{\"logical\":\"" << jesc(d.logical) << "\",\"name\":\"" << jesc(d.name)
           << "\",\"size\":" << d.size << ",\"sha256\":\"" << d.sha256
           << "\",\"sqliteHeaderValid\":" << (d.valid_header ? "true" : "false")
           << ",\"wal\":" << (d.has_wal ? "true" : "false")
           << ",\"shm\":" << (d.has_shm ? "true" : "false")
           << ",\"journal\":" << (d.has_journal ? "true" : "false") << "}";
        if (!first) os << ",";
        first = false;
        os << "\n        " << it.str();
        jl.line("database", it.str());
    }
    os << (dbs.empty() ? "" : "\n      ") << "]\n";
    os << "    }";
}


static void emit_prefs(std::ostream& os, JsonlSink& jl, const fs::path& prefs_dir,
                       const std::string& logical_prefix) {
    os << "    \"preferences\": {\n";
    os << "      \"exists\": " << (fs::exists(prefs_dir) ? "true" : "false") << ",\n";
    os << "      \"files\": [";
    bool first = true;
    std::error_code ec;
    if (fs::exists(prefs_dir, ec)) {
        for (auto it = fs::directory_iterator(prefs_dir, ec);
             it != fs::directory_iterator(); ++it) {
            std::error_code fe;
            if (!it->is_regular_file(fe)) continue;
            std::ifstream in(it->path().string(), std::ios::binary);
            std::stringstream ss;
            ss << in.rdbuf();
            std::string xml = ss.str();
            auto items = parse_prefs_xml(xml);
            std::ostringstream it_json;
            it_json << "{\"file\":\"" << jesc(logical_prefix + it->path().filename().string())
                    << "\",\"size\":" << it->file_size(fe) << ",\"keys\":" << items.size()
                    << ",\"entries\":[";
            for (size_t i = 0; i < items.size(); i++) {
                if (i) it_json << ", ";
                it_json << "{\"type\":\"" << items[i].type << "\",\"key\":\""
                        << jesc(items[i].key) << "\",\"value\":\""
                        << jesc(items[i].value) << "\"}";
            }
            it_json << "]}";
            if (!first) os << ",";
            first = false;
            os << "\n        " << it_json.str();
            jl.line("preference_file", it_json.str());
        }
    }
    os << (first ? "" : "\n      ") << "]\n";
    os << "    }";
}

static void emit_provenance(std::ostream& os, JsonlSink& jl, const std::string& pkg,
                            const std::string& record_body, const fs::path& base_apk,
                            const std::string& mode) {
    bool sha_ok = false;
    std::string live_sha = sha256_file(base_apk.string(), &sha_ok);
    os << "    \"provenance\": {\n";
    os << "      \"graph\": [\n";
    auto edge = [&](const char* from, const char* to, const char* label,
                    const std::string& detail, bool comma) {
        std::ostringstream it;
        it << "{\"from\":\"" << from << "\",\"to\":\"" << to << "\",\"label\":\""
           << label << "\",\"detail\":\"" << jesc(detail) << "\"}";
        os << "        " << it.str() << (comma ? "," : "") << "\n";
        jl.line("provenance_edge", it.str());
    };
    edge("SOURCE_APK", "INSTALL", "install (F-NEW-231 pkgstore)",
         "apkSha256=" + record_string(record_body, "apkSha256") + " at " +
             record_string(record_body, "installedAt"),
         true);
    edge("INSTALL", "INSTALLED_BASE_APK", "commit copy+record",
         base_apk.string() + " sha=" + live_sha, true);
    edge("INSTALLED_BASE_APK", "MANIFEST", "AXML parse",
         "AndroidManifest.xml -> components/permissions/meta-data", true);
    edge("INSTALLED_BASE_APK", "DEX", "classes*.dex",
         "class/method/field inventory + native methods", true);
    edge("INSTALLED_BASE_APK", "RESOURCES", "resources.arsc",
         "package/type/name inventory + configs", true);
    edge("INSTALLED_BASE_APK", "ASSETS", "assets/**",
         "ZIP entries (stored/deflate)", true);
    edge("INSTALLED_BASE_APK", "LIBS", "lib/<abi>/*.so",
         "ELF/ABI/SONAME/JNI symbols", true);
    edge("INSTALLED_BASE_APK", "APP_DATA", "sandbox trees",
         "data/data/<pkg> + storage/emulated/0/Android/{data,media,obb}/" + pkg,
         false);
    os << "      ],\n";
    os << json_esc_pair("mode", mode, true);
    os << json_esc_pair("package", pkg, true);
    os << json_esc_pair("sourceApkSha256", record_string(record_body, "apkSha256"),
                        true);
    os << json_esc_pair("installedBaseApkSha256", live_sha, true);
    os << json_esc_pair("note",
                        "SOURCE_APK visibility is install-time only; the "
                        "installed identity is package+data-root. Provenance "
                        "classes: INSTALLED_APK, APP_DATA_FILE, "
                        "EXTERNAL_APP_FILE, RESOURCE, GENERATED_RUNTIME_FILE, "
                        "DEVICE_NODE, OTHER.",
                        false);
    os << "    }";
}

// ═════════════════════════════════════════════════════════════════════════
// cmd_pkg_inspect — the GATE A inspection entry point
// ═════════════════════════════════════════════════════════════════════════
int cmd_pkg_inspect(const InspectRequest& req) {
    std::string apk_path;
    std::string pkg = req.package;
    std::string record_body;
    std::string mode;

    if (!req.apk_path.empty()) {
        // DIRECT-APK MODE: inspect an APK without the package store.
        apk_path = req.apk_path;
        mode = "DIRECT_APK";
        if (pkg.empty()) {
            apk::ApkParser p0;
            auto i0 = p0.parse(apk_path);
            pkg = i0.package_name;
        }
    } else {
        if (req.package.empty() || req.data_root.empty()) {
            std::cerr << "[ERROR] pkginspect requires --package <pkg> --data-root "
                         "<dir> (or --apk <path>)\n";
            return 1;
        }
        mode = "INSTALLED_STORE";
        auto base_apk =
            fs::path(req.data_root) / "data" / "app" / req.package / "base.apk";
        std::error_code ec;
        if (!fs::exists(base_apk, ec)) {
            // AOSP PackageManager.NAME_NOT_FOUND law: loud failure, no fake
            // partial output.
            std::cerr << "[ERROR] Package not installed: " << req.package
                      << " (looked for " << base_apk.string() << ")\n";
            return 1;
        }
        apk_path = base_apk.string();
        std::ifstream rec_in(
            (fs::path(req.data_root) / "data" / "app" / req.package / "package.json")
                .string());
        if (rec_in) {
            std::stringstream ss;
            ss << rec_in.rdbuf();
            record_body = ss.str();
        }
    }

    // Section filter.
    std::set<std::string> want;
    if (req.what == "all") {
        for (const char* s : {"identity", "manifest", "entries", "dex", "resources",
                              "assets", "libs", "media", "data", "external", "dbs",
                              "prefs", "provenance"})
            want.insert(s);
    } else {
        std::string cur;
        std::istringstream ss(req.what);
        while (std::getline(ss, cur, ',')) want.insert(cur);
    }

    JsonlSink jl;
    if (!req.jsonl_out.empty()) {
        jl.out.open(req.jsonl_out, std::ios::binary | std::ios::trunc);
        jl.enabled = (bool)jl.out;
        jl.package = pkg;
        if (!jl.enabled)
            std::cerr << "[WARN] JSONL output not openable: " << req.jsonl_out << "\n";
    }

    // Parse the APK once.
    apk::ApkParser parser;
    parser.set_verbose(req.verbose);
    auto info = parser.parse(apk_path);
    if (!info.is_valid) {
        std::cerr << "[ERROR] APK parse failed: " << info.validation_error << "\n";
        return 1;
    }
    if (pkg.empty()) pkg = info.package_name;

    // ZIP central directory.
    std::vector<ZipEntryMeta> entries;
    std::string zip_err;
    bool zip_ok = read_zip_central_directory(apk_path, entries, zip_err);

    std::cout << "{\n";
    std::cout << "  \"inspect\": \"INSTALL_ENVIRONMENT_INSPECTION\",\n";
    std::cout << "  \"gate\": \"A\",\n";
    std::cout << "  \"mode\": \"" << mode << "\",\n";
    std::cout << "  \"package\": \"" << jesc(pkg) << "\",\n";
    std::cout << "  \"apkPath\": \"" << jesc(apk_path) << "\",\n";
    std::cout << "  \"sections\": {";

    bool emitted_any = false;
    auto comma = [&]() {
        if (emitted_any) std::cout << ",";
        emitted_any = true;
    };

    fs::path pkg_data_dir, ext_root;
    if (mode == "INSTALLED_STORE") {
        pkg_data_dir = fs::path(req.data_root) / "data" / "data" / req.package;
        ext_root = fs::path(req.data_root) / "storage" / "emulated" / "0" / "Android";
    }

    if (want.count("identity")) {
        comma();
        std::cout << "\n";
        emit_identity(std::cout, jl, pkg, apk_path, record_body, info);
    }
    if (want.count("manifest")) {
        auto manifest_bytes = parser.extract_entry(apk_path, "AndroidManifest.xml");
        if (!manifest_bytes.empty()) {
            comma();
            std::cout << "\n";
            emit_manifest(std::cout, jl, manifest_bytes, info);
        } else {
            std::cerr << "[WARN] AndroidManifest.xml not extractable\n";
        }
    }
    if (want.count("entries")) {
        comma();
        std::cout << "\n";
        if (zip_ok) emit_entries(std::cout, jl, apk_path, entries);
        else std::cout << "    \"entries\": {\"error\": \"" << jesc(zip_err) << "\"}";
    }
    if (want.count("dex")) {
        comma();
        std::cout << "\n";
        std::vector<std::string> dex_names;
        for (const auto& e : entries)
            if (classify_entry(e.name) == "DEX") dex_names.push_back(e.name);
        emit_dex(std::cout, jl, apk_path, parser, dex_names, 40);
    }
    if (want.count("resources")) {
        auto arsc_bytes = parser.extract_entry(apk_path, "resources.arsc");
        comma();
        std::cout << "\n";
        if (!arsc_bytes.empty()) emit_resources(std::cout, jl, arsc_bytes);
        else std::cout << "    \"resources\": {\"arscPresent\": false}";
    }
    if (want.count("assets")) {
        comma();
        std::cout << "\n";
        emit_assets(std::cout, jl, entries, parser, apk_path);
    }
    if (want.count("libs")) {
        comma();
        std::cout << "\n";
        emit_libs(std::cout, jl, entries, parser, apk_path);
    }
    if (want.count("media")) {
        comma();
        std::cout << "\n";
        emit_media(std::cout, jl, entries);
    }
    if (mode == "INSTALLED_STORE") {
        if (want.count("data")) {
            comma();
            std::cout << "\n";
            std::vector<FileRow> rows;
            walk_tree(pkg_data_dir, "/data/data/" + req.package, rows);
            emit_file_rows(std::cout, jl, "dataTree", rows, "APP_DATA_FILE");
        }
        if (want.count("external")) {
            comma();
            std::cout << "\n";
            std::vector<FileRow> rows;
            for (const char* fam : {"data", "media", "obb"})
                walk_tree(ext_root / fam / req.package,
                          "/storage/emulated/0/Android/" + std::string(fam) + "/" +
                              req.package,
                          rows);
            emit_file_rows(std::cout, jl, "externalTree", rows, "EXTERNAL_APP_FILE");
        }
        if (want.count("dbs")) {
            comma();
            std::cout << "\n";
            auto dbs = inventory_databases(pkg_data_dir / "databases",
                                           "/data/data/" + req.package + "/databases/");
            os_dbs(std::cout, jl, dbs);
        }
        if (want.count("prefs")) {
            comma();
            std::cout << "\n";
            emit_prefs(std::cout, jl, pkg_data_dir / "shared_prefs",
                       "/data/data/" + req.package + "/shared_prefs/");
        }
    }
    if (want.count("provenance")) {
        comma();
        std::cout << "\n";
        emit_provenance(std::cout, jl, pkg, record_body, apk_path, mode);
    }

    std::cout << (emitted_any ? "\n  " : "") << "}\n";
    std::cout << "}\n";
    return 0;
}

bool zip_contains_entry(const std::string& apk, const std::string& entry,
                        bool* stored) {
    if (stored) *stored = false;
    std::vector<ZipEntryMeta> entries;
    std::string err;
    if (!read_zip_central_directory(apk, entries, err)) return false;
    for (const auto& e : entries) {
        if (e.name == entry) {
            if (stored) *stored = (e.method == 0);
            return true;
        }
    }
    return false;
}

} // namespace gatea
} // namespace miniandroid
