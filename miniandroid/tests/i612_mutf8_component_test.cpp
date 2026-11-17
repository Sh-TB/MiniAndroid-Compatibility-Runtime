// ISSUE-612 WAVE-2 — L0 component test: dex/mutf8 (production TU, minimal closure)
//
// Phase 4 contract: this executable links ONLY build/dex/mutf8.o — the
// production implementation, not a test duplicate. A change to mutf8.cpp
// rebuilds one ~0.2s object and relinks a ~1MB binary; the full runtime and
// the 216s dalvik TU are NOT involved.
//
// Build (via Makefile target `mutf8_component` or dev.py):
//   make DEV=1 mutf8_component
#include <cstdint>
#include <cstddef>
#include <string>
#include <cassert>
#include <cstdio>

#include "dex/mutf8.h"

using miniandroid::dex::mutf8::read_uleb128;
using miniandroid::dex::mutf8::read_sleb128;
using miniandroid::dex::mutf8::append_utf8;
using miniandroid::dex::mutf8::utf16le_to_utf8;
using miniandroid::dex::mutf8::decode_string_data;

static int g_checks = 0;
#define CHECK(cond) do { ++g_checks; if (!(cond)) { \
    std::fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #cond); return 1; } } while (0)

int main() {
    // ── L0: ULEB128 decode — canonical widths + truncation detection ──
    {   // 1-byte (0..0x7f)
        const uint8_t in[] = {0x00, 0x01, 0x7f};
        size_t pos = 0; bool ok = true; size_t width = 0;
        CHECK(read_uleb128(in, sizeof in, pos, ok, &width) == 0x00 && ok && width == 1);
        pos = 1;
        CHECK(read_uleb128(in, sizeof in, pos, ok, &width) == 0x01 && ok && width == 1);
        pos = 2;
        CHECK(read_uleb128(in, sizeof in, pos, ok, &width) == 0x7f && ok && width == 1);
    }
    {   // 2-byte (0x80 0x01 = 128) and 3-byte continuation
        const uint8_t in[] = {0x80, 0x01, 0xff, 0x7f};
        size_t pos = 0; bool ok = true; size_t width = 0;
        CHECK(read_uleb128(in, sizeof in, pos, ok, &width) == 128 && ok && width == 2);
        pos = 2;
        CHECK(read_uleb128(in, sizeof in, pos, ok, &width) == 0x3fff && ok && width == 2);
    }
    {   // 4-byte max (0x0fffffff), 5-byte 0x1fffffff and 0x20000000 (DEX limit family)
        const uint8_t in[] = {0xff, 0xff, 0xff, 0x7f,
                              0xff, 0xff, 0xff, 0xff, 0x01,
                              0x80, 0x80, 0x80, 0x80, 0x02};
        size_t pos = 0; bool ok = true;
        CHECK(read_uleb128(in, sizeof in, pos, ok) == 0x0fffffffu && ok);
        CHECK(read_uleb128(in, sizeof in, pos, ok) == 0x1fffffffu && ok);
        CHECK(read_uleb128(in, sizeof in, pos, ok) == 0x20000000u && ok);
    }
    {   // 5th byte > 0x0F would exceed 32 bits — must fail cleanly (WineDroid-005 law)
        const uint8_t in[] = {0xff, 0xff, 0xff, 0xff, 0x10};
        size_t pos = 0; bool ok = true;
        read_uleb128(in, sizeof in, pos, ok);
        CHECK(!ok);
    }
    {   // truncated stream must fail cleanly (ok=false), not read OOB
        const uint8_t in[] = {0x80};
        size_t pos = 0; bool ok = true;
        read_uleb128(in, sizeof in, pos, ok);
        CHECK(!ok);
    }

    // ── L0: SLEB128 — negative + sign-extension discipline ──
    {   // -1 encodes as 0x7f (1 byte); -64 as {0xc0, 0x7f}
        const uint8_t in[] = {0x7f, 0xc0, 0x7f};
        size_t pos = 0; bool ok = true; size_t width = 0;
        CHECK(read_sleb128(in, sizeof in, pos, ok, &width) == -1 && ok && width == 1);
        CHECK(read_sleb128(in, sizeof in, pos, ok, &width) == -64 && ok && width == 2);
    }

    // ── L0: append_utf8 — 1/2/3-byte encodes ──
    {
        std::string out;
        append_utf8(out, 'A');              // 1-byte
        append_utf8(out, 0x00e9);           // 2-byte é
        append_utf8(out, 0x20ac);           // 3-byte €
        CHECK(out.size() == 1 + 2 + 3);
        CHECK((uint8_t)out[0] == 0x41);
        CHECK((uint8_t)out[1] == 0xc3 && (uint8_t)out[2] == 0xa9);
        CHECK((uint8_t)out[3] == 0xe2 && (uint8_t)out[4] == 0x82 && (uint8_t)out[5] == 0xac);
    }

    // ── L0: utf16le_to_utf8 — ASCII + paired-surrogate combine (AOSP law) ──
    {
        const uint8_t ascii[] = {'H', 0, 'i', 0};
        CHECK(utf16le_to_utf8(ascii, 4) == "Hi");
    }
    {
        // U+1F600 = D83D DE00 in UTF-16LE → 4-byte UTF-8 (F0 9F 98 80)
        const uint8_t emoji[] = {0x3d, 0xd8, 0x00, 0xde};
        std::string s = utf16le_to_utf8(emoji, 4);
        CHECK(s.size() == 4 && (uint8_t)s[0] == 0xf0 && (uint8_t)s[1] == 0x9f);
    }

    // ── L0: decode_string_data — MUTF-8 contract ──
    {   // "AB" with utf16_size=2
        const uint8_t item[] = {0x02, 'A', 'B', 0x00};
        auto r = decode_string_data(item, sizeof item, 0);
        CHECK(r.stream_ok && r.declared_match);
        CHECK(r.utf8 == "AB" && r.decoded_units == 2 && r.declared_units == 2);
    }
    {   // 0xC0 0x80 = encoded NUL (U+0000) — must NOT terminate the string;
        // declared=1 (one UTF-16 unit). PRODUCTION LAW: any declared/decoded
        // mismatch also clears stream_ok (post-loop cross-check in mutf8.cpp).
        const uint8_t item[] = {0x01, 0xc0, 0x80, 0x00};
        auto r = decode_string_data(item, sizeof item, 0);
        CHECK(r.stream_ok && r.declared_match);
        CHECK(r.utf8.size() == 1 && r.utf8[0] == '\0' && r.decoded_units == 1);
    }
    {   // CESU-8 surrogate pair ED A0 BD / ED B8 B8 → U+1F600 → 4-byte UTF-8
        const uint8_t item[] = {0x02, 0xed, 0xa0, 0xbd, 0xed, 0xb8, 0xb8, 0x00};
        auto r = decode_string_data(item, sizeof item, 0);
        CHECK(r.stream_ok && r.utf8.size() == 4 && (uint8_t)r.utf8[0] == 0xf0);
    }
    {   // declared > actual → declared_match=false (integrity cross-check)
        const uint8_t item[] = {0x05, 'A', 0x00};
        auto r = decode_string_data(item, sizeof item, 0);
        CHECK(!r.declared_match);
    }

    std::printf("PASS mutf8_component — %d checks (production dex/mutf8.o closure)\n", g_checks);
    return 0;
}
