// GP-582 ASan reproducer probes — resources parsers (GP-RES-001/002/003)
// Compiled against the REAL repo sources under ASan; each probe feeds a
// crafted malformed chunk and must NOT perform OOB accesses post-fix.
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <vector>
#include <string>

#include "resources/string_pool.h"
#include "resources/arsc_parser.h"

using namespace miniandroid::resources;

static void put32(std::vector<uint8_t>& v, size_t off, uint32_t x) {
    v[off] = x & 0xff; v[off+1] = (x>>8)&0xff; v[off+2] = (x>>16)&0xff; v[off+3] = (x>>24)&0xff;
}
static void put16(std::vector<uint8_t>& v, size_t off, uint16_t x) {
    v[off] = x & 0xff; v[off+1] = (x>>8)&0xff;
}

// ── GP-RES-001: strings_start + off wraps in uint32 → OOB decode ──
bool probe_res001() {
    // 64-byte pool: header 28 + offset table (1 entry) + 4 bytes string data
    std::vector<uint8_t> buf(64, 0);
    put32(buf, 0, 0x0001);      // type = RES_STRING_POOL_TYPE
    put16(buf, 2, 28);          // header_size
    put32(buf, 4, 64);          // chunk_size
    put32(buf, 8, 1);           // string_count = 1
    put32(buf, 12, 0);          // style_count
    put32(buf, 16, 0);          // flags = UTF-16
    put32(buf, 20, 0xFFFFFFF0); // strings_start (wraps with the entry offset)
    put32(buf, 24, 0);          // styles_start
    put32(buf, 28, 0x20);       // entry[0] offset = 0x20 → 0xFFFFFFF0+0x20 wraps to 0x10 < 64
    ResStringPool pool;
    size_t consumed = 0;
    std::string err;
    bool ok = pool.parse(buf.data(), buf.size(), consumed, &err);
    printf("[GP-RES-001] parse ok=%d err=%s strings=%zu\n", (int)ok,
           err.c_str(), pool.strings.size());
    return true;
}

// ── GP-RES-001b: string_count*4u wraps → offset-table check bypassed ──
bool probe_res001_alloc() {
    std::vector<uint8_t> buf(64, 0);
    put32(buf, 0, 0x0001);
    put16(buf, 2, 28);
    put32(buf, 4, 64);
    put32(buf, 8, 0x40000000);  // string_count = 1G → *4u wraps to 0 → check passes → huge resize
    put32(buf, 12, 0);
    put32(buf, 16, 0);
    put32(buf, 20, 40);
    put32(buf, 24, 0);
    ResStringPool pool;
    size_t consumed = 0;
    std::string err;
    bool ok = pool.parse(buf.data(), buf.size(), consumed, &err);
    printf("[GP-RES-001b] parse ok=%d err=%s strings=%zu\n", (int)ok,
           err.c_str(), pool.strings.size());
    return true;
}

// ── Minimal resources.arsc builder: table hdr + empty global pool + pkg ──
// Returns the buffer; type_chunk config/size customized by the caller.
struct ArscBuild {
    std::vector<uint8_t> buf;
    size_t type_chunk_pos = 0;
};

static ArscBuild build_arsc(size_t type_chunk_bytes, uint32_t config_size_claim,
                            size_t config_real_bytes) {
    // config_real_bytes = 0 → the buffer ENDS at tp+20 (the 4 config-size
    // bytes deliberately do not exist — that IS the GP-RES-002 face).
    // Otherwise the buffer ends at tp+20+config_real_bytes.
    ArscBuild b;
    std::vector<uint8_t>& buf = b.buf;
    // table header (12)
    buf.resize(12, 0);
    put16(buf, 0, 0x0002);      // RES_TABLE_TYPE
    put16(buf, 2, 12);          // header_size
    put32(buf, 8, 1);           // package_count
    // global string pool (28 bytes, 0 strings)
    size_t gp = buf.size();
    buf.resize(gp + 28, 0);
    put16(buf, gp, 0x0001);
    put16(buf, gp + 2, 28);
    put32(buf, gp + 4, 28);
    put32(buf, gp + 8, 0);      // string_count
    // package chunk at 40
    size_t pk = buf.size();
    size_t cfg_field_bytes = (config_real_bytes == 0) ? 0 : 4;  // size word exists only if config does
    size_t type_chunk_avail = 20 + cfg_field_bytes + config_real_bytes;
    size_t pkg_total = 288 + type_chunk_avail;
    buf.resize(pk + pkg_total, 0);
    put16(buf, pk, 0x0200);     // RES_TABLE_PACKAGE_TYPE
    put16(buf, pk + 2, 288);    // header_size
    put32(buf, pk + 4, (uint32_t)pkg_total);
    put32(buf, pk + 8, 0x7f);   // package id
    put32(buf, pk + 268, 0);    // type_strings_off = 0
    put32(buf, pk + 276, 0);    // key_strings_off = 0
    // type chunk
    size_t tp = pk + 288;
    b.type_chunk_pos = tp;
    put16(buf, tp, 0x0201);
    put16(buf, tp + 2, 20);     // header_size
    put32(buf, tp + 4, (uint32_t)type_chunk_bytes);
    buf[tp + 8] = 1;            // type_id
    buf[tp + 9] = 0;            // flags (dense)
    buf[tp + 10] = 0;           // reserved
    put32(buf, tp + 12, 0);     // entry_count = 0
    put32(buf, tp + 16, 20);    // entries_start = 20
    if (cfg_field_bytes) {
        put32(buf, tp + 20, config_size_claim);
        // config bytes: language 'en', country 'US' (bytes 8..11 of config)
        buf[tp + 28] = 'e'; buf[tp + 29] = 'n';
        buf[tp + 30] = 'U'; buf[tp + 31] = 'S';
        buf.resize(tp + 20 + config_real_bytes);
    }
    // table total_size = whole buffer
    put32(buf, 4, (uint32_t)buf.size());
    return b;
}

// ── GP-RES-002: type chunk validated to 20 bytes, config_size read at p+20 ──
bool probe_res002() {
    ArscBuild b = build_arsc(20, 0, 0);   // no config bytes present at all
    ArscParser p;
    bool ok = p.parse(b.buf);
    printf("[GP-RES-002] arsc parse ok=%d err=%s\n", (int)ok,
           p.last_error().c_str());
    return true;
}

// ── GP-RES-003: config_to_string trusts embedded size over cfg_size ──
bool probe_res003() {
    // 12 real config bytes, embedded size claim 36 → pre-fix reads cfg[26..35]
    ArscBuild b = build_arsc(32, 36, 12);
    ArscParser p;
    bool ok = p.parse(b.buf);
    printf("[GP-RES-003] arsc parse ok=%d err=%s\n", (int)ok,
           p.last_error().c_str());
    return true;
}

int main() {
    probe_res001();
    probe_res001_alloc();
    probe_res002();
    probe_res003();
    printf("[PROBES-DONE]\n");
    return 0;
}
