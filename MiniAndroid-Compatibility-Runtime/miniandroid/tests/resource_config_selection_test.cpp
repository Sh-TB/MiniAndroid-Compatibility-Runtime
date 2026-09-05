// GOLDEN-02 P1 — GENERIC resource-configuration selection regression.
//
// Proves the AOSP configuration law (ResourceTypes.cpp match()/isBetterThan/
// AssetManager2::FindEntryInternal) for default/v16/v21 resource variants —
// the law the G31 session fixed (requested.size != 0 gate; version-qualified
// tie-break). Synthetic in-memory resources.arsc tables: NO fixture APK
// dependency, no app-specific names.
//
// Checks (each counted; zero-skip law):
//   [unit]    from_bytes: 28-byte config parses (size kept, sdk extracted);
//             size-0 config = qualifier-less default
//   [unit]    match(): v21 candidate matches sdk34 but NOT sdk16 device
//   [unit]    isBetterThan: qualified beats DEFAULT on a matching device
//   [unit]    isBetterThan: v16 vs v21 = tie BOTH ways (AOSP-EXACT:
//             no version preference between two qualified candidates →
//             first in table order wins)
//   [unit]    requested.size == 0 disables the law (the G31 regression)
//   [arsc]    synthetic table order (default,v16,v21) resolved at
//             device34 → v16 (tie-break law), device17 → v16,
//             device9  → default fallback
//   [arsc]    reversed table order (default,v21,v16) at device34 → v21
//             (order-sensitivity proves the tie-break, not accident)
//   [arsc]    apk_path_for(device) returns the SELECTED variant's path
//
// Oracle: aosp-mirror/platform_frameworks_base ResourceTypes.cpp
// (@1cdfff555f4a) — isBetterThan @2641, match @2909; version tie-break
// @2489-2501 (see src/resources/res_config.cpp for the transferred law).
#include "../src/resources/arsc_parser.h"
#include "../src/resources/res_config.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

using namespace miniandroid::resources;

static int g_pass = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    if (ok) { g_pass++; std::cout << "  PASS: " << what << "\n"; }
    else    { g_fail++; std::cout << "  FAIL: " << what << "\n"; }
}

// ── synthetic ARSC builder ────────────────────────────────────────────────
static void put16(std::vector<uint8_t>& v, size_t off, uint16_t x) {
    v[off] = x & 0xFF; v[off + 1] = (x >> 8) & 0xFF;
}
static void put32(std::vector<uint8_t>& v, size_t off, uint32_t x) {
    v[off] = x & 0xFF; v[off+1] = (x>>8)&0xFF; v[off+2] = (x>>16)&0xFF; v[off+3] = (x>>24)&0xFF;
}
static void append16(std::vector<uint8_t>& v, uint16_t x) { size_t o=v.size(); v.resize(o+2); put16(v,o,x); }
static void append32(std::vector<uint8_t>& v, uint32_t x) { size_t o=v.size(); v.resize(o+4); put32(v,o,x); }

// UTF-8 string pool chunk (ResStringPool, UTF8_FLAG) over the given strings.
static std::vector<uint8_t> build_string_pool(const std::vector<std::string>& strings) {
    std::vector<uint8_t> offsets_blob;
    std::vector<uint8_t> data_blob;
    for (const auto& s : strings) {
        append32(offsets_blob, (uint32_t)data_blob.size());
        // UTF-8 pool entry: u8 char-length, u8 byte-length, bytes, NUL
        data_blob.push_back((uint8_t)s.size());      // char len (ASCII == byte len)
        data_blob.push_back((uint8_t)s.size());      // byte len
        data_blob.insert(data_blob.end(), s.begin(), s.end());
        data_blob.push_back(0);
    }
    while (data_blob.size() % 4) data_blob.push_back(0);

    const uint32_t string_count = (uint32_t)strings.size();
    const uint32_t header_size = 28;
    const uint32_t offsets_start = header_size;
    const uint32_t strings_start = offsets_start + string_count * 4;
    const uint32_t chunk_size = strings_start + (uint32_t)data_blob.size();

    std::vector<uint8_t> out;
    append16(out, 0x0001);            // RES_STRING_POOL_TYPE
    append16(out, (uint16_t)header_size);
    append32(out, chunk_size);
    append32(out, string_count);
    append32(out, 0);                 // styleCount
    append32(out, 1u << 8);           // flags = UTF8_FLAG
    append32(out, strings_start);
    append32(out, 0);                 // stylesStart
    out.insert(out.end(), offsets_blob.begin(), offsets_blob.end());
    out.insert(out.end(), data_blob.begin(), data_blob.end());
    return out;
}

