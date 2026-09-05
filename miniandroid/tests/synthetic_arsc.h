// GOLDEN-03 — shared synthetic resources.arsc builder for generic tests.
//
// Builds byte-exact binary ARSC tables (same AOSP chunk layout law as
// resource_config_selection_test.cpp's builder, generalized): arbitrary
// string pools, multiple types, multiple entries per type, simple values of
// any Res_value type, and complex (bag) entries with ResTable_map keys and a
// ResTable_map_entry parent. NO fixture-APK dependency; used by the §4/§6/§8
// law test and the §14 hostile-input test.
#ifndef MINIANDROID_TESTS_SYNTHETIC_ARSC_H
#define MINIANDROID_TESTS_SYNTHETIC_ARSC_H

#include "../src/resources/arsc_parser.h"

#include <cstdint>
#include <string>
#include <vector>

namespace synthetic_arsc {

inline void put16(std::vector<uint8_t>& v, size_t off, uint16_t x) {
    v[off] = x & 0xFF; v[off + 1] = (x >> 8) & 0xFF;
}
inline void put32(std::vector<uint8_t>& v, size_t off, uint32_t x) {
    v[off] = x & 0xFF; v[off+1] = (x>>8)&0xFF; v[off+2] = (x>>16)&0xFF; v[off+3] = (x>>24)&0xFF;
}
inline void append16(std::vector<uint8_t>& v, uint16_t x) { size_t o=v.size(); v.resize(o+2); put16(v,o,x); }
inline void append32(std::vector<uint8_t>& v, uint32_t x) { size_t o=v.size(); v.resize(o+4); put32(v,o,x); }

// UTF-8 ResStringPool chunk over the given strings.
inline std::vector<uint8_t> string_pool(const std::vector<std::string>& strings) {
    std::vector<uint8_t> offsets_blob, data_blob;
    for (const auto& s : strings) {
        append32(offsets_blob, (uint32_t)data_blob.size());
        data_blob.push_back((uint8_t)s.size());   // char len (ASCII)
        data_blob.push_back((uint8_t)s.size());   // byte len
        data_blob.insert(data_blob.end(), s.begin(), s.end());
        data_blob.push_back(0);
    }
    while (data_blob.size() % 4) data_blob.push_back(0);
    const uint32_t n = (uint32_t)strings.size(), header_size = 28;
    const uint32_t strings_start = header_size + n * 4;
    const uint32_t chunk_size = strings_start + (uint32_t)data_blob.size();
    std::vector<uint8_t> out;
    append16(out, 0x0001); append16(out, (uint16_t)header_size); append32(out, chunk_size);
    append32(out, n); append32(out, 0); append32(out, 1u << 8);
    append32(out, strings_start); append32(out, 0);
    out.insert(out.end(), offsets_blob.begin(), offsets_blob.end());
    out.insert(out.end(), data_blob.begin(), data_blob.end());
    return out;
}

// 28-byte ResTable_config with only sdkVersion set (sdk 0 → all-zero fields).
inline std::vector<uint8_t> config28(uint16_t sdk) {
    std::vector<uint8_t> c(28, 0);
    put32(c, 0, 28);
    put16(c, 24, sdk);
    return c;
}

struct BagItem {
    uint32_t key = 0;
    uint8_t  type = 0x03;
    uint32_t data = 0;
};

struct EntrySpec {
    std::string name;
    bool     complex = false;
    uint32_t parent  = 0;                 // bag parent resource id
    uint8_t  value_type = 0x03;           // simple value dataType
    uint32_t value_data = 0;              // simple value data word
    int      string_index = -1;           // >= 0 → STRING value w/ global pool index
    std::vector<BagItem> bag;
};

// One (type, config-variant) chunk group: all entries share the config.
struct TypeVariant {
    uint8_t  type_id = 1;
    std::string type_name;
    uint16_t sdk = 0;                     // 0 → default-qualifier 28-byte config
    std::vector<EntrySpec> entries;
};

// Emit one simple Res_value or complex map entry; returns chunk bytes.
inline void append_entry(std::vector<uint8_t>& out, const EntrySpec& e,
                         uint32_t key_index) {
    if (!e.complex) {
        // ResTable_entry {size=8, flags=0, key} + Res_value {size=8, res0, type, data}
        append16(out, 8); append16(out, 0); append32(out, key_index);
        uint32_t data = e.string_index >= 0 ? (uint32_t)e.string_index : e.value_data;
        append16(out, 8); out.push_back(0); out.push_back(e.value_type); append32(out, data);
        return;
    }
    // ResTable_map_entry {size=16, flags=COMPLEX(1), key, parent, count}
    append16(out, 16); append16(out, 1); append32(out, key_index);
    append32(out, e.parent); append32(out, (uint32_t)e.bag.size());
    for (const auto& item : e.bag) {
        // ResTable_map {name, Res_value{size=8, res0, type, data}}
        append32(out, item.key);
        append16(out, 8); out.push_back(0); out.push_back(item.type); append32(out, item.data);
    }
}

// Full RES_TABLE_TYPE blob. type/key string pools are derived from variants.
inline std::vector<uint8_t> build(const std::vector<std::string>& global_strings,
                                  const std::vector<TypeVariant>& variants,
                                  uint32_t package_id = 0x7f,
                                  const std::string& package_name = "t") {
    std::vector<uint8_t> pool = string_pool(global_strings);
    // type strings (1-based ids): unique type names in variant order
    std::vector<std::string> type_names;
    for (const auto& v : variants)
        if (std::find(type_names.begin(), type_names.end(), v.type_name) == type_names.end())
            type_names.push_back(v.type_name);
    // key strings: entry names in first-seen order
    std::vector<std::string> key_names;
    auto key_index_of = [&](const std::string& n) -> uint32_t {
        auto it = std::find(key_names.begin(), key_names.end(), n);
        if (it != key_names.end()) return (uint32_t)(it - key_names.begin());
        key_names.push_back(n);
        return (uint32_t)(key_names.size() - 1);
    };

    std::vector<uint8_t> type_pool = string_pool(type_names);
    // NOTE: key_pool is built AFTER the variant loop below — key_index_of()
    // populates key_names lazily while emitting entries (first-seen order).

    // inner: type-spec chunk + type chunks
    std::vector<uint8_t> inner;
    {
        std::vector<uint8_t> seen;
        for (const auto& v : variants) {
            if (std::find(seen.begin(), seen.end(), v.type_id) != seen.end()) continue;
            seen.push_back(v.type_id);
            size_t count = 0;
            for (const auto& w : variants) if (w.type_id == v.type_id)
                for (const auto& e : w.entries) count++;
            append16(inner, 0x0202); append16(inner, 16);
            append32(inner, 16 + 4 * count);
            inner.push_back(v.type_id); inner.push_back(0); append16(inner, 0);
            append32(inner, count);
            for (uint32_t f = 0; f < count; f++) append32(inner, 0);
        }
    }
    for (const auto& v : variants) {
        const uint32_t n_entries = (uint32_t)v.entries.size();
        std::vector<uint8_t> cfg = config28(v.sdk);
        const uint16_t header_size = (uint16_t)(20 + cfg.size());
        const uint32_t entries_start = header_size + 4 * n_entries;

        // entry bytes first (need total size)
        std::vector<uint8_t> entries_blob;
        std::vector<uint32_t> entry_offsets(n_entries, 0xFFFFFFFFu);
        for (uint32_t i = 0; i < n_entries; i++) {
            entry_offsets[i] = (uint32_t)entries_blob.size();
            append_entry(entries_blob, v.entries[i], key_index_of(v.entries[i].name));
        }
        const uint32_t chunk_size = entries_start + (uint32_t)entries_blob.size();

        append16(inner, 0x0201); append16(inner, header_size); append32(inner, chunk_size);
        inner.push_back(v.type_id); inner.push_back(0); append16(inner, 0);
        append32(inner, n_entries);
        append32(inner, entries_start);
        inner.insert(inner.end(), cfg.begin(), cfg.end());
        for (uint32_t i = 0; i < n_entries; i++) append32(inner, entry_offsets[i]);
        inner.insert(inner.end(), entries_blob.begin(), entries_blob.end());
    }

    // key pool AFTER entries: key_index_of above has now filled key_names.
    std::vector<uint8_t> key_pool = string_pool(key_names);

    // package header (288 bytes)
    const uint32_t pkg_hdr = 288;
    const uint32_t type_strings_off = pkg_hdr;
    const uint32_t key_strings_off  = type_strings_off + (uint32_t)type_pool.size();
    const uint32_t pkg_size = key_strings_off + (uint32_t)key_pool.size() + (uint32_t)inner.size();
    std::vector<uint8_t> pkg(pkg_hdr, 0);
    put16(pkg, 0, 0x0200); put16(pkg, 2, (uint16_t)pkg_hdr); put32(pkg, 4, pkg_size);
    put32(pkg, 8, package_id);
    for (size_t i = 0; i < package_name.size() && i < 256; i++) pkg[12 + 2*i] = package_name[i];
    put32(pkg, 268, type_strings_off); put32(pkg, 272, (uint32_t)type_names.size());
    put32(pkg, 276, key_strings_off);  put32(pkg, 280, (uint32_t)key_names.size());
    std::vector<uint8_t> pkg_all = pkg;
    pkg_all.insert(pkg_all.end(), type_pool.begin(), type_pool.end());
    pkg_all.insert(pkg_all.end(), key_pool.begin(), key_pool.end());
    pkg_all.insert(pkg_all.end(), inner.begin(), inner.end());

    const uint32_t total = 12 + (uint32_t)pool.size() + (uint32_t)pkg_all.size();
    std::vector<uint8_t> out;
    append16(out, 0x0002); append16(out, 12); append32(out, total);
    append32(out, 1);   // packageCount
    out.insert(out.end(), pool.begin(), pool.end());
    out.insert(out.end(), pkg_all.begin(), pkg_all.end());
    return out;
}

} // namespace synthetic_arsc

#endif // MINIANDROID_TESTS_SYNTHETIC_ARSC_H
