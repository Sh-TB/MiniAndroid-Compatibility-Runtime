// string_pool.h — ONE canonical Android ResStringPool decoder.
//
// REUSE-FIRST CAMPAIGN (FIND-REUSE-004): the RES_STRING_POOL_TYPE chunk
// parse previously existed as THREE separate implementations:
//   * ArscParser::parse_string_pool      (resources.arsc global/key/type pools)
//   * AxmlParser::parse_string_pool      (binary AXML string pool)
//   * ManifestReader::parse_string_pool  (binary manifest string pool)
// AOSP androidfw uses ONE ResStringPool class for all three consumers
// (frameworks/base/libs/androidfw/ResourceTypes.cpp); MiniAndroid now
// does too.
//
// Format law (AOSP ResourceTypes.h ResStringPool_header):
//   header {type u16, headerSize u16, size u32, stringCount u32,
//           styleCount u32, flags u32, stringsStart u32, stylesStart u32}
//   stringCount × u32 offsets (relative to stringsStart)
//   entry: UTF-8 pool → uleb128 u16len, uleb128 u8len, bytes;
//          UTF-16 pool → u16len (2-chars high:low when high bit set),
//          UTF-16LE bytes.
// Decoding reuses dex/mutf8.h primitives (FIND-REUSE-001/002):
// read_uleb128 + utf16le_to_utf8 — one varint law, one encoding law.
//
// License: original MiniAndroid code (GPL-3.0-or-later).

#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid {
namespace resources {

struct ResStringPool {
    std::vector<std::string> strings;
    bool utf8_pool = false;

    // Parse one RES_STRING_POOL_TYPE chunk located at `p` (`avail` bytes
    // readable). On success returns true, `strings` is filled and
    // `consumed` = declared chunk size. On failure returns false with
    // `err` (optional) set to a diagnostic; `consumed` = 0.
    //
    // Malformed entries (offset past chunk end) decode to empty strings,
    // matching the pre-consolidation ArscParser behavior (the strictest
    // of the three former copies).
    bool parse(const uint8_t* p, size_t avail, size_t& consumed,
               std::string* err = nullptr);

    uint32_t count() const { return static_cast<uint32_t>(strings.size()); }

    // Out-of-range index → empty string (all three former copies behaved
    // this way at their call sites).
    const std::string& at(uint32_t i) const {
        static const std::string kEmpty;
        return i < strings.size() ? strings[i] : kEmpty;
    }
};

}  // namespace resources
}  // namespace miniandroid