// One config variant: 28-byte ResTable_config with optional sdkVersion.
static std::vector<uint8_t> config28(uint16_t sdk) {
    std::vector<uint8_t> c(28, 0);
    put32(c, 0, 28);
    put16(c, 24, sdk);
    return c;
}

// type chunk (0x0201) with ONE entry (key idx 0), value = STRING pool ref.
static std::vector<uint8_t> build_type_chunk(uint8_t type_id, uint16_t sdk,
                                             uint32_t string_pool_idx) {
    // layout: header(20) + config(config28) + offsets[1] + entry(8) + value(8)
    std::vector<uint8_t> cfg = config28(sdk);
    const uint16_t header_size = (uint16_t)(20 + cfg.size());
    const uint32_t entries_start = header_size + 4;  // + 1 offset u32
    const uint32_t chunk_size = entries_start + 8 + 8;

    std::vector<uint8_t> out;
    append16(out, 0x0201);            // RES_TABLE_TYPE_TYPE
    append16(out, header_size);
    append32(out, chunk_size);
    out.push_back(type_id);           // id
    out.push_back(0);                 // res0
    append16(out, 0);                 // res1
    append32(out, 1);                 // entryCount
    append32(out, entries_start);
    out.insert(out.end(), cfg.begin(), cfg.end());
    append32(out, 0);                 // offset[0] = 0 (present)
    // ResTable_entry {size=8, flags=0, key=0}
    append16(out, 8); append16(out, 0); append32(out, 0);
    // Res_value {size=8, res0=0, dataType=STRING(3), data=pool idx}
    append16(out, 8); out.push_back(0); out.push_back(0x03); append32(out, string_pool_idx);
    return out;
}

static std::vector<uint8_t> build_type_spec(uint8_t type_id) {
    // ResTable_typeSpec: header(8: type/hdrSize/size) + id/res0/res1(4) +
    // entryCount(4) + flags[entryCount](4). Declared size MUST equal the
    // bytes actually emitted — the parser's chunk walk uses it verbatim.
    std::vector<uint8_t> out;
    append16(out, 0x0202);            // RES_TABLE_TYPE_SPEC_TYPE
    append16(out, 16);                // headerSize (through entryCount)
    append32(out, 16 + 4);            // total size = header + flags[1]
    out.push_back(type_id); out.push_back(0); append16(out, 0);
    append32(out, 1);                 // entryCount
    append32(out, 0);                 // flags[0]: no attributes defined
    return out;
}

