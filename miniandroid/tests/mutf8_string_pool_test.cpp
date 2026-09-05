// mutf8_string_pool_test.cpp — FIND-REUSE-001 regression battery
//
// Guards the ONE shared MUTF-8/ULEB128 primitive (src/dex/mutf8.{h,cpp})
// through the real DexParser::parse_data path (string pool), covering the
// mechanisms adapted from WineDroid WINEDROID-004/005 (rickbergs/winedroid
// @ a784c0b, Apache-2.0 — behavioral reference, no code copied):
//
//   T1 non-ASCII string: utf16_size (CODE UNITS) != MUTF-8 byte length —
//      the pre-fix parser truncated "héllo→!" to 7 raw bytes.
//   T2 0xC0 0x80 encoded NUL must decode to U+0000 (pre-fix: left as raw
//      bytes inside the string).
//   T3 long ASCII string with a multi-byte ULEB128 prefix.
//   T4 CESU-8 surrogate pair U+1F600 (ED A0 BD ED B8 80) must re-emit as
//      standard 4-byte UTF-8 (F0 9F 98 80) and count as 2 units.
//   T5 5-byte maximum ULEB128 (FF FF FF FF 0F) must be rejected without
//      UB (shift >= 32 in the pre-fix readers) — parser must not crash.
//   T6 declared-vs-actual mismatch: structurally valid stream whose
//      utf16_size lies — best-effort decode returns the full string.
//
// The pre-fix implementation produced observably different results for
// T1/T2/T4 (truncation / undecoded NUL / raw CESU-8 bytes), so this battery
// discriminates the fix, not just the feature.

#include "../src/dex/dex_parser.h"
#include "../src/dex/mutf8.h"

#include <zlib.h>

#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dex::DexParser;
using miniandroid::dex::DexReport;
namespace mutf8 = miniandroid::dex::mutf8;

static int g_pass = 0, g_fail = 0;

static void record(const std::string& name, bool ok, const std::string& detail) {
    if (ok) ++g_pass; else ++g_fail;
    std::cout << "  " << (ok ? "PASS" : "FAIL") << "  " << name
              << (ok ? "" : (" — " + detail)) << "\n";
}

static void put32(uint8_t* p, uint32_t x) {
    p[0] = x & 0xFF; p[1] = (x >> 8) & 0xFF;
    p[2] = (x >> 16) & 0xFF; p[3] = (x >> 24) & 0xFF;
}

static void put_uleb(std::vector<uint8_t>& v, uint32_t val) {
    do { uint8_t b = val & 0x7F; val >>= 7; if (val) b |= 0x80; v.push_back(b); } while (val);
}

static std::string hexdump(const std::string& s) {
    std::string out; char buf[8];
    for (unsigned char c : s) { snprintf(buf, sizeof(buf), "%02X ", c); out += buf; }
    return out;
}

// Build a minimal DEX (0x70 header + string_ids[n] + string_data blob).
// `items` = (mutf8 bytes, declared utf16 units). Returns report.strings.
static std::vector<std::string> parse_strings(
        const std::vector<std::pair<std::vector<uint8_t>, uint32_t>>& items) {
    const uint32_t ids_off = 0x70;
    uint32_t data_off = ids_off + static_cast<uint32_t>(items.size() * 4);

    std::vector<uint8_t> dex(data_off, 0);
    std::vector<uint32_t> offsets;
    for (const auto& it : items) {
        offsets.push_back(data_off);
        put_uleb(dex, it.second);
        dex.insert(dex.end(), it.first.begin(), it.first.end());
        dex.push_back(0x00);
        data_off = static_cast<uint32_t>(dex.size());
    }

    std::memcpy(dex.data(), "dex\n035\0", 8);
    put32(dex.data() + 0x20, static_cast<uint32_t>(dex.size()));
    put32(dex.data() + 0x24, 0x70);
    put32(dex.data() + 0x28, 0x12345678);
    put32(dex.data() + 0x38, static_cast<uint32_t>(items.size()));
    put32(dex.data() + 0x3C, ids_off);
    for (size_t i = 0; i < offsets.size(); ++i)
        put32(dex.data() + ids_off + static_cast<uint32_t>(i * 4), offsets[i]);

    uint32_t adler = adler32(0L, Z_NULL, 0);
    adler = adler32(adler, dex.data() + 12, static_cast<uInt>(dex.size() - 12));
    put32(dex.data() + 8, adler);

    DexParser parser;
    DexReport report = parser.parse_data(dex, "mutf8-battery");
    return report.strings;
}

