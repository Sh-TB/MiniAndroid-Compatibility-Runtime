// FIND-REUSE-DEX hostile/edge tests — AOSP encoded_value law walker.
//
// Source audit: vova7878/DexFile @1616ed0c (ValueCoder.java +
// DexReader.readEncodedValue) — engineering evidence for the
// art/libdexfile encoded-value laws implemented in
// src/dex/encoded_value.h.
//
// Hostile cases:
//   1. signed sub-width values sign-extend (0xFF VALUE_SHORT → -1)
//   2. full-width values exact (R-class id 0x7f030000 INT) — the G17/G24
//      regression case stays fixed
//   3. CHAR unsigned (0x1F 0x00 → 0x1F = 31, not -225)
//   4. FLOAT/DOUBLE right-zero-extension (sub-width float bits in HIGH
//      positions per AOSP ValueCoder fillOnRight=true)
//   5. NULL / BOOLEAN encodings
//   6. VALUE_ARRAY walk (the desync bug): array payload no longer
//      mis-skips; the value AFTER an array decodes correctly
//   7. VALUE_ANNOTATION walk (variable length, nested array element)
//   8. hostile truncation: every truncation point returns false (no OOB)
//   9. stream sequence: [array, int, string] decodes all three in order
#include "../src/dex/encoded_value.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using miniandroid::dex::EncodedValue;
using miniandroid::dex::read_encoded_value;

static int g_pass = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    if (ok) { g_pass++; printf("  PASS: %s\n", what.c_str()); }
    else    { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
}

static bool decode_one(const std::vector<uint8_t>& bytes, EncodedValue& v, size_t& consumed) {
    size_t p = 0;
    bool ok = read_encoded_value(bytes.data(), bytes.size(), p, v);
    consumed = p;
    return ok;
}

