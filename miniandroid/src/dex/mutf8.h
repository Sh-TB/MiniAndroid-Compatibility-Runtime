// mutf8.h — ONE shared primitive for DEX string decoding + varint +
// UTF-16LE→UTF-8 encoding.
//
// REUSE-FIRST CAMPAIGN (FIND-REUSE-001): the ULEB128 + MUTF-8 logic that
// previously existed as THREE separate copies (dex_parser.cpp class-data
// lambda, dex_parser.cpp::read_dex_string, dalvik_engine.cpp::
// read_dex_string_from_raw) now lives here exactly once.
//
// REUSE-FIRST CAMPAIGN (FIND-REUSE-002/003, this session): the same
// consolidation law applied to the remaining format primitives:
//   * read_sleb128 — was 2 inline lambda copies in dalvik_engine.cpp
//     (exception dispatch + find_catch_handler_for_pc)
//   * utf16le_to_utf8 / append_utf8 — was 4 separate encoder copies:
//     arsc_parser.cpp string pool, axml_parser.cpp string pool,
//     manifest_reader.cpp string pool (that copy lacked surrogate-pair
//     handling — non-BMP manifest strings double-encoded; fixed by this
//     consolidation), dalvik_engine.cpp String.replace utf8_of lambda.
//
// Mechanisms (provenance):
//   * WINEDROID-005 (WineDroid rickbergs/winedroid @ a784c0b, Apache-2.0,
//     crates/winedroid-core/src/dex.rs read_uleb128): max 5 bytes; final
//     byte at index 4 must be <= 0x0F; bounds-checked. Adapted (not copied)
//     to C++ for MiniAndroid.
//   * WINEDROID-004 (same source, decode_mutf8): MUTF-8 decoding with
//     0xC0 0x80 encoded NUL, CESU-8 surrogate pairs, and the
//     declared-vs-actual utf16-length cross-check. Adapted to MiniAndroid.
//   * DEX format law: string_data_item = utf16_size (ULEB128, UTF-16 code
//     units) + data (MUTF-8 bytes, NUL-terminated);
//     encoded_catch_handler_list = sleb128 size + |size|×(uleb128 type_idx,
//     uleb128 addr) [+ uleb128 catch_all_addr].
//     https://source.android.com/docs/core/runtime/dex-format
//   * AOSP String.cpp utf16_to_utf8 law: UTF-16LE pools combine surrogate
//     pairs into 4-byte UTF-8; unpaired surrogates emit U+FFFD
//     (frameworks/base/libs/androidfw + core/jni/String.cpp).
//
// License: this file is original MiniAndroid code (GPL-3.0-or-later like the
// rest of the repository); the WineDroid sources were used as a behavioral
// reference only — no code was copied.

#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

namespace miniandroid {
namespace dex {
namespace mutf8 {

// Hardened ULEB128 reader.
//   data : buffer base
//   cap  : total buffer size (bounds limit)
//   pos  : in/out cursor; advanced past the encoding on success
//   ok   : set false on truncation, >5 bytes, or u32 overflow
//   width: optional out — number of bytes consumed
// Returns 0 when !ok.
uint32_t read_uleb128(const uint8_t* data, size_t cap, size_t& pos,
                      bool& ok, size_t* width = nullptr);

// Hardened SLEB128 reader (DEX signed varint: encoded_catch_handler sizes
// and debug_info offsets). Same bounds/width discipline as read_uleb128.
//   data : buffer base
//   cap  : bounds limit (pass the SUB-BUFFER end to reproduce the old
//          handler_list_end-scoped lambdas)
//   pos  : in/out cursor; advanced past the encoding on success
//   ok   : set false on truncation, >5 bytes, or sign-overflow past i32
//   width: optional out — number of bytes consumed
// Returns 0 when !ok.
int32_t read_sleb128(const uint8_t* data, size_t cap, size_t& pos,
                     bool& ok, size_t* width = nullptr);

// Append one code point to `out` as standard UTF-8 (1–4 bytes).
// Shared by decode_string_data re-encoding and single-code-point callers
// (e.g. String.replace(char,char) building needle/replacement strings).
void append_utf8(std::string& out, uint32_t cp);

// Encode a UTF-16LE byte stream (ARSC/AXML/manifest string pools) as
// standard UTF-8. Combines surrogate pairs into 4-byte sequences; an
// unpaired high/low surrogate emits U+FFFD (AOSP String.cpp law).
//   bytes    : UTF-16LE byte stream base
//   byte_len : length in BYTES (an odd trailing byte is ignored)
std::string utf16le_to_utf8(const uint8_t* bytes, size_t byte_len);

struct DecodeResult {
    std::string utf8;        // best-effort decoded string (standard UTF-8)
    uint32_t decoded_units;  // UTF-16 code units actually decoded
    uint32_t declared_units; // utf16_size read from the item prefix
    bool stream_ok;          // structural integrity (valid ULEB, valid MUTF-8
                             // sequences, NUL terminator found within cap)
    bool declared_match;     // decoded_units == declared_units
};

// Decode one DEX string_data_item located at data[offset..cap):
// ULEB128 utf16_size, then MUTF-8 bytes terminated by 0x00.
//
// MUTF-8 specifics handled:
//   * 0xC0 0x80 is the encoded NUL (U+0000) — not a terminator
//   * 3-byte CESU-8 surrogate pairs (ED A0-BF .. ED B8-BF) are combined and
//     re-emitted as standard 4-byte UTF-8
//   * invalid sequences emit U+FFFD and clear stream_ok (diagnostic, not
//     fatal — the runtime keeps running and the corruption is observable)
DecodeResult decode_string_data(const uint8_t* data, size_t cap, size_t offset);

}  // namespace mutf8
}  // namespace dex
}  // namespace miniandroid
