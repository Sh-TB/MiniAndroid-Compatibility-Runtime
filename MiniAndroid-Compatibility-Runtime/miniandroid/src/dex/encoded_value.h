// FIND-REUSE-DEX — AOSP encoded_value law (generic walker).
//
// Source audit: vova7878/DexFile @1616ed0c (raw/DexReader.java
// readEncodedValue + io/ValueCoder.java) — a faithful transfer of the
// art/libdexfile encoded-value laws. GitHub source used as engineering
// evidence for the spec laws; the laws themselves are AOSP/DEX-spec.
//
// Laws implemented here (see also dex_parser.cpp parse_static_values):
//   * value_arg is "payload byte count - 1" for every fixed-width type.
//   * BYTE/SHORT/INT/LONG: LITTLE-ENDIAN payload, SIGN-EXTENDED from
//     width*8 bits (ValueCoder readSignedInt/readSignedLong: load into
//     the high bits, then arithmetic shift right).
//   * CHAR (0x03): UNSIGNED, zero-extended on the left.
//   * FLOAT/DOUBLE: payload bits are RIGHT-ZERO-EXTENDED (stored in the
//     HIGH positions of the 32/64-bit value) — ValueCoder fillOnRight=true.
//   * STRING/TYPE/FIELD/METHOD/ENUM/METHOD_TYPE/METHOD_HANDLE: unsigned
//     index of value_arg+1 bytes.
//   * NULL: no payload. BOOLEAN: value_arg IS the value.
//   * ARRAY: ULEB128 count + count recursively-encoded values.
//   * ANNOTATION: ULEB128 name_idx + ULEB128 count + count
//     (ULEB128 name_idx + encoded_value) pairs. VARIABLE length — a fixed
//     skip desynchronizes the stream (the pre-audit decoder's bug).
//
// Hostile-input safe: bounds-checked reads, ULEB128 width caps, recursion
// is bounded by the data size (each element consumes >= 1 byte).
#ifndef MINIANDROID_DEX_ENCODED_VALUE_H
#define MINIANDROID_DEX_ENCODED_VALUE_H

#include <cstdint>
#include <cstddef>