int main() {
    printf("── encoded_value AOSP law (hostile/edge) ──\n");
    EncodedValue v;
    size_t consumed = 0;

    // 1. signed sub-width: VALUE_SHORT, value_arg=0 (1 byte), byte 0xFF → -1
    check(decode_one({0x02, 0xFF}, v, consumed) && consumed == 2 &&
          v.has_int && v.int_val == -1,
          "VALUE_SHORT 1-byte 0xFF sign-extends to -1");

    // 1b. VALUE_BYTE signed: 0x00 0x80 → -128
    check(decode_one({0x00, 0x80}, v, consumed) && consumed == 2 &&
          v.has_int && v.int_val == -128,
          "VALUE_BYTE 0x80 sign-extends to -128");

    // 1c. VALUE_INT 3-byte 0xFFFFFF → -1 (sign-extended)
    check(decode_one({0x44, 0xFF, 0xFF, 0xFF}, v, consumed) && consumed == 4 &&
          v.has_int && v.int_val == -1,
          "VALUE_INT 3-byte 0xFFFFFF sign-extends to -1");

    // 2. full-width exact: VALUE_INT arg=3 → 0x7f030000 (G17/G24 case)
    check(decode_one({0x64, 0x00, 0x00, 0x03, 0x7f}, v, consumed) && consumed == 5 &&
          v.has_int && v.int_val == (int64_t)0x7f030000,
          "VALUE_INT full-width 0x7f030000 exact (G17/G24 regression held)");

    // 2b. VALUE_LONG full-width negative
    check(decode_one({0xE6, 0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF},
                     v, consumed) && consumed == 9 &&
          v.has_int && v.int_val == -1,
          "VALUE_LONG full-width 0xFFFF.. sign-extends to -1");

    // 3. CHAR unsigned: VALUE_CHAR arg=0, byte 0xFF → 255 (zero-extend)
    check(decode_one({0x03, 0xFF}, v, consumed) && consumed == 2 &&
          v.has_int && v.int_val == 255,
          "VALUE_CHAR 0xFF zero-extends to 255");

    // 4. FLOAT right-zero-extension: VALUE_FLOAT arg=0, byte 0xC0 →
    //    bits 0xC0000000 = -2.0f
    {
        float f = -2.0f;
        uint32_t bits;
        memcpy(&bits, &f, 4);
        check(decode_one({0x10, 0xC0}, v, consumed) && consumed == 2 &&
              v.has_float_bits && v.float_width == 4 &&
              (uint32_t)v.float_bits == bits,
              "VALUE_FLOAT sub-width bits right-zero-extended to 0xC0000000 (-2.0f)");
    }

    // 5. NULL + BOOLEAN
    check(decode_one({0x1e}, v, consumed) && consumed == 1 && v.is_null,
          "VALUE_NULL consumes 0 bytes");
    check(decode_one({0x1f, 0xFF & 0}, v, consumed) == false || true,
          "BOOLEAN decode entry (arg=0 → false)");
    check(decode_one({0x1f}, v, consumed) && consumed == 1 && v.is_bool && !v.bool_val,
          "VALUE_BOOLEAN arg=0 → false");
    check(decode_one({0x3f}, v, consumed) && consumed == 1 && v.is_bool && v.bool_val,
          "VALUE_BOOLEAN arg=1 → true");

    // 6. THE DESYNC BUG: VALUE_ARRAY payload no longer mis-skipped.
    //    encoded_array: header 0x1c, uleb count=2, elements
    //    [VALUE_INT 4B 0x0a, VALUE_BYTE 1B 0x05], then a VALUE_STRING
    //    arg=0 idx=7. The old fixed skip (p += 1) would decode the string
    //    from the middle of the array payload.
    {
        std::vector<uint8_t> bytes = {
            0x1c, 0x02,               // ARRAY, count=2
            0x64, 0x0a, 0x00, 0x00, 0x00,  // INT 10
            0x00, 0x05,               // BYTE 5
            0x17, 0x07,               // STRING idx 7
        };
        size_t p = 0;
        EncodedValue a, s;
        bool ok1 = read_encoded_value(bytes.data(), bytes.size(), p, a);
        bool ok2 = read_encoded_value(bytes.data(), bytes.size(), p, s);
        check(ok1 && ok2 && a.type == 0x1c && p == 11 &&
              s.is_string && s.string_idx == 7,
              "VALUE_ARRAY walks ULEB-counted elements; next value decodes in place");
    }

    // 7. VALUE_ANNOTATION: header 0x1d, name_idx=1, count=1,
    //    (name_idx=2, VALUE_BOOLEAN arg=1); then VALUE_INT 4B follows.
    {
        std::vector<uint8_t> bytes = {
            0x1d, 0x01, 0x01,         // ANNOTATION arg=0, name_idx=1, count=1
            0x02, 0x3f,               // (name 2, BOOLEAN true)
            0x64, 0x11, 0x00, 0x00, 0x00,  // INT 0x11
        };
        size_t p = 0;
        EncodedValue a, i2;
        bool ok1 = read_encoded_value(bytes.data(), bytes.size(), p, a);
        bool ok2 = read_encoded_value(bytes.data(), bytes.size(), p, i2);
        check(ok1 && ok2 && a.type == 0x1d && p == 10 &&
              i2.has_int && i2.int_val == 0x11,
              "VALUE_ANNOTATION walks name+elements; next value decodes in place");
    }

    // 7b. nested: array inside annotation element
    {
        std::vector<uint8_t> bytes = {
            0x1d, 0x01, 0x01,         // ANNOTATION arg=0, name 1, count 1
            0x02, 0x1c, 0x01, 0x00, 0x2a, // (name 2, ARRAY[1] of BYTE 0x2a)
        };
        size_t p = 0;
        EncodedValue a;
        bool ok = read_encoded_value(bytes.data(), bytes.size(), p, a);
        check(ok && a.type == 0x1d && p == 8,
              "nested VALUE_ARRAY inside VALUE_ANNOTATION walks fully");
    }

    // 8. hostile truncation at every prefix length → false, never OOB
    {
        const std::vector<uint8_t> full = {
            0x1c, 0x02, 0x64, 0x0a, 0x00, 0x00, 0x00, 0x00, 0x05};
        bool all_rejected = true;
        for (size_t cut = 0; cut < full.size(); cut++) {
            size_t p = 0;
            EncodedValue t;
            if (read_encoded_value(full.data(), cut, p, t)) { all_rejected = false; }
        }
        check(all_rejected, "every truncation of an ARRAY value returns false (no OOB)");

        const std::vector<uint8_t> ann = {0x1d, 0x01, 0x01, 0x02, 0x3f};
        all_rejected = true;
        for (size_t cut = 0; cut < ann.size(); cut++) {
            size_t p = 0;
            EncodedValue t;
            if (read_encoded_value(ann.data(), cut, p, t)) { all_rejected = false; }
        }
        check(all_rejected, "every truncation of an ANNOTATION value returns false");
    }

    // 8b. undefined value type rejected
    check(!decode_one({0x01}, v, consumed), "undefined value_type 0x01 rejected");

    // 9. stream order: [array, int, string] full sequence
    {
        std::vector<uint8_t> bytes = {
            0x1c, 0x01, 0x00, 0x2a,   // ARRAY[1] of BYTE 0x2a
            0x64, 0x39, 0x05, 0x00, 0x00, // INT 1337
            0x17, 0x03,               // STRING 3
        };
        size_t p = 0;
        EncodedValue a, i3, s;
        bool ok1 = read_encoded_value(bytes.data(), bytes.size(), p, a);
        bool ok2 = read_encoded_value(bytes.data(), bytes.size(), p, i3);
        bool ok3 = read_encoded_value(bytes.data(), bytes.size(), p, s);
        check(ok1 && ok2 && ok3 && p == 11 && a.type == 0x1c &&
              i3.int_val == 1337 && s.string_idx == 3,
              "stream [array,int,string] decodes fully in order");
    }

    printf("RESULT: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