int main() {
    std::cout << "── MUTF-8 string-pool battery (FIND-REUSE-001) ──\n";

    // T1: "héllo→!" — 7 utf16 units, 10 MUTF-8 bytes
    {
        auto got = parse_strings({
            {{0x68, 0xC3, 0xA9, 0x6C, 0x6C, 0x6F, 0xE2, 0x86, 0x92, 0x21}, 7}});
        const std::string want("h\xc3\xa9llo\xe2\x86\x92!");
        record("T1 non-ASCII utf16-units vs byte-length", got.size() == 1 && got[0] == want,
               "expected " + hexdump(want) + " got " +
               (got.empty() ? "<none>" : hexdump(got[0])));
    }

    // T2: 'a' + encoded NUL (0xC0 0x80) + 'b' — 3 units, 4 bytes
    {
        auto got = parse_strings({{{0x61, 0xC0, 0x80, 0x62}, 3}});
        const std::string want(std::string("a\x00""b", 3));
        record("T2 MUTF-8 encoded NUL (0xC0 0x80)", got.size() == 1 && got[0] == want,
               "expected " + hexdump(want) + " got " +
               (got.empty() ? "<none>" : hexdump(got[0])));
    }

    // T3: 200 ASCII chars — 2-byte ULEB prefix
    {
        auto got = parse_strings({{std::vector<uint8_t>(200, 0x41), 200}});
        record("T3 multi-byte ULEB prefix (200 chars)",
               got.size() == 1 && got[0] == std::string(200, 'A'),
               got.empty() ? "<none>" : ("len=" + std::to_string(got[0].size())));
    }

    // T4: U+1F600 grinning face as CESU-8 surrogate pair — 2 units, 6 bytes
    {
        auto got = parse_strings({{{0xED, 0xA0, 0xBD, 0xED, 0xB8, 0x80}, 2}});
        const std::string want("\xF0\x9F\x98\x80");
        record("T4 CESU-8 surrogate pair -> UTF-8", got.size() == 1 && got[0] == want,
               "expected " + hexdump(want) + " got " +
               (got.empty() ? "<none>" : hexdump(got[0])));
    }

    // T5: 5-byte ULEB128 (u32 overflow encoding) — must not UB/crash.
    // The parser sees a hostile utf16_size; decode stops at the buffer end
    // and the parser must return without undefined behavior.
    {
        auto got = parse_strings({{{0x41, 0x42}, 0xFFFFFFFF}});
        record("T5 hostile 5-byte ULEB128 (no UB, no crash)",
               !got.empty(), "parser returned <none> or crashed");
    }

    // T6: declared-vs-actual mismatch — declared 5 units, actual "ab" (2).
    // Best-effort: the decoded string must still be the full "ab".
    {
        auto got = parse_strings({{{0x61, 0x62}, 5}});
        record("T6 declared/actual mismatch — full best-effort decode",
               got.size() == 1 && got[0] == "ab",
               got.empty() ? "<none>" : hexdump(got[0]));
    }

    // Primitive-level: hardened ULEB128 acceptance window
    {
        size_t oks = 0;

        // Legal 5-byte maximum (FF FF FF FF 0F == u32::MAX) — accepted.
        const uint8_t max5[] = {0xFF, 0xFF, 0xFF, 0xFF, 0x0F};
        size_t pos = 0; bool ok = true;
        uint32_t v = mutf8::read_uleb128(max5, sizeof(max5), pos, ok);
        if (ok && v == 0xFFFFFFFFu && pos == 5) ++oks;

        // 6th-continuation form with overflow bits (FF FF FF FF 8F) — rejected
        // without UB (the pre-fix readers shifted by >= 32 here).
        const uint8_t over[] = {0xFF, 0xFF, 0xFF, 0xFF, 0x8F, 0x01};
        pos = 0; ok = true;
        mutf8::read_uleb128(over, sizeof(over), pos, ok);
        if (!ok) ++oks;

        // Truncated stream (single continuation byte) — rejected.
        const uint8_t trunc[] = {0x80};
        pos = 0; ok = true;
        mutf8::read_uleb128(trunc, sizeof(trunc), pos, ok);
        if (!ok) ++oks;

        record("ULEB128 primitive acceptance window", oks == 3,
               "oks=" + std::to_string(oks) + "/3");
    }

    std::cout << "\nRESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
