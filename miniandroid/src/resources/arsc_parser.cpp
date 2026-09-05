/*
 * UNIFIED_007 — ARSC Parser implementation (P0)
 * See arsc_parser.h for design. Zero-dependency binary reader.
 */
#include "arsc_parser.h"
#include "string_pool.h"  // FIND-REUSE-004: the ONE ResStringPool decoder

namespace miniandroid {
namespace resources {

// ---------------------------------------------------------------------------
// Little-endian readers
// ---------------------------------------------------------------------------
static inline uint16_t rd16(const uint8_t* p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static inline uint32_t rd32(const uint8_t* p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

// Decode a COMPLEX_MANTISSA — AOSP TypedValue.complexToFloat (authoritative,
// verified against platform_frameworks_base TypedValue.java):
//   value = (data & (MANTISSA_MASK << MANTISSA_SHIFT)) * RADIX_MULTS[(data>>4)&3]
//   MANTISSA_MASK=0xFFFFFF, MANTISSA_SHIFT=8 → MANTISSA_MULT = 2^-8
//   UNIT = data & 0xF (COMPLEX_UNIT_SHIFT = 0)
float complex_to_float(uint32_t data) {
    static const float MANTISSA_MULT = 1.0f / (1 << 8);
    static const float RADIX_MULTS[] = {
        1.0f * MANTISSA_MULT,
        1.0f / (1 << 7)  * MANTISSA_MULT,
        1.0f / (1 << 15) * MANTISSA_MULT,
        1.0f / (1 << 23) * MANTISSA_MULT,
    };
    uint32_t mantissa = data & 0xFFFFFF00u;
    // sign-extend: mantissa is a signed 24-bit value in bits 8..31
    int32_t signed_m = (int32_t)mantissa;
    return signed_m * RADIX_MULTS[(data >> 4) & 3];
}

// ---------------------------------------------------------------------------
// String pool — FIND-REUSE-004: the parse itself lives ONCE in
// ResStringPool (string_pool.cpp); this wrapper only adapts the Pool type.
// ---------------------------------------------------------------------------
bool ArscParser::parse_string_pool(const uint8_t* base, size_t avail, size_t chunk_offset, Pool& out) {
    if (chunk_offset > avail) { last_error_ = "string pool: offset past data"; return false; }
    ResStringPool pool;
    size_t consumed = 0;
    std::string err;
    if (!pool.parse(base + chunk_offset, avail - chunk_offset, consumed, &err)) {
        last_error_ = "string pool: " + err;
        return false;
    }
    out.utf8 = pool.utf8_pool;
    out.strings = std::move(pool.strings);
    return true;
}

// ---------------------------------------------------------------------------
// Config → human string (subset of AOSP ResTable_config)
// ---------------------------------------------------------------------------
std::string ArscParser::config_to_string(const uint8_t* cfg, size_t /*cfg_size*/) {
    if (!cfg) return "";
    uint32_t size = rd32(cfg);
    std::string out;
    auto add = [&](const char* q) { if (!out.empty()) out += "-"; out += q; };
    // language[8..9], country[10..11] (2-byte ISO, possibly unicode pack suffix)
    if (size >= 12) {
        char lang[3] = {(char)cfg[8], (char)cfg[9], 0};
        char country[3] = {(char)cfg[10], (char)cfg[11], 0};
        if (cfg[8] || cfg[9]) add(lang);
        if (cfg[10] || cfg[11]) { out += "-r"; out += country; }
    }
    if (size >= 16) {
        uint8_t orientation = cfg[12], touchscreen = cfg[13], density = cfg[14];
        if (orientation == 1) add("port");
        else if (orientation == 2) add("land");
        (void)touchscreen;
        if (density) {
            out += "-";
            out += std::to_string(density == 0xFF ? 65535 : density);
            out += "dpi";
        }
    }
    if (size >= 20) {
        uint8_t keyboard = cfg[15], navigation = cfg[16], input_flags = cfg[17];
        (void)keyboard; (void)navigation; (void)input_flags;
        uint16_t screen_w = rd16(cfg + 18), screen_h = rd16(cfg + 20);
        if (screen_w || screen_h) { out += "-"; out += std::to_string(screen_w) + "x" + std::to_string(screen_h); }
    }
    if (size >= 28) {
        uint16_t sdk = rd16(cfg + 26);
        (void)sdk;
        uint8_t screen_layout = cfg[28];
        // smallest width dp
        if (size >= 32) {
            uint16_t sw = rd16(cfg + 30);
            if (sw) { out += "-sw" + std::to_string(sw) + "dp"; }
        }
        if (size >= 36) {
            uint16_t wdp = rd16(cfg + 32), hdp = rd16(cfg + 34);
            if (wdp) out += "-w" + std::to_string(wdp) + "dp";
            if (hdp) out += "-h" + std::to_string(hdp) + "dp";
        }
        (void)screen_layout;
    }
    return out;
}

// ---------------------------------------------------------------------------
// Res_value decode
// ---------------------------------------------------------------------------
bool ArscParser::decode_res_value(const uint8_t* p, size_t avail, const Pool& /*global*/,
                                  const Package& pkg, ResValue& out) {
    if (avail < 8) { return false; }
    uint16_t vsize = rd16(p);
    uint8_t res0 = p[2];
    uint8_t dtype = p[3];
    uint32_t ddata = rd32(p + 4);
    if (vsize < 8 || res0 != 0) { /* tolerate */ }
    out.type = (DataType)dtype;
    out.data = ddata;
    switch ((DataType)dtype) {
        case DataType::STRING: {
            const std::string* s = pkg.key_strings.get(ddata);  // placeholder; real table uses global pool
            (void)s;
            break;
        }
        case DataType::DIMENSION: {
            out.dim_value = complex_to_float(ddata);
            out.dim_unit = (uint8_t)(ddata & 0xF);   // COMPLEX_UNIT_SHIFT = 0
            break;
        }
        case DataType::REFERENCE:
        case DataType::ATTRIBUTE:
        case DataType::DYNAMIC_REFERENCE:
            out.ref_id = ddata;
            break;
        default: break;
    }
    return true;
}

// ---------------------------------------------------------------------------
// Type chunk (0x0201)
// ---------------------------------------------------------------------------
bool ArscParser::parse_type_chunk(const uint8_t* base, size_t avail, Package& pkg,
                                  size_t chunk_offset, size_t chunk_size) {
    if (chunk_offset + 20 > avail) { last_error_ = "type: truncated"; return false; }
    const uint8_t* p = base + chunk_offset;
    uint16_t header_size = rd16(p + 2);
    uint8_t  type_id = p[8];
    uint8_t  res0 = p[9];
    uint8_t  flags = p[10];
    uint32_t entry_count = rd32(p + 12);
    uint32_t entries_start = rd32(p + 16);
    uint32_t config_size = rd32(p + 20);
    (void)res0;

    if (chunk_offset + chunk_size > avail) { last_error_ = "type: overruns"; return false; }
    if (header_size < 20) { last_error_ = "type: bad header"; return false; }

    TypeChunk tc;
    tc.type_id = type_id;
    tc.entry_count = entry_count;
    tc.config_desc = config_to_string(p + 20, config_size);
    const uint8_t* cfg = p + 20;
    // CAMPAIGN 009 §6: parse the full AOSP ResTable_config for this bucket
    {
        size_t cfg_off = chunk_offset + 20;
        if (config_size >= 4 && cfg_off < avail) {
            size_t cfg_avail = std::min((size_t)config_size, avail - cfg_off);
            tc.config = ResTableConfig::from_bytes(cfg, cfg_avail);
            tc.has_config = tc.config.size != 0;
        }
    }

    if (flags & TYPE_FLAG_SPARSE) {
        // Sparse entries: header extended by 4 bytes; offsets are
        // ResTable_sparseTypeEntry pairs {u16 idx, u32le 24-bit offset<<2}
        if (header_size < 24) { last_error_ = "type: sparse bad header"; return false; }
        uint16_t off16 = rd16(p + 22);
        (void)off16;
        const uint8_t* sp = p + header_size;
        for (uint32_t i = 0; i < entry_count; i++) {
            if ((size_t)(sp - base) + 4 > avail) return false;
            uint16_t idx = rd16(sp);
            uint16_t off_field = rd16(sp + 2);
            uint32_t pos = ((uint32_t)off_field) << 2;
            tc.entry_offsets.push_back((int32_t)idx);
            tc.entry_positions.push_back(entries_start + pos);
            sp += 4;
        }
        stats_.entry_count += entry_count;
    } else {
        const uint32_t* offs = (const uint32_t*)(p + header_size);
        for (uint32_t i = 0; i < entry_count; i++) {
            uint32_t o = offs[i];
            tc.entry_offsets.push_back(o == NO_ENTRY ? -1 : (int32_t)i);
            tc.entry_positions.push_back(entries_start + (o == NO_ENTRY ? 0 : o));
        }
        uint32_t present = 0;
        for (uint32_t i = 0; i < entry_count; i++) if (tc.entry_offsets[i] >= 0) present++;
        stats_.entry_count += present;
    }

    // Parse entries now (need parent package for pools)
    // NOTE: values referencing strings use the GLOBAL table string pool.
    for (uint32_t i = 0; i < entry_count; i++) {
        if (tc.entry_offsets[i] < 0) continue;
        size_t ep = chunk_offset + tc.entry_positions[i];
        if (ep + 8 > avail) continue;
        const uint8_t* e = base + ep;
        uint16_t esize = rd16(e);
        uint16_t eflags = rd16(e + 2);
        uint32_t key_idx = rd32(e + 4);
        ArscEntry entry;
        entry.package_id = pkg.id;
        entry.type_index = type_id;
        entry.entry_index = i;
        entry.is_complex = (eflags & ENTRY_FLAG_COMPLEX) != 0;
        entry.config_desc = tc.config_desc;
        entry.config = tc.config;          // CAMPAIGN 009 §6
        entry.has_config = tc.has_config;
        const std::string* key = pkg.key_strings.get(key_idx);
        if (key) entry.name = *key;
        // value
        size_t vp = ep + esize;
        // For simple entries esize==8 and Res_value follows.
        // For complex (map) entries, size field is 8 + parent + count header.
        if (!entry.is_complex) {
            ResValue v;
            if (decode_res_value(base + vp, avail - vp, global_strings_, pkg, v)) {
                if (v.is_string()) {
                    const std::string* s = global_strings_.get(v.data);
                    if (s) v.string_value = *s;
                }
                entry.value = v;
            }
        } else {
            // ResTable_map_entry: {size, flags, key, parent(ref), count}
            if (ep + 16 <= avail) {
                uint32_t parent = rd32(e + 8);
                uint32_t count = rd32(e + 12);
                entry.value.type = DataType::ATTRIBUTE;
                entry.value.ref_id = parent;
                const uint8_t* m = base + ep + 16;
                for (uint32_t mi = 0; mi < count && (size_t)(m - base) + 20 <= avail; mi++, m += 20) {
                    ResValue item;
                    if (decode_res_value(m + 4, avail - (m - base) - 4, global_strings_, pkg, item)) {
                        if (item.is_string()) {
                            const std::string* s = global_strings_.get(item.data);
                            if (s) item.string_value = *s;
                        }
                        entry.complex_items.push_back(item);
                    }
                }
                // style: first item often text color; keep simple value = first
                if (!entry.complex_items.empty()) entry.value = entry.complex_items[0];
            }
        }
        type_entries_.push_back(std::move(entry));
    }

    pkg.types[type_id].push_back(std::move(tc));
    stats_.type_count++;
    return true;
}

// ---------------------------------------------------------------------------
// Package chunk (0x0200)
// ---------------------------------------------------------------------------
bool ArscParser::parse_package(const uint8_t* base, size_t avail, size_t chunk_offset, size_t chunk_size) {
    if (chunk_offset + 288 > avail) { last_error_ = "package: truncated"; return false; }
    const uint8_t* p = base + chunk_offset;
    uint16_t header_size = rd16(p + 2);
    uint32_t pkg_id = rd32(p + 8);
    // name: 256 bytes UTF-16 at +12
    std::string name;
    {
        const char16_t* np = (const char16_t*)(p + 12);
        for (int i = 0; i < 128 && np[i]; i++) {
            char16_t c = np[i];
            if (c < 0x80) name += (char)c;
            else { name += '?'; }
        }
    }
    uint32_t type_strings_off = rd32(p + 268);
    uint32_t key_strings_off  = rd32(p + 276);

    Package pkg;
    pkg.id = pkg_id;
    pkg.name = name;

    if (type_strings_off) {
        if (!parse_string_pool(base, avail, chunk_offset + type_strings_off, pkg.type_strings))
            return false;
    }
    if (key_strings_off) {
        if (!parse_string_pool(base, avail, chunk_offset + key_strings_off, pkg.key_strings))
            return false;
    }

    // iterate inner chunks after header (+ the two pools' sizes)
    size_t pos = chunk_offset + header_size;
    // skip the two string pools if they are directly after header
    // (their sizes are in their own headers)
    auto chunk_size_at = [&](size_t off) -> uint32_t {
        if (off + 8 > avail) return 0;
        return rd32(base + off + 4);
    };
    if (type_strings_off && pos == chunk_offset + type_strings_off) {
        pos += chunk_size_at(pos);
    }
    if (key_strings_off && pos == chunk_offset + key_strings_off) {
        pos += chunk_size_at(pos);
    }
    size_t pkg_end = chunk_offset + chunk_size;
    while (pos + 8 <= pkg_end && pos + 8 <= avail) {
        uint16_t ctype = rd16(base + pos);
        uint32_t csize = rd32(base + pos + 4);
        if (csize == 0) break;
        if (ctype == RES_TABLE_TYPE_TYPE) {
            if (!parse_type_chunk(base, avail, pkg, pos, csize)) return false;
        } else if (ctype == RES_TABLE_TYPE_SPEC_TYPE) {
            // skip
        } else {
            // unknown — skip
        }
        pos += csize;
    }

    packages_.push_back(std::move(pkg));
    stats_.package_count++;
    return true;
}

// ---------------------------------------------------------------------------
// Top-level parse
// ---------------------------------------------------------------------------
bool ArscParser::parse(const std::vector<uint8_t>& data) {
    valid_ = false;
    data_ = data.data();
    size_ = data.size();
    packages_.clear();
    type_entries_.clear();
    id_index_.clear();
    stats_ = Stats{};

    if (size_ < 12) { last_error_ = "too small"; return false; }
    const uint8_t* p = data_;
    uint16_t type = rd16(p);
    uint16_t header_size = rd16(p + 2);
    uint32_t total_size = rd32(p + 4);
    uint32_t package_count = rd32(p + 8);
    if (type != RES_TABLE_TYPE) { last_error_ = "not RES_TABLE_TYPE"; return false; }
    if (total_size > size_) { last_error_ = "size overruns data"; return false; }

    // global string pool directly after header
    if (!parse_string_pool(p, size_, header_size, global_strings_)) return false;
    stats_.global_string_count = (uint32_t)global_strings_.strings.size();
    uint32_t pool_size = rd32(p + header_size + 4);

    size_t pos = header_size + pool_size;
    size_t pkg_seen = 0;
    while (pos + 8 <= total_size && pkg_seen < package_count) {
        uint16_t ctype = rd16(p + pos);
        uint32_t csize = rd32(p + pos + 4);
        if (csize == 0) break;
        if (ctype == RES_TABLE_PACKAGE_TYPE) {
            if (!parse_package(p, size_, pos, csize)) return false;
            pkg_seen++;
        }
        pos += csize;
    }

    // build id index
    finish_index();

    valid_ = true;
    last_error_.clear();
    return true;
}

void ArscParser::finish_index() {
    by_id_.clear();
    pkg_of_id_.clear();
    for (auto& e : type_entries_) {
        uint32_t id = ((e.package_id & 0xFF) << 24) | ((e.type_index & 0xFF) << 16) | (e.entry_index & 0xFFFF);
        e.resource_id = id;
    }
    for (auto& e : type_entries_) {
        by_id_[e.resource_id].push_back(&e);
    }
    // type_name from package type strings (each entry may lack it)
    for (auto& e : type_entries_) {
        if (!e.type_name.empty()) continue;
        uint32_t pid = (e.resource_id >> 24) & 0xFF;
        uint8_t tid = (e.resource_id >> 16) & 0xFF;
        for (const auto& pkg : packages_) {
            if (pkg.id == pid) {
                const std::string* tn = pkg.type_strings.get(tid - 1);
                if (tn) e.type_name = *tn;
                break;
            }
        }
    }
    stats_.named_ids = (uint32_t)by_id_.size();
    stats_.entries_by_type.clear();
    for (const auto& kv : by_id_) {
        if (!kv.second.empty())
            stats_.entries_by_type[kv.second.front()->type_name]++;
    }
}

// ---------------------------------------------------------------------------
// Resolution — CAMPAIGN 009 §6: AOSP configuration matching.
// Oracle: aosp-mirror/platform_frameworks_base ResourceTypes.cpp — a config is
// chosen among candidates that match() the device settings via isBetterThan();
// if nothing matches, the default (qualifier-less) entry is used, mirroring
// AssetsProvider behavior for unqualified tables.
// ---------------------------------------------------------------------------
const ArscEntry* ResolvedResource::best() const {
    if (configs.empty()) return nullptr;
    const ResTableConfig& device = device_config();
    const ArscEntry* best = nullptr;
    for (const auto& c : configs) {
        if (c.has_config && !c.config.match(device)) continue;
        if (!best) { best = &c; continue; }
        const bool c_has = c.has_config;
        const bool b_has = best->has_config;
        if (c_has && b_has) {
            if (c.config.isBetterThan(best->config, device)) best = &c;
        } else if (c_has && !b_has) {
            // qualified config beats default when the qualifier matches the device
            if (c.config.locale || c.config.density || c.config.smallestScreenWidthDp ||
                c.config.screenSizeDpMask || c.config.screenConfig || c.config.imsi ||
                c.config.version || c.config.screenConfig2 || c.config.screenType) {
                best = &c;
            }
        }
        // !c_has && b_has → keep existing best (default never beats a matching qualifier)
    }
    if (best) return best;
    // No bucket matched the device: fall back to the default config if present.
    for (const auto& c : configs) if (!c.has_config) return &c;
    return &configs.front();
}

std::optional<ResolvedResource> ArscParser::resolve(uint32_t resource_id) const {
    auto it = by_id_.find(resource_id);
    if (it == by_id_.end() || it->second.empty()) return std::nullopt;
    ResolvedResource out;
    out.id = resource_id;
    uint32_t pid = (resource_id >> 24) & 0xFF;
    uint8_t  tid = (resource_id >> 16) & 0xFF;
    for (const auto& pkg : packages_) {
        if (pkg.id == pid) { out.package_name = pkg.name; break; }
    }
    for (const auto* e : it->second) {
        out.configs.push_back(*e);
    }
    if (!out.configs.empty()) {
        out.type_name = out.configs.front().type_name;
        out.name = out.configs.front().name;
    }
    // ensure type_name is set even when the front entry missed it
    if (out.type_name.empty()) {
        for (const auto& pkg : packages_) if (pkg.id == pid) {
            const std::string* tn = pkg.type_strings.get(tid - 1);
            if (tn) out.type_name = *tn;
            break;
        }
        for (auto& e : out.configs) e.type_name = out.type_name;
    }
    return out;
}

std::optional<uint32_t> ArscParser::find_id(const std::string& package, const std::string& type,
                                            const std::string& name) const {
    for (const auto& kv : by_id_) {
        const ArscEntry* e = kv.second.front();
        if (!name.empty() && e->name != name) continue;
        if (!type.empty() && e->type_name != type) continue;
        if (!package.empty()) {
            uint32_t pid = (kv.first >> 24) & 0xFF;
            bool match = false;
            for (const auto& pkg : packages_) if (pkg.id == pid && pkg.name == package) { match = true; break; }
            if (!match) continue;
        }
        return kv.first;
    }
    return std::nullopt;
}

std::optional<ResValue> ArscParser::resolve_value(uint32_t resource_id) const {
    auto r = resolve(resource_id);
    if (!r) return std::nullopt;
    const ArscEntry* e = r->best();
    if (!e) return std::nullopt;
    ResValue v = e->value;
    // follow one reference hop (e.g. color → @color/other, string alias)
    int hops = 0;
    while (v.is_reference() && hops < 4) {
        auto r2 = resolve(v.ref_id);
        if (!r2) break;
        const ArscEntry* e2 = r2->best();
        if (!e2) break;
        v = e2->value;
        hops++;
    }
    return v;
}

std::optional<std::string> ArscParser::resolve_string(uint32_t resource_id) const {
    auto v = resolve_value(resource_id);
    if (v && v->is_string()) return v->string_value;
    return std::nullopt;
}

std::vector<std::pair<uint32_t, std::string>> ArscParser::list_type(
        const std::string& package, const std::string& type) const {
    std::vector<std::pair<uint32_t, std::string>> out;
    for (const auto& kv : by_id_) {
        auto r = resolve(kv.first);
        if (!r) continue;
        if (r->type_name != type) continue;
        if (!package.empty() && r->package_name != package) continue;
        out.push_back({kv.first, r->name});
    }
    std::sort(out.begin(), out.end());
    return out;
}

std::optional<std::string> ArscParser::apk_path_for(uint32_t resource_id,
                                                    const std::vector<std::string>& apk_paths) const {
    auto r = resolve(resource_id);
    if (!r) return std::nullopt;

    // CAMPAIGN 013 (§18): REAL Android resolution for file-backed resources.
    // In resources.arsc a file-backed entry's VALUE IS THE PATH (STRING type,
    // e.g. "res/w6.xml"). AGP resource obfuscation renames the FILES and
    // rewrites these values — the entry NAME no longer appears anywhere in
    // res/. The old name-matching heuristic returned NONE for every layout of
    // obfuscated APKs (notesbillthefarmer: name=main, value=res/w6.xml).
    // Value-first also removes the O(type*files) name scan for normal APKs.
    for (const auto& cfg : r->configs) {
        const std::string& v = cfg.value.string_value;
        if (cfg.value.type == DataType::STRING && v.size() > 4 &&
            v.compare(0, 4, "res/") == 0) {
            for (const auto& path : apk_paths)
                if (path == v) return path;
        }
    }

    // Fallback: legacy name matching (entry name = file stem).
    // candidates: res/<type>-<config>/<name>.<ext> — we match by suffix
    for (const auto& path : apk_paths) {
        // path like res/layout/act_gmdice.xml or res/drawable-hdpi/icon.png
        const std::string prefix = "res/";
        if (path.compare(0, prefix.size(), prefix) != 0) continue;
        size_t slash2 = path.find('/', prefix.size());
        if (slash2 == std::string::npos) continue;
        std::string dir = path.substr(prefix.size(), slash2 - prefix.size());
        // dir = layout | layout-v21 | drawable-hdpi ...
        std::string base_dir = dir;
        size_t dash = base_dir.find('-');
        if (dash != std::string::npos) base_dir = base_dir.substr(0, dash);
        if (base_dir != r->type_name) continue;
        std::string fname = path.substr(slash2 + 1);
        size_t dot = fname.find('.');
        std::string stem = dot == std::string::npos ? fname : fname.substr(0, dot);
        if (stem == r->name) return path;
    }
    return std::nullopt;
}

// ---------------------------------------------------------------------------
// JSON evidence
// ---------------------------------------------------------------------------
std::string ArscParser::to_json(size_t max_entries) const {
    std::ostringstream o;
    o << "{\"valid\":" << (valid_ ? "true" : "false")
      << ",\"packages\":" << stats_.package_count
      << ",\"global_strings\":" << stats_.global_string_count
      << ",\"type_chunks\":" << stats_.type_count
      << ",\"entry_configs\":" << stats_.entry_count
      << ",\"named_ids\":" << stats_.named_ids
      << ",\"entries_by_type\":{";
    bool first = true;
    for (auto& kv : stats_.entries_by_type) {
        if (!first) o << ",";
        first = false;
        o << "\"" << kv.first << "\":" << kv.second;
    }
    o << "},\"sample\":[";
    size_t n = 0;
    for (const auto& kv : by_id_) {
        if (n++ >= max_entries) break;
        auto r = resolve(kv.first);
        if (!r) continue;
        const ArscEntry* e = r->best();
        if (!e) continue;
        if (n > 1) o << ",";
        o << "{\"id\":0x" << std::hex << kv.first << std::dec
          << ",\"type\":\"" << r->type_name << "\""
          << ",\"name\":\"" << r->name << "\""
          << ",\"config\":\"" << e->config_desc << "\"";
        if (e->value.is_string()) {
            std::string esc;
            for (char c : e->value.string_value) {
                if (c == '"') esc += "\\\"";
                else if (c == '\\') esc += "\\\\";
                else if (c == '\n') esc += "\\n";
                else if ((unsigned char)c < 0x20) esc += ' ';
                else esc += c;
            }
            o << ",\"value\":\"" << esc << "\"";
        }
        else o << ",\"dtype\":" << (int)e->value.type << ",\"data\":" << e->value.data;
        o << "}";
    }
    o << "]}";
    return o.str();
}

} // namespace resources
} // namespace miniandroid
