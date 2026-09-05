// mutf8.cpp — implementation of the shared DEX string-decoding primitive.
// See mutf8.h for the mechanism provenance (WINEDROID-004/005 adaptation).

#include "mutf8.h"

namespace miniandroid {
namespace dex {
namespace mutf8 {

uint32_t read_uleb128(const uint8_t* data, size_t cap, size_t& pos,
                      bool& ok, size_t* width) {
    ok = true;
    if (width) *width = 0;
    if (pos >= cap) { ok = false; return 0; }

    uint32_t value = 0;
    int shift = 0;
    for (int i = 0; i < 5; ++i) {
        if (pos >= cap) { ok = false; return 0; }
        const uint8_t byte = data[pos++];
        if (width) *width = static_cast<size_t>(i + 1);
        if (i == 4 && byte > 0x0F) {  // would exceed 32 bits (WineDroid-005 law)
            ok = false;
            return 0;
        }
        value |= static_cast<uint32_t>(byte & 0x7F) << shift;
        if ((byte & 0x80) == 0) return value;
        shift += 7;
    }
    ok = false;  // 5 continuation bytes — malformed (value > u32::MAX)
    return 0;
}

namespace {

// Append one code point to the output as standard UTF-8.
void append_utf8_impl(std::string& out, uint32_t cp) {
    if (cp < 0x80) {
        out.push_back(static_cast<char>(cp));
    } else if (cp < 0x800) {
        out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else if (cp < 0x10000) {
        out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else {
        out.push_back(static_cast<char>(0xF0 | (cp >> 18)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
}

constexpr uint32_t REPLACEMENT = 0xFFFD;
constexpr uint32_t HIGH_MIN = 0xD800, HIGH_MAX = 0xDBFF;
constexpr uint32_t LOW_MIN = 0xDC00, LOW_MAX = 0xDFFF;

inline bool is_continuation(uint8_t b) { return (b & 0xC0) == 0x80; }

}  // namespace

int32_t read_sleb128(const uint8_t* data, size_t cap, size_t& pos,
                     bool& ok, size_t* width) {
    ok = true;
    if (width) *width = 0;
    if (pos >= cap) { ok = false; return 0; }

    int32_t value = 0;
    int shift = 0;
    uint8_t byte = 0;
    for (int i = 0; i < 5; ++i) {
        if (pos >= cap) { ok = false; return 0; }
        byte = data[pos++];
        if (width) *width = static_cast<size_t>(i + 1);
        if (i == 4) {
            // 5th byte contributes bits 28..31 only (4 value bits); a
            // continuation bit or a 5th value bit would exceed i32 —
            // hardened reject (mirrors read_uleb128's >0x0F law, keeps
            // the shift inside defined behavior).
            if ((byte & 0x80) || (byte & 0x7F) > 0x0F) { ok = false; return 0; }
            value |= static_cast<int32_t>(byte & 0x0F) << 28;
            return value;  // bit 31 already carries the sign (two's complement)
        }
        value |= static_cast<int32_t>(byte & 0x7F) << shift;
        shift += 7;
        if ((byte & 0x80) == 0) {
            // Sign-extend from bit 6 of the final byte (SLEB128 law).
            if (shift < 32 && (byte & 0x40)) value |= -(1 << shift);
            return value;
        }
    }
    ok = false;  // unreachable — every path above returns
    return 0;
}

void append_utf8(std::string& out, uint32_t cp) { append_utf8_impl(out, cp); }

std::string utf16le_to_utf8(const uint8_t* bytes, size_t byte_len) {
    std::string out;
    out.reserve(byte_len);  // upper bound: 1 byte per UTF-16 unit for ASCII
    size_t i = 0;
    while (i + 1 < byte_len) {
        uint32_t ch = static_cast<uint32_t>(bytes[i]) |
                      (static_cast<uint32_t>(bytes[i + 1]) << 8);
        if (ch >= HIGH_MIN && ch <= HIGH_MAX) {
            // High surrogate: combine ONLY with a following low surrogate;
            // a truncated pair or a non-low tail emits U+FFFD (AOSP law —
            // the pre-consolidation copies encoded the raw surrogate as
            // invalid 3-byte WTF-8 instead).
            bool combined = false;
            if (i + 3 < byte_len) {
                const uint32_t lo = static_cast<uint32_t>(bytes[i + 2]) |
                                    (static_cast<uint32_t>(bytes[i + 3]) << 8);
                if (lo >= LOW_MIN && lo <= LOW_MAX) {
                    ch = 0x10000 + ((ch - HIGH_MIN) << 10) + (lo - LOW_MIN);
                    i += 2;  // consume the low surrogate too
                    combined = true;
                }
            }
            if (!combined) ch = REPLACEMENT;
        } else if (ch >= LOW_MIN && ch <= LOW_MAX) {
            ch = REPLACEMENT;  // standalone low surrogate
        }
        i += 2;
        append_utf8_impl(out, ch);
    }
    return out;
}

DecodeResult decode_string_data(const uint8_t* data, size_t cap, size_t offset) {
    DecodeResult r;
    r.decoded_units = 0;
    r.declared_units = 0;
    r.stream_ok = true;
    r.declared_match = false;

    if (offset >= cap) {
        r.stream_ok = false;
        return r;
    }

    size_t pos = offset;
    bool uleb_ok = true;
    r.declared_units = read_uleb128(data, cap, pos, uleb_ok);
    if (!uleb_ok) {
        r.stream_ok = false;
        return r;
    }

    while (true) {
        if (pos >= cap) { r.stream_ok = false; break; }
        const uint8_t b1 = data[pos++];

        if (b1 == 0x00) break;  // NUL terminator (spec)

        if (b1 < 0x80) {                      // 1-byte ASCII
            r.utf8.push_back(static_cast<char>(b1));
            ++r.decoded_units;
            continue;
        }

        if ((b1 & 0xE0) == 0xC0) {            // 2-byte (MUTF-8: 0xC0 0x80 = NUL)
            if (pos >= cap || !is_continuation(data[pos])) {
                append_utf8(r.utf8, REPLACEMENT);
                r.stream_ok = false;
                ++r.decoded_units;
                continue;
            }
            const uint8_t b2 = data[pos++];
            const uint32_t cp = (static_cast<uint32_t>(b1 & 0x1F) << 6) |
                                static_cast<uint32_t>(b2 & 0x3F);
            append_utf8(r.utf8, cp);          // includes 0xC0 0x80 -> U+0000
            ++r.decoded_units;
            continue;
        }

        if ((b1 & 0xF0) == 0xE0) {            // 3-byte, may start a surrogate pair
            if (pos + 1 >= cap || !is_continuation(data[pos]) ||
                !is_continuation(data[pos + 1])) {
                append_utf8(r.utf8, REPLACEMENT);
                r.stream_ok = false;
                ++r.decoded_units;
                continue;
            }
            const uint8_t b2 = data[pos], b3 = data[pos + 1];
            const uint32_t cp = (static_cast<uint32_t>(b1 & 0x0F) << 12) |
                                (static_cast<uint32_t>(b2 & 0x3F) << 6) |
                                static_cast<uint32_t>(b3 & 0x3F);
            pos += 2;

            if (cp >= HIGH_MIN && cp <= HIGH_MAX) {
                // High surrogate: a valid MUTF-8 stream must continue with the
                // low surrogate as a second 3-byte CESU-8 sequence:
                //   0xED, 0xB0..0xBF, continuation
                if (pos + 2 < cap && data[pos] == 0xED &&
                    data[pos + 1] >= 0xB0 && data[pos + 1] <= 0xBF &&
                    is_continuation(data[pos + 2])) {
                    const uint32_t low =
                        0xD000 + (static_cast<uint32_t>(data[pos + 1] & 0x3F) << 6) +
                        static_cast<uint32_t>(data[pos + 2] & 0x3F);
                    pos += 3;  // consume lead + 2 continuations of the low surrogate
                    if (low >= LOW_MIN && low <= LOW_MAX) {
                        const uint32_t combined =
                            0x10000 + ((cp - HIGH_MIN) << 10) + (low - LOW_MIN);
                        append_utf8(r.utf8, combined);
                    } else {
                        append_utf8(r.utf8, REPLACEMENT);
                        r.stream_ok = false;
                    }
                    r.decoded_units += 2;  // a supplementary pair = 2 units
                    continue;
                }
                // high surrogate without a valid low tail
                append_utf8(r.utf8, REPLACEMENT);
                r.stream_ok = false;
                ++r.decoded_units;
                continue;
            }

            if (cp >= LOW_MIN && cp <= LOW_MAX) {
                // standalone low surrogate — malformed MUTF-8
                append_utf8(r.utf8, REPLACEMENT);
                r.stream_ok = false;
                ++r.decoded_units;
                continue;
            }

            append_utf8(r.utf8, cp);          // plain 3-byte BMP character
            ++r.decoded_units;
            continue;
        }

        // MUTF-8 has no 4-byte form and no 0x80..0xBF/0xF8..0xFF leads.
        append_utf8(r.utf8, REPLACEMENT);
        r.stream_ok = false;
        ++r.decoded_units;
    }

    r.declared_match = (r.decoded_units == r.declared_units);
    if (!r.declared_match) r.stream_ok = false;
    return r;
}

}  // namespace mutf8
}  // namespace dex
}  // namespace miniandroid