// Full minimal table: 1 package, type "layout", entry "main", variants in
// the given (path, sdk) ORDER — order is part of the law under test.
struct Variant { std::string path; uint16_t sdk; };  // sdk 0 = default
static std::vector<uint8_t> build_table(const std::vector<Variant>& variants) {
    // global pool: [0]=variants[0].path, [1]=..., typeStrings=["layout"], keyStrings=["main"]
    std::vector<std::string> global;
    for (auto& v : variants) global.push_back(v.path);

    const uint16_t table_header = 12;
    std::vector<uint8_t> pool = build_string_pool(global);
    std::vector<uint8_t> type_pool = build_string_pool({"layout"});
    std::vector<uint8_t> key_pool = build_string_pool({"main"});

    // package body: spec chunk + one type chunk per variant
    std::vector<uint8_t> inner;
    std::vector<uint8_t> spec = build_type_spec(1);
    inner.insert(inner.end(), spec.begin(), spec.end());
    for (size_t i = 0; i < variants.size(); i++) {
        std::vector<uint8_t> tc = build_type_chunk(1, variants[i].sdk, (uint32_t)i);
        inner.insert(inner.end(), tc.begin(), tc.end());
    }

    // package header (288 bytes): typeStrings/keyStrings offsets AFTER header
    const uint32_t pkg_hdr = 288;
    const uint32_t type_strings_off = pkg_hdr;
    const uint32_t key_strings_off = type_strings_off + (uint32_t)type_pool.size();
    const uint32_t pkg_size = pkg_hdr + (uint32_t)type_pool.size() + (uint32_t)key_pool.size()
                            + (uint32_t)inner.size();

    std::vector<uint8_t> pkg(pkg_hdr, 0);
    put16(pkg, 0, 0x0200);
    put16(pkg, 2, (uint16_t)pkg_hdr);
    put32(pkg, 4, pkg_size);
    put32(pkg, 8, 0x7f);              // package id
    // name at +12 (UTF-16 "t" NUL-padded)
    pkg[12] = 't';
    put32(pkg, 268, type_strings_off);
    put32(pkg, 272, 1);               // lastPublicType
    put32(pkg, 276, key_strings_off);
    put32(pkg, 280, 1);               // lastPublicKey
    std::vector<uint8_t> pkg_all = pkg;
    pkg_all.insert(pkg_all.end(), type_pool.begin(), type_pool.end());
    pkg_all.insert(pkg_all.end(), key_pool.begin(), key_pool.end());
    pkg_all.insert(pkg_all.end(), inner.begin(), inner.end());

    const uint32_t total = table_header + (uint32_t)pool.size() + (uint32_t)pkg_all.size();
    std::vector<uint8_t> out;
    append16(out, 0x0002);            // RES_TABLE_TYPE
    append16(out, (uint16_t)table_header);
    append32(out, total);
    append32(out, 1);                 // packageCount
    out.insert(out.end(), pool.begin(), pool.end());
    out.insert(out.end(), pkg_all.begin(), pkg_all.end());
    return out;
}

// Device config for the matrix: only sdkVersion varies.
static ResTableConfig device_with_sdk(uint16_t sdk, uint32_t size_field = 64) {
    ResTableConfig c;
    c.size = size_field;
    c.sdkVersion = sdk;
    c.compute_fields();
    return c;
}

static const uint32_t RES_ID = 0x7f010000;  // package 0x7f, type 1, entry 0

// Resolve the variant path selected for a device on a parsed table.
static std::string selected_path(ArscParser& arsc, const ResTableConfig& dev,
                                 const std::vector<std::string>& paths) {
    auto r = arsc.resolve(RES_ID);
    if (!r) return "<NONE>";
    auto e = r->best_for(dev);
    if (!e) return "<NONE>";
    std::string val = e->value.string_value;
    // Cross-check with the apk_path_for law (same device).
    auto p = arsc.apk_path_for(RES_ID, paths, dev);
    if (p && *p != val) val += " (MISMATCH vs apk_path_for: " + *p + ")";
    return val;
}

