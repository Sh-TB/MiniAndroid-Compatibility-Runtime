// string_pool.cpp — implementation of the ONE canonical ResStringPool
// decoder. See string_pool.h for the format law and FIND-REUSE-004
// provenance.

#include "string_pool.h"

#include "dex/mutf8.h"  // read_uleb128 + utf16le_to_utf8 (FIND-REUSE-001/002)

namespace miniandroid {
namespace resources {

// Chunk constants (AOSP ResourceTypes.h ResStringPool_header). Kept local:
// arsc_parser.h already exports the same values under the same names.
constexpr uint16_t RES_STRING_POOL_TYPE = 0x0001;
constexpr uint32_t RES_STRING_POOL_UTF8_FLAG = 1u << 8;

namespace {
// AOSP ResourceTypes.cpp decodeLength law: pool entry lengths (both the
// UTF-16-unit count of UTF-8 entries and the UTF-8 byte count) use the
// 1-or-2-byte form — high bit set → 2 bytes, (b&0x7F)<<8 | next — NOT the
// generic ULEB128 (they diverge on 3+-byte sequences; real pools never
// carry those, and AOSP defines only the 2-byte form).
inline uint32_t decode_pool_length(const uint8_t* s, size_t remain, size_t& o,
                                   bool& ok) {
    ok = true;
    if (o >= remain) { ok = false; return 0; }
    const uint8_t b = s[o];
    if (b & 0x80) {
        if (o + 1 >= remain) { ok = false; return 0; }
        o += 2;
        return (static_cast<uint32_t>(b & 0x7F) << 8) | s[o - 1];
    }
    o += 1;
    return b;
}
}  // namespace

bool ResStringPool::parse(const uint8_t* p, size_t avail, size_t& consumed,
                          std::string* err) {
    consumed = 0;
    auto fail = [&](const char* msg) {
        if (err) *err = msg;
        return false;
    };

    if (avail < 28) return fail("pool: truncated header");
    const uint16_t type = static_cast<uint16_t>(p[0] | (p[1] << 8));
    const uint16_t header_size = static_cast<uint16_t>(p[2] | (p[3] << 8));
    const uint32_t chunk_size = static_cast<uint32_t>(
        p[4] | (p[5] << 8) | (p[6] << 16) | (static_cast<uint32_t>(p[7]) << 24));
    if (type != RES_STRING_POOL_TYPE) return fail("pool: bad chunk type");
    if (header_size < 28) return fail("pool: header too small");
    if (chunk_size > avail) return fail("pool: chunk overruns data");

    const uint32_t string_count = static_cast<uint32_t>(
        p[8] | (p[9] << 8) | (p[10] << 16) | (static_cast<uint32_t>(p[11]) << 24));
    // p[12..15] = styleCount (unused; styles are not consumed by any
    // former copy — resource styles resolve through the table, not pools)
    const uint32_t flags = static_cast<uint32_t>(
        p[16] | (p[17] << 8) | (p[18] << 16) | (static_cast<uint32_t>(p[19]) << 24));
    const uint32_t strings_start = static_cast<uint32_t>(
        p[20] | (p[21] << 8) | (p[22] << 16) | (static_cast<uint32_t>(p[23]) << 24));

    utf8_pool = (flags & RES_STRING_POOL_UTF8_FLAG) != 0;
    strings.clear();
    strings.resize(string_count);

    if (header_size + string_count * 4u > chunk_size)
        return fail("pool: offset table overruns chunk");

    const uint8_t* sdata = p + strings_start;
    for (uint32_t i = 0; i < string_count; i++) {
        const uint32_t off = static_cast<uint32_t>(
            p[header_size + i * 4] |
            (p[header_size + i * 4 + 1] << 8) |
            (p[header_size + i * 4 + 2] << 16) |
            (static_cast<uint32_t>(p[header_size + i * 4 + 3]) << 24));
        if (strings_start + off >= chunk_size) {
            strings[i].clear();  // malformed entry → empty (Arsc law)
            continue;
        }
        const uint8_t* s = sdata + off;
        const size_t remain = chunk_size - strings_start - off;

        if (utf8_pool) {
            // UTF-8 pool entry: u16len then u8len (AOSP 1-or-2-byte
            // decodeLength form each), then u8len UTF-8 bytes.
            size_t o = 0;
            bool lok = true;
            decode_pool_length(s, remain, o, lok);  // u16len (units) — skipped
            if (!lok) { strings[i].clear(); continue; }
            const uint32_t u8len = decode_pool_length(s, remain, o, lok);
            if (!lok) { strings[i].clear(); continue; }
            const size_t cap = u8len < (remain - o) ? u8len : (remain - o);
            strings[i].assign(reinterpret_cast<const char*>(s + o), cap);
        } else {
            // UTF-16 pool entry: u16len (high bit → 2-char high:low form,
            // AOSP decodingString16), then UTF-16LE bytes → UTF-8 via the
            // ONE shared encoder.
            if (remain < 2) { strings[i].clear(); continue; }
            const uint16_t c0 = static_cast<uint16_t>(s[0] | (s[1] << 8));
            size_t o;
            uint32_t u16len;
            if (c0 & 0x8000) {
                if (remain < 4) { strings[i].clear(); continue; }
                const uint16_t c1 = static_cast<uint16_t>(s[2] | (s[3] << 8));
                u16len = (static_cast<uint32_t>(c0 & 0x7FFF) << 16) | c1;
                o = 4;
            } else {
                u16len = c0;
                o = 2;
            }
            const size_t bytes = u16len * 2u < (remain - o) ? u16len * 2u
                                                            : ((remain - o) & ~1u);
            strings[i] = miniandroid::dex::mutf8::utf16le_to_utf8(s + o, bytes);
        }
    }

    consumed = chunk_size;
    return true;
}

}  // namespace resources
}  // namespace miniandroid
