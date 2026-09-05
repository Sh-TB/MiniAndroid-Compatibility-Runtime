#!/usr/bin/env python3
"""Apply FIND-REUSE-001 edits with exact whitespace preservation.

Restores the intended logical changes to:
  - miniandroid/src/dex/dex_parser.cpp   (include + read_dex_string + ULEB lambda)
  - miniandroid/src/dex/dalvik_engine.cpp (include + read_dex_string_from_raw)
  - miniandroid/Makefile                  (add mutf8.cpp to DEX_SOURCES)

Anchors are replaced INCLUSIVE of the start anchor, EXCLUSIVE of the end
anchor. All new code uses 4-space indentation (no tabs), matching style.
"""

import sys

ROOT = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid"


def replace_span(text, start, end, new_block):
    """Replace [start..end) — start included, end kept — with new_block."""
    i = text.find(start)
    if i < 0:
        return text, False
    j = text.find(end, i + len(start))
    if j < 0:
        return text, False
    return text[:i] + new_block + text[j:], True


def edit(path, transforms):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for name, fn in transforms:
        new_text, ok = fn(text)
        if not ok:
            print(f"FAIL {path} :: {name} (anchor not found)")
            return False
        text = new_text
        print(f"ok   {path} :: {name}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def add_include(text, anchor_header):
    old = f'#include "{anchor_header}"\n'
    if '#include "mutf8.h"' in text:
        return text, True
    if old not in text:
        return text, False
    return text.replace(old, old + '#include "mutf8.h"\n', 1), True


# ---------------------------------------------------------------- dex_parser
DP = f"{ROOT}/src/dex/dex_parser.cpp"

NEW_READ_DEX_STRING = '''std::string DexParser::read_dex_string(const uint8_t* data, uint32_t offset) {
    if (offset >= current_size_) {
        return "<out of bounds>";
    }

    // FIND-REUSE-001: ONE shared MUTF-8 primitive (src/dex/mutf8.h).
    // Previously this function inlined a second ULEB128 reader and treated
    // the utf16_size prefix as a BYTE count, truncating every non-ASCII
    // string and leaving 0xC0 0x80 (encoded NUL) undecoded.
    const auto r = miniandroid::dex::mutf8::decode_string_data(data, current_size_, offset);
    if (!r.stream_ok) {
        char off_hex[16];
        snprintf(off_hex, sizeof(off_hex), "%x", offset);
        log("  MUTF-8 WARNING: string@0x" + std::string(off_hex) +
            " stream-corrupt (declared_utf16=" + std::to_string(r.declared_units) +
            " decoded=" + std::to_string(r.decoded_units) + ")");
    }
    return r.utf8;
}

'''

NEW_ULEB_LAMBDA = '''    // Read encoded header using ULEB128 - delegated to the shared
    // mutf8::read_uleb128 primitive (FIND-REUSE-001 dedup; adds the
    // 5-byte/32-bit-overflow cap this lambda previously lacked).
    auto read_uleb128 = [&data, &offset, this](uint32_t& value, const char* field_name) -> bool {
        bool ok = true;
        size_t width = 0;
        value = miniandroid::dex::mutf8::read_uleb128(data, current_size_, offset, ok, &width);
        if (!ok) {
            log(std::string("  ULEB128 ERROR at ") + field_name +
                (offset >= current_size_ ? ": offset beyond end" : ": value exceeds 32 bits"));
            return false;
        }

        log("  ULEB128[" + std::string(field_name) + "] @ 0x" + std::to_string(offset - width) +
            " = " + std::to_string(value));
        return true;
    };

'''


def dp_includes(text):
    return add_include(text, "dex_parser.h")


def dp_read_dex_string(text):
    start = "std::string DexParser::read_dex_string(const uint8_t* data, uint32_t offset) {"
    end = "std::string DexParser::get_string(uint32_t index) const {"
    return replace_span(text, start, end, NEW_READ_DEX_STRING)


def dp_uleb_lambda(text):
    start = "    // Read encoded header using ULEB128"
    end = "    DexClassDataHeader header;"
    return replace_span(text, start, end, NEW_ULEB_LAMBDA)


# -------------------------------------------------------------- dalvik_engine
DE = f"{ROOT}/src/dex/dalvik_engine.cpp"

NEW_FROM_RAW = '''    uint32_t string_data_off;
    std::memcpy(&string_data_off, raw.data() + sids_off + string_idx * 4, 4);

    if (string_data_off >= raw.size()) return "<str_data_oob>";

    // FIND-REUSE-001: delegate to the ONE shared MUTF-8 primitive.
    // Previously a third inline ULEB128 copy lived here with the same
    // utf16-size-as-byte-count truncation bug for non-ASCII strings.
    const auto r = miniandroid::dex::mutf8::decode_string_data(raw.data(), raw.size(), string_data_off);
    if (!r.stream_ok && r.utf8.empty()) return "<str_truncated>";  // structural failure, nothing decoded
    return r.utf8;
}
'''


def de_includes(text):
    return add_include(text, "dex_parser.h")


def de_from_raw(text):
    start = "    uint32_t string_data_off;"
    end = "\n\n// EXP-065: Per-DEX string resolution."
    return replace_span(text, start, end, NEW_FROM_RAW)


# -------------------------------------------------------------------- Makefile
MK = f"{ROOT}/Makefile"


def mk_sources(text):
    old = "DEX_SOURCES = $(SRCDIR)/dex/dex_parser.cpp "
    new = "DEX_SOURCES = $(SRCDIR)/dex/dex_parser.cpp $(SRCDIR)/dex/mutf8.cpp "
    if new in text:
        return text, True
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def main():
    ok = True
    ok &= edit(DP, [("includes", dp_includes),
                    ("read_dex_string", dp_read_dex_string),
                    ("uleb_lambda", dp_uleb_lambda)])
    ok &= edit(DE, [("includes", de_includes),
                    ("read_dex_string_from_raw", de_from_raw)])
    ok &= edit(MK, [("dex_sources", mk_sources)])
    if not ok:
        sys.exit(1)
    print("ALL EDITS APPLIED")


if __name__ == "__main__":
    main()