int main() {
    std::cout << "── resource-config selection regression (generic law) ──\n";

    // ── [unit] from_bytes: 28-byte v16 config ─────────────────────────────
    {
        std::vector<uint8_t> c = config28(16);
        ResTableConfig t = ResTableConfig::from_bytes(c.data(), c.size());
        check(t.size == 28, "from_bytes keeps ResTableConfig.size=28");
        check(t.sdkVersion == 16, "from_bytes extracts sdkVersion=16 (v16 qualifier)");
        check(t.version == 1, "from_bytes sets version field (v!=0)");

        std::vector<uint8_t> zero(28, 0);
        ResTableConfig d = ResTableConfig::from_bytes(zero.data(), zero.size());
        check(d.size == 0 && d.version == 0,
              "from_bytes size-0 config = qualifier-less default");
    }

    // ── [unit] match(): v21 vs device sdk34 / sdk16 ───────────────────────
    {
        std::vector<uint8_t> c = config28(21);
        ResTableConfig v21 = ResTableConfig::from_bytes(c.data(), c.size());
        check(v21.match(device_with_sdk(34)), "match: v21 candidate matches device sdk34");
        check(!v21.match(device_with_sdk(16)), "match: v21 candidate REJECTED on device sdk16");
    }

    // ── [unit] isBetterThan: qualified beats default ─────────────────────
    {
        std::vector<uint8_t> cq = config28(21);
        ResTableConfig v21 = ResTableConfig::from_bytes(cq.data(), cq.size());
        ResTableConfig def;  // size 0, no qualifiers
        check(v21.isBetterThan(def, device_with_sdk(34)),
              "isBetterThan: v21 beats DEFAULT on matching device");
        check(!def.isBetterThan(v21, device_with_sdk(34)),
              "isBetterThan: DEFAULT does not beat v21");
    }

    // ── [unit] isBetterThan: v16 vs v21 tie BOTH ways (AOSP law) ─────────
    {
        std::vector<uint8_t> c16 = config28(16), c21 = config28(21);
        ResTableConfig v16 = ResTableConfig::from_bytes(c16.data(), c16.size());
        ResTableConfig v21 = ResTableConfig::from_bytes(c21.data(), c21.size());
        check(!v21.isBetterThan(v16, device_with_sdk(34)) &&
              !v16.isBetterThan(v21, device_with_sdk(34)),
              "isBetterThan: v16 vs v21 = tie BOTH ways (first in table order wins)");
    }

    // ── [unit] requested.size == 0 disables the law (G31 regression) ─────
    {
        std::vector<uint8_t> cq = config28(21);
        ResTableConfig v21 = ResTableConfig::from_bytes(cq.data(), cq.size());
        ResTableConfig def;
        ResTableConfig req0 = device_with_sdk(34, /*size_field=*/0);
        check(!v21.isBetterThan(def, req0),
              "requested.size==0 gates isBetterThan (G31 fix is load-bearing)");
    }

    // ── [arsc] synthetic table, ascending order (aapt2 emission order) ───
    {
        std::vector<uint8_t> blob = build_table({
            {"res/layout/default.xml", 0},
            {"res/layout/v16.xml", 16},
            {"res/layout/v21.xml", 21},
        });
        ArscParser arsc;
        check(arsc.parse(blob), "synthetic arsc (default,v16,v21) parses");
        if (arsc.valid()) {
            const std::vector<std::string> paths = {
                "res/layout/default.xml", "res/layout/v16.xml", "res/layout/v21.xml"};
            check(selected_path(arsc, device_with_sdk(34), paths) == "res/layout/v16.xml",
                  "device sdk34 → v16 (version tie-break: first qualified in table order)");
            check(selected_path(arsc, device_with_sdk(17), paths) == "res/layout/v16.xml",
                  "device sdk17 → v16 (v21 rejected by match, v16 beats default)");
            check(selected_path(arsc, device_with_sdk(9), paths) == "res/layout/default.xml",
                  "device sdk9 → default fallback (no qualified match)");
        }
    }

    // ── [arsc] reversed order → device34 flips to v21 ─────────────────────
    {
        std::vector<uint8_t> blob = build_table({
            {"res/layout/default.xml", 0},
            {"res/layout/v21.xml", 21},
            {"res/layout/v16.xml", 16},
        });
        ArscParser arsc;
        check(arsc.parse(blob), "synthetic arsc (default,v21,v16) parses");
        if (arsc.valid()) {
            const std::vector<std::string> paths = {
                "res/layout/default.xml", "res/layout/v21.xml", "res/layout/v16.xml"};
            check(selected_path(arsc, device_with_sdk(34), paths) == "res/layout/v21.xml",
                  "device sdk34 → v21 when v21 is first in table order (order-sensitivity)");
            check(selected_path(arsc, device_with_sdk(17), paths) == "res/layout/v16.xml",
                  "device sdk17 → v16 in reversed order (v21 rejected by match, v16 matches)");
        }
    }

    // ── [arsc] default-only table always resolves to default ──────────────
    {
        std::vector<uint8_t> blob = build_table({{"res/layout/only.xml", 0}});
        ArscParser arsc;
        check(arsc.parse(blob), "default-only arsc parses");
        if (arsc.valid()) {
            check(selected_path(arsc, device_with_sdk(34), {"res/layout/only.xml"}) ==
                      "res/layout/only.xml",
                  "default-only table resolves to default on any device");
        }
    }

    std::cout << "RESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