namespace miniandroid {
namespace dex {

// Generic encoded_value walker (hostile-input safe, bounds-checked).
// Advances p past ONE encoded_value. On success returns true and fills out
// fields that apply; unknown-but-skippable payloads still return true.
// Returns false only when the stream is malformed/truncated (caller stops).
struct EncodedValue {
    uint8_t type = 0;           // raw value_type (0x00..0x1f)
    bool is_null = false;
    bool is_bool = false;
    bool bool_val = false;
    bool has_int = false;       // BYTE/SHORT/CHAR/INT/LONG (sign- or zero-extended)
    int64_t int_val = 0;
    bool has_float_bits = false;// FLOAT (32) / DOUBLE (64) raw right-zero-extended bits
    int64_t float_bits = 0;
    uint8_t float_width = 0;    // 4 or 8
    bool is_string = false;
    uint32_t string_idx = 0;
    bool has_index = false;     // TYPE/FIELD/METHOD/ENUM/METHOD_TYPE/METHOD_HANDLE unsigned idx
    uint32_t index_val = 0;
};

inline bool read_encoded_value(const uint8_t* data, size_t size, size_t& p, EncodedValue& out) {
    if (p >= size) return false;
    uint8_t header = data[p++];
    uint8_t value_type = header & 0x1f;
    uint8_t value_arg = (header >> 5) & 0x07;
    const size_t width = (size_t)value_arg + 1;
    out.type = value_type;

    auto read_le = [&](uint64_t& v) -> bool {
        v = 0;
        if (p + width > size) return false;
        for (size_t s = 0; s < width; s++) v |= (uint64_t)data[p++] << (s * 8);
        return true;
    };
    auto sign_extend = [](uint64_t v, size_t bytes) -> int64_t {
        size_t bits = bytes * 8;
        if (bits < 64 && (v >> (bits - 1)) & 1) {
            return (int64_t)(v | (~0ULL << bits));
        }
        return (int64_t)v;
    };

    // ULEB128 with completeness check: a stream that ends before the
    // terminating byte is MALFORMED (silent 0 would let truncated streams
    // "decode" as empty arrays/annotations).
    auto read_uleb = [&](uint64_t& out_val) -> bool {
        out_val = 0;
        int shift = 0;
        while (p < size) {
            uint8_t b = data[p++];
            out_val |= (uint64_t)(b & 0x7f) << shift;
            if (!(b & 0x80)) return true;
            shift += 7;
            if (shift > 63) return false;
        }
        return false;  // truncated uleb
    };

    switch (value_type) {
        case 0x00: { // VALUE_BYTE — signed
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_int = true; out.int_val = sign_extend(raw, width);
            break;
        }
        case 0x02: { // VALUE_SHORT — signed
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_int = true; out.int_val = sign_extend(raw, width);
            break;
        }
        case 0x03: { // VALUE_CHAR — unsigned zero-extended
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_int = true; out.int_val = (int64_t)raw;
            break;
        }
        case 0x04: { // VALUE_INT — signed
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_int = true; out.int_val = sign_extend(raw, width);
            break;
        }
        case 0x06: { // VALUE_LONG — signed
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_int = true; out.int_val = sign_extend(raw, width);
            break;
        }
        case 0x10: { // VALUE_FLOAT — right-zero-extended to 32 bits
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_float_bits = true; out.float_width = 4;
            out.float_bits = (int64_t)(raw << (8 * (4 - width)));
            break;
        }
        case 0x11: { // VALUE_DOUBLE — right-zero-extended to 64 bits
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_float_bits = true; out.float_width = 8;
            out.float_bits = (int64_t)(raw << (8 * (8 - width)));
            break;
        }
        case 0x15: // VALUE_METHOD_TYPE
        case 0x16: // VALUE_METHOD_HANDLE
        case 0x18: // VALUE_TYPE
        case 0x19: // VALUE_FIELD
        case 0x1a: // VALUE_METHOD
        case 0x1b: { // VALUE_ENUM — unsigned index
            uint64_t raw; if (!read_le(raw)) return false;
            out.has_index = true; out.index_val = (uint32_t)raw;
            break;
        }
        case 0x17: { // VALUE_STRING — unsigned string_idx
            uint64_t raw; if (!read_le(raw)) return false;
            out.is_string = true; out.string_idx = (uint32_t)raw;
            break;
        }
        case 0x1e: { // VALUE_NULL — no payload (spec: value_arg must be 0)
            out.is_null = true;
            break;
        }
        case 0x1f: { // VALUE_BOOLEAN — value_arg IS the value
            out.is_bool = true; out.bool_val = (value_arg != 0);
            break;
        }
        case 0x1c: { // VALUE_ARRAY — ULEB128 count + count encoded_values
            uint64_t count = 0;
            if (!read_uleb(count)) return false;
            for (uint64_t i = 0; i < count; i++) {
                EncodedValue elem;  // recursive walk; elements discarded here
                if (!read_encoded_value(data, size, p, elem)) return false;
            }
            break;
        }
        case 0x1d: { // VALUE_ANNOTATION — uleb name_idx + uleb count + (name, value) pairs
            uint64_t name_idx = 0;
            if (!read_uleb(name_idx)) return false;
            (void)name_idx;
            uint64_t count = 0;
            if (!read_uleb(count)) return false;
            for (uint64_t i = 0; i < count; i++) {
                uint64_t n = 0;
                if (!read_uleb(n)) return false;
                (void)n;
                EncodedValue elem;
                if (!read_encoded_value(data, size, p, elem)) return false;
            }
            break;
        }
        default:
            return false;  // undefined value type — malformed stream
    }
    return true;
}


}} // namespace miniandroid::dex

#endif // MINIANDROID_DEX_ENCODED_VALUE_H
